# Bug Report: Standalone `.app` frozen on landing page when launched from Finder

**Date discovered:** 2026-04-24
**Branch:** feature/stand-alone-build
**Severity:** High — standalone `.app` unusable when double-clicked, even though the same binary worked from a terminal

---

## Symptoms

The built `dist/ARIbrain.app` behaved differently depending on how it was
launched:

| Launch method | Result |
|---|---|
| `dist/ARIbrain.app/Contents/MacOS/ARIbrain` from a terminal (any `cwd`) | App works end-to-end |
| Double-click `ARIbrain.app` in Finder | App opens, data-loading page appears, clicking **Next** does nothing — UI frozen |

No visible error. The app process stayed alive; the landing page just refused
to transition to the main UI. No traceback in `Console.app` or `log stream`.
Every run of the app from dev (`.venv`) and from the pipx `install.sh`
workflow had always worked — only the standalone `.app` from Finder was
affected.

## Root cause

Two independent bugs, both latent for months, both exposed only when the
process environment matched what launchd gives a double-clicked `.app` (no
shell env, `cwd=/`). Fixing the first one uncovered the second.

### Bug 1: premature `setup_viewer()` in `load_bg`

`ari_application/models/nifti_loader.py` ended `load_bg` with:

```python
if hasattr(self, 'metrics'):
    self.metrics.show_metrics()
OrthViewSetup(self.brain_nav).setup_viewer()
```

`load_bg` runs at [main_window.py:143](../../ari_application/ui/main_window.py#L143)
during `BrainNav.__init__`. `setup_viewer()` accesses
`self.brain_nav.axial_crosshair_h`, but the crosshair widgets are created
later by `init_panes()` at
[main_window.py:235](../../ari_application/ui/main_window.py#L235) — after
`load_bg` has already returned.

So every fresh-start launch threw
`AttributeError: 'BrainNav' object has no attribute 'axial_crosshair_h'`
from inside `load_bg`. The surrounding `try/except Exception` swallowed it
and just printed `Error in load_bg: ...`. `BrainNav.__init__` continued,
`init_panes()` ran, and `runARI()` later called `setup_viewer()` a second
time — which succeeded, because by then the crosshairs existed.

In dev and from terminal, the first (failed) call and the second
(successful) call together produced a working UI. Under Finder launch
something in the Qt event-loop / activation timing after the silent
failure prevented the UI transition from completing.

Additionally, `if hasattr(self, 'metrics')` was dead code: `self` is the
`NiftiLoader` instance, which never has a `metrics` attribute — this
branch never ran.

### Bug 2: `ErrorHandler` writing to a relative path

`ari_application/error_handling/ErrorHandler.py` opened the log file with
whatever path the caller passed in:

```python
handler = logging.FileHandler(log_file)
```

The one live caller passed a bare filename:

```python
# ari_application/ui/components/upload_files.py:56
self.error_handler = ErrorHandler(log_file='upload_files_errors.log')
```

Terminal launches inherit the shell's `cwd` — usually the repo root or the
user's home, both writable. The log file just landed wherever the app was
run from, and nobody noticed (the crumb file `upload_files_errors.log` was
visible in the repo root for months).

Finder-launched `.app`s get `cwd=/` from launchd. The relative path
resolves to `/upload_files_errors.log`, and `/` is read-only on modern
macOS, so `FileHandler.__init__` raised:

```
OSError: [Errno 30] Read-only file system: '/upload_files_errors.log'
```

This crashed `UploadFiles.__init__`, which crashed `BrainNav.__init__`,
which bubbled into the `next_button_pressed` slot — where PyQt5 caught it
silently. Result: clicking **Next** appeared to do nothing.

## Why it was never an issue in dev or in `install.sh` installs

Three overlapping reasons, none obvious in isolation:

1. **`cwd` is always writable in dev / CLI launches.** The relative
   `upload_files_errors.log` path worked by accident — the terminal's
   current directory happened to be writable every time.
2. **Silent exception handlers hid the first bug.** The `Error in load_bg`
   message was printed on every single launch but never raised. Nobody
   looked for it because the app still reached a working state.
3. **Qt event-loop timing differs between launch methods.** A sequence
   that arrives at a working UI from the terminal can get stuck when
   launched via launchd. Same binary, same Python — different life cycle.

Bug 1 stayed hidden because dev launches always recovered downstream.
Bug 2 stayed hidden because dev launches never ran with a read-only
`cwd`. The standalone-from-Finder scenario is the first environment
where both conditions collided.

## Why fixing bug 1 exposed bug 2

Once `setup_viewer()` no longer ran prematurely in `load_bg`,
`BrainNav.__init__` progressed further on Finder launch — far enough to
hit `UploadFiles.__init__` and the `ErrorHandler` constructor, which then
blew up on the read-only filesystem. Each layer revealed the next,
initially giving the misleading impression of a regression.

## The fix

Two changes.

**`ari_application/models/nifti_loader.py`** — remove the premature block
from `load_bg`:

```diff
-            # Display metrics and set up the viewer
-            # Metrics.show_metrics(self.brain_nav)
-            if hasattr(self, 'metrics'):
-                self.metrics.show_metrics()
-            OrthViewSetup(self.brain_nav).setup_viewer()
-
             except Exception as e:
```

`runARI()` still calls `setup_viewer()` after populating
`aligned_templateInfo` — which is the correct place for it, since
`update_slices` depends on that dict being populated.

**`ari_application/error_handling/ErrorHandler.py`** — resolve non-absolute
log paths against a user-writable directory:

```python
def _log_dir():
    if sys.platform == 'darwin':
        return os.path.expanduser('~/Library/Logs/ARIbrain')
    return os.path.expanduser('~/.aribrain/logs')


class ErrorHandler:
    def __init__(self, log_file):
        if not os.path.isabs(log_file):
            log_dir = _log_dir()
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, log_file)
        ...
```

Callers unchanged. Logs now land in `~/Library/Logs/ARIbrain/` on macOS
regardless of `cwd`.

## Impact

- **User-facing:** standalone `.app` double-clicked from Finder now
  behaves identically to terminal launch and dev runs.
- **Non-visible:** the `Error in load_bg: 'BrainNav' object has no
  attribute 'axial_crosshair_h'` message that every launch had been
  printing for months is gone. Every fresh-start run had been doing one
  wasted `setup_viewer()` attempt that silently failed and was then
  redone by `runARI()` — ordinary users never saw this, but it was
  clutter in stdout and a ticking time bomb: any future refactor that
  reordered `runARI()` or removed its second `setup_viewer()` call would
  have broken the app with no clear trace of why.
- **Diagnostic lesson:** broad `try/except Exception` blocks that just
  print an error are a stronger anti-pattern in GUI apps than in
  scripts — they hide bugs that downstream timing happens to paper over,
  and the symptoms only surface in environments (like Finder launch)
  that don't paper over them.

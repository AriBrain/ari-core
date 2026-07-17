# Error logging refactor

Branch: `feature/enhanced-error-logging`

This change unifies error reporting around the in-app message log so that
errors users care about actually reach them, while keeping a persistent
on-disk record for post-mortem.

## What changed

### `MessageLogger` — full rewrite

[ari_application/ui/components/message_box.py](../ari_application/ui/components/message_box.py)

- Four leveled methods replace the single `log_message()`:
  - `info(msg, *, html=False)` — neutral status
  - `warn(msg, *, html=False)` — orange, prefixed `[WARN]`
  - `error(msg, *, exc_info=None, html=False)` — red, prefixed `[ERROR]`;
    `exc_info=True` or a `(type, value, tb)` tuple attaches a traceback to
    both the UI and the file log
  - `debug(msg, *, html=False)` — gray, prefixed `[DEBUG]`; only renders in
    the UI when `debug_enabled` is set, always writes to file
- Each row is timestamped (`[HH:MM:SS]`) and color-coded per level.
- A `logging.FileHandler` at `~/.aribrain/aribrain.log` records every
  leveled call, plain text, regardless of UI readiness.
- Messages emitted before `init_message_box()` builds the `QTextEdit` are
  buffered and flushed when the widget exists. Subsystems can therefore log
  during `BrainNav.__init__` without crashing.
- A re-entrancy guard (`_rendering`) prevents recursion if a render itself
  fails.
- The most recent instance is exposed as `MessageLogger.get_active()` for
  the global excepthook.
- `log_message()` is preserved as a thin shim to `info(..., html=True)` so
  any code that still calls it keeps working.

### Global `sys.excepthook`

[ari_application/main.py](../ari_application/main.py)

`_install_excepthook()` runs before `QApplication` is created. The hook:

1. Calls the default `sys.excepthook` first, so the traceback still reaches
   stderr and any attached debugger.
2. Looks up `MessageLogger.get_active()` and pushes
   `error("Uncaught …", exc_info=(…))` to it.

Uncaught exceptions in Qt slots used to die silently — now they surface in
the in-app log with a traceback.

### Migration: happy-path calls

Every existing `log_message(...)` call in the following files was migrated
to the leveled API. Inline `<span style="color: ...">` wrappers were
dropped where the level conveys the color; the green "success" spans were
collapsed to plain `info(...)` calls.

- [save_and_export.py](../ari_application/ui/components/save_and_export.py) — 10 sites
- [whole_brain_thresholding.py](../ari_application/ui/components/tabs/whole_brain_thresholding.py) — 8 sites
- [metrics.py](../ari_application/models/metrics.py) — 9 sites (incl. cluster history banners)
- [left_side_bar.py](../ari_application/ui/components/left_side_bar.py) — 2 sites
- [three_d_viewer.py](../ari_application/ui/components/three_d_viewer.py) — 2 sites
- [cluster_work_station.py](../ari_application/ui/components/cluster_work_station.py) — 4 sites

### Migration: silent errors

Bare `except:` clauses and `print()`-only error paths now route to the UI
logger:

- [nifti_loader.py](../ari_application/models/nifti_loader.py) — `load_bg`,
  `load_data_as_bg`, `load_overlay`, `check_file_type` all call
  `message_box.error(..., exc_info=True)` on failure instead of printing.
- [metrics.py](../ari_application/models/metrics.py) — the no-op
  `MNI_xyzs [0, 0, 0]` bug at lines 894 and 914 (latent
  `NameError`/silent-corruption hazard) was replaced with a real fallback
  + `message_box.warn(...)`. Bare `except:` tightened to
  `except Exception`. High-frequency crosshair-tick fallbacks at lines 79
  and 120 stay silent (commented why) to avoid log spam on every mouse
  move.
- [ui_helpers.py](../ari_application/ui/components/ui_helpers.py) —
  `refresh_ui`'s `except: print("No table data to update")` now calls
  `message_box.debug(...)`.
- [cluster_work_station.py](../ari_application/ui/components/cluster_work_station.py)
  — TDP-validation prints replaced with `message_box.warn(...)`.

### `ErrorHandler` removed

The file-logging responsibility now lives entirely in `MessageLogger`, so
the parallel `ErrorHandler` class was redundant.

- [ari_application/error_handling/ErrorHandler.py](../ari_application/error_handling/) — **deleted**
- [upload_files.py](../ari_application/ui/components/upload_files.py) —
  no longer instantiates `ErrorHandler`; both `except` blocks call
  `message_box.error(..., exc_info=True)` directly.
- [image_processing.py](../ari_application/models/image_processing.py) —
  dead `ErrorHandler` import removed.

## Smoke checks performed

Headless PyQt verification (no full app launch):

- All migrated modules import cleanly.
- `MessageLogger` buffers pre-init writes and flushes them on
  `init_message_box()`.
- Post-init writes append directly to the widget.
- `MessageLogger.get_active()` returns the most recent instance.
- A `FileHandler` is attached to the file logger.
- `_install_excepthook()` correctly routes a synthesised `RuntimeError` to
  both stderr and the UI logger, including the traceback.

## Manual verification suggested

1. **Threshold a map** — message log shows `[INFO]` lines for TDP/Z-score
   changes, `[WARN]` (orange) when slider limits are hit, `[ERROR]` (red)
   on invalid text input.
2. **Force an upload failure** (point at a missing/corrupt NIfTI) — error
   appears in the in-app log with a traceback, and in
   `~/.aribrain/aribrain.log`.
3. **Force an uncaught exception** in a slot — the excepthook surfaces it
   instead of silently dying.

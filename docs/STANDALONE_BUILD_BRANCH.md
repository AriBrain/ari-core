# Standalone Build Branch — `feature/stand-alone-build`

## What this branch is for

Making the PyInstaller-based standalone `ARIbrain.app` for macOS work
correctly. The app bundles Python, all dependencies, compiled Cython
extensions, and data files (templates, atlases, logos) into a single `.app`
that end users can run without installing Python.

## What's been done

### Committed (`a4d7560`)

- **`aribrain.spec`** — PyInstaller build config, now tracked in git
- **`docs/BUILD_INSTRUCTIONS.md`** — step-by-step guide for building the
  standalone app
- **`docs/USER_GUIDE.md`** — end-user documentation
- **`.gitignore`** — added `!aribrain.spec` negation so the spec file is
  tracked

### Uncommitted (in working tree, ready to commit)

**1. Path resolution fix — `get_package_dir()` helper**

The standalone app crashed because the code used
`os.path.dirname(__file__) + '../public/...'` to locate templates, atlases,
and logos. Inside the `.app` bundle, `__file__` resolves to a different
directory structure than in dev mode, so those paths broke.

Fix: added `get_package_dir()` in `ari_application/__init__.py` that returns
`sys._MEIPASS` when running frozen (PyInstaller) and `os.path.dirname(__file__)`
in dev mode. Updated 7 references across 4 files:

| File | What changed |
|---|---|
| `ari_application/__init__.py` | Added `get_package_dir()` helper |
| `ari_application/main.py` | Icon path uses `get_package_dir()` |
| `ari_application/ui/splash_screen.py` | Logo path uses `get_package_dir()` |
| `ari_application/ui/start_window.py` | Template dir, template mask, and background logo paths use `get_package_dir()` |
| `ari_application/models/nifti_loader.py` | Atlas and codebook paths use `get_package_dir()` |

**2. `data_bg_index` guard — `main_window.py`**

When the template path failed (bug #1), `load_bg` caught the exception and
returned early. `data_bg_index` was never set. Then line 267
`self.metrics.show_metrics()` ran unconditionally and crashed with
`AttributeError: 'BrainNav' object has no attribute 'data_bg_index'`.

Fix: changed the unconditional `show_metrics()` call at line 267 to only run
when `data_bg_index` exists (`elif hasattr(self, 'data_bg_index')`). This is
a safety net — with bug #1 fixed, `load_bg` completes and sets
`data_bg_index` normally. But if anything else goes wrong during init, the
app won't crash.

**3. `launch.json` — `justMyCode` toggle**

Changed `justMyCode` from `false` to `true` to avoid debugpy overhead on
Cython extensions, which was causing intermittent segfaults during debugging.

## What still needs to be done

### On this branch

- [ ] **Commit the working tree changes** (path resolution fix +
  data_bg_index guard + launch.json)
- [ ] **Rebuild the standalone app** and test:
  ```bash
  pipx reinstall aribrain
  ~/.local/pipx/venvs/aribrain/bin/pyinstaller aribrain.spec
  dist/ARIbrain.app/Contents/MacOS/ARIbrain
  ```
- [ ] **Fix hardcoded pipx path in `aribrain.spec:8`**:
  ```python
  site_packages = '/Users/lucaspeek/.local/pipx/venvs/aribrain/lib/python3.10/site-packages'
  ```
  This only works on Lucas's machine. Needs to be parameterized (e.g.,
  derive from `sysconfig` or accept an env var).
- [ ] **Open PR** to main

### On separate branches (already done or in progress)

- [x] **Hommel indexing fix** — committed on `fix/hommel-zero-indexing`
  (`5e2761b`), pushed. `np.arange(m)` → `np.arange(1, m + 1)` in
  `hommel.py:141`. See `docs/BUG_REPORT_hommel_indexing.md` on that branch.
- [x] **Dev environment setup** — merged to main via PR #3
  (`feature/debug-setup-logic`). VS Code debug config, `.venv` + editable
  install, `setup.py` absolute path fix, `docs/DEVELOPMENT.md`.

### Follow-up work (after merge)

- [ ] **Audit `discoveries[k-1]` vs `discoveries[k]`** in `hommel.py:153`.
  The indexing audit flagged this as potentially returning the penultimate
  count instead of the final count. Needs a test case to verify.
- [ ] **Delete `lucp88/ari-core` fork** on GitHub (leftover from earlier
  workflow experiment).

## How to rebuild after changes

1. Make sure the pipx venv has the latest code:
   ```bash
   pipx reinstall aribrain
   ```
2. Build:
   ```bash
   ~/.local/pipx/venvs/aribrain/bin/pyinstaller aribrain.spec
   ```
3. Test (launches with terminal output for debugging):
   ```bash
   dist/ARIbrain.app/Contents/MacOS/ARIbrain
   ```

## Error log from the standalone build (before fixes)

```
Error in load_bg: [Errno 2] No such file or directory:
  '.../ARIbrain.app/Contents/Frameworks/ari_application/ui/../public/templates'

Traceback (most recent call last):
  File "ari_application/ui/start_window.py", line 503, in next_button_pressed
    self.main_window = BrainNav(start_input)
  File "ari_application/ui/main_window.py", line 267, in __init__
    self.metrics.show_metrics()
  File "ari_application/models/metrics.py", line 88, in show_metrics
    if file_nr_template == self.brain_nav.data_bg_index:
AttributeError: 'BrainNav' object has no attribute 'data_bg_index'
```

Bug #1 (path resolution) caused bug #2 (data_bg_index). Fixing the paths
resolves both, but the `hasattr` guard provides defense in depth.

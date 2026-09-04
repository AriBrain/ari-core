# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

ARIbrain is a PyQt5 desktop application that performs All-Resolutions
Inference (ARI) on fMRI statistical maps and visualizes the result as
orthogonal slice views plus a 3D brain. Numerically heavy work
(`findDiscoveries`, `forestTDP`, cluster search) lives in C++ behind
Cython bindings; everything else is Python. Python is pinned to
`>=3.10.11, <=3.10.14` — Cython extensions are compiled against this
ABI and won't load on other versions.

## Common commands

### Dev environment (editable install)

```bash
python3.10 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

`pip install -e .` invokes `setup.py`, which uses `Cython.Build.cythonize`
to compile the two extension modules in-place. The `.so` files land next
to the `.pyx` sources at
`ari_application/cpp_extensions/cython_modules/`. After this, the venv
holds no copy of the package — it's an editable pointer back to the
source tree, so `.py` edits take effect on the next run without
reinstalling.

### Run

```bash
.venv/bin/aribrain                 # entry point defined in pyproject.toml
# equivalent:
.venv/bin/python -m ari_application.main
```

In VS Code: **Run and Debug → ARIbrain (debugpy)** uses
`.vscode/launch.json` (module-mode launch with `cwd=workspaceFolder`,
`justMyCode=false`).

### When to rerun `pip install -e .`

- After editing any `.pyx`, `.cpp`, or `.h` in
  `ari_application/cpp_extensions/`.
- After adding a dependency to `pyproject.toml`.
- After a fresh clone or a `git clean`.

Plain `.py` edits never require a reinstall.

### End-user install (pipx, what `install.sh` does)

```bash
curl -sSL https://raw.githubusercontent.com/AriBrain/ari-core/main/install.sh | bash
```

Installs a pipx venv at `~/.local/pipx/venvs/aribrain/` with a *copy* of
`ari_application` (not editable). End users get the `aribrain` CLI and
never touch the repo. To exercise the same path in dev: `pipx reinstall
aribrain`. See [README.md](README.md) for full installer details
including the Windows PowerShell flow.

## Mental model: two Python environments

Two independent installs of `ari_application` coexist on a dev machine
and conflating them is the most common source of confusion:

| Env | Where | Contents | Used for |
|---|---|---|---|
| Dev `.venv/` | repo root | editable install (`.pth` pointer back to source) | day-to-day work, debugger |
| pipx venv | `~/.local/pipx/venvs/aribrain/` | non-editable copy installed by `install.sh` | exercising the end-user install path |

Both read from `pyproject.toml`, so adding a dependency means editing
`pyproject.toml` and reinstalling whichever env needs it. See
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) section 3 for the full
"adding a dependency" checklist; the punchline is **commit the
`pyproject.toml` change in the same commit as the code that uses the
new dep**, or the next user `install.sh` will hit `ModuleNotFoundError`.

## High-level architecture

### Launch flow

```
ari_application/main.py
    main() → QApplication → SplashScreen → StartWindow
StartWindow                          (ui/start_window.py)
    user picks New Project / Load Project, configures inputs
    on "Next": BrainNav(start_input) → main_window.show() → runARI()
BrainNav                             (ui/main_window.py)
    central QMainWindow; holds ALL app state and ALL subsystem instances
pyARI.runARI()                       (analyses/ARI.py)
    runs the analysis, populates aligned_templateInfo, calls
    OrthViewSetup.setup_viewer() to display the result
```

### The `BrainNav` god-object pattern

`BrainNav.__init__` instantiates every subsystem and stores them as
attributes on `self`. Each subsystem is constructed with `self` (the
`BrainNav` instance) as its only argument and stores it as
`self.brain_nav`, so any subsystem can reach any other subsystem and any
piece of state by traversing back through `brain_nav`. Concretely:

```python
self.nifti_loader       = NiftiLoader(self)
self.orth_view_setup    = OrthViewSetup(self)
self.mouse_interactions = MouseInteractions(self)
self.orth_view_update   = OrthViewUpdate(self)
self.metrics            = Metrics(self)
self.upload_files       = UploadFiles(self)
self.image_processing   = ImageProcessing(self)
self.ARI                = pyARI(self)
# ...plus UI components: TblARI, UIHelpers, ThreeDViewer, WBTing,
# SaveAndExportTab, InitiateTabs, ClusterWorkStation, MessageLogger,
# LeftSideBar, OrthViewerControls, MenuBar
```

**Implications for changes:**
- Subsystems are tightly coupled through the shared `brain_nav`
  reference. Decoupling one usually means following `self.brain_nav.X`
  chains across multiple files.
- Init order in `BrainNav.__init__` matters. Anything that touches a
  later-initialized attribute will fail. Crosshair widgets, for
  example, are created inside `init_panes()` (called late in `__init__`);
  code that runs earlier must not call into `setup_viewer()` which
  touches them.
- State that downstream code reads — `file_nr`, `file_nr_template`,
  `templates`, `aligned_templateInfo`, `data_bg_index`, slice indices,
  `ui_params` — lives on `BrainNav` and is mutated from many places.
  Treat it as the shared mutable bus.

### Two project paths through `BrainNav.__init__`

`BrainNav(start_input, load_data=False, data2load=None)` branches:

- **Fresh start (`load_data=False`)** — empty dicts initialized, then
  `nifti_loader.load_overlay()` and `nifti_loader.load_bg()` populate
  `fileInfo`, `templates`, `atlasInfo`, `data_bg_index`. The orth views
  remain empty until `pyARI.runARI()` populates `aligned_templateInfo`
  and finally calls `setup_viewer()`.
- **Resume from a saved `.ari` project (`load_data=True`)** — all dicts
  are restored from the pickle passed in `data2load`. `setup_viewer()`
  is called directly at the end of `__init__` because the dicts are
  already populated.

The pattern `if hasattr(self, 'data_bg_index')` guards code that depends
on the fresh-start path having reached the point of populating it.

### Package layout

```
ari_application/
├── main.py            # entry point (QApplication, splash, start window)
├── ui/                # all Qt widgets
│   ├── main_window.py # BrainNav (central QMainWindow + app state)
│   ├── start_window.py
│   ├── splash_screen.py
│   └── components/    # left side bar, menu, 3D viewer, work station,
│       └── tabs/      # tables, whole-brain thresholding, etc.
├── models/            # data layer: nifti_loader, metrics, image_processing
├── controllers/       # mouse_interactions (Qt eventFilter + drag/pan/zoom)
├── orth_views/        # orth_view_setup, orth_view_update
│                      #   — the axial/sagittal/coronal slice viewers
├── analyses/          # ARI.py (orchestrator), hommel.py, getClusters.py,
│                      #   getAdjList.py, utils.py — Python wrappers over
│                      #   the Cython modules below
├── cpp_extensions/    # numerically heavy core
│   ├── cpp_sources/   # hommel.{cpp,h}, ARICluster.{cpp,h}
│   └── cython_modules/# .pyx bindings, plus compiled .so after build
├── error_handling/    # ErrorHandler (logging + traceback formatting)
├── resources/         # styles.py (Qt stylesheets)
└── public/            # bundled NIfTI templates, atlases (AAL2 etc.),
                       #   template masks, demo data, logos
```

The `controllers/`, `models/`, `ui/` split is loose — the architecture
is best understood as "Qt UI hanging off a central state object" rather
than strict MVC.

### Cython extensions

Two C++ modules are wrapped by Cython:

- **`hommel`** — `findDiscoveries`, `findalpha`, `findhull`,
  `adjustedElementary`, `findHalpha`, `findConcentration`. Used by both
  `analyses/hommel.py` (Python `pyHommel` class) and `analyses/ARI.py`.
- **`ARICluster`** — `forestTDP`, `heavyPathTDP`, `findClusters`,
  `queryPreparation`, `answerQuery*`, `descendants`, `findNeighbours`,
  voxel index/coord helpers. Used by `analyses/ARI.py`.

`setup.py` declares both as `setuptools.Extension`s and calls
`Cython.Build.cythonize`. Built with `-g -O0 -Wall` (debug-friendly,
not optimized for release).

**Watch for indexing conventions.** The C++ side of `hommel` expects
**1-based indices** (it does `allp[idx[i] - 1]` internally). The Python
caller in `analyses/hommel.py` must build `ix_sorted_p` with
`np.arange(1, m + 1)` not `np.arange(m)`. A 0-based call segfaults when
the smallest p-value is in the selection and silently returns wrong TDP
values otherwise. See
[docs/BUG_REPORT_hommel_indexing.md](docs/BUG_REPORT_hommel_indexing.md)
for the full incident. Apply the same scrutiny to any new array passed
into a Cython function — check whether the C++ side subtracts 1 before
indexing.

### Resource loading

Templates, atlases, masks, and logos live under
`ari_application/public/`. Code paths that need them typically build
the path from the module location:

```python
os.path.join(os.path.dirname(__file__), '..', 'public', '...')
```

This works in dev because `__file__` resolves to the source tree.

### Project save/load (`.ari`)

`SaveAndExportTab.save_project` (in `ui/components/save_and_export.py`)
pickles a dict containing `fileInfo`, `atlasInfo`, `templates`,
`statmap_templates`, `aligned_templateInfo`, `aligned_statMapInfo`,
`ui_params`, file/template indices, and `data_bg_index`. `StartWindow.
load_project` unpickles it and hands it to `BrainNav` as `data2load`.
Any new top-level attribute on `BrainNav` that needs to persist must be
added to both ends, or loading old projects will break.

### Error logging

`error_handling/ErrorHandler.py` wraps `logging.FileHandler`. The only
live instantiation is in `ui/components/upload_files.py` with
`log_file='upload_files_errors.log'`. Errors that go through
`handle_exception` are written to the log file and the traceback is
printed to stdout. Many call sites instead use bare
`try/except Exception as e: print(...)`; that pattern hides bugs that
later code happens to paper over, so prefer raising or routing through
`ErrorHandler` for anything non-trivial.

## Conventions and gotchas

- **No test suite.** There is one ad-hoc smoke file at
  `ari_application/cpp_extensions/cython_modules/test_hommel.py` but no
  pytest harness, no CI tests, no fixtures. Verification is currently
  by running the app and clicking through.
- **No linter / formatter configured.** Match local style in whatever
  file you're editing.
- **`.env` is loaded** in `main_window.py` via `dotenv.load_dotenv()`.
  Used at least for `PYDEVD_WARN_EVALUATION_TIMEOUT`. Don't commit
  `.env` files.
- **Theme is dark, fixed.** `qdarktheme.setup_theme("dark")` in
  `main.py`. Light theme is not exercised — Qt stylesheets in
  `resources/styles.py` assume dark backgrounds.
- **The app opens fullscreen** via
  `QDesktopWidget().screenGeometry()` in `BrainNav.__init__`. On
  multi-monitor setups it picks the primary screen.

## Pointers to deeper docs

- [README.md](README.md) — end-user install (macOS, Linux, Windows) and
  contributing workflow.
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) — dev environment setup,
  debugger config, adding a Python dependency, troubleshooting.
- [docs/BUG_REPORT_hommel_indexing.md](docs/BUG_REPORT_hommel_indexing.md)
  — full write-up of the Cython 1-based vs 0-based indexing incident.
- [architecture.txt](architecture.txt) — flat tree of the package
  layout (slightly out of date, treat as orientation only).

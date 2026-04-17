# ARIbrain Development Guide

This guide covers the day-to-day development workflow: setting up a working
dev environment, running the app with a debugger attached, and managing
Python dependencies so that end-users and the standalone `.app` stay in sync
with what you're building against.

For end-user installation, see the top-level [README.md](../README.md).
For building the macOS standalone app, see [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md).

---

## The mental model

There are two independent Python environments in play, and keeping them
straight is the whole trick:

1. **The end-user environment** — a pipx venv at
   `~/.local/pipx/venvs/aribrain/`, created by `install.sh` / `install.ps1`.
   It contains a *copy* of `ari_application` in its site-packages. End users
   never touch the repo.

2. **The developer environment** — a `.venv/` at the repo root, created by
   you (see step 1 below). Instead of a copy, it contains an *editable
   install* pointer back to `ari-core/ari_application/`. Every edit you make
   is picked up on the next Python run — no reinstall needed.

You want your dev environment (2) to behave as close as possible to the
end-user environment (1), so that bugs you catch while developing are the
same bugs end-users would hit. The single source of truth for "what should
be installed" is [`pyproject.toml`](../pyproject.toml); both environments
read from it.

---

## 1. One-time setup

These steps assume you already cloned the repo.

### 1a. Create the dev venv and install the app editable

From the repo root:

```bash
python3.10 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

What each step does:

- `python3.10 -m venv .venv` creates an isolated Python 3.10 environment at
  `.venv/` inside the repo. It's gitignored (`.venv/` is in `.gitignore`),
  so it never gets committed. Roughly 400–700 MB once populated.
- `pip install --upgrade pip` bumps pip to a version that understands modern
  `pyproject.toml` metadata.
- `pip install -e .` reads `pyproject.toml`, finds the
  `setuptools.build_meta` backend, runs `setup.py` to compile the Cython
  extensions (`ARICluster`, `hommel`) *in place* — dropping
  `.cpython-310-darwin.so` files next to the `.pyx` sources — and then
  writes a `.pth` pointer in `.venv/lib/python3.10/site-packages/` that
  redirects any `import ari_application` back to the source tree. No second
  copy on disk.

After this, the dev venv has exactly one physical copy of `ari_application`
(the source tree), and edits to `.py` files take effect immediately on the
next run. You only need to rerun `pip install -e .` when you change a
`.pyx`, `.cpp`, or `.h` file in `ari_application/cpp_extensions/`, or when
you add a new dependency to `pyproject.toml` (see section 3).

### 1b. Point VS Code at the dev venv

`.vscode/settings.json` already sets `python.defaultInterpreterPath` to
`${workspaceFolder}/.venv/bin/python`, so in most cases VS Code picks it up
automatically. If it doesn't:

1. `Cmd+Shift+P` → **Python: Select Interpreter**.
2. Pick `./.venv/bin/python`. If it's not in the list, use
   **Enter interpreter path → Find...** and navigate to it.

VS Code remembers the selection in its workspace state.

---

## 2. Running the app with the debugger

1. Open the **Run and Debug** panel (`Cmd+Shift+D`).
2. In the dropdown at the top, pick **ARIbrain (debugpy)**.
3. Press `F5` (or click the green play arrow).

The app launches exactly like `aribrain` from the command line, but with
breakpoints, watch expressions, step in/over/out, and exception pausing all
available. Tracebacks print to the *Debug Console* and the *Terminal* panel.

Relevant launch options (in `.vscode/launch.json`):

- **`justMyCode: false`** — lets you step into third-party libraries (PyQt5,
  numpy, pyqtgraph, etc.). Flip to `true` if that's distracting.
- **`module: ari_application.main`** — the debugger runs
  `python -m ari_application.main` from the workspace root, matching how
  the installed `aribrain` entry point invokes the app.
- **`cwd: ${workspaceFolder}`** — working directory is the repo root, so
  any relative paths the app uses resolve the way they would in a normal
  run.

There's no `python` key in `launch.json` — the debugger uses whichever
interpreter VS Code has selected, which should be `.venv/bin/python`.

---

## 3. Adding a Python dependency

The single source of truth for dependencies is
[`pyproject.toml`](../pyproject.toml). Everything flows from there:

- **End users** running `install.sh` / `install.ps1` get dependencies via
  `pipx install`, which reads `pyproject.toml`.
- **The standalone macOS `.app`** is built by PyInstaller from whatever is
  installed in the venv you build it from — which should match
  `pyproject.toml`.
- **Your dev venv** also reads `pyproject.toml` when you run
  `pip install -e .`, so adding a dep there keeps all three in sync.

### Workflow when adding a library

1. **Install into your dev env immediately** so you can start using it:

   ```bash
   .venv/bin/pip install <library-name>
   ```

2. **Try it out.** Write the code that uses it. Confirm it actually solves
   your problem and you want to keep the dependency.

3. **Add it to [`pyproject.toml`](../pyproject.toml)** under the
   `dependencies` list. Pin a version only if you have a specific
   compatibility reason — otherwise leave it unpinned so pip resolves a
   current version at install time.

4. **Commit the code change and the `pyproject.toml` update together.**
   They must land in the same commit, otherwise you'll break the next
   person (or future-you) who runs `install.sh`.

5. **(Optional but recommended) Simulate a fresh install** to catch
   discrepancies between your dev env and what a clean user would get:

   ```bash
   pipx reinstall aribrain
   ```

   This blows away the pipx venv and rebuilds from the current
   `pyproject.toml`. If the `aribrain` CLI still works afterwards,
   end-users are covered. If it breaks, something is installed in your
   dev env that isn't declared in `pyproject.toml`.

### Why this matters

The risk of skipping step 3 is the classic "works on my machine" failure:
you add a library manually to your venv, forget to update `pyproject.toml`,
and commit the feature. Next time anyone runs `install.sh` they hit
`ModuleNotFoundError` — but *you* don't, because your dev env still has the
library from step 1. The `pipx reinstall` in step 5 is the fastest way to
catch this before shipping.

### Removing a dependency

Reverse order: remove from `pyproject.toml`, then
`.venv/bin/pip uninstall <library-name>` (and optionally
`pipx reinstall aribrain` to clean it out of the pipx venv too).

---

## 4. Building the standalone `.app`

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md). Key thing to remember:
PyInstaller bundles whatever is in the pipx venv at build time, so make sure
you've done a `pipx reinstall aribrain` (or at least installed any new deps
into that venv) before running the build. The dev `.venv/` is not used for
building the standalone app.

---

## 5. Troubleshooting

**`ModuleNotFoundError: No module named 'ari_application.cpp_extensions.cython_modules.ARICluster'`**
— The Cython extensions weren't built into the source tree. Rerun
`.venv/bin/pip install -e .` from the repo root.

**`ModuleNotFoundError: No module named 'qdarktheme'` (or any other declared dependency)**
— VS Code is running the wrong Python interpreter. Use
**Python: Select Interpreter** to pick `.venv/bin/python`, then restart
the debugger.

**Breakpoints set in source files aren't being hit**
— You're probably running a different copy of the code. Check that
`launch.json` uses `"module"` (not `"program"`) and that `"cwd"` is
`"${workspaceFolder}"`. With those settings and the editable install in
place, Python imports resolve to the source tree and breakpoints bind
correctly.

**Code changes don't take effect on restart**
— Stale `__pycache__` directories. Delete them:
`find . -name __pycache__ -type d -exec rm -rf {} +`. They're gitignored so
this is safe.

**`pip install -e .` fails with "setup script specifies an absolute path"**
— Modern setuptools rejects absolute paths in `setup()` arguments. If
you're editing `setup.py`, keep all source paths relative to the repo root.

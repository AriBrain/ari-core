# ARIbrain macOS App Build Instructions

## Overview

This document describes how to build a standalone `ARIbrain.app` from the
ari-core repository using PyInstaller. The resulting `.app` bundles Python,
all dependencies, compiled Cython extensions, and data files (templates,
atlases, logos) into a single application that end users can run without
installing Python.

For day-to-day development setup (creating the `.venv`, running the app
with the debugger, adding dependencies), see
[DEVELOPMENT.md](DEVELOPMENT.md).

## Prerequisites

- macOS (ARM64 / Apple Silicon or x86_64)
- The dev `.venv/` set up per [DEVELOPMENT.md](DEVELOPMENT.md) section 1a
- PyInstaller — installed automatically via the `[build]` extra when you
  run `pip install -e ".[build]"`

## Build environment

The build runs out of the dev `.venv/`. [aribrain.spec](../aribrain.spec)
locates the `ari_application` package by importing it, so whichever Python
executes PyInstaller must have the package installed — which is already
the case in `.venv` via the editable install. This also means the build
automatically picks up any changes you've made to the source tree: no
reinstall step is needed between code edits and a rebuild.

The compiled Cython extensions (`.so` files) live alongside the `.pyx`
sources in `ari_application/cpp_extensions/cython_modules/` after
`pip install -e ".[build]"`. The spec globs that directory, so any `.so`
found there is bundled.

## Build steps

### 1. (One-time) Set up the dev env

Follow [DEVELOPMENT.md section 1a](DEVELOPMENT.md#1a-create-the-dev-venv-and-install-the-app-editable).
The `[build]` extra installs PyInstaller.

### 2. Clean previous build artifacts

```bash
rm -rf build dist
```

PyInstaller's `--clean` flag clears its internal cache but does **not**
delete `build/` or `dist/`. For a release or verification build, remove
them manually so stale files from a previous run can't leak into the new
bundle.

### 3. Build the app

From the repo root:

```bash
.venv/bin/pyinstaller aribrain.spec --clean
```

Build takes a few minutes. `--clean` invalidates PyInstaller's cached
analysis so imports are re-resolved from scratch.

### 4. Output

- `dist/ARIbrain.app` — the standalone macOS application (~1 GB)
- `dist/ARIbrain/` — intermediate folder (safe to delete)
- `build/` — PyInstaller's build cache (safe to delete)

### 5. Create a distributable zip

```bash
cd dist
zip -r ARIbrain-macos.zip ARIbrain.app
```

## Testing

Run the app from the terminal so you see tracebacks if something crashes:

```bash
dist/ARIbrain.app/Contents/MacOS/ARIbrain
```

Or double-click `ARIbrain.app` in Finder for the normal user experience.

## Release builds

For a build you intend to publish on the website, do the build from a
fresh clone at a tagged commit so the artifact corresponds 1:1 with a
release tag, rather than from your working dev tree:

```bash
git clone https://github.com/AriBrain/ari-core.git /tmp/ari-core-release
cd /tmp/ari-core-release
git checkout v0.1.0                           # the tag you're releasing
python3.10 -m venv .build-venv
.build-venv/bin/pip install --upgrade pip
.build-venv/bin/pip install -e ".[build]"
.build-venv/bin/pyinstaller aribrain.spec --clean
cd dist && zip -r ARIbrain-v0.1.0-macos.zip ARIbrain.app
```

Reasons: no dev cruft from interactive experimentation, the build matches
a specific commit, and `/tmp/ari-core-release` is throwaway.

## Troubleshooting

### Missing Cython extensions at build time
If PyInstaller skips the `.so` files or the glob finds nothing:
- Confirm the extensions were compiled: `ls
  ari_application/cpp_extensions/cython_modules/*.so` should show at
  least `ARICluster.cpython-*.so` and `hommel.cpython-*.so`.
- If they're missing, rerun `.venv/bin/pip install -e ".[build]"` to
  trigger the Cython build.

### Missing imports at runtime
Add the module name to the `hiddenimports` list in
[aribrain.spec](../aribrain.spec) and rebuild.

### Missing resources
Add the source path to the `datas` list in
[aribrain.spec](../aribrain.spec) and rebuild. At runtime, the app
resolves resource paths via `get_package_dir()` in
[ari_application/__init__.py](../ari_application/__init__.py), which
returns `sys._MEIPASS` inside a frozen bundle.

## Notes

- The app is code-signed with an ad-hoc signature (sufficient for local
  use). For App Store distribution or notarization, additional signing
  with an Apple Developer certificate is required.

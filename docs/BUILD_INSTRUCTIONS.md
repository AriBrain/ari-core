# ARIbrain macOS App Build Instructions

## Overview

This document describes how to build a standalone `ARIbrain.app` from the ari-core repository using PyInstaller.

## Prerequisites

- macOS with ARM64 (Apple Silicon) or x86_64 architecture
- Python 3.10.14 installed via pipx with aribrain package
- PyInstaller 6.18.0+

## Build Environment

The build uses the existing pipx virtual environment where aribrain is installed:
- Python: `/Users/lucaspeek/.local/pipx/venvs/aribrain/bin/python`
- Site-packages: `/Users/lucaspeek/.local/pipx/venvs/aribrain/lib/python3.10/site-packages`

This environment contains the compiled Cython extensions (`.so` files) which are required for the app to run.

## Build Steps

### 1. Install PyInstaller in the pipx venv

```bash
/Users/lucaspeek/.local/pipx/venvs/aribrain/bin/python -m pip install pyinstaller
```

### 2. Create the spec file

The `aribrain.spec` file in the repo root configures the build. Key elements:

- **binaries**: Explicitly includes the compiled Cython extensions (`ARICluster.cpython-310-darwin.so`, `hommel.cpython-310-darwin.so`)
- **datas**: Includes resources, public assets, and the cpp_extensions directory
- **hiddenimports**: Lists all required modules including scientific libraries (numpy, scipy, pandas, nibabel, nilearn, pyvista, etc.)
- **console=False**: Creates a GUI app without terminal window
- **argv_emulation=True**: macOS-specific for proper app behavior

### 3. Build the app

```bash
cd /Users/lucaspeek/PostDocs/Weeda/ari-core
/Users/lucaspeek/.local/pipx/venvs/aribrain/bin/pyinstaller aribrain.spec --clean
```

### 4. Output

- `dist/ARIbrain.app` - The standalone macOS application (768MB)
- `dist/ARIbrain/` - Intermediate build folder (can be deleted)
- `build/` - Build cache (can be deleted)

### 5. Create distributable zip

```bash
cd dist
zip -r ARIbrain-macos.zip ARIbrain.app
```

Final zip size: ~762MB

## Testing

Run the app directly to test:

```bash
./dist/ARIbrain.app/Contents/MacOS/ARIbrain
```

Or double-click `ARIbrain.app` in Finder.

## Troubleshooting

### Missing Cython extensions
If you get `ModuleNotFoundError: No module named 'ari_application.cpp_extensions'`:
- Ensure you're building with the pipx Python that has the compiled extensions
- Verify the `.so` files exist in the pipx site-packages

### Missing imports at runtime
Add the module name to the `hiddenimports` list in `aribrain.spec` and rebuild.

### Missing resources
Add the path to the `datas` list in `aribrain.spec` and rebuild.

## Files Created

| File | Size | Description |
|------|------|-------------|
| `aribrain.spec` | 2KB | PyInstaller configuration |
| `dist/ARIbrain.app` | 768MB | Standalone macOS application |
| `dist/ARIbrain-macos.zip` | 762MB | Distributable archive |

## Known Issues

### Main UI not loading after landing screen

The app opens and allows loading data files, but clicking "Next" may not transition to the main UI. Likely causes:

1. **Missing resources/data files** - The main UI might need files from `public/` (templates, atlases) that aren't being found at runtime. The app looks for them relative to `__file__` which changes when bundled.

2. **Path resolution issue** - Code like this in `main.py:29`:
   ```python
   icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'public', 'logo.jpg'))
   ```
   Needs adjustment for PyInstaller. Bundled apps should use:
   ```python
   import sys
   if getattr(sys, 'frozen', False):
       base_path = sys._MEIPASS
   else:
       base_path = os.path.dirname(__file__)
   ```

3. **Silent exception** - The transition to main UI might be throwing an error that's being swallowed. Test with console output to see tracebacks:
   ```bash
   ./dist/ARIbrain.app/Contents/MacOS/ARIbrain
   ```

## Notes

- The app is code-signed with ad-hoc signature (sufficient for local use)
- For distribution via App Store or notarization, additional signing with Apple Developer certificate is required
- Build tested on macOS 26.2 (arm64)

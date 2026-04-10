# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

site_packages = '/Users/lucaspeek/.local/pipx/venvs/aribrain/lib/python3.10/site-packages'
cython_dir = os.path.join(site_packages, 'ari_application/cpp_extensions/cython_modules')

hidden_imports = collect_submodules('ari_application') + [
    'nibabel', 'nilearn', 'scipy', 'pandas', 'numpy',
    'pyqtgraph', 'pyvista', 'pyvistaqt', 'PyQt5',
    'cython', 'dotenv', 'qdarktheme',
    'ari_application.cpp_extensions',
    'ari_application.cpp_extensions.cython_modules',
    'ari_application.cpp_extensions.cython_modules.ARICluster',
    'ari_application.cpp_extensions.cython_modules.hommel',
]

binaries = [
    (os.path.join(cython_dir, 'ARICluster.cpython-310-darwin.so'), 'ari_application/cpp_extensions/cython_modules'),
    (os.path.join(cython_dir, 'hommel.cpython-310-darwin.so'), 'ari_application/cpp_extensions/cython_modules'),
]

datas = collect_data_files('ari_application') + [
    ('ari_application/resources', 'ari_application/resources'),
    ('ari_application/public', 'ari_application/public'),
    (os.path.join(site_packages, 'ari_application/cpp_extensions'), 'ari_application/cpp_extensions'),
]

a = Analysis(
    ['ari_application/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ARIbrain',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ARIbrain',
)

app = BUNDLE(
    coll,
    name='ARIbrain.app',
    icon=None,
    bundle_identifier='org.aribrain.app',
    info_plist={
        'CFBundleName': 'ARIbrain',
        'CFBundleDisplayName': 'ARIbrain',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHighResolutionCapable': True,
    },
)

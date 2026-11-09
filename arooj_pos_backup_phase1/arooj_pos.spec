# -*- mode: python ; coding: utf-8 -*-
# PyInstaller Spec File for Arooj Cloth and Bedsheet Parda Desktop POS

import sys
import os
from pathlib import Path

block_cipher = None
project_dir = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(project_dir, 'app', 'resources'), 'app/resources'),
    (os.path.join(project_dir, 'app', 'migrations'), 'app/migrations'),
    (os.path.join(project_dir, 'app', 'seed'), 'app/seed'),
]

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'sqlite3',
        'decimal',
        'hashlib',
        'shutil',
        'json',
        'datetime',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'app.migrations._001_initial_schema',
        'app.seed.initial_catalog'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
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
    name='Arooj_POS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed desktop application (no cmd prompt on launch)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_dir, 'app', 'resources', 'icons', 'app_icon.ico') if os.path.exists(os.path.join(project_dir, 'app', 'resources', 'icons', 'app_icon.ico')) else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Arooj_POS',
)

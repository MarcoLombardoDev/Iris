# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for Iris - Email Sender.

Usage:  pyinstaller Iris.spec

No absolute path of a development machine is hard-coded here, and the
ttkbootstrap resources are collected automatically with collect_all().

WARNING: do not run `pyinstaller --name=Iris main.py` from the project
folder — it would overwrite this file with a generated one containing absolute
paths. Use `python build.py`, which writes the temporary spec into build/.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.scrolledtext',
    'fitz', 'openpyxl', 'xlrd', 'docx',
    'PIL', 'PIL.Image', 'PIL.ImageTk',
    # Required at runtime by PIL.ImageTk (see build.py).
    'PIL._tkinter_finder',
    'iris.gui',
    'iris', 'iris.config_store', 'iris.i18n',
    'iris.mailer', 'iris.msgwriter', 'iris.parsers',
    'iris.paths', 'iris.version',
]

# Optional resources: bundled only when present in the project folder.
for resource in (os.path.join('assets', 'app_icon.ico'), os.path.join('assets', 'app_icon.png')):
    if os.path.exists(resource):
        datas.append((resource, 'assets'))

# ttkbootstrap is optional: without it the app falls back to the ttk theme.
try:
    tb_datas, tb_binaries, tb_hiddenimports = collect_all('ttkbootstrap')
    datas += tb_datas
    binaries += tb_binaries
    hiddenimports += tb_hiddenimports
except Exception:
    pass

# .msg generation through Outlook only exists on Windows.
if sys.platform.startswith('win'):
    hiddenimports += [
        'win32com', 'win32com.client', 'win32com.client.gencache',
        'pythoncom', 'win32timezone',
    ]

icon_path = os.path.join('assets', 'app_icon.ico')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'PyQt6',
        'PySide2', 'PySide6', 'jupyter', 'IPython', 'sphinx', 'pytest',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Iris',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[icon_path] if os.path.exists(icon_path) else None,
)

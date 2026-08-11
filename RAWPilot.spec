# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["run_rawpilot.py"],
    pathex=["."],
    binaries=[],
    datas=[("lightroom_plugin", "lightroom_plugin")],
    hiddenimports=["rawpy", "exifread", "PIL._tkinter_finder"],
    hookspath=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="RAWPilot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

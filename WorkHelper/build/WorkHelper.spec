# -*- mode: python ; coding: utf-8 -*-
# Build:
#   pyinstaller build/WorkHelper.spec
# Or from project root:
#   pyinstaller --onefile --windowed --name WorkHelper \
#     --add-data "assets;assets" --add-data "data;data" \
#     --add-data "version.txt;." main.py

a = Analysis(
    ['../main.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../assets', 'assets'),
        ('../data', 'data'),
        ('../version.txt', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui',
        'pyperclip', 'keyboard', 'pynput', 'pyautogui', 'plyer',
        'plyer.platforms.win.notification',
        'PIL', 'PIL.Image', 'PIL.ImageQt',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WorkHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # windowed mode (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='../assets/icons/app.ico',  # uncomment when icon is ready
)

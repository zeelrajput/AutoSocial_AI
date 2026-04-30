# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['local_agent\\agent.py'],
    pathex=['D:\\blockchain_internshipe\\Autosocial_ai platform\\Autosocial_ai'],
    binaries=[],
    datas=[],
    hiddenimports=['automation_engine', 'automation_engine.executor.task_runner', 'automation_engine.browser.browser_manager'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

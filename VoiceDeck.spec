# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('voicedeck', 'voicedeck'), ('config.example.toml', '.')]
binaries = []
hiddenimports = ['voicedeck', 'voicedeck.main', 'voicedeck.config', 'voicedeck.gui', 'voicedeck.gui.main_window', 'voicedeck.gui.settings_dialog', 'voicedeck.gui.styles', 'voicedeck.gui.widgets', 'voicedeck.gui.widgets.record_button', 'voicedeck.gui.widgets.level_meter', 'voicedeck.gui.widgets.led_indicator', 'voicedeck.audio', 'voicedeck.audio.recorder', 'voicedeck.stt', 'voicedeck.stt.base', 'voicedeck.stt.openai_client', 'voicedeck.keyring_storage', 'scipy.io', 'scipy.io.wavfile', 'numpy', 'keyring.backends', 'keyring.backends.SecretService', 'secretstorage']
tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('keyring')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='VoiceDeck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceDeck',
)

# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all

datas = [('voicedeck', 'voicedeck'), ('config.example.toml', '.')]
binaries = []
hiddenimports = [
    'voicedeck', 'voicedeck.main', 'voicedeck.config',
    'voicedeck.gui', 'voicedeck.gui.main_window',
    'voicedeck.gui.settings_dialog', 'voicedeck.gui.styles',
    'voicedeck.gui.widgets', 'voicedeck.gui.widgets.record_button',
    'voicedeck.gui.widgets.level_meter', 'voicedeck.gui.widgets.led_indicator',
    'voicedeck.audio', 'voicedeck.audio.recorder',
    'voicedeck.stt', 'voicedeck.stt.base', 'voicedeck.stt.openai_client',
    'voicedeck.keyring_storage',
    'scipy.io', 'scipy.io.wavfile', 'numpy',
    'platformdirs',
    'keyring.backends',
]

# Platform-specific keyring backends
if sys.platform == 'linux':
    hiddenimports += ['keyring.backends.SecretService', 'secretstorage']
elif sys.platform == 'darwin':
    hiddenimports += ['keyring.backends.macOS']
elif sys.platform == 'win32':
    hiddenimports += ['keyring.backends.Windows']

tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('keyring')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Platform-specific icon
if sys.platform == 'win32':
    icon_file = 'assets/voicedeck.ico'
elif sys.platform == 'darwin':
    icon_file = 'assets/voicedeck.icns'
else:
    icon_file = 'assets/voicedeck.png'


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
    icon=icon_file,
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

# macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='VoiceDeck.app',
        icon=icon_file,
        bundle_identifier='com.voicedeck.app',
        info_plist={
            'CFBundleName': 'VoiceDeck',
            'CFBundleDisplayName': 'VoiceDeck',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSMicrophoneUsageDescription':
                'VoiceDeck needs microphone access to record audio for transcription.',
            'NSHighResolutionCapable': True,
        },
    )

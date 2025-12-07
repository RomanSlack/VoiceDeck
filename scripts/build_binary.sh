#!/bin/bash
# Build VoiceDeck into a standalone binary using PyInstaller

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$PROJECT_DIR/build"

echo "Building VoiceDeck binary..."
echo "Project directory: $PROJECT_DIR"

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR/voicedeck" "$DIST_DIR/VoiceDeck"

cd "$PROJECT_DIR"

# Create a launcher script that PyInstaller can use
cat > "$PROJECT_DIR/launcher.py" << 'EOF'
#!/usr/bin/env python3
import sys
import os

# Add the package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voicedeck.main import main

if __name__ == "__main__":
    sys.exit(main())
EOF

# Run PyInstaller
pyinstaller \
    --name="VoiceDeck" \
    --onedir \
    --windowed \
    --noconfirm \
    --clean \
    --add-data="voicedeck:voicedeck" \
    --add-data="config.example.toml:." \
    --hidden-import="voicedeck" \
    --hidden-import="voicedeck.main" \
    --hidden-import="voicedeck.config" \
    --hidden-import="voicedeck.gui" \
    --hidden-import="voicedeck.gui.main_window" \
    --hidden-import="voicedeck.gui.settings_dialog" \
    --hidden-import="voicedeck.gui.styles" \
    --hidden-import="voicedeck.gui.widgets" \
    --hidden-import="voicedeck.gui.widgets.record_button" \
    --hidden-import="voicedeck.gui.widgets.level_meter" \
    --hidden-import="voicedeck.gui.widgets.led_indicator" \
    --hidden-import="voicedeck.audio" \
    --hidden-import="voicedeck.audio.recorder" \
    --hidden-import="voicedeck.stt" \
    --hidden-import="voicedeck.stt.base" \
    --hidden-import="voicedeck.stt.openai_client" \
    --hidden-import="voicedeck.keyring_storage" \
    --hidden-import="scipy.io" \
    --hidden-import="scipy.io.wavfile" \
    --hidden-import="numpy" \
    --hidden-import="keyring.backends" \
    --hidden-import="keyring.backends.SecretService" \
    --hidden-import="secretstorage" \
    --collect-all="sounddevice" \
    --collect-all="keyring" \
    launcher.py

# Clean up launcher
rm -f "$PROJECT_DIR/launcher.py"

echo ""
echo "Build complete!"
echo "Binary location: $DIST_DIR/VoiceDeck/VoiceDeck"

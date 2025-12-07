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

# Run PyInstaller
pyinstaller \
    --name="VoiceDeck" \
    --onedir \
    --windowed \
    --noconfirm \
    --clean \
    --add-data="config.example.toml:." \
    --hidden-import="scipy.io" \
    --hidden-import="scipy.io.wavfile" \
    --hidden-import="numpy" \
    --collect-all="sounddevice" \
    --collect-all="PySide6" \
    voicedeck/main.py

echo ""
echo "Build complete!"
echo "Binary location: $DIST_DIR/VoiceDeck/VoiceDeck"

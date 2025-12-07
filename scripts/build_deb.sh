#!/bin/bash
# Build a .deb package for VoiceDeck

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

APP_NAME="voicedeck"
VERSION="1.0.0"
ARCH="amd64"
MAINTAINER="VoiceDeck Contributors"
DESCRIPTION="Desktop voice recorder with speech-to-text transcription"

DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}"
DIST_DIR="$PROJECT_DIR/dist"
BINARY_DIR="$DIST_DIR/VoiceDeck"
DEB_ROOT="$DIST_DIR/$DEB_NAME"

echo "Building .deb package for VoiceDeck..."

# Check if binary exists
if [ ! -d "$BINARY_DIR" ]; then
    echo "Error: Binary not found at $BINARY_DIR"
    echo "Run build_binary.sh first."
    exit 1
fi

# Clean previous deb build
rm -rf "$DEB_ROOT"
rm -f "$DIST_DIR/${DEB_NAME}.deb"

# Create directory structure
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/opt/voicedeck"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps"

# Copy binary directory
cp -r "$BINARY_DIR"/* "$DEB_ROOT/opt/voicedeck/"

# Create symlink in /usr/bin
ln -s /opt/voicedeck/VoiceDeck "$DEB_ROOT/usr/bin/voicedeck"

# Copy desktop file
cp "$PROJECT_DIR/debian/voicedeck.desktop" "$DEB_ROOT/usr/share/applications/"

# Copy icons
if [ -f "$PROJECT_DIR/assets/voicedeck.png" ]; then
    cp "$PROJECT_DIR/assets/voicedeck.png" "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps/"
fi
if [ -f "$PROJECT_DIR/assets/voicedeck.svg" ]; then
    cp "$PROJECT_DIR/assets/voicedeck.svg" "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps/"
fi

# Calculate installed size (in KB)
INSTALLED_SIZE=$(du -sk "$DEB_ROOT" | cut -f1)

# Create control file
cat > "$DEB_ROOT/DEBIAN/control" << EOF
Package: $APP_NAME
Version: $VERSION
Section: sound
Priority: optional
Architecture: $ARCH
Installed-Size: $INSTALLED_SIZE
Depends: libasound2t64 | libasound2, libportaudio2, gnome-keyring | libsecret-1-0
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 VoiceDeck is a desktop application for recording voice and
 transcribing it to text using OpenAI's Speech-to-Text API.
 Features a minimal dark-themed GUI, supports long recordings
 up to 60 minutes, and includes clipboard integration.
EOF

# Create postinst script to update icon cache
cat > "$DEB_ROOT/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications || true
fi
exit 0
EOF
chmod 755 "$DEB_ROOT/DEBIAN/postinst"

# Create postrm script
cat > "$DEB_ROOT/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications || true
fi
exit 0
EOF
chmod 755 "$DEB_ROOT/DEBIAN/postrm"

# Set permissions
find "$DEB_ROOT" -type d -exec chmod 755 {} \;
find "$DEB_ROOT/opt/voicedeck" -type f -exec chmod 644 {} \;
chmod 755 "$DEB_ROOT/opt/voicedeck/VoiceDeck"
# Make all .so files executable
find "$DEB_ROOT/opt/voicedeck" -name "*.so*" -exec chmod 755 {} \;
# Desktop file and icons must be world-readable
chmod 644 "$DEB_ROOT/usr/share/applications/voicedeck.desktop"
find "$DEB_ROOT/usr/share/icons" -type f -exec chmod 644 {} \;

# Build the .deb package
dpkg-deb --build --root-owner-group "$DEB_ROOT"

echo ""
echo "Package built successfully!"
echo "Location: $DIST_DIR/${DEB_NAME}.deb"
echo ""
echo "Install with: sudo apt install ./$DEB_NAME.deb"

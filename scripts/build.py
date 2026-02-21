#!/usr/bin/env python3
"""Cross-platform build script for VoiceDeck.

Usage:
    python scripts/build.py binary    # Build standalone binary via PyInstaller
    python scripts/build.py package   # Build platform installer (.deb / .exe / .dmg)
    python scripts/build.py all       # Both steps
"""

import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"
SPEC_FILE = PROJECT_DIR / "VoiceDeck.spec"
LAUNCHER = PROJECT_DIR / "launcher.py"

APP_NAME = "voicedeck"
VERSION = "1.0.0"


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command, printing it first."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=True, **kwargs)


# ---------------------------------------------------------------------------
# Binary
# ---------------------------------------------------------------------------

def build_binary() -> None:
    """Build the standalone binary using PyInstaller."""
    print("=== Building VoiceDeck binary ===")

    # Create launcher.py if it doesn't exist
    if not LAUNCHER.exists():
        LAUNCHER.write_text(textwrap.dedent("""\
            #!/usr/bin/env python3
            import sys
            import os

            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

            from voicedeck.main import main

            if __name__ == "__main__":
                sys.exit(main())
        """))
        print(f"  Created {LAUNCHER}")

    # Clean previous builds
    for d in [BUILD_DIR, DIST_DIR / "VoiceDeck"]:
        if d.exists():
            shutil.rmtree(d)

    run([
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        str(SPEC_FILE),
    ], cwd=str(PROJECT_DIR))

    binary_dir = DIST_DIR / "VoiceDeck"
    if sys.platform == "darwin":
        print(f"\nBuild complete: {DIST_DIR / 'VoiceDeck.app'}")
    else:
        exe_name = "VoiceDeck.exe" if sys.platform == "win32" else "VoiceDeck"
        print(f"\nBuild complete: {binary_dir / exe_name}")


# ---------------------------------------------------------------------------
# Linux .deb
# ---------------------------------------------------------------------------

def package_linux() -> None:
    """Build a .deb package (ports logic from build_deb.sh)."""
    arch = "amd64"
    deb_name = f"{APP_NAME}_{VERSION}_{arch}"
    binary_dir = DIST_DIR / "VoiceDeck"
    deb_root = DIST_DIR / deb_name

    if not binary_dir.exists():
        print("Error: Binary not found. Run 'build.py binary' first.")
        sys.exit(1)

    print("=== Building .deb package ===")

    # Clean
    if deb_root.exists():
        shutil.rmtree(deb_root)
    deb_file = DIST_DIR / f"{deb_name}.deb"
    deb_file.unlink(missing_ok=True)

    # Create directory structure
    for d in [
        deb_root / "DEBIAN",
        deb_root / "opt" / "voicedeck",
        deb_root / "usr" / "bin",
        deb_root / "usr" / "share" / "applications",
        deb_root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps",
        deb_root / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy binary directory
    shutil.copytree(binary_dir, deb_root / "opt" / "voicedeck", dirs_exist_ok=True)

    # Symlink
    (deb_root / "usr" / "bin" / "voicedeck").symlink_to("/opt/voicedeck/VoiceDeck")

    # Desktop file
    desktop_src = PROJECT_DIR / "debian" / "voicedeck.desktop"
    if desktop_src.exists():
        shutil.copy2(desktop_src, deb_root / "usr" / "share" / "applications")

    # Icons
    png_src = PROJECT_DIR / "assets" / "voicedeck.png"
    if png_src.exists():
        shutil.copy2(
            png_src,
            deb_root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps",
        )
    svg_src = PROJECT_DIR / "assets" / "voicedeck.svg"
    if svg_src.exists():
        shutil.copy2(
            svg_src,
            deb_root / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps",
        )

    # Installed size (KB)
    total_size = sum(
        f.stat().st_size for f in deb_root.rglob("*") if f.is_file()
    ) // 1024

    # Control file
    (deb_root / "DEBIAN" / "control").write_text(textwrap.dedent(f"""\
        Package: {APP_NAME}
        Version: {VERSION}
        Section: sound
        Priority: optional
        Architecture: {arch}
        Installed-Size: {total_size}
        Depends: libasound2t64 | libasound2, libportaudio2, gnome-keyring | libsecret-1-0
        Maintainer: VoiceDeck Contributors
        Description: Desktop voice recorder with speech-to-text transcription
         VoiceDeck is a desktop application for recording voice and
         transcribing it to text using OpenAI's Speech-to-Text API.
         Features a minimal dark-themed GUI, supports long recordings
         up to 60 minutes, and includes clipboard integration.
    """))

    # postinst
    postinst = deb_root / "DEBIAN" / "postinst"
    postinst.write_text(textwrap.dedent("""\
        #!/bin/bash
        set -e
        if command -v gtk-update-icon-cache &> /dev/null; then
            gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
        fi
        if command -v update-desktop-database &> /dev/null; then
            update-desktop-database /usr/share/applications || true
        fi
        exit 0
    """))
    postinst.chmod(0o755)

    # postrm
    postrm = deb_root / "DEBIAN" / "postrm"
    postrm.write_text(textwrap.dedent("""\
        #!/bin/bash
        set -e
        if command -v gtk-update-icon-cache &> /dev/null; then
            gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
        fi
        if command -v update-desktop-database &> /dev/null; then
            update-desktop-database /usr/share/applications || true
        fi
        exit 0
    """))
    postrm.chmod(0o755)

    # Set permissions
    for p in deb_root.rglob("*"):
        if p.is_dir():
            p.chmod(0o755)
    for p in (deb_root / "opt" / "voicedeck").rglob("*"):
        if p.is_file():
            p.chmod(0o644)
    (deb_root / "opt" / "voicedeck" / "VoiceDeck").chmod(0o755)
    for p in (deb_root / "opt" / "voicedeck").rglob("*.so*"):
        if p.is_file():
            p.chmod(0o755)

    run(["dpkg-deb", "--build", "--root-owner-group", str(deb_root)])

    print(f"\nPackage built: {deb_file}")
    print(f"Install with: sudo apt install ./{deb_name}.deb")


# ---------------------------------------------------------------------------
# Windows Inno Setup
# ---------------------------------------------------------------------------

def package_windows() -> None:
    """Generate an Inno Setup .iss script and compile it to an installer .exe."""
    binary_dir = DIST_DIR / "VoiceDeck"
    if not binary_dir.exists():
        print("Error: Binary not found. Run 'build.py binary' first.")
        sys.exit(1)

    print("=== Building Windows installer ===")

    ico_path = PROJECT_DIR / "assets" / "voicedeck.ico"
    iss_path = DIST_DIR / "voicedeck_setup.iss"

    iss_content = textwrap.dedent(f"""\
        [Setup]
        AppName=VoiceDeck
        AppVersion={VERSION}
        AppPublisher=VoiceDeck Contributors
        DefaultDirName={{autopf}}\\VoiceDeck
        DefaultGroupName=VoiceDeck
        OutputDir={DIST_DIR}
        OutputBaseFilename=VoiceDeck_Setup_{VERSION}
        SetupIconFile={ico_path}
        Compression=lzma2
        SolidCompression=yes
        ArchitecturesInstallIn64BitMode=x64compatible
        UninstallDisplayIcon={{app}}\\VoiceDeck.exe

        [Tasks]
        Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

        [Files]
        Source: "{binary_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

        [Icons]
        Name: "{{group}}\\VoiceDeck"; Filename: "{{app}}\\VoiceDeck.exe"; IconFilename: "{{app}}\\VoiceDeck.exe"
        Name: "{{group}}\\Uninstall VoiceDeck"; Filename: "{{uninstallexe}}"
        Name: "{{commondesktop}}\\VoiceDeck"; Filename: "{{app}}\\VoiceDeck.exe"; Tasks: desktopicon

        [Run]
        Filename: "{{app}}\\VoiceDeck.exe"; Description: "Launch VoiceDeck"; Flags: nowait postinstall skipifsilent
    """)

    iss_path.write_text(iss_content)
    print(f"  Created Inno Setup script: {iss_path}")

    # Try to compile with Inno Setup
    iscc_paths = [
        Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
        / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("PROGRAMFILES", "C:\\Program Files"))
        / "Inno Setup 6" / "ISCC.exe",
    ]

    iscc = None
    for p in iscc_paths:
        if p.exists():
            iscc = p
            break

    if iscc is None:
        # Also check PATH
        iscc_in_path = shutil.which("ISCC") or shutil.which("iscc")
        if iscc_in_path:
            iscc = Path(iscc_in_path)

    if iscc:
        run([str(iscc), str(iss_path)])
        print(f"\nInstaller built: {DIST_DIR / f'VoiceDeck_Setup_{VERSION}.exe'}")
    else:
        print("\nInno Setup (ISCC) not found. The .iss script has been generated.")
        print(f"Compile it manually: ISCC.exe {iss_path}")
        print("Download Inno Setup from: https://jrsoftware.org/isdownload.php")


# ---------------------------------------------------------------------------
# macOS .dmg
# ---------------------------------------------------------------------------

def package_macos() -> None:
    """Create a .dmg from the .app bundle."""
    app_path = DIST_DIR / "VoiceDeck.app"
    if not app_path.exists():
        print("Error: VoiceDeck.app not found. Run 'build.py binary' first.")
        sys.exit(1)

    print("=== Building macOS .dmg ===")

    dmg_path = DIST_DIR / f"VoiceDeck_{VERSION}.dmg"
    dmg_path.unlink(missing_ok=True)

    # Create a temporary directory for the DMG contents
    dmg_staging = DIST_DIR / "dmg_staging"
    if dmg_staging.exists():
        shutil.rmtree(dmg_staging)
    dmg_staging.mkdir()

    # Copy .app to staging
    shutil.copytree(app_path, dmg_staging / "VoiceDeck.app", symlinks=True)

    # Create Applications symlink
    (dmg_staging / "Applications").symlink_to("/Applications")

    # Build DMG
    run([
        "hdiutil", "create",
        "-volname", "VoiceDeck",
        "-srcfolder", str(dmg_staging),
        "-ov", "-format", "UDZO",
        str(dmg_path),
    ])

    # Cleanup staging
    shutil.rmtree(dmg_staging)

    print(f"\nDMG built: {dmg_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def package() -> None:
    """Build the platform-appropriate installer."""
    if sys.platform == "linux":
        package_linux()
    elif sys.platform == "win32":
        package_windows()
    elif sys.platform == "darwin":
        package_macos()
    else:
        print(f"Unsupported platform: {sys.platform}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build VoiceDeck")
    parser.add_argument(
        "command",
        choices=["binary", "package", "all"],
        help="binary: PyInstaller build; package: platform installer; all: both",
    )
    args = parser.parse_args()

    if args.command == "binary":
        build_binary()
    elif args.command == "package":
        package()
    elif args.command == "all":
        build_binary()
        package()


if __name__ == "__main__":
    main()

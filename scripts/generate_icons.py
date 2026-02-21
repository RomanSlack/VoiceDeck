#!/usr/bin/env python3
"""Generate icon assets (.png, .ico, .icns) from voicedeck.svg.

Requires: pip install Pillow cairosvg

Usage:
    python scripts/generate_icons.py
"""

import io
import struct
import sys
from pathlib import Path

try:
    import cairosvg
    from PIL import Image
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install Pillow cairosvg")
    sys.exit(1)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
SVG_PATH = ASSETS_DIR / "voicedeck.svg"


def svg_to_png(svg_path: Path, size: int) -> Image.Image:
    """Render SVG to a PIL Image at the given size."""
    png_data = cairosvg.svg2png(
        url=str(svg_path), output_width=size, output_height=size
    )
    return Image.open(io.BytesIO(png_data))


def create_icns(images: dict[int, Image.Image], output_path: Path) -> None:
    """Create a macOS .icns file from a dict of {size: PIL.Image}.

    Supports sizes: 16, 32, 64, 128, 256, 512, 1024.
    Uses PNG-encoded icon types (ic07-ic14, icp4-icp6).
    """
    # macOS icon type codes for PNG-encoded entries
    icon_types = {
        16: b"icp4",
        32: b"icp5",
        64: b"icp6",
        128: b"ic07",
        256: b"ic08",
        512: b"ic09",
        1024: b"ic10",
    }

    entries = []
    for size, img in sorted(images.items()):
        if size not in icon_types:
            continue
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        type_code = icon_types[size]
        # Each entry: 4-byte type + 4-byte length (includes header) + data
        entry_length = 8 + len(png_bytes)
        entries.append(struct.pack(">4sI", type_code, entry_length) + png_bytes)

    # File header: 'icns' + total file size
    body = b"".join(entries)
    total_size = 8 + len(body)
    with open(output_path, "wb") as f:
        f.write(struct.pack(">4sI", b"icns", total_size))
        f.write(body)


def main() -> None:
    if not SVG_PATH.exists():
        print(f"SVG not found: {SVG_PATH}")
        sys.exit(1)

    print(f"Generating icons from {SVG_PATH}...")

    # Generate PNG at 256x256 (primary size for Linux desktop icons)
    img_256 = svg_to_png(SVG_PATH, 256)
    png_path = ASSETS_DIR / "voicedeck.png"
    img_256.save(png_path, format="PNG")
    print(f"  Created {png_path}")

    # Generate .ico (Windows) — multiple sizes embedded
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_images = [svg_to_png(SVG_PATH, s) for s in ico_sizes]
    ico_path = ASSETS_DIR / "voicedeck.ico"
    # Save largest first, append smaller sizes
    ico_images[-1].save(
        ico_path, format="ICO",
        append_images=ico_images[:-1]
    )
    print(f"  Created {ico_path}")

    # Generate .icns (macOS) — multiple sizes embedded
    icns_sizes = [16, 32, 64, 128, 256, 512, 1024]
    icns_images = {s: svg_to_png(SVG_PATH, s) for s in icns_sizes}
    icns_path = ASSETS_DIR / "voicedeck.icns"
    create_icns(icns_images, icns_path)
    print(f"  Created {icns_path}")

    print("Done!")


if __name__ == "__main__":
    main()

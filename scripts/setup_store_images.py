#!/usr/bin/env python3
"""
Helper script to set up store-specific heatmap images.

Usage:
    python setup_store_images.py --store-code "Spar-XXXXX-Name" --source-folder "/path/to/images"
    python setup_store_images.py --store-code "Spar-XXXXX-Name" --source-folder "/path/to/images" --copy-all

This script:
1. Creates a folder for the new store
2. Copies images from the source folder to the store-specific folder
3. Validates that images were copied successfully
"""

import os
import shutil
import argparse
from pathlib import Path


def setup_store_images(store_code, source_folder, copy_all=False):
    """Set up store-specific heatmap images."""

    # Get the heatmap base directory
    script_dir = Path(__file__).parent
    heatmap_base = script_dir.parent / "app" / "static" / "img" / "heatmap"

    # Create store-specific folder
    store_folder = heatmap_base / store_code
    store_folder.mkdir(parents=True, exist_ok=True)

    print(f"✓ Created store folder: {store_folder}")

    # Validate source folder
    source_path = Path(source_folder)
    if not source_path.exists():
        print(f"✗ Source folder does not exist: {source_folder}")
        return False

    # Find all JPG images in source folder
    source_images = list(source_path.glob("*.jpg")) + list(source_path.glob("*.JPG"))

    if not source_images:
        print(f"✗ No JPG images found in: {source_folder}")
        return False

    # Copy images
    copied_count = 0
    skipped = []

    for source_image in sorted(source_images):
        dest_image = store_folder / source_image.name

        # Skip if already exists (unless --copy-all flag)
        if dest_image.exists() and not copy_all:
            skipped.append(source_image.name)
            continue

        try:
            shutil.copy2(source_image, dest_image)
            copied_count += 1
            print(f"  ✓ Copied: {source_image.name}")
        except Exception as e:
            print(f"  ✗ Failed to copy {source_image.name}: {e}")

    print(f"\n✓ Copied {copied_count} image(s)")

    if skipped:
        print(f"⊘ Skipped {len(skipped)} existing file(s)")

    # Get final count
    final_images = list(store_folder.glob("*.jpg")) + list(store_folder.glob("*.JPG"))
    print(f"\n✓ Store folder now contains {len(final_images)} image(s)")
    print(f"  Location: {store_folder}")

    return True


def list_store_folders():
    """List all existing store folders."""
    script_dir = Path(__file__).parent
    heatmap_base = script_dir.parent / "app" / "static" / "img" / "heatmap"

    if not heatmap_base.exists():
        print("Heatmap folder not found.")
        return

    stores = [d for d in heatmap_base.iterdir() if d.is_dir()]

    if not stores:
        print("No store folders found.")
        return

    print("Existing store folders:")
    for store_path in sorted(stores):
        jpg_images = list(store_path.glob("*.jpg")) + list(store_path.glob("*.JPG"))
        image_count = len(jpg_images)
        print(f"  📁 {store_path.name}")
        print(f"     └─ {image_count} image(s)")
        if image_count > 0:
            for img in sorted(jpg_images)[:3]:
                print(f"        • {img.name}")
            if image_count > 3:
                print(f"        • ... and {image_count - 3} more")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Setup store-specific heatmap images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup images for a new store (copy all JPG files)
  python setup_store_images.py --store-code 'Spar-XXXXX-Name' --source-folder '/path/to/images'

  # Copy all images including existing ones
  python setup_store_images.py --store-code 'Spar-XXXXX-Name' --source-folder '/path/to/images' --copy-all

  # List all existing store folders and image counts
  python setup_store_images.py --list

Image Requirements:
  - Images must be in JPEG format (.jpg or .JPG)
  - Naming convention: location{number}- {description}.jpg
    Example: "location01- FMCG Food.jpg"
  - No fixed number of images required - supports any count per store
        """
    )
    parser.add_argument("--store-code", type=str, help="Store code (e.g., Spar-20016-TSM-Mall-Udupi)")
    parser.add_argument("--source-folder", type=str, help="Source folder with images")
    parser.add_argument("--copy-all", action="store_true", help="Overwrite existing images")
    parser.add_argument("--list", action="store_true", help="List all store folders")

    args = parser.parse_args()

    if args.list:
        list_store_folders()
    elif args.store_code and args.source_folder:
        success = setup_store_images(args.store_code, args.source_folder, args.copy_all)
        exit(0 if success else 1)
    else:
        parser.print_help()

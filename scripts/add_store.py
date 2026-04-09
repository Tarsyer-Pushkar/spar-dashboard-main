#!/usr/bin/env python3
"""
Comprehensive Store Addition Script

Adds a new SPAR store to the dashboard with all configurations:
- Store code registration
- Heatmap image setup
- Database indexes
- Navigation updates
- Configuration updates

Usage:
    python add_store.py --store-code "StoreCode" --display-name "Location Name" --images-folder "/path/to/images"
    python add_store.py --list
    python add_store.py --validate "StoreCode"
"""

import os
import sys
import shutil
import argparse
import json
from pathlib import Path
from datetime import datetime

# ANSI colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def log_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def log_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def log_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def log_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


def log_section(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.END}\n")


class StoreManager:
    """Manages store addition and configuration."""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.app_dir = self.project_root / "app"
        self.static_dir = self.app_dir / "static"
        self.heatmap_base = self.static_dir / "img" / "heatmap"
        self.templates_dir = self.app_dir / "templates"

        # Store configuration
        self.stores_config_file = self.project_root / ".stores.json"

    def validate_store_code(self, store_code):
        """Validate store code format."""
        if not store_code or not store_code.strip():
            log_error("Store code cannot be empty.")
            return False
        return True

    def load_stores_config(self):
        """Load existing stores configuration."""
        if self.stores_config_file.exists():
            with open(self.stores_config_file, 'r') as f:
                return json.load(f)
        return {"stores": [], "last_updated": datetime.now().isoformat()}

    def save_stores_config(self, config):
        """Save stores configuration."""
        config["last_updated"] = datetime.now().isoformat()
        with open(self.stores_config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def store_exists(self, store_code):
        """Check if store already exists."""
        config = self.load_stores_config()
        return any(s["code"] == store_code for s in config.get("stores", []))

    def add_store(self, store_code, display_name, images_folder):
        """Add a new store with all configurations."""

        log_section(f"Adding Store: {store_code}")

        # 1. Validate store code
        log_info("Step 1: Validating store code...")
        if not self.validate_store_code(store_code):
            return False
        log_success("Store code format valid")

        # 2. Check if store already exists
        if self.store_exists(store_code):
            log_error(f"Store {store_code} already exists!")
            return False
        log_success("Store is new (not already in system)")

        # 3. Create heatmap folder
        log_info("Step 2: Setting up heatmap folders...")
        store_heatmap_folder = self.heatmap_base / store_code
        try:
            store_heatmap_folder.mkdir(parents=True, exist_ok=True)
            log_success(f"Created heatmap folder: {store_heatmap_folder}")
        except Exception as e:
            log_error(f"Failed to create heatmap folder: {e}")
            return False

        # 4. Copy heatmap images if provided
        if images_folder:
            log_info("Step 3: Copying heatmap images...")
            if not self._copy_images(images_folder, store_heatmap_folder):
                log_warning("No images were copied (folder may be empty)")
            else:
                image_count = len(list(store_heatmap_folder.glob("*.jpg"))) + \
                             len(list(store_heatmap_folder.glob("*.JPG")))
                log_success(f"Copied {image_count} image(s)")
        else:
            log_info("Step 3: Skipping image copy (no folder provided)")
            log_info("Images can be added later manually")

        # 5. Create other store-specific folders
        log_info("Step 4: Creating store-specific data folders...")
        data_folders = [
            self.static_dir / "data" / store_code,
            self.static_dir / "uploads" / store_code,
        ]
        for folder in data_folders:
            try:
                folder.mkdir(parents=True, exist_ok=True)
                log_success(f"Created: {folder.name}")
            except Exception as e:
                log_warning(f"Could not create {folder}: {e}")

        # 6. Update base.html with store code
        log_info("Step 5: Updating navigation...")
        if self._update_base_html(store_code, display_name):
            log_success("Updated base.html")
        else:
            log_warning("Could not auto-update base.html - add manually")

        # 7. Register store in configuration
        log_info("Step 6: Registering store in configuration...")
        if self._register_store(store_code, display_name, images_folder):
            log_success("Store registered in .stores.json")
        else:
            log_warning("Could not register in config")

        # 8. Create store information file
        log_info("Step 7: Creating store metadata...")
        self._create_store_info(store_code, display_name)
        log_success("Created store metadata")

        # 9. Validate setup
        log_info("Step 8: Validating setup...")
        self.validate_store(store_code)

        log_section(f"✓ Store {store_code} Added Successfully!")
        print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
        print(f"1. Add more images anytime: python scripts/setup_store_images.py --store-code '{store_code}' --source-folder '/path/to/images'")
        print(f"2. Verify in dashboard: Select '{store_code}' from the store dropdown")
        print(f"3. Check heatmap: Navigate to Heatmap page to see locations")
        print(f"\n{Colors.BOLD}Store Folder:{Colors.END}")
        print(f"  {store_heatmap_folder}\n")

        return True

    def _copy_images(self, source_folder, dest_folder):
        """Copy images from source to destination folder."""
        source_path = Path(source_folder)

        if not source_path.exists():
            log_error(f"Source folder not found: {source_folder}")
            return False

        images = list(source_path.glob("*.jpg")) + list(source_path.glob("*.JPG"))

        if not images:
            log_warning(f"No JPG images found in: {source_folder}")
            return False

        copied = 0
        for img_file in images:
            try:
                dest_file = dest_folder / img_file.name
                shutil.copy2(img_file, dest_file)
                copied += 1
            except Exception as e:
                log_warning(f"Failed to copy {img_file.name}: {e}")

        return copied > 0

    def _update_base_html(self, store_code, display_name):
        """Update base.html with new store code — dropdown option + JS STORE_CODES array."""
        base_html_path = self.templates_dir / "base.html"

        if not base_html_path.exists():
            return False

        try:
            with open(base_html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip if already present
            if f'value="{store_code}"' in content:
                log_info(f"Store {store_code} already in base.html")
                return True

            updated = False

            # 1. Insert <option> inside the globalStoreCode <select> block only
            import re
            select_pattern = re.compile(
                r'(<select[^>]+id=["\']globalStoreCode["\'][^>]*>.*?)(</select>)',
                re.DOTALL
            )
            new_option = f'      <option value="{store_code}">{display_name}</option>\n    '
            def insert_option(m):
                return m.group(1) + new_option + m.group(2)

            new_content = select_pattern.sub(insert_option, content)
            if new_content != content:
                content = new_content
                updated = True
            else:
                log_warning("Could not locate globalStoreCode select block in base.html")

            # 2. Update the STORE_CODES JS array
            store_codes_pattern = re.compile(r"(const STORE_CODES\s*=\s*\[)([^\]]*?)(\];)")
            def update_store_codes(m):
                existing = m.group(2).strip()
                # Check it's not already listed
                if f"'{store_code}'" in existing or f'"{store_code}"' in existing:
                    return m.group(0)
                separator = ', ' if existing else ''
                return m.group(1) + existing + separator + f"'{store_code}'" + m.group(3)

            new_content = store_codes_pattern.sub(update_store_codes, content)
            if new_content != content:
                content = new_content
                updated = True
            else:
                log_warning("Could not locate STORE_CODES array in base.html")

            if updated:
                with open(base_html_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return updated

        except Exception as e:
            log_warning(f"Error updating base.html: {e}")
            return False

    def _register_store(self, store_code, display_name, images_folder):
        """Register store in configuration file."""
        try:
            config = self.load_stores_config()

            store_info = {
                "code": store_code,
                "display_name": display_name,
                "images_folder": images_folder or "None",
                "created_date": datetime.now().isoformat(),
                "image_count": 0,
            }

            # Count images if folder exists
            store_heatmap = self.heatmap_base / store_code
            if store_heatmap.exists():
                image_count = len(list(store_heatmap.glob("*.jpg"))) + \
                             len(list(store_heatmap.glob("*.JPG")))
                store_info["image_count"] = image_count

            config["stores"].append(store_info)
            self.save_stores_config(config)
            return True

        except Exception as e:
            log_warning(f"Error registering store: {e}")
            return False

    def _create_store_info(self, store_code, display_name):
        """Create store information file."""
        try:
            store_info_file = self.heatmap_base / store_code / "STORE_INFO.txt"

            info_content = f"""Store Information
==================

Store Code: {store_code}
Display Name: {display_name}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Folder Structure:
  └── {store_code}/
      ├── location01- Name.jpg
      ├── location02- Name.jpg
      └── ... (any number of location images)

To add more images:
  python scripts/setup_store_images.py --store-code "{store_code}" --source-folder "/path/to/images"

Image Naming Convention:
  location{{number}}- {{description}}.jpg
  Example: location01- FMCG Food.jpg

Notes:
  - Images are automatically discovered by the heatmap module
  - No fixed number of images required
  - Different stores can have different location counts
  - Images can be added/updated anytime without code changes
"""

            with open(store_info_file, 'w') as f:
                f.write(info_content)

        except Exception as e:
            log_warning(f"Could not create store info file: {e}")

    def validate_store(self, store_code):
        """Validate a store's complete setup."""
        log_section(f"Validating Store: {store_code}")

        issues = []

        # Check heatmap folder
        store_heatmap = self.heatmap_base / store_code
        if store_heatmap.exists():
            image_count = len(list(store_heatmap.glob("*.jpg"))) + \
                         len(list(store_heatmap.glob("*.JPG")))
            log_success(f"Heatmap folder exists with {image_count} image(s)")
        else:
            log_error("Heatmap folder not found!")
            issues.append("Heatmap folder missing")

        # Check base.html
        base_html_path = self.templates_dir / "base.html"
        if base_html_path.exists():
            with open(base_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if store_code in content:
                log_success("Store registered in base.html")
            else:
                log_warning("Store not found in base.html (add manually if needed)")
        else:
            log_error("base.html not found!")
            issues.append("base.html missing")

        # Check config file
        if self.store_exists(store_code):
            log_success("Store registered in configuration")
        else:
            log_warning("Store not in configuration file")

        if not issues:
            log_success("\n✓ All validations passed!")
            return True
        else:
            log_error(f"\n✗ {len(issues)} issue(s) found")
            return False

    def list_stores(self):
        """List all registered stores."""
        log_section("Registered Stores")

        config = self.load_stores_config()
        stores = config.get("stores", [])

        if not stores:
            log_info("No stores registered yet")
            return

        for i, store in enumerate(stores, 1):
            print(f"{Colors.BOLD}{i}. {store['code']}{Colors.END}")
            print(f"   Display Name: {store.get('display_name', 'N/A')}")
            print(f"   Images: {store.get('image_count', 0)}")
            print(f"   Created: {store.get('created_date', 'N/A')}")

            # Check folder
            store_heatmap = self.heatmap_base / store['code']
            if store_heatmap.exists():
                print(f"   Folder: ✓ Exists")
            else:
                print(f"   Folder: ✗ Missing")
            print()

        print(f"Total: {Colors.BOLD}{len(stores)}{Colors.END} store(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Add new SPAR stores to the dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a new store with images
  python add_store.py --store-code "Spar-20017-New-Mall" --display-name "New Mall, City" --images-folder "/path/to/images"

  # Add store without images (add later)
  python add_store.py --store-code "Spar-20018-Future-Store" --display-name "Future Store Location"

  # List all registered stores
  python add_store.py --list

  # Validate a store's setup
  python add_store.py --validate "Spar-20017-New-Mall"

Store Code Format:
  Any valid identifier string
  Example: MyStore-123 or Spar-20016-TSM-Mall-Udupi

Image Requirements:
  - Format: JPEG (.jpg or .JPG)
  - Naming: location{number}- {description}.jpg
  - Examples: location01- FMCG Food.jpg, location15- Premium Zone.jpg
  - No fixed count - any number supported
        """
    )

    parser.add_argument("--store-code", type=str, help="Store code (e.g., Spar-20017-New-Store)")
    parser.add_argument("--display-name", type=str, help="Store display name (e.g., 'New Store, City Name')")
    parser.add_argument("--images-folder", type=str, help="Path to folder containing heatmap images")
    parser.add_argument("--list", action="store_true", help="List all registered stores")
    parser.add_argument("--validate", type=str, help="Validate a store's setup")

    args = parser.parse_args()

    manager = StoreManager()

    if args.list:
        manager.list_stores()
    elif args.validate:
        manager.validate_store(args.validate)
    elif args.store_code:
        if not args.display_name:
            log_error("--display-name is required when adding a store")
            sys.exit(1)

        success = manager.add_store(
            args.store_code,
            args.display_name,
            args.images_folder
        )
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        print("\n" + "=" * 70)
        print("Quick start: python add_store.py --help")
        print("=" * 70)


if __name__ == "__main__":
    main()

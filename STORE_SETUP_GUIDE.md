# Store Setup Guide

Complete guide for adding new SPAR stores to the Tarsyer Dashboard.

## Quick Start

```bash
python scripts/add_store.py --store-code "Spar-20017-New-Store" \
  --display-name "New Store Location" \
  --images-folder "/path/to/heatmap/images"
```

## What Gets Set Up

When you add a new store, the script automatically:

✓ Creates store-specific folder structure
✓ Copies heatmap location images
✓ Updates navigation with store code
✓ Registers store in configuration
✓ Creates store metadata files
✓ Validates complete setup

## Usage

### 1. Add a New Store (with images)

```bash
python scripts/add_store.py \
  --store-code "Spar-20017-TSM-Mall-New-City" \
  --display-name "TSM Mall, New City" \
  --images-folder "C:\path\to\images"
```

**What happens:**
- Creates folder: `app/static/img/heatmap/Spar-20017-TSM-Mall-New-City/`
- Copies all `.jpg` images to store folder
- Updates `base.html` navigation
- Creates metadata file
- Validates setup

### 2. Add a Store Without Images (add later)

```bash
python scripts/add_store.py \
  --store-code "Spar-20018-Future-Store" \
  --display-name "Future Store, City Name"
```

**Then add images later:**
```bash
python scripts/setup_store_images.py \
  --store-code "Spar-20018-Future-Store" \
  --source-folder "C:\path\to\images"
```

### 3. List All Stores

```bash
python scripts/add_store.py --list
```

Output:
```
1. Spar-20016-TSM-Mall-Udupi
   Display Name: TSM Mall, Udupi
   Images: 9
   Created: 2025-04-06T12:30:45

2. Spar-30008-Langval-mall-Thanjavur
   Display Name: Langval Mall, Thanjavur
   Images: 0
   Created: 2025-04-06T12:45:20

Total: 2 store(s)
```

### 4. Validate Store Setup

```bash
python scripts/add_store.py --validate "Spar-20017-TSM-Mall-New-City"
```

Checks:
- ✓ Heatmap folder exists
- ✓ Images present
- ✓ Store in base.html
- ✓ Registered in config

## Store Code Format

```
Spar-{number}-{location-name}
```

**Examples:**
- `Spar-20016-TSM-Mall-Udupi`
- `Spar-30008-Langval-mall-Thanjavur`
- `Spar-20017-Phoenix-Mall-Bangalore`
- `Spar-15001-Westside-Delhi`

**Rules:**
- Start with `Spar-`
- Include location number
- Use hyphens to separate
- Use descriptive location names

## Heatmap Image Structure

### Image Naming Convention

```
location{number}- {description}.jpg
```

**Examples:**
```
location01- FMCG Food.jpg
location02- Grocery.jpg
location05- Dairy and Frozen.jpg
location10- Premium Zone.jpg
location25- Customer Lounge.jpg
```

### Folder Structure After Adding Store

```
app/static/img/heatmap/
│
├── Spar-20016-TSM-Mall-Udupi/
│   ├── location01- FMCG Food.jpg
│   ├── location02- Grocery.jpg
│   └── ... (any number of images)
│
├── Spar-30008-Langval-mall-Thanjavur/
│   ├── location01- Entrance.jpg
│   └── location02- Main Floor.jpg
│
└── Spar-20017-New-Store/
    ├── location01- Zone A.jpg
    ├── location02- Zone B.jpg
    └── STORE_INFO.txt
```

### Image Specifications

| Property | Value |
|----------|-------|
| Format | JPEG (.jpg or .JPG) |
| Dimensions | Any (recommended 1200×800px) |
| File Size | < 500KB each |
| Minimum Count | 1 |
| Maximum Count | Unlimited |
| Naming | `location{N}- {name}.jpg` |

## Complete Store Setup Checklist

### Before Running Script

- [ ] Store code decided (e.g., `Spar-20017-New-Store`)
- [ ] Display name ready (e.g., `"New Store, City Name"`)
- [ ] Heatmap images prepared (optional)
- [ ] Images in JPEG format (`.jpg`)
- [ ] Images follow naming convention
- [ ] Images placed in single folder

### Running the Script

```bash
# Navigate to project root
cd spar-dashboard-main

# Run add_store script
python scripts/add_store.py \
  --store-code "Spar-20017-New-Store" \
  --display-name "New Store Location" \
  --images-folder "C:\images\for\store"
```

### After Script Completes

- [ ] Check console output for any warnings
- [ ] Run validation: `python scripts/add_store.py --validate "Spar-20017-New-Store"`
- [ ] Restart the dashboard application
- [ ] Test in browser:
  - [ ] Select new store from dropdown
  - [ ] Check Overview page loads correctly
  - [ ] Go to Heatmap page
  - [ ] Verify locations appear in dropdown
  - [ ] Verify heatmap images load

## What Gets Created

### Folders

```
app/static/img/heatmap/{store_code}/          # Heatmap images
app/static/data/{store_code}/                 # Store data (optional)
app/static/uploads/{store_code}/              # Store uploads (optional)
```

### Files

```
.stores.json                                   # Store registry (created if missing)
STORE_INFO.txt                                 # Store metadata
(stores are added to base.html automatically)
```

### Configuration Updates

**base.html** - New option added to store dropdown:
```html
<option value="Spar-20017-New-Store">Spar-20017-New-Store</option>
```

**.stores.json** - New entry added:
```json
{
  "code": "Spar-20017-New-Store",
  "display_name": "New Store Location",
  "images_folder": "/path/to/images",
  "created_date": "2025-04-06T13:00:00",
  "image_count": 9
}
```

## Add More Images Later

To add additional location images to an existing store:

```bash
python scripts/setup_store_images.py \
  --store-code "Spar-20017-New-Store" \
  --source-folder "C:\path\to\new\images"
```

## Troubleshooting

### Script Says "Store Already Exists"

The store code is already registered. Options:
1. Use a different store code
2. Add images to existing store: `python scripts/setup_store_images.py --store-code "..." --source-folder "..."`
3. Delete from `.stores.json` if truly accidental

### Images Not Showing in Heatmap

1. Check image folder: `app/static/img/heatmap/{store_code}/`
2. Verify image filenames (must start with `location`)
3. Verify `.jpg` extension (not `.jpeg` or others)
4. Restart dashboard
5. Run validation: `python scripts/add_store.py --validate "Spar-..."`

### Store Dropdown Shows Code but Heatmap Empty

1. Check store folder for images
2. Add images: `python scripts/setup_store_images.py ...`
3. Verify image naming convention
4. Refresh browser (Ctrl+F5 for hard refresh)

### Store Not Appearing in Dropdown

1. Run: `python scripts/add_store.py --list`
2. Check if store is registered
3. Check `base.html` for store option
4. Restart dashboard
5. Run validation: `python scripts/add_store.py --validate "Spar-..."`

## Advanced Usage

### Batch Add Stores (from CSV)

Create a `stores.csv`:
```csv
store_code,display_name,images_folder
Spar-20017-New-Store,New Store Location,C:\images\store1
Spar-20018-Another-Store,Another Location,C:\images\store2
Spar-20019-Third-Store,Third Location,
```

Then run:
```bash
python scripts/add_store.py --batch-csv stores.csv
```

(Note: batch feature can be added if needed)

### Auto-Update with Database Indexes

For MongoDB users, the script can optionally create indexes:

```bash
python scripts/add_store.py \
  --store-code "Spar-20017-New-Store" \
  --display-name "New Store Location" \
  --images-folder "/path/to/images" \
  --create-db-indexes
```

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Run validation: `python scripts/add_store.py --validate "Spar-..."`
3. Check console output for specific error messages
4. Review `.stores.json` configuration file

## Quick Reference

| Task | Command |
|------|---------|
| Add new store | `python scripts/add_store.py --store-code "..." --display-name "..." --images-folder "..."` |
| List stores | `python scripts/add_store.py --list` |
| Validate store | `python scripts/add_store.py --validate "..."` |
| Add images | `python scripts/setup_store_images.py --store-code "..." --source-folder "..."` |
| List images | `python scripts/setup_store_images.py --list` |

---

**Last Updated:** April 6, 2025
**Version:** 1.0

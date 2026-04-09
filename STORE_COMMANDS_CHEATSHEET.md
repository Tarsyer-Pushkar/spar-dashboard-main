# Store Management Commands Cheat Sheet

Quick reference for all store-related commands.

## Add Store

### Add with Images
```bash
python scripts/add_store.py \
  --store-code "Spar-20017-New-Store" \
  --display-name "New Store, City Name" \
  --images-folder "C:\path\to\images"
```

### Add Without Images
```bash
python scripts/add_store.py \
  --store-code "Spar-20017-New-Store" \
  --display-name "New Store, City Name"
```

## Manage Images

### Copy Images to Existing Store
```bash
python scripts/setup_store_images.py \
  --store-code "Spar-20017-New-Store" \
  --source-folder "C:\path\to\images"
```

### Overwrite Existing Images
```bash
python scripts/setup_store_images.py \
  --store-code "Spar-20017-New-Store" \
  --source-folder "C:\path\to\images" \
  --copy-all
```

## View & Validate

### List All Stores
```bash
python scripts/add_store.py --list
```

### List All Store Images
```bash
python scripts/setup_store_images.py --list
```

### Validate Store Setup
```bash
python scripts/add_store.py --validate "Spar-20017-New-Store"
```

## File Locations

### Store Configuration
```
.stores.json
```

### Heatmap Images
```
app/static/img/heatmap/
├── Spar-20016-TSM-Mall-Udupi/
├── Spar-30008-Langval-mall-Thanjavur/
└── Spar-20017-New-Store/
```

### Navigation Config
```
app/templates/base.html    (store dropdown)
```

### Store Info
```
app/static/img/heatmap/{store_code}/STORE_INFO.txt
```

## Common Workflows

### Workflow 1: Add Store with All Images

```bash
# 1. Prepare images in C:\images\my_store with correct naming:
#    - location01- Zone A.jpg
#    - location02- Zone B.jpg

# 2. Add store
python scripts/add_store.py \
  --store-code "Spar-20017-My-Store" \
  --display-name "My Store Location" \
  --images-folder "C:\images\my_store"

# 3. Validate
python scripts/add_store.py --validate "Spar-20017-My-Store"

# 4. Restart dashboard and test
```

### Workflow 2: Add Store Now, Images Later

```bash
# 1. Add store (no images)
python scripts/add_store.py \
  --store-code "Spar-20017-Future-Store" \
  --display-name "Future Store"

# 2. Later, when images ready:
python scripts/setup_store_images.py \
  --store-code "Spar-20017-Future-Store" \
  --source-folder "C:\images\future_store"

# 3. Verify
python scripts/add_store.py --list
```

### Workflow 3: Update Images for Existing Store

```bash
# 1. Prepare new images
# 2. Copy with overwrite
python scripts/setup_store_images.py \
  --store-code "Spar-20016-TSM-Mall-Udupi" \
  --source-folder "C:\new\images" \
  --copy-all

# 3. Refresh browser
```

### Workflow 4: Multiple Stores at Once

```bash
# Add Store 1
python scripts/add_store.py \
  --store-code "Spar-20017-Store-One" \
  --display-name "Store One" \
  --images-folder "C:\images\store1"

# Add Store 2
python scripts/add_store.py \
  --store-code "Spar-20018-Store-Two" \
  --display-name "Store Two" \
  --images-folder "C:\images\store2"

# Add Store 3
python scripts/add_store.py \
  --store-code "Spar-20019-Store-Three" \
  --display-name "Store Three" \
  --images-folder "C:\images\store3"

# List all
python scripts/add_store.py --list
```

## Naming Conventions

### Store Code
```
Format: Spar-{number}-{location-name}

✓ Correct:
  - Spar-20016-TSM-Mall-Udupi
  - Spar-30008-Langval-mall-Thanjavur
  - Spar-20017-Phoenix-Mall-Bangalore

✗ Incorrect:
  - TSM-Mall-Udupi (missing Spar- prefix)
  - Spar20016TSM (missing hyphens)
  - spar-20016-udupi (lowercase)
```

### Image Names
```
Format: location{N}- {description}.jpg

✓ Correct:
  - location01- FMCG Food.jpg
  - location02- Grocery.jpg
  - location10- Premium Zone.jpg
  - location25- Customer Lounge.jpg

✗ Incorrect:
  - location1-food.jpg (wrong format)
  - location_01_FMCG.jpg (wrong separators)
  - zone01.jpg (missing "location" prefix)
  - location01 FMCG.jpg (missing hyphen after number)
```

## Display Names

Good display names should be:
- Descriptive
- Include location
- Professional

```
✓ Correct:
  - "TSM Mall, Udupi"
  - "Langval Mall, Thanjavur"
  - "Phoenix Mall, Bangalore"
  - "Westside, Delhi - Store 1"

✗ Avoid:
  - "Store 1" (too generic)
  - "Spar-20017" (just use store code)
  - "New" (too vague)
```

## Quick Help

```bash
# Show add_store options
python scripts/add_store.py --help

# Show setup_store_images options
python scripts/setup_store_images.py --help
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Store not appearing in dropdown | Run: `python scripts/add_store.py --list` |
| Images not showing | Check: `app/static/img/heatmap/{store_code}/` |
| Store exists error | Use different store code or add images: `python scripts/setup_store_images.py ...` |
| Validation fails | Run: `python scripts/add_store.py --validate "{store_code}"` |
| Image copy failed | Check image format (.jpg), folder path, file names |
| Permission denied | Run terminal as Administrator |

---

**Pro Tips:**

1. **Verify Before Adding:**
   ```bash
   # Check if store code already exists
   python scripts/add_store.py --list | grep "your-store-code"
   ```

2. **Batch Operations:**
   ```bash
   # Add multiple stores quickly
   for store in Spar-20017-A Spar-20018-B Spar-20019-C
   do
     python scripts/add_store.py --store-code "$store" --display-name "$store"
   done
   ```

3. **Image Validation:**
   ```bash
   # Check image naming before adding
   ls /path/to/images | grep "location"
   ```

4. **After Adding:**
   - Restart dashboard
   - Test in browser
   - Select new store from dropdown
   - Navigate to Heatmap
   - Verify locations appear

---

**Last Updated:** April 6, 2025

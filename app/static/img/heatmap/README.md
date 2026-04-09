# Heatmap Store-Specific Images

This folder contains heatmap background images organized by store code. Each store can have **any number of location images** - the system dynamically discovers available locations.

## Folder Structure

```
heatmap/
├── Spar-20016-TSM-Mall-Udupi/          # Images for Udupi store (any number)
│   ├── location01- FMCG Food.jpg
│   ├── location02- Grocery.jpg
│   ├── location03- Grocery 2.jpg
│   ├── location04- Home and Living.jpg
│   └── ... more locations if needed
│
├── Spar-30008-Langval-mall-Thanjavur/  # Images for Thanjavur store
│   ├── location01- FMCG Food.jpg
│   ├── location02- Grocery.jpg
│   └── ... more locations if needed
│
└── README.md                             # This file
```

## Adding New Stores

### Option 1: Using Helper Script (Recommended)

```bash
python scripts/setup_store_images.py \
  --store-code "Spar-XXXXX-Store-Name" \
  --source-folder "/path/to/images"
```

List existing stores:
```bash
python scripts/setup_store_images.py --list
```

### Option 2: Manual Setup

1. **Create a new folder** with the store code name:
   ```bash
   mkdir -p app/static/img/heatmap/[NEW-STORE-CODE]
   ```

2. **Add heatmap location images** - Copy JPEG files with location naming:
   ```
   location01- Location Name.jpg
   location02- Location Name.jpg
   location03- Location Name.jpg
   ... (any number of locations)
   ```

3. **Update the store code list** in `app/templates/base.html`:
   ```html
   <option value="Spar-XXXXX-Store-Name">Spar-XXXXX-Store-Name</option>
   ```

## How It Works

1. **User selects store** → Dropdown in navigation bar
2. **Store code passed** → `/api/heatmap-data?store_code=Spar-XXXXX-Name`
3. **Dynamic location discovery** → API scans store folder for `location*.jpg` files
4. **Locations displayed** → Frontend shows all available locations for that store
5. **Images loaded** → Correct store-specific images display in heatmap

## Image Specifications

- **Format**: JPEG (.jpg or .JPG)
- **Naming Convention**: `location{number}- {description}.jpg`
  - Examples:
    - `location01- FMCG Food.jpg`
    - `location02- Grocery.jpg`
    - `location10- Special Promo Zone.jpg`
- **Dimensions**: Recommended 1200px × 800px (any aspect ratio supported)
- **File Size**: Keep under 500KB for optimal performance

## Flexible Image Count

- **No fixed minimum** - Support 1 or 100+ locations per store
- **Dynamically loaded** - No hardcoding required
- **Easy scaling** - Add more locations by adding more images to the folder

## Image Name Parsing

The system automatically extracts location information from filenames:

```
Input:  location01- FMCG Food.jpg
Output: ID=location01, Label=FMCG Food

Input:  location05- Dairy and Frozen.jpg
Output: ID=location05, Label=Dairy and Frozen
```

## Current Stores

| Store Code | Images | Location |
|---|---|---|
| `Spar-20016-TSM-Mall-Udupi` | 9 | TSM Mall, Udupi |
| `Spar-30008-Langval-mall-Thanjavur` | 0 (ready for upload) | Langval Mall, Thanjavur |

## Adding Images to Existing Stores

To add more locations to a store that already exists:

1. Add new image files to the store folder
2. Follow naming: `location{number}- {description}.jpg`
3. Restart the app or refresh the browser
4. New locations appear automatically in dropdown

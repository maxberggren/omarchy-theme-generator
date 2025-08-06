# Omarchy Theme Generator

A theme generator system for [Omarchy](https://omarchy.org) featuring centralized color management and intelligent image-to-theme color extraction.

## 🚀 Quick Start

### Basic Usage

```bash
# Extract colors from any image and build a custom theme
./extract_colors_from_image.py "templates/backgrounds/wallpapersden.com_mount-fuji-4k_3840x2160.jpg" -o colors.json --build
mkdir -p ~/.config/omarchy/themes/generated-theme
cp -r * ~/.config/omarchy/themes/generated-theme/

# If you want to edit some of the extracted colors in colors.json you can then run
./build_theme.py

# Generate a preview of extracted colors
./extract_colors_from_image.py "templates/backgrounds/wallpapersden.com_mount-fuji-4k_3840x2160.jpg" --preview
```

## 🎨 Features

### 🖼️ **Image-to-Theme Color Extraction**
- Extract dominant colors from any image using advanced K-means clustering
- Intelligently map colors to theme categories (dark, middle, light, accents)
- Generate complete themes that match your favorite wallpapers
- **Automatically copy source image as `wallpaper.png` to backgrounds folder**
- Visual color preview generation
- Support for various image formats (JPEG, PNG, etc.)

### 🔧 **Centralized Color Management**
- All colors defined in a single `colors.json` file
- Automatic format conversion for different applications
- Template-based configuration generation
- Consistent colors across all applications

### 🎯 **Smart Color Mapping**
- Brightness and saturation analysis
- Perceptual color distance calculations
- Golden ratio-based accent color generation
- Contrast validation for readability

### 🛠️ **Flexible Build System**
- Build themes from specific color files
- Custom output directories
- Comprehensive error handling
- Backward compatibility maintained

## 📖 Usage Guide

### Image-to-Theme Extraction

Transform any image into a complete theme:

```bash
# Basic extraction (copies image to backgrounds/wallpaper.png)
./extract_colors_from_image.py image.jpg

# Save to specific file with preview
./extract_colors_from_image.py wallpaper.jpg -o my_theme.json --preview

# Complete workflow: extract + build theme + copy wallpaper
./extract_colors_from_image.py background.jpg --build

# Fine-tune with cluster count
./extract_colors_from_image.py photo.png -k 12 --preview
```

**Note**: The script automatically copies your source image to `backgrounds/wallpaper.png` (converted to PNG format) so it's available as a wallpaper for your theme.

#### Options
- `-o, --output`: Specify output file name (default: `colors_from_image.json`)
- `-k, --clusters`: Number of color clusters to extract (default: 8, recommended: 6-12)
- `--preview`: Generate a visual preview of extracted colors
- `--build`: Automatically run `build_theme.py` after extraction

#### Tips for Best Results
- **High contrast images** work best (varied light and dark areas)
- **Images with distinct color areas** produce better accent colors
- Use `-k 6` for simpler, cleaner color palettes
- Use `-k 12-16` for complex images with many distinct colors
- **Natural photos** often yield the most pleasing themes

### Manual Theme Building

Build themes from color definition files:

```bash
# Use default colors.json
python build_theme.py

# Build from specific color file
python build_theme.py custom_colors.json

# Build to custom output directory
python build_theme.py colors.json -o ~/my-themes/

# Get help
python build_theme.py --help
```

### Color Management

#### Adding New Colors

1. Add the color to your `colors.json`:
```json
{
  "colors": {
    "new_color": {
      "hex": "#FF5733",
      "opacity": 1.0,
      "description": "Description of the color"
    }
  }
}
```

2. Use in templates with these placeholders:
   - `{{new_color_hash}}` - `#FF5733`
   - `{{new_color_0x}}` - `0xFF5733`
   - `{{new_color_rgba_1_0}}` - `rgba(255,87,51,1.0)`
   - `{{new_color_rgba_ee}}` - `rgba(#FF5733ee)` (for Hyprland)

3. Run `python build_theme.py` to regenerate files

## 🏗️ How It Works

### Color Extraction Methodology

**K-means Clustering**:
- Resizes images to 200x200 for faster processing while preserving color relationships
- Applies K-means clustering to group similar colors together
- Extracts cluster centers as dominant colors
- Sorts by cluster size to prioritize most prominent colors

**Smart Color Selection**:
- Analyzes brightness, saturation, and hue of extracted colors
- Filters out near-grayscale colors for accent selection
- Uses perceptual color distance for better human-perceived results

### Color Mapping Strategy

| Category | Purpose | Selection Criteria |
|----------|---------|-------------------|
| `base_dark` | Main dark background | Darkest color, not pure black |
| `waybar` | Waybar background | Same as base_dark with opacity |
| `base_middle` | Primary text color | Medium brightness, readable |
| `base01` | Secondary/inactive text | Darker than base_middle |
| `border` | UI element borders | Light, low saturation |
| `base_light01/02` | Light backgrounds | Brightest available colors |
| `accent01-08` | Highlight colors | High saturation, diverse hues |

### Application Format Support

The system automatically converts colors to application-specific formats:

- **Alacritty**: `0xRRGGBB` format
- **btop**: `#RRGGBB` format  
- **Hyprland**: `rgba(#RRGGBBaa)` format with hex alpha
- **Hyprlock**: `rgba(R,G,B,opacity)` format with decimal values
- **Mako**: `#RRGGBB` format
- **CSS files**: `#RRGGBB` and `rgba(R,G,B,opacity)` formats

## 📁 Project Structure

```
night-owl/
├── README.md                           # This comprehensive guide
├── colors.json                         # Central color definitions
├── build_theme.py                      # Theme build script
├── extract_colors_from_image.py        # Image color extraction script
├── templates/                          # Template directory
│   ├── alacritty.toml.template
│   ├── btop.theme.template
│   ├── hyprland.conf.template
│   ├── hyprlock.conf.template
│   ├── mako.ini.template
│   ├── neovim.lua.template
│   ├── swayosd.css.template
│   ├── walker.css.template
│   ├── waybar.css.template
│   └── wofi.css.template
├── backgrounds/                        # Sample background images
└── [generated config files]
```

## 🔄 Workflow Examples

### Creating a Theme from a Wallpaper

```bash
# Test different cluster counts to find the best result
./extract_colors_from_image.py sunset.jpg -k 6 --preview
./extract_colors_from_image.py sunset.jpg -k 10 --preview
./extract_colors_from_image.py sunset.jpg -k 14 --preview

# Build and apply the best result (also copies to backgrounds/wallpaper.png)
./extract_colors_from_image.py sunset.jpg -k 10 --build
```

**Result**: Your `sunset.jpg` is now available as `backgrounds/wallpaper.png` and a complete theme has been generated to match it!

### Creating Multiple Theme Variants

```bash
# Extract colors from different images
./extract_colors_from_image.py ocean.jpg -o ocean_theme.json
./extract_colors_from_image.py forest.jpg -o forest_theme.json
./extract_colors_from_image.py sunset.jpg -o sunset_theme.json

# Build specific variants
python build_theme.py ocean_theme.json -o ~/themes/ocean/
python build_theme.py forest_theme.json -o ~/themes/forest/
python build_theme.py sunset_theme.json -o ~/themes/sunset/
```

### Manual Color Customization

1. **Edit colors**: Modify `colors.json` to change or add colors
2. **Edit templates**: Modify template files if needed for layout changes
3. **Build**: Run `python build_theme.py` to generate configs
4. **Deploy**: Generated files are ready to use

## 🔧 Technical Details

### Dependencies (Auto-managed with uv)

The image extraction script automatically manages its dependencies:

- `pillow` - Image processing
- `scikit-learn` - K-means clustering
- `matplotlib` - Color preview generation  
- `opencv-python` - Image manipulation
- `numpy` - Numerical operations

Dependencies are automatically installed when running the script with `uv`.

### Color Space Considerations
- Extracts colors in RGB space for compatibility
- Uses HSV space for perceptual color analysis
- Implements luminance-based brightness calculations
- Applies color theory principles for accent generation

### Performance Optimizations
- Image resizing for faster K-means convergence
- Efficient numpy operations for pixel processing
- Cached color space conversions
- Optimized cluster analysis

## 🚨 Troubleshooting

### Common Issues

**"No suitable dark colors found"**
- Try increasing cluster count (`-k 12` or higher)
- Check if image has sufficient contrast

**"Colors look too similar"**  
- Use fewer clusters (`-k 6`)
- Try a different image with more color variety

**"Theme looks washed out"**
- Image may be oversaturated or heavily processed
- Try a more natural, unfiltered image

**Build script errors**
```bash
# View available color files
python build_theme.py nonexistent.json
# Shows: Available JSON files in directory

# Get help for any script
./extract_colors_from_image.py --help
python build_theme.py --help
```

## 🎯 Advanced Usage

### Template Customization

Available placeholder formats for any color named `colorname`:
- `{{colorname_hash}}` - `#RRGGBB`
- `{{colorname_0x}}` - `0xRRGGBB` 
- `{{colorname_rgba_1_0}}` - `rgba(R,G,B,1.0)`
- `{{colorname_rgba_0_8}}` - `rgba(R,G,B,0.8)`
- `{{colorname_rgba_ee}}` - `rgba(#RRGGBBee)` (Hyprland format)
- `{{colorname_rgba_88}}` - `rgba(#RRGGBB88)` (Hyprland format)
- `{{colorname_rgba}}` - `rgba(R, G, B, opacity)`

### Integration Benefits

- **Centralized**: All colors defined in one place
- **Consistent**: Same colors across all applications
- **Flexible**: Easy to create variants or adjust specific colors
- **Maintainable**: Changes propagate automatically to all configs
- **Type-safe**: Templates catch missing color references

## ⚠️ Important Notes

- Never edit the generated config files directly - edit templates instead
- Always run the build script after making changes
- Back up your original configs before first use
- Template files use `{{placeholder}}` syntax - don't remove the double braces
- The image extraction script creates themes compatible with the existing template system

## 🌟 What's New

### Recent Updates

**Enhanced Build System**:
- Added command-line argument support to `build_theme.py`
- Can now specify which JSON color file to build from
- Enhanced error handling with helpful suggestions
- Output directory customization option

**Image Color Extraction**:
- Full K-means clustering implementation for robust color extraction
- Intelligent color mapping based on perceptual characteristics
- Automatic theme building integration
- Visual color preview generation

**Improved Workflow**:
- Seamless integration between extraction and building
- Backward compatibility maintained
- Multiple theme variant support
- Enhanced error messages and debugging

This theme system transforms any image into a cohesive, beautiful theme that works across your entire desktop environment!
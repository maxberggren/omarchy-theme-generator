# Night Owl Theme - Centralized Color Management

This theme system uses a centralized color management approach where all colors are defined in a single `colors.json` file and then generated into the appropriate formats for each application.

## 🎨 Color Management

### Main Files

- **`colors.json`** - Central color definitions in `#RRGGBB` format with opacity values
- **`build_theme.py`** - Script that generates all configuration files from templates
- **`templates/`** - Directory containing template files with color placeholders

### Color Format Support

The system automatically converts colors from the central `#RRGGBB` format to these application-specific formats:

- **Alacritty**: `0xRRGGBB` format
- **btop**: `#RRGGBB` format  
- **Hyprland**: `rgba(#RRGGBBaa)` format with hex alpha
- **Hyprlock**: `rgba(R,G,B,opacity)` format with decimal values
- **Mako**: `#RRGGBB` format
- **CSS files**: `#RRGGBB` format and `rgba(R,G,B,opacity)` format

## 🔧 Usage

### Building Theme Files

Run the build script to generate all configuration files:

```bash
python3 build_theme.py
```

This will:
1. Load colors from `colors.json`
2. Process all template files in `templates/`
3. Generate the final configuration files

### Adding New Colors

1. Add the new color to `colors.json`:
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

2. Use the color in templates with these placeholders:
   - `{{new_color_hash}}` - `#FF5733`
   - `{{new_color_0x}}` - `0xFF5733`
   - `{{new_color_rgba_1_0}}` - `rgba(255,87,51,1.0)`
   - `{{new_color_rgba_ee}}` - `rgba(#FF5733ee)` (for Hyprland)
   - etc.

3. Run `python3 build_theme.py` to regenerate files

### Modifying Templates

Template files are located in `templates/` and use `{{variable_name}}` placeholders for colors.

Available placeholder formats for any color named `colorname`:
- `{{colorname_hash}}` - `#RRGGBB`
- `{{colorname_0x}}` - `0xRRGGBB` 
- `{{colorname_rgba_1_0}}` - `rgba(R,G,B,1.0)`
- `{{colorname_rgba_0_8}}` - `rgba(R,G,B,0.8)`
- `{{colorname_rgba_ee}}` - `rgba(#RRGGBBee)` (Hyprland format)
- `{{colorname_rgba_88}}` - `rgba(#RRGGBB88)` (Hyprland format)
- `{{colorname_rgba}}` - `rgba(R, G, B, opacity)`

## 📁 File Structure

```
night-owl/
├── colors.json              # Central color definitions
├── build_theme.py          # Build script
├── templates/              # Template directory
│   ├── alacritty.toml.template
│   ├── btop.theme.template
│   ├── hyprland.conf.template
│   ├── hyprlock.conf.template
│   ├── mako.ini.template
│   ├── swayosd.css.template
│   ├── walker.css.template
│   ├── waybar.css.template
│   └── wofi.css.template
└── [generated config files]
```

## 🔄 Workflow

1. **Edit colors**: Modify `colors.json` to change or add colors
2. **Edit templates**: Modify template files if needed for layout changes
3. **Build**: Run `python3 build_theme.py` to generate configs
4. **Deploy**: Generated files are ready to use

## 🎯 Benefits

- **Centralized**: All colors defined in one place
- **Consistent**: Same colors across all applications
- **Flexible**: Easy to create variants or adjust specific colors
- **Maintainable**: Changes propagate automatically to all configs
- **Type-safe**: Templates catch missing color references

## 🚀 Creating Theme Variants

To create a new theme variant:

1. Copy `colors.json` to `colors-variant.json`
2. Modify the colors in the new file
3. Update the build script to use the new color file
4. Run the build script

## ⚠️ Important Notes

- Never edit the generated config files directly - edit templates instead
- Always run the build script after making changes
- Back up your original configs before first use
- Template files use `{{placeholder}}` syntax - don't remove the double braces
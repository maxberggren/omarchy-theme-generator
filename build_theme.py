#!/usr/bin/env python3
"""
Theme Builder Script for Night Owl
Generates configuration files from templates using centralized color definitions.
"""

import json
import os
import re
from pathlib import Path


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def format_color(color_name, color_data, format_type):
    """Format a color according to the specified format type."""
    hex_color = color_data["hex"]
    opacity = color_data.get("opacity", 1.0)
    
    if format_type == "hash":
        return hex_color
    
    elif format_type == "0x":
        return f"0x{hex_color[1:]}"
    
    elif format_type.startswith("rgba"):
        r, g, b = hex_to_rgb(hex_color)
        
        # Handle different rgba formats
        if format_type == "rgba_1_0":
            return f"rgba({r},{g},{b},{opacity})"
        elif format_type == "rgba_0_8":
            return f"rgba({r},{g},{b},0.8)"
        elif format_type == "rgba_ee":
            # Hyprland format: rgba(HEXee) where ee is alpha in hex (no # symbol)
            return f"rgba({hex_color[1:]}ee)"
        elif format_type == "rgba_88":
            # Hyprland format: rgba(HEX88) where 88 is alpha in hex (no # symbol)  
            return f"rgba({hex_color[1:]}88)"
        elif format_type == "rgba":
            return f"rgba({r}, {g}, {b}, {opacity})"
        else:
            return f"rgba({r},{g},{b},{opacity})"
    
    return hex_color


def load_colors(colors_file):
    """Load colors from JSON file."""
    with open(colors_file, 'r') as f:
        data = json.load(f)
    return data['colors']


def generate_color_vars(colors):
    """Generate all color variables for template replacement."""
    color_vars = {}
    
    # First, generate standard color variants
    for color_name, color_data in colors.items():
        # Generate different format variants
        formats = ["hash", "0x", "rgba_1_0", "rgba_0_8", "rgba_ee", "rgba_88", "rgba"]
        
        for fmt in formats:
            var_name = f"{color_name}_{fmt}"
            color_vars[var_name] = format_color(color_name, color_data, fmt)
    
    # Add hardcoded alpha variants that reference base colors with specific alpha values
    alpha_variants = {
        # New alpha variants using new color names
        "base_dark_alpha": ("base_dark", 0.8),
        "base_dark_low_alpha": ("base_dark", 0.53),
        "base_middle_alpha": ("base_middle", 0.93),
        "base_light01_alpha": ("base_light01", 0.93),
        
        # Legacy alpha variants for backward compatibility
        "base_dark01_alpha": ("base_dark", 0.8),
        "base_dark01_low_alpha": ("base_dark", 0.53),
        "base03_alpha": ("base_dark", 0.8),
        "base03_low_alpha": ("base_dark", 0.53),
        "base0_alpha": ("base_middle", 0.93),
        "base2_alpha": ("base_light01", 0.93),
    }
    
    # Generate format variants for alpha colors
    for alpha_name, (base_color_name, alpha_value) in alpha_variants.items():
        if base_color_name in colors:
            base_color_data = colors[base_color_name].copy()
            base_color_data["opacity"] = alpha_value
            
            formats = ["hash", "0x", "rgba_1_0", "rgba_0_8", "rgba_ee", "rgba_88", "rgba"]
            for fmt in formats:
                var_name = f"{alpha_name}_{fmt}"
                color_vars[var_name] = format_color(alpha_name, base_color_data, fmt)
    
    return color_vars


def process_template(template_path, output_path, color_vars):
    """Process a template file and generate the output configuration."""
    print(f"Processing {template_path} -> {output_path}")
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Replace all color variables in the template
    for var_name, color_value in color_vars.items():
        placeholder = f"{{{{{var_name}}}}}"
        content = content.replace(placeholder, color_value)
    
    # Check for any unreplaced placeholders
    remaining_placeholders = re.findall(r'\{\{[^}]+\}\}', content)
    if remaining_placeholders:
        print(f"Warning: Unreplaced placeholders in {template_path}: {remaining_placeholders}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the processed content
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated {output_path}")


def main():
    """Main build function."""
    script_dir = Path(__file__).parent
    colors_file = script_dir / "colors.json"
    templates_dir = script_dir / "templates"
    
    print("🎨 Building Night Owl theme configurations...")
    print(f"Loading colors from: {colors_file}")
    
    # Load colors
    colors = load_colors(colors_file)
    print(f"Loaded {len(colors)} color definitions")
    
    # Generate color variables
    color_vars = generate_color_vars(colors)
    print(f"Generated {len(color_vars)} color variables")
    
    # Define template mappings
    template_mappings = {
        "alacritty.toml.template": "alacritty.toml",
        "btop.theme.template": "btop.theme",
        "hyprland.conf.template": "hyprland.conf",
        "hyprlock.conf.template": "hyprlock.conf",
        "mako.ini.template": "mako.ini",
        "neovim.lua.template": "neovim.lua",
        "swayosd.css.template": "swayosd.css",
        "walker.css.template": "walker.css",
        "waybar.css.template": "waybar.css",
        "wofi.css.template": "wofi.css",
    }
    
    print("\n📁 Processing templates...")
    
    # Process each template
    for template_name, output_name in template_mappings.items():
        template_path = templates_dir / template_name
        output_path = script_dir / output_name
        
        if template_path.exists():
            process_template(template_path, output_path, color_vars)
        else:
            print(f"Warning: Template {template_path} not found")
    
    print("\n✅ Theme build completed!")
    print("\nGenerated files:")
    for output_name in template_mappings.values():
        output_path = script_dir / output_name
        if output_path.exists():
            print(f"  ✓ {output_name}")
        else:
            print(f"  ✗ {output_name} (failed)")


if __name__ == "__main__":
    main()
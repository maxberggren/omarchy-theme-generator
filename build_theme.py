#!/usr/bin/env python3
"""
Theme Builder Script for Night Owl
Generates configuration files from templates using centralized color definitions.
"""

import argparse
import json
import os
import re
import shutil
import hashlib
import subprocess
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
    
    elif format_type == "rgb_array":
        r, g, b = hex_to_rgb(hex_color)
        return f"[{r}, {g}, {b}]"
    
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
        formats = ["hash", "0x", "rgb_array", "rgba_1_0", "rgba_0_8", "rgba_ee", "rgba_88", "rgba"]
        
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
            
            formats = ["hash", "0x", "rgb_array", "rgba_1_0", "rgba_0_8", "rgba_ee", "rgba_88", "rgba"]
            for fmt in formats:
                var_name = f"{alpha_name}_{fmt}"
                color_vars[var_name] = format_color(alpha_name, base_color_data, fmt)
    
    return color_vars


def create_crx_package(theme_dir, output_path):
    """Create a CRX package from the theme directory."""
    try:
        # Try to create a simple zip package (CRX is essentially a zip with headers)
        import zipfile
        
        zip_path = output_path.with_suffix('.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in theme_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(theme_dir)
                    zipf.write(file_path, arcname)
        
        # Rename to .crx for browser recognition
        crx_path = output_path.with_suffix('.crx')
        zip_path.rename(crx_path)
        return crx_path
    except Exception as e:
        print(f"Warning: Could not create CRX package: {e}")
        return None


def install_browser_extension(theme_dir):
    """Install the Chromium theme extension into supported browsers using multiple methods."""
    installed_browsers = []
    failed_browsers = []
    
    # Browser configurations with multiple installation methods
    browsers = [
        ("Google Chrome", 
         [Path.home() / ".config" / "google-chrome"],
         ["External Extensions", "Extensions"]),
        ("Chromium", 
         [Path.home() / ".config" / "chromium"],
         ["External Extensions", "Extensions"]),
        ("Microsoft Edge", 
         [Path.home() / ".config" / "microsoft-edge"],
         ["External Extensions", "Extensions"]),
        ("Brave", 
         [Path.home() / ".config" / "BraveSoftware" / "Brave-Browser"],
         ["External Extensions", "Extensions"]),
        ("Vivaldi", 
         [Path.home() / ".config" / "vivaldi"],
         ["External Extensions", "Extensions"]),
    ]
    
    # Generate consistent extension ID from theme directory path
    extension_id = hashlib.sha256(str(theme_dir).encode()).hexdigest()[:32]
    # Replace numbers with letters to ensure valid extension ID
    extension_id = ''.join(['abcdefghij'[int(c)] if c.isdigit() else c for c in extension_id])
    
    # Try to create a CRX package for better compatibility
    crx_path = create_crx_package(theme_dir, theme_dir.parent / f"theme_{extension_id}")
    
    for browser_name, config_dirs, ext_subpaths in browsers:
        browser_installed = False
        for config_dir in config_dirs:
            if config_dir.exists():
                try:
                    # Method 1: External Extensions (development mode)
                    if "External Extensions" in ext_subpaths:
                        ext_dir = config_dir / "External Extensions"
                        ext_dir.mkdir(parents=True, exist_ok=True)
                        
                        ext_config = {
                            "path": str(theme_dir),
                            "location": "external"
                        }
                        
                        config_file = ext_dir / f"{extension_id}.json"
                        with open(config_file, 'w') as f:
                            json.dump(ext_config, f, indent=2)
                        
                        print(f"  ✓ {browser_name} (External): {config_file}")
                    
                    # Method 2: Direct Extensions directory with symlink
                    if "Extensions" in ext_subpaths:
                        ext_dir = config_dir / "Extensions" / extension_id
                        ext_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Create version directory
                        version_dir = ext_dir / "1.0_0"
                        if version_dir.exists():
                            shutil.rmtree(version_dir)
                        
                        # Copy theme files directly
                        shutil.copytree(theme_dir, version_dir)
                        print(f"  ✓ {browser_name} (Direct): {version_dir}")
                    
                    # Method 3: Try CRX installation if available
                    if crx_path and crx_path.exists():
                        try:
                            # Copy CRX to browser's extension directory
                            crx_dest = config_dir / f"theme_{extension_id}.crx"
                            shutil.copy2(crx_path, crx_dest)
                            print(f"  ✓ {browser_name} (CRX): {crx_dest}")
                        except Exception:
                            pass  # CRX method failed, but others might work
                    
                    # Method 4: Preferences modification (advanced)
                    try:
                        prefs_file = config_dir / "Default" / "Preferences"
                        if prefs_file.exists():
                            # Try to add extension to preferences
                            with open(prefs_file, 'r') as f:
                                prefs = json.load(f)
                            
                            # Ensure extensions section exists
                            if 'extensions' not in prefs:
                                prefs['extensions'] = {}
                            if 'settings' not in prefs['extensions']:
                                prefs['extensions']['settings'] = {}
                            
                            # Add our extension
                            prefs['extensions']['settings'][extension_id] = {
                                "active_permissions": {"api": ["theme"]},
                                "creation_flags": 1,
                                "from_webstore": False,
                                "location": 4,  # External extension
                                "manifest": {
                                    "description": "A dark theme generated from extracted colors",
                                    "manifest_version": 3,
                                    "name": "Generated Theme",
                                    "theme": True,
                                    "version": "1.0"
                                },
                                "path": str(theme_dir),
                                "state": 1,  # Enabled
                                "was_installed_by_default": False
                            }
                            
                            # Write back preferences
                            with open(prefs_file, 'w') as f:
                                json.dump(prefs, f, indent=2)
                            
                            print(f"  ✓ {browser_name} (Prefs): Extension added to preferences")
                    except Exception as e:
                        pass  # Preferences modification failed
                    
                    if not browser_installed:
                        installed_browsers.append(browser_name)
                        browser_installed = True
                    break  # Config dir found, move to next browser
                    
                except Exception as e:
                    if not browser_installed:
                        failed_browsers.append(f"{browser_name}: {str(e)}")
    
    # Method 5: Try system-wide installation (requires sudo)
    try_system_install(theme_dir, extension_id, installed_browsers, failed_browsers)
    
    # Method 6: Try command-line installation
    try_command_line_install(theme_dir, crx_path, installed_browsers, failed_browsers)
    
    return installed_browsers, failed_browsers


def try_command_line_install(theme_dir, crx_path, installed_browsers, failed_browsers):
    """Try installing via command line arguments."""
    browsers_cmd = [
        ("Google Chrome", ["google-chrome", "google-chrome-stable"]),
        ("Chromium", ["chromium", "chromium-browser"]),
        ("Microsoft Edge", ["microsoft-edge", "microsoft-edge-stable"]),
        ("Brave", ["brave", "brave-browser"]),
    ]
    
    for browser_name, commands in browsers_cmd:
        for cmd in commands:
            try:
                # Check if browser is available
                result = subprocess.run(['which', cmd], capture_output=True)
                if result.returncode == 0:
                    # Try to install the extension using command line
                    if crx_path and crx_path.exists():
                        try:
                            # Some browsers support loading extensions via command line
                            subprocess.run([
                                cmd, 
                                f'--load-extension={theme_dir}',
                                '--no-first-run',
                                '--no-default-browser-check'
                            ], capture_output=True, timeout=5)
                            print(f"  ✓ {browser_name} (CLI): Extension load attempted")
                            if f"{browser_name} (CLI)" not in installed_browsers:
                                installed_browsers.append(f"{browser_name} (CLI)")
                            break
                        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                            # Command line method failed, continue
                            pass
            except Exception:
                continue


def try_system_install(theme_dir, extension_id, installed_browsers, failed_browsers):
    """Try system-wide extension installation."""
    system_paths = [
        "/opt/google/chrome/extensions",
        "/usr/share/google-chrome/extensions",
        "/opt/chromium/extensions",
        "/usr/share/chromium/extensions"
    ]
    
    for sys_path in system_paths:
        sys_dir = Path(sys_path)
        if sys_dir.parent.exists():
            try:
                # Try without sudo first (in case user has permissions)
                sys_dir.mkdir(parents=True, exist_ok=True)
                
                config_file = sys_dir / f"{extension_id}.json"
                ext_config = {
                    "external_crx": str(theme_dir),
                    "external_version": "1.0"
                }
                
                with open(config_file, 'w') as f:
                    json.dump(ext_config, f, indent=2)
                
                print(f"  ✓ System-wide: {config_file}")
                if "System-wide" not in installed_browsers:
                    installed_browsers.append("System-wide")
                break
                
            except PermissionError:
                # Try with sudo
                try:
                    subprocess.run(['sudo', 'mkdir', '-p', str(sys_dir)], check=True, capture_output=True)
                    
                    config_content = json.dumps({
                        "external_crx": str(theme_dir),
                        "external_version": "1.0"
                    }, indent=2)
                    
                    process = subprocess.run(
                        ['sudo', 'tee', str(config_file)],
                        input=config_content,
                        text=True,
                        capture_output=True
                    )
                    
                    if process.returncode == 0:
                        print(f"  ✓ System-wide (sudo): {config_file}")
                        if "System-wide" not in installed_browsers:
                            installed_browsers.append("System-wide")
                        break
                        
                except subprocess.CalledProcessError:
                    continue
            except Exception:
                continue


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


def write_readme(output_dir: Path, colors_file: Path):
    """Generate a README.md with activation and Chromium theme instructions."""
    readme_path = output_dir / "README.md"

    default_omarchy_dir = Path.home() / ".config" / "omarchy" / "themes"
    is_under_default = str(output_dir).startswith(str(default_omarchy_dir))

    theme_folder_name = output_dir.name
    chromium_dir = output_dir / "chromium-theme"

    lines = []
    lines.append(f"# Omarchy Theme: {theme_folder_name}")
    lines.append("")
    lines.append("This folder was generated by the Omarchy theme generator.")
    lines.append("Colors source: `colors.json`")
    lines.append("")
    lines.append("## Activate the Omarchy desktop theme")
    if is_under_default:
        lines.append(f"This theme is already placed under the default Omarchy themes dir: `{default_omarchy_dir}`.")
    else:
        lines.append("You can keep this theme here or move/symlink it under the default directory:")
        lines.append(f"`{default_omarchy_dir}/`")
    lines.append("")
    lines.append("- Ensure Omarchy is installed and running")
    lines.append("- Select this theme in the Omarchy theme selector or place it under the directory above")
    lines.append("- Reload Hyprland and related apps if needed:")
    lines.append("  - `hyprctl reload` (if Hyprland is running)")
    lines.append("  - Wallpaper is at `backgrounds/wallpaper.png`; common reload methods:")
    lines.append("    - `hyprctl hyprpaper preload <path>` then `hyprctl hyprpaper wallpaper <monitor>,<path>`")
    lines.append("    - `swww img <path>`")
    lines.append("")
    lines.append("Generated configs cover Hyprland, Waybar, Mako, Wofi, Walker, SwayOSD, Alacritty, Neovim, and btop.")
    lines.append("")
    lines.append("## Chromium/Chrome/Brave/Vivaldi theme (manual install)")
    if chromium_dir.exists() and (chromium_dir / "manifest.json").exists():
        lines.append("A Chromium theme has been generated in `chromium-theme/`.")
    else:
        lines.append("If `chromium-theme/` exists, you can load it as an unpacked extension.")
    lines.append("")
    lines.append("Steps:")
    lines.append("1. Open `chrome://extensions/`")
    lines.append("2. Enable 'Developer mode'")
    lines.append("3. Click 'Load unpacked' and select the `chromium-theme` folder inside this theme")
    lines.append("")
    lines.append("To remove or disable, manage it from `chrome://extensions/`.")
    lines.append("")
    lines.append("## Rebuilding")
    lines.append("Regenerate this folder with:")
    lines.append("```")
    lines.append("python3 build_theme.py colors.json -o .")
    lines.append("```")
    lines.append("")
    lines.append("Or extract colors and build in one step:")
    lines.append("```")
    lines.append("./extract_colors_from_image.py <image-path-or-url> --build --output <colors.json> --output-dir <target-folder>")
    lines.append("```")

    readme_path.write_text("\n".join(lines))
    print(f"  ✓ README.md written to: {readme_path}")

def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Build Night Owl theme from color definitions")
    parser.add_argument("colors_file", nargs="?", default="colors.json",
                       help="Path to colors JSON file (default: colors.json)")
    parser.add_argument("-o", "--output-dir", help="Output directory for generated files")
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    
    # Handle colors file path
    colors_file = Path(args.colors_file)
    if not colors_file.is_absolute():
        colors_file = script_dir / colors_file
    
    # Handle output directory - default to Omarchy themes directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Generate directly to Omarchy themes directory instead of polluting project root
        output_dir = Path.home() / ".config" / "omarchy" / "themes" / "generated-theme"
        output_dir.mkdir(parents=True, exist_ok=True)
    
    templates_dir = script_dir / "templates"
    
    print("🎨 Building Night Owl theme configurations...")
    print(f"Loading colors from: {colors_file}")
    
    if not colors_file.exists():
        print(f"❌ Error: Colors file '{colors_file}' not found.")
        print(f"Available JSON files in {script_dir}:")
        for json_file in script_dir.glob("*.json"):
            print(f"  • {json_file.name}")
        return 1
    
    # Load colors
    try:
        colors = load_colors(colors_file)
        print(f"Loaded {len(colors)} color definitions")
    except Exception as e:
        print(f"❌ Error loading colors: {e}")
        return 1
    
    # Generate color variables
    color_vars = generate_color_vars(colors)
    print(f"Generated {len(color_vars)} color variables")
    
    # Define template mappings
    template_mappings = {
        "alacritty.toml.template": "alacritty.toml",
        "btop.theme.template": "btop.theme",
        "chromium-theme/manifest.json.template": "chromium-theme/manifest.json",
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
        output_path = output_dir / output_name
        
        if template_path.exists():
            process_template(template_path, output_path, color_vars)
            
            # Special handling for chromium-theme: copy additional files
            if template_name.startswith("chromium-theme/"):
                template_dir = templates_dir / "chromium-theme"
                output_dir_chromium = output_path.parent
                
                # Copy any non-template files from the chromium-theme template directory
                for file_path in template_dir.glob("*"):
                    if file_path.is_file() and not file_path.name.endswith(".template"):
                        dest_path = output_dir_chromium / file_path.name
                        shutil.copy2(file_path, dest_path)
                        print(f"Copied {file_path.name} to {dest_path}")
        else:
            print(f"Warning: Template {template_path} not found")
    
    print("\n✅ Theme build completed!")
    print(f"📁 Generated directly to: {output_dir}")
    print("\nGenerated files:")
    for output_name in template_mappings.values():
        output_path = output_dir / output_name
        if output_path.exists():
            print(f"  ✓ {output_name}")
        else:
            print(f"  ✗ {output_name} (failed)")
    
    # Copy backgrounds directory from project root to theme output
    project_backgrounds = script_dir / "backgrounds"
    theme_backgrounds = output_dir / "backgrounds"
    
    if project_backgrounds.exists():
        # Copy backgrounds from project to theme directory
        if theme_backgrounds.exists():
            shutil.rmtree(theme_backgrounds)
        shutil.copytree(project_backgrounds, theme_backgrounds)
        print(f"  ✓ backgrounds/ (copied from project)")
    elif theme_backgrounds.exists():
        print(f"  ✓ backgrounds/ (already exists in theme)")
    
    # Copy the colors file into the output directory as colors.json
    try:
        dest_colors_path = output_dir / "colors.json"
        shutil.copy2(colors_file, dest_colors_path)
        print(f"  ✓ colors.json (copied to theme folder)")
    except Exception as e:
        print(f"⚠️  Failed to copy colors file: {e}")

    # Copy this build script into the output directory for easy rebuilding
    try:
        script_source = Path(__file__).resolve()
        script_dest = output_dir / "build_theme.py"
        shutil.copy2(script_source, script_dest)
        print(f"  ✓ build_theme.py (copied to theme folder)")
    except Exception as e:
        print(f"⚠️  Failed to copy build script: {e}")

    print(f"\n🎨 Your theme is now ready to be selected in the Omarchy theme selector!")
    print(f"💡 If you're happy with the results, rename the folder to preserve it from overwrites.")

    # Generate README with instructions (and rely on manual browser installation)
    try:
        write_readme(output_dir, colors_file)
    except Exception as e:
        print(f"⚠️  Failed to write README.md: {e}")
    
    # Automatic reloads are disabled; reload manually if desired
    
    return 0


def try_reload_hyprland(theme_dir):
    """Reload actions disabled by request."""
    return


def try_reload_wallpaper(theme_dir):
    """Reload actions disabled by request."""
    return


def try_reload_other_apps(theme_dir):
    """Reload actions disabled by request."""
    return


if __name__ == "__main__":
    import sys
    sys.exit(main())
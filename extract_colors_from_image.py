#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pillow",
#     "scikit-learn", 
#     "matplotlib",
#     "opencv-python",
#     "numpy",
# ]
# ///
"""
Image-to-Theme Color Extraction Script
Extract colors from an image and generate a Night Owl theme configuration.

This script uses K-means clustering to extract dominant colors from an image,
then intelligently maps them to theme color categories based on brightness,
saturation, and visual characteristics.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any
import colorsys
import numpy as np

try:
    from PIL import Image
    from sklearn.cluster import KMeans
    import matplotlib.pyplot as plt
    import cv2
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Dependencies should be automatically installed by uv.")
    print("If you're not using uv, install manually:")
    print("pip install pillow scikit-learn matplotlib opencv-python numpy")
    sys.exit(1)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def rgb_to_hsv(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB (0-255) to HSV (0-1, 0-1, 0-1)."""
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_rgb(hsv: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert HSV (0-1, 0-1, 0-1) to RGB (0-255)."""
    r, g, b = colorsys.hsv_to_rgb(*hsv)
    return (int(r * 255), int(g * 255), int(b * 255))


def extract_dominant_colors(image_path: str, k: int = 8, resize_size: Tuple[int, int] = (200, 200)) -> List[Tuple[int, int, int]]:
    """
    Extract dominant colors from an image using K-means clustering.
    
    Args:
        image_path: Path to the image file
        k: Number of clusters (colors) to extract
        resize_size: Size to resize image for faster processing
        
    Returns:
        List of RGB tuples representing dominant colors
    """
    # Load and resize image for faster processing
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize(resize_size, Image.Resampling.LANCZOS)
    
    # Convert to numpy array and reshape to list of pixels
    img_array = np.array(img)
    pixels = img_array.reshape((-1, 3))
    
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Get cluster centers (dominant colors)
    colors = kmeans.cluster_centers_.astype(int)
    
    # Get cluster sizes to sort by dominance
    labels = kmeans.labels_
    unique, counts = np.unique(labels, return_counts=True)
    
    # Sort colors by cluster size (most dominant first)
    color_counts = list(zip(colors, counts))
    color_counts.sort(key=lambda x: x[1], reverse=True)
    
    return [tuple(color) for color, _ in color_counts]


def calculate_brightness(rgb: Tuple[int, int, int]) -> float:
    """Calculate perceived brightness using luminance formula."""
    r, g, b = rgb
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


def calculate_saturation(rgb: Tuple[int, int, int]) -> float:
    """Calculate color saturation."""
    _, s, _ = rgb_to_hsv(rgb)
    return s


def is_near_grayscale(rgb: Tuple[int, int, int], threshold: float = 0.15) -> bool:
    """Check if a color is near grayscale (low saturation)."""
    return calculate_saturation(rgb) < threshold


def find_color_category(colors: List[Tuple[int, int, int]], category: str) -> Tuple[int, int, int]:
    """
    Find the best color for a specific category based on brightness and saturation.
    
    Args:
        colors: List of dominant colors
        category: Category name ('dark', 'middle', 'light', 'accent')
        
    Returns:
        RGB tuple for the best matching color
    """
    if category == 'dark':
        # Find darkest color that's not pure black
        candidates = [c for c in colors if calculate_brightness(c) < 0.3 and calculate_brightness(c) > 0.05]
        if not candidates:
            candidates = [c for c in colors if calculate_brightness(c) < 0.4]
        return min(candidates, key=calculate_brightness) if candidates else colors[-1]
    
    elif category == 'middle':
        # Find medium brightness color, prefer slightly saturated
        candidates = [c for c in colors if 0.25 < calculate_brightness(c) < 0.75]
        if not candidates:
            candidates = colors
        return min(candidates, key=lambda c: abs(calculate_brightness(c) - 0.5))
    
    elif category == 'light':
        # Find bright color that's not pure white
        candidates = [c for c in colors if calculate_brightness(c) > 0.7 and calculate_brightness(c) < 0.95]
        if not candidates:
            candidates = [c for c in colors if calculate_brightness(c) > 0.6]
        return max(candidates, key=calculate_brightness) if candidates else colors[0]
    
    elif category == 'accent':
        # Find most saturated color that's not too dark or too light
        candidates = [c for c in colors if 0.2 < calculate_brightness(c) < 0.8 and not is_near_grayscale(c)]
        if not candidates:
            candidates = [c for c in colors if not is_near_grayscale(c)]
        return max(candidates, key=calculate_saturation) if candidates else colors[0]
    
    return colors[0]


def adjust_color_brightness(rgb: Tuple[int, int, int], target_brightness: float) -> Tuple[int, int, int]:
    """Adjust a color's brightness while maintaining hue and saturation."""
    h, s, v = rgb_to_hsv(rgb)
    return hsv_to_rgb((h, s, target_brightness))


def generate_color_variations(base_rgb: Tuple[int, int, int], variations: List[float]) -> List[Tuple[int, int, int]]:
    """Generate brightness variations of a base color."""
    h, s, _ = rgb_to_hsv(base_rgb)
    return [hsv_to_rgb((h, s, v)) for v in variations]


def map_colors_to_theme(dominant_colors: List[Tuple[int, int, int]]) -> Dict[str, Any]:
    """
    Map extracted dominant colors to theme color categories.
    
    Args:
        dominant_colors: List of dominant colors from image
        
    Returns:
        Dictionary containing theme color definitions
    """
    # Find base colors for main categories
    base_dark = find_color_category(dominant_colors, 'dark')
    base_middle = find_color_category(dominant_colors, 'middle')
    base_light = find_color_category(dominant_colors, 'light')
    
    # Generate variations for the base colors
    # Create darker and lighter versions of middle color for base01 and border
    middle_h, middle_s, middle_v = rgb_to_hsv(base_middle)
    base01 = hsv_to_rgb((middle_h, middle_s, max(0.1, middle_v - 0.2)))  # Darker version
    border = hsv_to_rgb((middle_h, max(0.3, middle_s - 0.2), min(0.9, middle_v + 0.2)))  # Lighter, less saturated
    
    # Generate light variations
    light_h, light_s, light_v = rgb_to_hsv(base_light)
    base_light01 = base_light
    base_light02 = hsv_to_rgb((light_h, max(0, light_s - 0.1), min(1.0, light_v + 0.05)))
    
    # Find accent colors from remaining colors
    accent_candidates = [c for c in dominant_colors if not is_near_grayscale(c, 0.2)]
    
    # Generate diverse accent colors
    accents = []
    used_hues = set()
    
    for color in accent_candidates:
        h, s, v = rgb_to_hsv(color)
        hue_bucket = int(h * 12)  # Divide hue space into 12 buckets
        
        if hue_bucket not in used_hues and len(accents) < 8:
            # Ensure accent has good saturation and reasonable brightness
            accent_s = max(0.6, s)
            accent_v = max(0.4, min(0.8, v))
            accents.append(hsv_to_rgb((h, accent_s, accent_v)))
            used_hues.add(hue_bucket)
    
    # Fill remaining accents with color-shifted versions
    while len(accents) < 8:
        base_accent = accents[0] if accents else find_color_category(dominant_colors, 'accent')
        h, s, v = rgb_to_hsv(base_accent)
        
        # Shift hue by a golden ratio to get pleasing color combinations
        hue_shift = 0.618 * len(accents)  # Golden ratio
        new_h = (h + hue_shift) % 1.0
        accents.append(hsv_to_rgb((new_h, max(0.6, s), max(0.4, min(0.8, v)))))
    
    # Create theme color definitions
    theme_colors = {
        "base_dark": {
            "hex": rgb_to_hex(base_dark),
            "opacity": 1.0,
            "description": "Dark background used for most"
        },
        "waybar": {
            "hex": rgb_to_hex(base_dark),
            "opacity": 0.8,
            "description": "Waybar background"
        },
        "border": {
            "hex": rgb_to_hex(border),
            "opacity": 1.0,
            "description": "Border color derived from image"
        },
        "base01": {
            "hex": rgb_to_hex(base01),
            "opacity": 1.0,
            "description": "Dark text/inactive"
        },
        "base_middle": {
            "hex": rgb_to_hex(base_middle),
            "opacity": 1.0,
            "description": "Main text color derived from image"
        },
        "base_light01": {
            "hex": rgb_to_hex(base_light01),
            "opacity": 1.0,
            "description": "Light background"
        },
        "base_light02": {
            "hex": rgb_to_hex(base_light02),
            "opacity": 1.0,
            "description": "Lightest background"
        }
    }
    
    # Add accent colors
    accent_names = ["accent01", "accent02", "accent03", "accent04", 
                   "accent05", "accent06", "accent07", "accent08"]
    accent_descriptions = ["Red accent color", "Green accent color", "Yellow accent color", 
                          "Blue accent color", "Magenta accent color", "Cyan accent color",
                          "Violet accent color", "Orange accent color"]
    
    for i, (name, desc) in enumerate(zip(accent_names, accent_descriptions)):
        if i < len(accents):
            theme_colors[name] = {
                "hex": rgb_to_hex(accents[i]),
                "opacity": 1.0,
                "description": f"{desc} derived from image"
            }
    
    return theme_colors


def create_color_preview(colors: List[Tuple[int, int, int]], output_path: str, title: str = "Extracted Colors"):
    """Create a visual preview of extracted colors."""
    fig, ax = plt.subplots(1, 1, figsize=(12, 2))
    
    # Create color swatches
    for i, color in enumerate(colors):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, facecolor=np.array(color)/255.0))
        
        # Add hex label
        hex_color = rgb_to_hex(color)
        brightness = calculate_brightness(color)
        text_color = 'white' if brightness < 0.5 else 'black'
        
        ax.text(i + 0.5, 0.5, hex_color, ha='center', va='center', 
                color=text_color, fontsize=8, rotation=90)
    
    ax.set_xlim(0, len(colors))
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=14, pad=20)
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def copy_wallpaper_to_backgrounds(source_image_path: str, script_dir: Path) -> str:
    """
    Copy the source image to backgrounds folder as wallpaper.png.
    
    Args:
        source_image_path: Path to the source image
        script_dir: Script directory containing backgrounds folder
        
    Returns:
        Path to the copied wallpaper file
    """
    source_path = Path(source_image_path)
    backgrounds_dir = script_dir / "backgrounds"
    
    # Create backgrounds directory if it doesn't exist
    backgrounds_dir.mkdir(exist_ok=True)
    
    # Target wallpaper path - always PNG
    wallpaper_path = backgrounds_dir / "wallpaper.png"
    
    try:
        # Load image and convert to PNG format
        from PIL import Image
        with Image.open(source_path) as img:
            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Convert RGBA/LA/P to RGB with white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = rgb_img
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as PNG
            img.save(wallpaper_path, 'PNG', optimize=True)
        
        return str(wallpaper_path)
    except Exception as e:
        print(f"⚠️  Warning: Could not copy wallpaper to backgrounds folder - {e}")
        return ""


def main():
    """Main function to run the image-to-theme extraction."""
    parser = argparse.ArgumentParser(description="Extract colors from image and generate theme")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("-o", "--output", help="Output colors.json file path", 
                       default="colors_from_image.json")
    parser.add_argument("-k", "--clusters", type=int, default=8, 
                       help="Number of color clusters to extract (default: 8)")
    parser.add_argument("--preview", help="Generate color preview image", 
                       action="store_true")
    parser.add_argument("--build", help="Automatically run build_theme.py after extraction", 
                       action="store_true")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found.")
        sys.exit(1)
    
    print(f"🎨 Extracting colors from: {args.image_path}")
    print(f"📊 Using {args.clusters} color clusters")
    
    # Get script directory for copying wallpaper
    script_dir = Path(__file__).parent
    
    # Copy image to backgrounds folder as wallpaper
    print("📁 Copying image to backgrounds folder...")
    wallpaper_path = copy_wallpaper_to_backgrounds(args.image_path, script_dir)
    if wallpaper_path:
        print(f"🖼️  Wallpaper copied to: {wallpaper_path}")
    
    # Extract dominant colors
    try:
        dominant_colors = extract_dominant_colors(args.image_path, k=args.clusters)
        print(f"✅ Extracted {len(dominant_colors)} dominant colors")
    except Exception as e:
        print(f"❌ Error extracting colors: {e}")
        sys.exit(1)
    
    # Generate color preview if requested
    if args.preview:
        preview_path = args.output.replace('.json', '_preview.png')
        try:
            create_color_preview(dominant_colors, preview_path, 
                               f"Dominant Colors from {os.path.basename(args.image_path)}")
            print(f"🖼️  Color preview saved to: {preview_path}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create preview - {e}")
    
    # Map colors to theme
    print("🎯 Mapping colors to theme categories...")
    theme_colors = map_colors_to_theme(dominant_colors)
    
    # Create final colors.json structure
    colors_json = {
        "colors": theme_colors,
        "_metadata": {
            "source_image": os.path.abspath(args.image_path),
            "wallpaper_path": wallpaper_path if wallpaper_path else "not copied",
            "extraction_method": "k-means clustering",
            "clusters": args.clusters,
            "generated_by": "extract_colors_from_image.py"
        }
    }
    
    # Save colors.json
    try:
        with open(args.output, 'w') as f:
            json.dump(colors_json, f, indent=2)
        print(f"💾 Theme colors saved to: {args.output}")
    except Exception as e:
        print(f"❌ Error saving colors: {e}")
        sys.exit(1)
    
    # Show color mapping summary
    print("\n🎨 Generated Color Mapping:")
    for color_name, color_data in theme_colors.items():
        hex_color = color_data["hex"]
        description = color_data["description"]
        print(f"  {color_name:<15} {hex_color:<8} - {description}")
    
    # Automatically run build_theme.py if requested
    if args.build:
        script_dir = Path(__file__).parent
        build_script = script_dir / "build_theme.py"
        
        if build_script.exists():
            print(f"\n🔨 Running build_theme.py with {args.output}...")
            import subprocess
            
            try:
                result = subprocess.run([sys.executable, str(build_script), args.output], 
                                      cwd=str(script_dir), capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ Theme build completed successfully!")
                    print(result.stdout)
                else:
                    print("❌ Theme build failed:")
                    print(result.stderr)
            except Exception as e:
                print(f"❌ Error running build script: {e}")
        else:
            print(f"⚠️  Warning: build_theme.py not found at {build_script}")
    
    print("\n🎉 Image-to-theme extraction completed!")


if __name__ == "__main__":
    main()
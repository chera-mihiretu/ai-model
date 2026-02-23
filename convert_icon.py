#!/usr/bin/env python3
"""
Convert logo.png to icon.ico with multiple sizes for Windows
"""
from PIL import Image
import sys

def convert_to_ico(input_path, output_path):
    """Convert PNG to ICO with multiple sizes"""
    try:
        # Open the source image
        img = Image.open(input_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create different sizes
        sizes = [(256, 256), (48, 48), (32, 32), (16, 16)]
        
        # Resize and save as ICO
        img.save(output_path, format='ICO', sizes=sizes)
        print(f"✓ Successfully converted {input_path} to {output_path}")
        print(f"  Icon sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
        return True
    except Exception as e:
        print(f"✗ Error converting icon: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    input_file = 'story-bible-electron/frontend/public/assets/logo.png'
    output_file = 'story-bible-electron/electron/icon.ico'
    
    success = convert_to_ico(input_file, output_file)
    sys.exit(0 if success else 1)

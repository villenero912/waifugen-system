#!/usr/bin/env python3
"""
Dataset Builder for WaifuGen LoRA Training
"""

import os
import sys
import argparse
import requests
import shutil
from pathlib import Path
from urllib.parse import urlparse

# Add parent dir to path to import src if needed
sys.path.append(str(Path(__file__).parent.parent))

def download_image(url, save_dir, index):
    """Download a single image from a URL."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        if response.status_code == 200:
            # Try to guess extension
            path = urlparse(url).path
            ext = os.path.splitext(path)[1]
            if not ext:
                ext = ".jpg"
            
            filename = f"ref_{index:03d}{ext}"
            filepath = save_dir / filename
            
            with open(filepath, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
            
            print(f"✅ Downloaded: {filename}")
            return True
    except Exception as e:
        print(f"❌ Error downloading {url}: {e}")
    return False

def main():
    parser = argparse.ArgumentParser(description="WaifuGen Dataset Helper")
    parser.add_argument("--urls", type=str, help="Path to text file with image URLs")
    parser.add_argument("--name", type=str, required=True, help="Character name (e.g., 'aiko_hayashi')")
    parser.add_argument("--output", type=str, default="dataset/raw", help="Base output directory")
    
    args = parser.parse_args()
    
    # Create character-specific path: dataset/raw/character_name
    character_dir = Path(args.output) / args.name
    character_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Dataset Builder initialized for: {args.name}")
    print(f"Target Directory: {character_dir.resolve()}")
    
    if args.urls:
        if not os.path.exists(args.urls):
            print(f"❌ File not found: {args.urls}")
            return
            
        print(f"⬇️  Downloading images from {args.urls}...")
        with open(args.urls, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
            
        count = 0
        for i, url in enumerate(urls):
            if download_image(url, character_dir, i+1):
                count += 1
        
        print(f"\n✨ Dataset collection for '{args.name}' complete.")
        print(f"✅ {count} images downloaded.")
        print("next steps: Clean these images manually.")
        
    else:
        print("\nℹ️  Usage Mode:")
        print(f"python scripts/dataset_builder.py --name {args.name} --urls sources.txt")
        print("\nOr manually place images in the target folder.")

if __name__ == "__main__":
    main()

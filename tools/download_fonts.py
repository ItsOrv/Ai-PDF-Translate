"""
Script to download Persian fonts for the PDF translator.
"""
import os
import sys
import requests
import shutil
from pathlib import Path

def download_file(url, local_path):
    """Download a file from URL to local path."""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        print(f"Downloaded {url} to {local_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def main():
    """Download Persian fonts."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Create fonts directory if it doesn't exist
    fonts_dir = project_root / 'fonts'
    fonts_dir.mkdir(exist_ok=True)
    
    # Persian fonts to download
    font_urls = {
        # Vazirmatn fonts (a modern Persian font)
        'Vazirmatn-Regular.ttf': 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf',
        'Vazirmatn-Bold.ttf': 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf',
        'Vazirmatn-Light.ttf': 'https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Light.ttf',
        
        # Sahel font (updated URL)
        'Sahel-Regular.ttf': 'https://github.com/rastikerdar/sahel-font/raw/master/dist/Sahel.ttf',
        
        # Samim font (updated URL)
        'Samim-Regular.ttf': 'https://github.com/rastikerdar/samim-font/raw/master/dist/Samim.ttf'
    }
    
    # Download each font
    success_count = 0
    for font_name, font_url in font_urls.items():
        font_path = fonts_dir / font_name
        if font_path.exists():
            print(f"Font {font_name} already exists, skipping download")
            success_count += 1
            continue
            
        if download_file(font_url, font_path):
            success_count += 1
    
    print(f"\nDownloaded {success_count} of {len(font_urls)} fonts")
    
    if success_count == len(font_urls):
        print("All fonts downloaded successfully!")
    else:
        print("Some fonts could not be downloaded. Please check the error messages above.")

if __name__ == "__main__":
    main() 
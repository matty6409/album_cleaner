"""
File-related utility functions for infrastructure layer.
"""
from typing import Dict
import os


def clean_album_images(album_dir: str) -> Dict[str, str]:
    """
    Rename images in the album folder: first image to 'cover', others to 'supplementary_N'.
    Returns a mapping of old to new image names.
    """
    image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
    mapping = {}
    images = [f for f in os.listdir(album_dir) if os.path.splitext(f)[1].lower() in image_exts]
    for i, img in enumerate(sorted(images)):
        ext = os.path.splitext(img)[1].lower()
        if i == 0:
            new_name = f"cover{ext}"
        else:
            new_name = f"supplementary_{i}{ext}"
        mapping[img] = new_name
    return mapping

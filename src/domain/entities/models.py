from pydantic import BaseModel, validator, root_validator
from typing import Dict, List, Optional
import os

class Track(BaseModel):
    track_number: int
    name: str
    filename: str

class Album(BaseModel):
    singer_name: str
    album_name: str
    tracks: List[Track]
    expected_track_count: int
    images: Optional[List[str]] = None
    supplementary: Optional[List[str]] = None

    @root_validator
    def validate_tracks(cls, values):
        tracks = values.get('tracks', [])
        expected = values.get('expected_track_count', 0)
        # 1. Validate track count
        if len(tracks) != expected:
            raise ValueError(f"Expected {expected} tracks, got {len(tracks)}")
        # 2. Validate unique track names and numbers
        seen_names = set()
        seen_numbers = set()
        for t in tracks:
            if t.name in seen_names:
                raise ValueError(f"Duplicate track name: {t.name}")
            if t.track_number in seen_numbers:
                raise ValueError(f"Duplicate track number: {t.track_number}")
            seen_names.add(t.name)
            seen_numbers.add(t.track_number)
        # 3. Validate order (track numbers must be sorted)
        numbers = [t.track_number for t in tracks]
        if numbers != sorted(numbers):
            raise ValueError("Track numbers are not in order")
        return values

    @staticmethod
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
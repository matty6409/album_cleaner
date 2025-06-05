"""
Core domain entities and value objects for the Album Cleaner system.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict
import os


class Language(Enum):
    """Supported languages for track name processing."""
    ENGLISH = "English"
    TRADITIONAL_CHINESE = "Traditional Chinese"
    
    @classmethod
    def from_string(cls, value: str) -> "Language":
        """Create Language from string value."""
        for lang in cls:
            if lang.value.lower() == value.lower():
                return lang
        raise ValueError(f"Unsupported language: {value}")
    
    def __str__(self) -> str:
        return self.value


@dataclass
class Track:
    """Represents a music track."""
    filename: str
    track_number: Optional[int] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    
    def __post_init__(self):
        """Validate track data after initialization."""
        if not self.filename:
            raise ValueError("Track filename cannot be empty")


@dataclass
class Album:
    """Represents a music album."""
    name: str
    artist: str
    tracks: List[Track]
    language: Language = Language.ENGLISH
    year: Optional[int] = None
    
    def __post_init__(self):
        """Validate album data after initialization."""
        if not self.name:
            raise ValueError("Album name cannot be empty")
        if not self.artist:
            raise ValueError("Album artist cannot be empty")
        if not self.tracks:
            raise ValueError("Album must have at least one track")


@dataclass
class ProcessingOptions:
    """Options for album processing."""
    base_path: str
    language: Language = Language.ENGLISH
    output_mode: str = "copy"  # "copy" or "in_place"
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate processing options."""
        if not self.base_path:
            raise ValueError("Base path cannot be empty")
        if self.output_mode not in ["copy", "in_place"]:
            raise ValueError("Output mode must be 'copy' or 'in_place'")
        if self.max_retries < 1:
            raise ValueError("Max retries must be at least 1")


@dataclass
class ProcessingResult:
    """Result of processing an album."""
    album_path: str
    success: bool
    error_message: Optional[str] = None
    files_processed: int = 0
    language_used: Language = Language.ENGLISH


# Utility functions for backwards compatibility and album cleaning
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
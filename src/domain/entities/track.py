"""
Core domain entity representing an audio track.
"""
from dataclasses import dataclass
from typing import Optional
from .file import File


@dataclass
class Track:
    """Represents a music track with its core properties."""
    file: File
    track_number: Optional[int] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    
    def __post_init__(self):
        """Validate track data after initialization."""
        if not self.file:
            raise ValueError("Track must have an associated file")

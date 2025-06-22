"""
Core domain entity representing a music album.
"""
from dataclasses import dataclass
from typing import List, Optional
from .track import Track
from domain.values_objects.language import Language  # Updated import


@dataclass
class Album:
    """Represents a music album with its core properties."""
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

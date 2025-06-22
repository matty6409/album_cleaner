"""
Core domain entity representing a file in the system.
"""
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class File:
    """Represents a file in the system with its core properties."""
    path: str
    name: str
    extension: str
    
    @classmethod
    def from_path(cls, file_path: str) -> "File":
        """Create a File instance from a file path."""
        name, ext = os.path.splitext(os.path.basename(file_path))
        return cls(
            path=file_path,
            name=name,
            extension=ext
        )
    
    def __post_init__(self):
        """Validate file data after initialization."""
        if not self.path:
            raise ValueError("File path cannot be empty")
        if not self.name:
            raise ValueError("File name cannot be empty")

    @property
    def full_name(self) -> str:
        """Get the complete filename with extension."""
        return f"{self.name}{self.extension}"

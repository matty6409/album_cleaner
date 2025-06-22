"""
Value objects for language support.
"""
from enum import Enum


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

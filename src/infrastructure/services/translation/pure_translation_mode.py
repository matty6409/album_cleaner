"""
Implementation of pure translation mode for album_cleaner.
This is a direct conversion mode using OpenCC without any LLM processing.
Automatically detects and converts simplified Chinese to traditional Chinese.
"""
import os
from typing import Dict, List

from opencc import OpenCC
from infrastructure.logging.logger import logger


class PureTranslationMode:
    """
    Pure translation mode implementation for automatically converting filenames
    from Simplified to Traditional Chinese when detected, without using LLMs.
    """
    
    def __init__(self):
        """Initialize the pure translation mode with OpenCC converter."""
        self.cc = OpenCC('s2t')  # Simplified to Traditional Chinese converter
    
    def process_album(self, album_path: str, local_files: List[str]) -> Dict[str, str]:
        """
        Process an album by always translating filenames from Simplified to Traditional Chinese.
        
        Args:
            album_path: Path to the album directory
            local_files: List of local audio filenames
            
        Returns:
            Dictionary mapping old filename -> new filename with traditional Chinese
        """
        logger.info(f"Using pure translation mode for {len(local_files)} files")
        
        # Create mapping with automatic OpenCC conversion applied
        mapping = {}
        for filename in local_files:
            # Extract name and extension
            name, ext = os.path.splitext(filename)
            
            # Convert to traditional Chinese
            converted_name = self.cc.convert(name)
            
            # Clean filename of invalid characters
            converted_name = self._clean_filename(converted_name)
            
            # Create new filename
            new_filename = f"{converted_name}{ext}"
            mapping[filename] = new_filename
            
            if filename != new_filename:
                logger.info(f"Auto-translation: {filename} -> {new_filename}")
        
        return mapping
    
    def translate_artist_album(self, artist_name: str, album_name: str) -> tuple:
        """
        Automatically translate artist and album names to Traditional Chinese when simplified Chinese is detected.
        
        Args:
            artist_name: Artist name (potentially in Simplified Chinese)
            album_name: Album name (potentially in Simplified Chinese)
            
        Returns:
            Tuple of (converted_artist_name, converted_album_name)
        """
        converted_artist = self.cc.convert(artist_name)
        converted_album = self.cc.convert(album_name)
        
        if artist_name != converted_artist:
            logger.info(f"Auto-artist translation: {artist_name} -> {converted_artist}")
        if album_name != converted_album:
            logger.info(f"Auto-album translation: {album_name} -> {converted_album}")
            
        return converted_artist, converted_album
    
    def _clean_filename(self, name: str) -> str:
        """
        Clean filename of invalid characters.
        
        Args:
            name: Filename to clean
            
        Returns:
            Cleaned filename
        """
        import re
        return re.sub(r'[<>:"/\\|?*]', '', name)

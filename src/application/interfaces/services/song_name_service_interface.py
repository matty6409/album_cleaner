from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from domain.entities.models import Language

class SongNameService(ABC):
    """
    Abstract service for retrieving official song and album names.
    """
    
    @abstractmethod
    def search_album(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language = Language.ENGLISH
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Search for official album information.
        
        Args:
            artist_name: Artist name to search for
            album_name: Album name to search for
            language: Target language for results
            
        Returns:
            Tuple of (clean_artist_name, clean_album_name, track_names) or None if not found
        """
        pass
    
    @abstractmethod
    def get_track_names(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language = Language.ENGLISH
    ) -> Optional[List[str]]:
        """
        Get official track names for an album.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            language: Target language for results
            
        Returns:
            List of official track names in order, or None if not found
        """
        pass

"""
Interface for Quality Assurance Service.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from domain.values_objects.language import Language

class QualityAssuranceService(ABC):
    """
    Interface for LLM-powered quality assurance of album cleaning results.
    """
    
    @abstractmethod
    def review_mapping_quality(
        self,
        artist_name: str,
        album_name: str,
        local_files: List[str],
        proposed_mapping: Dict[str, str],
        official_tracks: List[str],
        target_language: Language
    ) -> Dict[str, any]:
        """
        Review the quality of a proposed filename mapping.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            local_files: List of original filenames
            proposed_mapping: Proposed old_file -> new_file mapping
            official_tracks: Official track names (if available)
            target_language: Target language for output
            
        Returns:
            Dictionary with review results:
            {
                "approved": bool,
                "issues": List[str],
                "recommendations": List[str],
                "confidence_score": float,
                "language_compliance": bool,
                "track_number_compliance": bool
            }
        """
        pass
    
    @abstractmethod
    def suggest_search_alternatives(
        self,
        artist_name: str,
        album_name: str,
        failed_searches: List[str],
        target_language: Language
    ) -> List[str]:
        """
        Suggest alternative search terms when initial Spotify searches fail.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            failed_searches: List of search terms that failed
            target_language: Target language
            
        Returns:
            List of alternative search terms to try
        """
        pass

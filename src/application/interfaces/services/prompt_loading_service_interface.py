from abc import ABC, abstractmethod
from typing import Dict, Any, List
from domain.values_objects.language import Language  # Updated import

class PromptLoadingService(ABC):
    """
    Abstract service for loading and processing prompt templates.
    """
    
    @abstractmethod
    def load_prompt_template(self, template_path: str) -> Dict[str, str]:
        """
        Load prompt template from file.
        
        Args:
            template_path: Path to the prompt template file
            
        Returns:
            Dictionary with 'system' and 'user' prompt templates
        """
        pass
    
    @abstractmethod
    def render_prompt(
        self, 
        template: str, 
        variables: Dict[str, Any]
    ) -> str:
        """
        Render a prompt template with variables using Jinja2.
        
        Args:
            template: The prompt template string with Jinja2 syntax
            variables: Dictionary of variables to substitute
            
        Returns:
            Rendered prompt string
        """
        pass
    
    @abstractmethod
    def render_album_cleaning_prompts(
        self,
        local_files: List[str],
        artist_name: str,
        album_name: str,
        official_tracks: List[str],
        language: Language
    ) -> Dict[str, str]:
        """
        Render complete album cleaning prompts with all required data.
        
        Args:
            local_files: List of current local filenames
            artist_name: Official artist name
            album_name: Official album name
            official_tracks: List of official track names (empty for LLM-only mode)
            language: Target language for processing
            
        Returns:
            Dictionary with 'system' and 'user' rendered prompts
        """
        pass
        
    @abstractmethod
    def render_search_terms_prompts(
        self,
        artist_name: str,
        album_name: str,
        language: Language,
        local_files: List[str] = None
    ) -> Dict[str, str]:
        """
        Render prompts for generating optimized search terms.
        
        Args:
            artist_name: Artist name to optimize for search
            album_name: Album name to optimize for search
            language: Target language for processing
            local_files: List of local filenames to analyze for artist clues
            
        Returns:
            Dictionary with 'system' and 'user' rendered prompts
        """
        pass

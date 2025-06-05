from typing import Dict, List
from application.interfaces.services.llm_service_interface import LLMService
from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

class OpenAILLMService(LLMService):
    """
    Example: Alternative LLM service implementation using OpenAI.
    Demonstrates how easy it is to add new providers with clean architecture.
    """
    
    def __init__(self, prompt_loader: PromptLoadingService, settings: Settings, prompt_path: str):
        """
        Initialize OpenAI LLM service.
        
        Args:
            prompt_loader: Service for loading prompt templates
            settings: Application settings (would need openai_api_key added)
            prompt_path: Path to the prompt template file
        """
        self.prompt_loader = prompt_loader
        self.settings = settings
        self.prompt_path = prompt_path
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load prompt templates from file."""
        try:
            templates = self.prompt_loader.load_prompt_template(self.prompt_path)
            self.system_template = templates['system']
            self.user_template = templates['user']
            logger.info(f"Loaded OpenAI prompt templates from {self.prompt_path}")
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {e}")
            raise
    
    def generate_filename_mapping(
        self, 
        local_files: List[str], 
        artist_name: str,
        album_name: str,
        official_tracks: List[str],
        language: str
    ) -> Dict[str, str]:
        """
        Generate mapping from local filenames to cleaned filenames using OpenAI.
        
        Args:
            local_files: List of current local filenames
            artist_name: Official artist name
            album_name: Official album name
            official_tracks: List of official track names in order
            language: Target language ('English' or 'Traditional Chinese')
            
        Returns:
            Dictionary mapping old filename -> new filename
        """
        try:
            # This would integrate with OpenAI API
            # For demo purposes, showing the interface compatibility
            
            logger.info(f"Using OpenAI for mapping {len(local_files)} files")
            
            # Prepare variables for prompt rendering
            variables = {
                'album_name': album_name,
                'artist_name': artist_name,
                'files': '\n'.join([f"{i+1}. {file}" for i, file in enumerate(local_files)]),
                'official_tracks': '\n'.join([f"{i+1}. {track}" for i, track in enumerate(official_tracks)]),
                'language': language
            }
            
            # Render prompts
            system_prompt = self.prompt_loader.render_prompt(self.system_template, variables)
            user_prompt = self.prompt_loader.render_prompt(self.user_template, variables)
            
            # Would call OpenAI API here instead of Perplexity
            # from openai import OpenAI
            # client = OpenAI(api_key=self.settings.openai_api_key)
            # response = client.chat.completions.create(...)
            
            # For demo, return a simple mapping
            mapping = {}
            for i, local_file in enumerate(local_files):
                if i < len(official_tracks):
                    # Extract extension
                    import os
                    ext = os.path.splitext(local_file)[1]
                    # Create standardized filename
                    track_num = f"{i+1:02d}"
                    official_name = official_tracks[i]
                    new_filename = f"{track_num} {official_name}{ext}"
                    mapping[local_file] = new_filename
            
            logger.info(f"Generated OpenAI mapping for {len(mapping)} files")
            return mapping
            
        except Exception as e:
            logger.error(f"OpenAI LLM request failed: {e}")
            raise

# Example of how to use the new service:
"""
# In the CLI service factory:
def create_services_with_openai(settings: Settings, prompt_path: str):
    prompt_loader = YamlPromptLoader()
    file_repository = FileRepository()
    
    # Use OpenAI instead of Perplexity
    llm_service = OpenAILLMService(prompt_loader, settings, prompt_path)
    song_name_service = SpotifySongNameService(settings)
    
    use_case = AlbumCleanerUseCase(llm_service, song_name_service, file_repository)
    return use_case
"""

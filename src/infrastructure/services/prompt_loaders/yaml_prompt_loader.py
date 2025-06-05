import yaml
import os
from typing import Dict, Any, List
from jinja2 import Template, Environment, BaseLoader
from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from domain.entities.models import Language

class YamlPromptLoader(PromptLoadingService):
    """
    Concrete implementation for loading YAML prompt templates with Jinja2 support.
    """
    
    def __init__(self, prompts_dir: str = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt templates
        """
        if prompts_dir is None:
            # Default to src/prompts directory from project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up to project root (from src/infrastructure/services/prompt_loaders)
            project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
            self.prompts_dir = os.path.join(project_root, "src", "prompts")
        else:
            self.prompts_dir = prompts_dir
        
        self.jinja_env = Environment(loader=BaseLoader())
    
    def load_prompt_template(self, template_path: str) -> Dict[str, str]:
        """
        Load prompt template from YAML file.
        
        Args:
            template_path: Path to the YAML prompt template file
            
        Returns:
            Dictionary with 'system' and 'user' prompt templates
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            if not isinstance(prompt_data, dict):
                raise ValueError(f"Invalid YAML structure in {template_path}")
                
            if 'system' not in prompt_data or 'user' not in prompt_data:
                raise ValueError(f"YAML file must contain 'system' and 'user' keys")
                
            return {
                'system': prompt_data['system'],
                'user': prompt_data['user']
            }
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template file not found: {template_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {template_path}: {e}")
    
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
        try:
            jinja_template = self.jinja_env.from_string(template)
            return jinja_template.render(**variables)
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")
    
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
        # Load the template
        template_path = os.path.join(self.prompts_dir, "cleaner_prompt.yaml")
        templates = self.load_prompt_template(template_path)
        
        # Prepare variables for rendering
        variables = {
            'files': local_files,  # Template expects 'files', not 'local_files'
            'artist_name': artist_name,
            'album_name': album_name,
            'official_tracks': official_tracks,
            'language': language.value,
            'has_official_tracks': len(official_tracks) > 0
        }
        
        # Render both prompts
        return {
            'system': self.render_prompt(templates['system'], variables),
            'user': self.render_prompt(templates['user'], variables)
        }
        
    def render_search_terms_prompts(
        self,
        artist_name: str,
        album_name: str,
        language: Language
    ) -> Dict[str, str]:
        """
        Render prompts for generating optimized search terms.
        
        Args:
            artist_name: Artist name to optimize for search
            album_name: Album name to optimize for search
            language: Target language for processing
            
        Returns:
            Dictionary with 'system' and 'user' rendered prompts
        """
        # Load the template
        template_path = os.path.join(self.prompts_dir, "search_terms_prompt.yaml")
        templates = self.load_prompt_template(template_path)
        
        # Prepare variables for rendering
        variables = {
            'artist_name': artist_name,
            'album_name': album_name,
            'language': language.value
        }
        
        # Render both prompts
        return {
            'system': self.render_prompt(templates['system'], variables),
            'user': self.render_prompt(templates['user'], variables)
        }

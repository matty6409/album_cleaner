from enum import Enum
from application.use_cases.album_cleaner_use_case import AlbumCleanerUseCase
from infrastructure.services.llm_services.perplexity_llm_service import PerplexityLLMService
from infrastructure.services.llm_services.openrouter_deepseek_llm_service import OpenRouterDeepSeekLLMService
from infrastructure.services.music_services.spotify_song_name_service import SpotifySongNameService
from infrastructure.services.music_services.enhanced_spotify_song_name_service import EnhancedSpotifySongNameService
from infrastructure.services.prompt_loaders.yaml_prompt_loader import YamlPromptLoader
from infrastructure.repositories.file_repository import FileRepository
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

class LLMProvider(Enum):
    """Supported LLM providers."""
    PERPLEXITY = "perplexity"
    OPENROUTER_DEEPSEEK = "openrouter-deepseek"

class ServiceFactory:
    """
    Factory for creating and wiring up services with dependency injection.
    Demonstrates the power of clean architecture - easy to swap implementations.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the service factory.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Create shared infrastructure services
        self.prompt_loader = YamlPromptLoader()
        self.file_repository = FileRepository()
        
        # Use basic Spotify service by default
        self.song_name_service = SpotifySongNameService(settings)
        self.use_enhanced_search = False
    
    def create_llm_service(self, provider: LLMProvider):
        """
        Create LLM service based on provider type.
        
        Args:
            provider: LLM provider to use
            
        Returns:
            Configured LLM service instance
        """
        if provider == LLMProvider.PERPLEXITY:
            logger.info("Creating Perplexity LLM service")
            return PerplexityLLMService(self.settings)
        elif provider == LLMProvider.OPENROUTER_DEEPSEEK:
            logger.info("Creating OpenRouter DeepSeek LLM service")
            return OpenRouterDeepSeekLLMService(self.settings)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def create_album_cleaner_use_case(self, llm_provider: LLMProvider) -> AlbumCleanerUseCase:
        """
        Create the main album cleaner use case with the specified LLM provider.
        
        Args:
            llm_provider: LLM provider to use
            
        Returns:
            Configured AlbumCleanerUseCase instance
        """
        # Create LLM service based on provider
        llm_service = self.create_llm_service(llm_provider)
        
        # Enable enhanced search if not already enabled
        if not self.use_enhanced_search:
            # Only create a new instance if needed (to avoid redundant creation)
            self.song_name_service = EnhancedSpotifySongNameService(
                settings=self.settings,
                llm_service=llm_service,
                prompt_service=self.prompt_loader
            )
            self.use_enhanced_search = True
            logger.info(f"Automatically enabled enhanced search with {llm_provider.value} provider")
        
        # Wire up the use case with all dependencies
        use_case = AlbumCleanerUseCase(
            llm_service=llm_service,
            song_name_service=self.song_name_service,
            file_repository=self.file_repository,
            prompt_service=self.prompt_loader
        )
        
        logger.info(f"Created album cleaner use case with {llm_provider} LLM provider")
        return use_case
    
    def list_available_providers(self) -> list[str]:
        """
        List all available LLM providers.
        
        Returns:
            List of provider names
        """
        return [provider.value for provider in LLMProvider]
    
    def validate_provider_config(self, provider: LLMProvider) -> bool:
        """
        Validate that the required configuration is available for a provider.
        
        Args:
            provider: LLM provider to validate
            
        Returns:
            True if configuration is valid
        """
        if provider == LLMProvider.PERPLEXITY:
            return bool(self.settings.perplexity_api_key)
        elif provider == LLMProvider.OPENROUTER_DEEPSEEK:
            return bool(self.settings.openrouter_api_key)
            
    def enable_enhanced_search(self, llm_provider: LLMProvider) -> None:
        """
        Enable enhanced search using LLM-optimized search terms.
        
        Args:
            llm_provider: LLM provider to use for search term generation
        """
        llm_service = self.create_llm_service(llm_provider)
        self.song_name_service = EnhancedSpotifySongNameService(
            settings=self.settings,
            llm_service=llm_service,
            prompt_service=self.prompt_loader
        )
        self.use_enhanced_search = True
        logger.info(f"Enabled enhanced search with {llm_provider.value} provider")
        return False

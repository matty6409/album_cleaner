from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """
    Pydantic settings for environment/configuration variables.
    Loads from .env by default.
    """
    # Perplexity API settings
    perplexity_api_key: str = Field(..., env="PERPLEXITY_API_KEY")
    base_url: str = Field(default="https://api.perplexity.ai")
    model: str = Field(default="sonar-pro")
    
    # Spotify API settings
    spotify_client_id: str = Field(..., env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(..., env="SPOTIFY_CLIENT_SECRET")
    
    # DeepSeek API settings (optional)
    deepseek_api_key: str = Field(default="", env="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", env="DEEPSEEK_MODEL")
    
    # OpenRouter API settings (optional)
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_deepseek_model: str = Field(default="deepseek/deepseek-chat", env="OPENROUTER_DEEPSEEK_MODEL")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file

from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """
    Pydantic settings for environment/configuration variables.
    Loads from .env by default.
    """
    perplexity_api_key: str = Field(..., env="PERPLEXITY_API_KEY")
    base_url: str = Field(default="https://api.perplexity.ai")
    model: str = Field(default="sonar-pro")
    deepseek_api_key: str = Field(default="", env="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", env="DEEPSEEK_MODEL")

    class Config:
        env_file = ".env" 
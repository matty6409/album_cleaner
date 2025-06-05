import json
from typing import Dict, List
from openai import OpenAI
from application.interfaces.services.llm_service_interface import LLMService
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

class PerplexityLLMService(LLMService):
    """
    Concrete implementation of LLM service using Perplexity API.
    Uses simplified interface that accepts pre-rendered prompts.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Perplexity LLM service.
        
        Args:
            settings: Application settings containing Perplexity credentials
        """
        self.settings = settings
        self._init_client()
    
    def _init_client(self) -> None:
        """Initialize OpenAI client configured for Perplexity."""
        try:
            self.client = OpenAI(
                api_key=self.settings.perplexity_api_key,
                base_url="https://api.perplexity.ai"
            )
            logger.info("Perplexity client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity client: {e}")
            raise
    
    def generate_response(
        self, 
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Generate response from Perplexity LLM using pre-rendered prompts.
        
        Args:
            system_prompt: Pre-rendered system prompt
            user_prompt: Pre-rendered user prompt
            
        Returns:
            Raw LLM response as string
        """
        try:
            logger.info("Generating response using Perplexity")
            
            response = self.client.chat.completions.create(
                model="llama-3.1-sonar-small-128k-online",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            result = response.choices[0].message.content
            logger.info("Successfully generated response from Perplexity")
            return result
            
        except Exception as e:
            logger.error(f"Error generating response from Perplexity: {e}")
            raise

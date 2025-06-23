from abc import ABC, abstractmethod
from typing import Dict, Any, List
from domain.values_objects.language import Language  # Updated import

class LLMService(ABC):
    """
    Abstract service for LLM operations with simplified interface.
    The use case will handle prompt loading and rendering.
    """
    
    @abstractmethod
    def generate_response(
        self, 
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Generate response from LLM using pre-rendered prompts.
        
        Args:
            system_prompt: Pre-rendered system prompt
            user_prompt: Pre-rendered user prompt
            
        Returns:
            Raw LLM response as string
        """
        pass
    
    def generate_search_terms(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> List[str]:
        """
        Generate optimized search terms using LLM.
        
        Args:
            system_prompt: Pre-rendered system prompt for search term generation
            user_prompt: Pre-rendered user prompt for search term generation
            
        Returns:
            List of optimized search terms/queries
        """
        # Default implementation delegates to generate_response and parses JSON result
        import json
        import re
        
        response = self.generate_response(system_prompt, user_prompt)
        
        # Try to extract JSON from response
        try:
            # First try direct JSON parsing
            if response.strip().startswith('['):
                return json.loads(response)
            
            # Try to extract JSON array from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find JSON array anywhere in the text
            json_match = re.search(r'(\[(?:[^[\]]|\[(?:[^[\]]|\[[^[\]]*\])*\])*\])', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
                
            # If no JSON found, look for quoted strings that look like search terms
            terms = re.findall(r'"(artist:[^"]+)"', response)
            if terms:
                return terms
                
            # Last resort: split by lines and take lines that look like search terms
            lines = [line.strip() for line in response.split('\n')]
            potential_terms = [line for line in lines if 'artist:' in line and 'album:' in line]
            if potential_terms:
                return potential_terms
                
            # If all else fails, return the full response as a single item
            return [response.strip()]
            
        except Exception as e:
            # If parsing fails, return response as a single item
            return [response.strip()]

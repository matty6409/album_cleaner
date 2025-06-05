"""
Unit tests for LLM services.
Tests both Perplexity and OpenRouter DeepSeek implementations.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from typing import Dict, List
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from application.interfaces.services.llm_service_interface import LLMService
from infrastructure.services.llm_services.perplexity_llm_service import PerplexityLLMService
from infrastructure.services.llm_services.openrouter_deepseek_llm_service import OpenRouterDeepSeekLLMService
from infrastructure.config.settings import Settings
from domain.entities.models import Language


class TestLLMServices:
    """Test cases for LLM service implementations."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.perplexity_api_key = "test_perplexity_key"
        settings.openrouter_api_key = "test_openrouter_key"
        return settings
    
    @pytest.fixture
    def sample_system_prompt(self):
        """Sample system prompt for testing."""
        return "You are a music file alignment specialist. Respond only with JSON mapping."
    
    @pytest.fixture
    def sample_user_prompt(self):
        """Sample user prompt for testing."""
        return """Please generate JSON mapping for these audio files:

Audio Files:
- 01 Track One.flac
- 02 Track Two.flac
- 03 Track Three.flac

Official Tracks:
1. Official Track One
2. Official Track Two
3. Official Track Three

Artist: Test Artist
Album: Test Album
Language: English"""

    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response with proper JSON format."""
        return '{"01 Track One.flac": "01 Official Track One.flac", "02 Track Two.flac": "02 Official Track Two.flac", "03 Track Three.flac": "03 Official Track Three.flac"}'

    def test_perplexity_service_initialization(self, mock_settings):
        """Test Perplexity LLM service initialization."""
        service = PerplexityLLMService(mock_settings)
        
        assert service.settings == mock_settings
        assert hasattr(service, 'generate_response')

    def test_openrouter_service_initialization(self, mock_settings):
        """Test OpenRouter DeepSeek LLM service initialization."""
        service = OpenRouterDeepSeekLLMService(mock_settings)
        
        assert service.settings == mock_settings
        assert hasattr(service, 'generate_response')

    @patch('infrastructure.services.llm_services.perplexity_llm_service.OpenAI')
    def test_perplexity_response_generation(
        self, 
        mock_openai,
        mock_settings,
        sample_system_prompt,
        sample_user_prompt,
        sample_llm_response
    ):
        """Test Perplexity LLM response generation."""
        # Setup mocks for OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = sample_llm_response
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = PerplexityLLMService(mock_settings)
        
        result = service.generate_response(
            system_prompt=sample_system_prompt,
            user_prompt=sample_user_prompt
        )
        
        assert result == sample_llm_response

    @patch('infrastructure.services.llm_services.openrouter_deepseek_llm_service.OpenAI')
    def test_openrouter_response_generation(
        self, 
        mock_openai,
        mock_settings,
        sample_system_prompt,
        sample_user_prompt,
        sample_llm_response
    ):
        """Test OpenRouter DeepSeek LLM response generation."""
        # Setup mocks for OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = sample_llm_response
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = OpenRouterDeepSeekLLMService(mock_settings)
        
        result = service.generate_response(
            system_prompt=sample_system_prompt,
            user_prompt=sample_user_prompt
        )
        
        assert result == sample_llm_response

    @patch('infrastructure.services.llm_services.perplexity_llm_service.OpenAI')
    def test_perplexity_api_error_handling(
        self,
        mock_openai,
        mock_settings,
        sample_system_prompt,
        sample_user_prompt
    ):
        """Test handling of API errors in Perplexity service."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        service = PerplexityLLMService(mock_settings)
        
        with pytest.raises(Exception) as exc_info:
            service.generate_response(
                system_prompt=sample_system_prompt,
                user_prompt=sample_user_prompt
            )
        
        assert "API Error" in str(exc_info.value)

    @patch('infrastructure.services.llm_services.openrouter_deepseek_llm_service.OpenAI')
    def test_openrouter_api_error_handling(
        self,
        mock_openai,
        mock_settings,
        sample_system_prompt,
        sample_user_prompt
    ):
        """Test handling of API errors in OpenRouter service."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        service = OpenRouterDeepSeekLLMService(mock_settings)
        
        with pytest.raises(Exception) as exc_info:
            service.generate_response(
                system_prompt=sample_system_prompt,
                user_prompt=sample_user_prompt
            )
        
        assert "API Error" in str(exc_info.value)

    @patch('infrastructure.services.llm_services.perplexity_llm_service.OpenAI')
    def test_chinese_language_prompt_handling(
        self,
        mock_openai,
        mock_settings
    ):
        """Test handling of Traditional Chinese prompts."""
        chinese_system_prompt = "你是音樂檔案對齊專家。只回覆JSON映射。"
        chinese_user_prompt = """請為這些音訊檔案生成JSON映射：

音訊檔案：
- 01 愛的故事.flac
- 02 月亮代表我的心.flac

官方曲目：
1. 愛的故事
2. 月亮代表我的心

歌手：鄧麗君
專輯：愛情故事
語言：繁體中文"""

        chinese_response = '{"01 愛的故事.flac": "01 愛的故事.flac", "02 月亮代表我的心.flac": "02 月亮代表我的心.flac"}'
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = chinese_response
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = PerplexityLLMService(mock_settings)
        
        result = service.generate_response(
            system_prompt=chinese_system_prompt,
            user_prompt=chinese_user_prompt
        )
        
        assert result == chinese_response
        assert "愛的故事" in result
        assert "月亮代表我的心" in result

    def test_service_interface_compliance(self, mock_settings):
        """Test that both services implement the LLMService interface."""
        perplexity_service = PerplexityLLMService(mock_settings)
        openrouter_service = OpenRouterDeepSeekLLMService(mock_settings)
        
        # Both should be instances of LLMService
        assert isinstance(perplexity_service, LLMService)
        assert isinstance(openrouter_service, LLMService)
        
        # Both should have the required generate_response method
        assert hasattr(perplexity_service, 'generate_response')
        assert hasattr(openrouter_service, 'generate_response')
        assert callable(perplexity_service.generate_response)
        assert callable(openrouter_service.generate_response)

    @patch('infrastructure.services.llm_services.perplexity_llm_service.OpenAI')
    def test_empty_response_handling(
        self,
        mock_openai,
        mock_settings,
        sample_system_prompt,
        sample_user_prompt
    ):
        """Test handling of empty responses from LLM."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = ""
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = PerplexityLLMService(mock_settings)
        
        result = service.generate_response(
            system_prompt=sample_system_prompt,
            user_prompt=sample_user_prompt
        )
        
        # Should return empty string without error
        assert result == ""

    @patch('infrastructure.services.llm_services.openrouter_deepseek_llm_service.OpenAI')
    def test_whitespace_response_handling(
        self,
        mock_openai,
        mock_settings,
        sample_system_prompt,
        sample_user_prompt
    ):
        """Test handling of whitespace-only responses from LLM."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "   \n\t   "
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = OpenRouterDeepSeekLLMService(mock_settings)
        
        result = service.generate_response(
            system_prompt=sample_system_prompt,
            user_prompt=sample_user_prompt
        )
        
        # Should return the whitespace content as-is
        assert result == "   \n\t   "

    @patch('infrastructure.services.llm_services.perplexity_llm_service.OpenAI')
    def test_large_prompt_handling(self, mock_openai):
        """Test handling of large prompts."""
        large_system_prompt = "You are a specialist. " * 1000
        large_user_prompt = "Process these files: " + ", ".join([f"file_{i}.mp3" for i in range(1000)])
        
        # Configure mock settings
        mock_settings = Mock(spec=Settings)
        mock_settings.perplexity_api_key = "test_perplexity_key"
        
        # Set up mock client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '{"result": "processed"}'
        mock_client.chat = Mock()
        mock_client.chat.completions = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        service = PerplexityLLMService(mock_settings)
        
        result = service.generate_response(
            system_prompt=large_system_prompt,
            user_prompt=large_user_prompt
        )
        

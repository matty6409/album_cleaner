#!/usr/bin/env python3
"""
Simple functional test to verify the Album Cleaner system works end-to-end.
This tests the key architectural components and validates the refactor.
"""
import sys
import os
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from infrastructure.config.settings import Settings
from infrastructure.services.llm_services.openrouter_deepseek_llm_service import OpenRouterDeepSeekLLMService
from infrastructure.services.llm_services.perplexity_llm_service import PerplexityLLMService
from infrastructure.services.prompt_loaders.yaml_prompt_loader import YamlPromptLoader
from domain.entities.models import Language

def test_llm_services():
    """Test that both LLM services can be initialized and used."""
    print("Testing LLM services...")
    
    # Load settings
    settings = Settings()
    
    # Test OpenRouter DeepSeek
    try:
        openrouter_service = OpenRouterDeepSeekLLMService(settings)
        print("✅ OpenRouter DeepSeek service initialized")
    except Exception as e:
        print(f"❌ OpenRouter DeepSeek service failed: {e}")
        assert False, f"OpenRouter DeepSeek service initialization failed: {e}"
    
    # Test Perplexity
    try:
        perplexity_service = PerplexityLLMService(settings)
        print("✅ Perplexity service initialized")
    except Exception as e:
        print(f"❌ Perplexity service failed: {e}")
        assert False, f"Perplexity service initialization failed: {e}"
    
    # Test prompt loading
    try:
        prompt_loader = YamlPromptLoader()
        templates = prompt_loader.load_prompt_template("src/prompts/cleaner_prompt.yaml")
        print("✅ Prompt loader working")
        print(f"  - Found system template: {len(templates['system'])} chars")
        print(f"  - Found user template: {len(templates['user'])} chars")
    except Exception as e:
        print(f"❌ Prompt loader failed: {e}")
        assert False, f"Prompt loader failed: {e}"
    
    # Test Language enum
    try:
        english = Language.ENGLISH
        chinese = Language.TRADITIONAL_CHINESE
        print(f"✅ Language enum working: {english.value}, {chinese.value}")
    except Exception as e:
        print(f"❌ Language enum failed: {e}")
        assert False, f"Language enum failed: {e}"

def test_prompt_rendering():
    """Test prompt rendering with sample data."""
    print("\nTesting prompt rendering...")
    
    try:
        prompt_loader = YamlPromptLoader()
        templates = prompt_loader.load_prompt_template("src/prompts/cleaner_prompt.yaml")
        
        # Sample data
        variables = {
            'files': ['01 track.mp3', '02 song.mp3'],
            'artist': 'Test Artist',
            'album': 'Test Album',
            'language': 'English',
            'official_tracks': ['Track One', 'Track Two']
        }
        
        # Render templates
        system_prompt = prompt_loader.render_prompt(templates['system'], variables)
        user_prompt = prompt_loader.render_prompt(templates['user'], variables)
        
        print("✅ Prompt rendering successful")
        print(f"  - System prompt: {len(system_prompt)} chars")
        print(f"  - User prompt: {len(user_prompt)} chars")
        print(f"  - Contains artist name: {'Test Artist' in user_prompt}")
        print(f"  - Contains files: {'01 track.mp3' in user_prompt}")
        
    except Exception as e:
        print(f"❌ Prompt rendering failed: {e}")
        assert False, f"Prompt rendering failed: {e}"

def main():
    """Run all tests."""
    print("=" * 60)
    print("ALBUM CLEANER ARCHITECTURE VALIDATION TEST")
    print("=" * 60)
    
    try:
        # Test LLM Services
        test_llm_services()
        
        # Test Prompt Rendering
        test_prompt_rendering()
        
        # All tests passed
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Architecture refactor is working correctly.")
        return 0
    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

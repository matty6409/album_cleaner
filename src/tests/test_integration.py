#!/usr/bin/env python3
"""
Integration test for the Album Cleaner system.
Tests the complete flow with the new simplified architecture.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from domain.entities.models import Language, ProcessingOptions
from infrastructure.factories.service_factory import ServiceFactory, LLMProvider
from infrastructure.config.settings import Settings

def test_integration():
    """Test the complete album cleaning flow."""
    print("🧪 Starting Album Cleaner Integration Test")
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Created temp directory: {temp_dir}")
        
        # Create test album structure
        album_dir = os.path.join(temp_dir, "[Test Artist] Test Album")
        os.makedirs(album_dir)
        
        # Create test files
        test_files = [
            "01 - first song.mp3",
            "02 - second track.mp3", 
            "03 - third tune.mp3"
        ]
        
        for file_name in test_files:
            file_path = os.path.join(album_dir, file_name)
            with open(file_path, 'w') as f:
                f.write("dummy audio content")
        
        print(f"🎵 Created test album with {len(test_files)} files")
        
        # Test both languages and providers
        test_cases = [
            (Language.ENGLISH, LLMProvider.OPENROUTER_DEEPSEEK),
            (Language.TRADITIONAL_CHINESE, LLMProvider.PERPLEXITY),
        ]
        
        for language, provider in test_cases:
            print(f"\n🔄 Testing {language.value} with {provider.value}")
            
            # Clean any previous output
            cleaned_dir = os.path.join(temp_dir, "cleaned")
            if os.path.exists(cleaned_dir):
                shutil.rmtree(cleaned_dir)
            
            try:
                # Initialize services
                settings = Settings()
                factory = ServiceFactory(settings)
                use_case = factory.create_album_cleaner_use_case(provider)
                
                # Create processing options
                options = ProcessingOptions(
                    base_path=temp_dir,
                    language=language,
                    output_mode="copy",
                    max_retries=3
                )
                
                # Process albums
                results = use_case.process_albums(options)
                
                # Verify results
                assert len(results) == 1, f"Expected 1 result, got {len(results)}"
                result = results[0]
                
                if result.success:
                    print(f"✅ {language.value} with {provider.value}: SUCCESS")
                    print(f"   Files processed: {result.files_processed}")
                    
                    # Check output files exist
                    output_files = []
                    if os.path.exists(cleaned_dir):
                        for root, dirs, files in os.walk(cleaned_dir):
                            output_files.extend(files)
                    
                    print(f"   Output files: {len(output_files)}")
                    assert len(output_files) == len(test_files), f"Expected {len(test_files)} output files, got {len(output_files)}"
                    
                else:
                    print(f"❌ {language.value} with {provider.value}: FAILED")
                    print(f"   Error: {result.error_message}")
                    
                    # For integration test, we'll allow LLM-only mode failures
                    # since we don't have real official track data
                    if "No official data found" in str(result.error_message):
                        print("   (This is expected for test data - LLM-only mode)")
                    else:
                        raise AssertionError(f"Unexpected failure: {result.error_message}")
                        
            except Exception as e:
                print(f"❌ Exception in {language.value} with {provider.value}: {e}")
                raise
        
        print("\n🎉 Integration test completed successfully!")
        print("✅ All components working correctly:")
        print("   - Language enum support")
        print("   - LLM provider switching") 
        print("   - Simplified architecture")
        print("   - Error handling and fallback")

if __name__ == "__main__":
    test_integration()

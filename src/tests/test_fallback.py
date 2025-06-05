#!/usr/bin/env python3
"""
Test script to verify the enhanced fallback functionality works end-to-end.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, '/Users/mattmac/Projects/album_cleaner/src')

# Create a test album directory
def create_test_album():
    """Create a temporary album directory with test files."""
    temp_dir = tempfile.mkdtemp(prefix="album_test_")
    # Create album directory in the expected format: [Artist] Album Name
    album_dir = Path(temp_dir) / "[Test Artist] Test Album"
    album_dir.mkdir(parents=True)
    
    # Create some dummy audio files
    test_files = [
        "01 - Track_Name_With_Underscores.flac",
        "02-Another Track (feat. Someone).mp3",
        "03.Final Song [Bonus].flac"
    ]
    
    for filename in test_files:
        (album_dir / filename).touch()
    
    print(f"Created test album at: {album_dir}")
    return str(album_dir), temp_dir

def test_fallback_workflow():
    """Test the complete workflow with fallback to LLM-only mode."""
    from infrastructure.config.settings import Settings
    from infrastructure.services.prompt_loaders.yaml_prompt_loader import YamlPromptLoader
    from infrastructure.services.llm_services.openrouter_deepseek_llm_service import OpenRouterDeepSeekLLMService
    from infrastructure.services.music_services.spotify_song_name_service import SpotifySongNameService
    from infrastructure.persistence.file_repository import FileRepository
    from application.use_cases.album_cleaner_use_case import AlbumCleanerUseCase
    from domain.entities.models import ProcessingOptions, Language
    
    # Create test album
    album_path, temp_dir = create_test_album()
    
    try:
        # Initialize settings (this will fail for Spotify but that's expected for testing fallback)
        settings = Settings()
        
        # Initialize services with correct parameters
        prompt_loader = YamlPromptLoader()
        llm_service = OpenRouterDeepSeekLLMService(settings)
        
        # Use a mock Spotify service that will always fail (simulating no API key or no results)
        class MockFailingSpotifyService:
            def get_track_names(self, artist_name: str, album_name: str):
                # Simulate Spotify failure
                raise Exception("Spotify API unavailable or no results found")
        
        spotify_service = MockFailingSpotifyService()
        file_repository = FileRepository()
        
        # Initialize use case
        use_case = AlbumCleanerUseCase(
            llm_service=llm_service,
            song_name_service=spotify_service,
            file_repository=file_repository,
            prompt_service=prompt_loader
        )
        
        print(f"Testing fallback workflow with album: {album_path}")
        print("Expected: Spotify will fail, system should fallback to LLM-only mode")
        
        # Create processing options
        options = ProcessingOptions(
            base_path=str(Path(album_path).parent),  # Use the parent directory which contains the [Artist] Album folder
            language=Language.ENGLISH,
            output_mode="copy",
            max_retries=3
        )
        
        # This should trigger the fallback logic
        results = use_case.process_albums(options)
        
        print(f"Workflow completed successfully!")
        print(f"Results: {results}")
        
        assert results[0].success, "Fallback workflow should succeed"
        assert results[0].files_processed == 3, "Should process 3 files"
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"Test failed with error: {e}"
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"Cleaned up test directory: {temp_dir}")

if __name__ == "__main__":
    print("Testing Album Cleaner Fallback Functionality")
    print("=" * 50)
    
    test_fallback_workflow()
    
    print("\n✅ Fallback functionality test completed!")

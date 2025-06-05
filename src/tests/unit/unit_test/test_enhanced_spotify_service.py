import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src directory to path for imports
sys.path.insert(0, './src')

from infrastructure.services.music_services.enhanced_spotify_song_name_service import EnhancedSpotifySongNameService
from domain.entities.models import Language

class TestEnhancedSpotifyService(unittest.TestCase):
    """Test suite for the Enhanced Spotify Song Name Service."""

    def setUp(self):
        """Set up test fixtures."""
        self.settings_mock = MagicMock()
        self.settings_mock.spotify_client_id = "test_id"
        self.settings_mock.spotify_client_secret = "test_secret"
        
        self.llm_service_mock = MagicMock()
        self.prompt_service_mock = MagicMock()
        
        # Mock Spotify client
        self.spotify_patcher = patch('spotipy.Spotify')
        self.mock_spotify = self.spotify_patcher.start()
        
        # Create service with mocks
        self.service = EnhancedSpotifySongNameService(
            settings=self.settings_mock,
            llm_service=self.llm_service_mock,
            prompt_service=self.prompt_service_mock
        )
        
        # Replace the real Spotify client with our mock
        self.service.spotify = MagicMock()

    def tearDown(self):
        """Tear down test fixtures."""
        self.spotify_patcher.stop()

    def test_generate_search_terms(self):
        """Test generating optimized search terms using LLM."""
        # Setup mocks
        self.prompt_service_mock.render_search_terms_prompts.return_value = {
            'system': 'system prompt',
            'user': 'user prompt'
        }
        
        self.llm_service_mock.generate_search_terms.return_value = [
            'artist:"Test Artist" album:"Test Album"',
            'artist:"Artist Test" album:"Album Test"',
            'artist:"Test" album:"Album"'
        ]
        
        # Call the method
        result = self.service._generate_search_terms(
            artist_name="[Test Artist]",
            album_name="Test Album (Deluxe)",
            language=Language.ENGLISH
        )
        
        # Assertions
        self.prompt_service_mock.render_search_terms_prompts.assert_called_once()
        self.llm_service_mock.generate_search_terms.assert_called_once_with(
            system_prompt='system prompt',
            user_prompt='user prompt'
        )
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], 'artist:"Test Artist" album:"Test Album"')

    def test_generate_search_terms_fallback(self):
        """Test fallback when LLM fails to generate search terms."""
        # Setup mocks to simulate error
        self.prompt_service_mock.render_search_terms_prompts.side_effect = Exception("Test error")
        
        # Call the method
        result = self.service._generate_search_terms(
            artist_name="Test Artist",
            album_name="Test Album",
            language=Language.ENGLISH
        )
        
        # Assertions - should fall back to the original search term
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'artist:"Test Artist" album:"Test Album"')

    def test_search_album_with_multiple_terms(self):
        """Test searching album with multiple optimized terms."""
        # Setup mocks
        search_terms = [
            'artist:"Test Artist" album:"Test Album"',
            'artist:"Artist Test" album:"Album Test"'
        ]
        
        # First search fails, second succeeds
        def mock_execute_search(query):
            if query == search_terms[0]:
                return None
            else:
                return ("Clean Artist", "Clean Album", ["Track 1", "Track 2"])
        
        # Mock the internal methods
        self.service._generate_search_terms = MagicMock(return_value=search_terms)
        self.service._execute_search = MagicMock(side_effect=mock_execute_search)
        
        # Call the method
        result = self.service.search_album(
            artist_name="Test Artist",
            album_name="Test Album",
            language=Language.ENGLISH
        )
        
        # Assertions
        self.service._generate_search_terms.assert_called_once()
        self.assertEqual(self.service._execute_search.call_count, 2)
        self.assertEqual(result, ("Clean Artist", "Clean Album", ["Track 1", "Track 2"]))

    def test_search_album_all_terms_fail(self):
        """Test when all search terms fail to find results."""
        # Setup mocks
        search_terms = [
            'artist:"Test Artist" album:"Test Album"',
            'artist:"Artist Test" album:"Album Test"'
        ]
        
        # Mock the internal methods
        self.service._generate_search_terms = MagicMock(return_value=search_terms)
        self.service._execute_search = MagicMock(return_value=None)
        
        # Call the method
        result = self.service.search_album(
            artist_name="Test Artist",
            album_name="Test Album",
            language=Language.ENGLISH
        )
        
        # Assertions
        self.service._generate_search_terms.assert_called_once()
        self.assertEqual(self.service._execute_search.call_count, 2)
        self.assertIsNone(result)

    def test_execute_search(self):
        """Test executing a single search query."""
        # Setup mock responses
        self.service.spotify.search.return_value = {
            'albums': {
                'items': [{
                    'id': 'album123',
                    'name': 'Clean Album',
                    'artists': [{'name': 'Clean Artist'}]
                }]
            }
        }
        
        self.service.spotify.album_tracks.return_value = {
            'items': [
                {'name': 'Track 1'},
                {'name': 'Track 2'}
            ]
        }
        
        # Call the method
        result = self.service._execute_search('artist:"Test" album:"Test"')
        
        # Assertions
        self.service.spotify.search.assert_called_once()
        self.service.spotify.album_tracks.assert_called_once_with('album123')
        self.assertEqual(result, ('Clean Artist', 'Clean Album', ['Track 1', 'Track 2']))

    def test_get_track_names(self):
        """Test getting track names using search_album method."""
        # Mock search_album
        self.service.search_album = MagicMock(
            return_value=('Clean Artist', 'Clean Album', ['Track 1', 'Track 2'])
        )
        
        # Call the method
        result = self.service.get_track_names(
            artist_name="Test Artist",
            album_name="Test Album",
            language=Language.ENGLISH
        )
        
        # Assertions
        self.service.search_album.assert_called_once()
        self.assertEqual(result, ['Track 1', 'Track 2'])


if __name__ == '__main__':
    unittest.main()

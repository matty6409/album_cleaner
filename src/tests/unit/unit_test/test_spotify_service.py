"""
Unit tests for Spotify song name service.
Tests album search, track retrieval, and error handling.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch
from typing import Optional, Tuple, List
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from application.interfaces.services.song_name_service_interface import SongNameService
from infrastructure.services.music_services.spotify_song_name_service import SpotifySongNameService
from infrastructure.config.settings import Settings
from domain.entities.models import Language


class TestSpotifySongNameService:
    """Test cases for Spotify song name service."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.spotify_client_id = "test-client-id"
        settings.spotify_client_secret = "test-client-secret"
        return settings
    
    @pytest.fixture
    def mock_spotify_response(self):
        """Mock Spotify API search response."""
        return {
            'albums': {
                'items': [
                    {
                        'id': 'test-album-id',
                        'name': 'Test Album',
                        'artists': [{'name': 'Test Artist'}]
                    }
                ]
            }
        }
    
    @pytest.fixture  
    def mock_tracks_response(self):
        """Mock Spotify API tracks response."""
        return {
            'items': [
                {'name': 'Track One'},
                {'name': 'Track Two'},
                {'name': 'Track Three'}
            ]
        }

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_service_initialization(self, mock_spotify_class, mock_settings):
        """Test Spotify service initialization."""
        mock_spotify_instance = Mock()
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        assert service.settings == mock_settings
        assert service.spotify == mock_spotify_instance

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_successful_album_search(
        self, 
        mock_spotify_class, 
        mock_settings,
        mock_spotify_response,
        mock_tracks_response
    ):
        """Test successful album search and track retrieval."""
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = mock_spotify_response
        mock_spotify_instance.album_tracks.return_value = mock_tracks_response
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        result = service.search_album("Test Artist", "Test Album")
        
        assert result is not None
        clean_artist, clean_album, track_names = result
        assert clean_artist == "Test Artist"
        assert clean_album == "Test Album"
        assert track_names == ["Track One", "Track Two", "Track Three"]
        
        # Verify API calls
        mock_spotify_instance.search.assert_called_once()
        mock_spotify_instance.album_tracks.assert_called_once_with('test-album-id')

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_no_albums_found(self, mock_spotify_class, mock_settings):
        """Test behavior when no albums are found."""
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = {'albums': {'items': []}}
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        result = service.search_album("Unknown Artist", "Unknown Album")
        
        assert result is None
        mock_spotify_instance.search.assert_called_once()

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_api_error_handling(self, mock_spotify_class, mock_settings):
        """Test handling of Spotify API errors."""
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.side_effect = Exception("Spotify API Error")
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        result = service.search_album("Test Artist", "Test Album")
        
        assert result is None

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_get_track_names_method(
        self,
        mock_spotify_class,
        mock_settings,
        mock_spotify_response,
        mock_tracks_response
    ):
        """Test get_track_names method."""
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = mock_spotify_response
        mock_spotify_instance.album_tracks.return_value = mock_tracks_response
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        track_names = service.get_track_names("Test Artist", "Test Album")
        
        assert track_names == ["Track One", "Track Two", "Track Three"]

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_get_track_names_no_album(self, mock_spotify_class, mock_settings):
        """Test get_track_names when album is not found."""
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = {'albums': {'items': []}}
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        track_names = service.get_track_names("Unknown Artist", "Unknown Album")
        
        assert track_names is None

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_search_query_formatting(self, mock_spotify_class, mock_settings):
        """Test that search queries are properly formatted."""
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = {'albums': {'items': []}}
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        service.search_album("Test Artist", "Test Album")
        
        # Verify the search query format
        call_args = mock_spotify_instance.search.call_args
        assert 'artist:"Test Artist"' in call_args[1]['q']
        assert 'album:"Test Album"' in call_args[1]['q']
        assert call_args[1]['type'] == 'album'
        assert call_args[1]['limit'] == 10

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_chinese_artist_and_album(
        self,
        mock_spotify_class,
        mock_settings
    ):
        """Test search with Chinese artist and album names."""
        chinese_response = {
            'albums': {
                'items': [
                    {
                        'id': 'chinese-album-id',
                        'name': '愛情故事',
                        'artists': [{'name': '張學友'}]
                    }
                ]
            }
        }
        
        chinese_tracks = {
            'items': [
                {'name': '愛的故事'},
                {'name': '月亮代表我的心'}
            ]
        }
        
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = chinese_response
        mock_spotify_instance.album_tracks.return_value = chinese_tracks
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        result = service.search_album("張學友", "愛情故事")
        
        assert result is not None
        clean_artist, clean_album, track_names = result
        assert clean_artist == "張學友"
        assert clean_album == "愛情故事"
        assert track_names == ["愛的故事", "月亮代表我的心"]

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_empty_track_list(
        self,
        mock_spotify_class,
        mock_settings,
        mock_spotify_response
    ):
        """Test handling of albums with no tracks."""
        empty_tracks_response = {'items': []}
        
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = mock_spotify_response
        mock_spotify_instance.album_tracks.return_value = empty_tracks_response
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        result = service.search_album("Test Artist", "Test Album")
        
        assert result is not None
        clean_artist, clean_album, track_names = result
        assert track_names == []

    @patch('infrastructure.music.spotify_song_name_service.spotipy.Spotify')
    def test_multiple_albums_first_match(self, mock_spotify_class, mock_settings):
        """Test that service returns the first (best) match when multiple albums found."""
        multiple_albums_response = {
            'albums': {
                'items': [
                    {
                        'id': 'best-match-id',
                        'name': 'Test Album',
                        'artists': [{'name': 'Test Artist'}]
                    },
                    {
                        'id': 'second-match-id', 
                        'name': 'Test Album (Deluxe)',
                        'artists': [{'name': 'Test Artist'}]
                    }
                ]
            }
        }
        
        mock_tracks_response = {
            'items': [
                {'name': 'Best Match Track One'},
                {'name': 'Best Match Track Two'}
            ]
        }
        
        mock_spotify_instance = Mock()
        mock_spotify_instance.search.return_value = multiple_albums_response
        mock_spotify_instance.album_tracks.return_value = mock_tracks_response
        mock_spotify_class.return_value = mock_spotify_instance
        
        service = SpotifySongNameService(mock_settings)
        
        result = service.search_album("Test Artist", "Test Album")
        
        assert result is not None
        clean_artist, clean_album, track_names = result
        assert clean_album == "Test Album"  # Should use first match
        assert track_names == ["Best Match Track One", "Best Match Track Two"]
        
        # Verify it used the first album ID
        mock_spotify_instance.album_tracks.assert_called_once_with('best-match-id')

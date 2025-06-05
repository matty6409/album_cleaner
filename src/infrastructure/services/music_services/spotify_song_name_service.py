import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional, List, Tuple
from application.interfaces.services.song_name_service_interface import SongNameService
from domain.entities.models import Language
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

class SpotifySongNameService(SongNameService):
    """
    Concrete implementation for retrieving song names from Spotify API.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize Spotify service.
        
        Args:
            settings: Application settings containing Spotify credentials
        """
        self.settings = settings
        self._init_spotify_client()
    
    def _init_spotify_client(self) -> None:
        """Initialize Spotify client with credentials."""
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.settings.spotify_client_id,
                client_secret=self.settings.spotify_client_secret
            )
            self.spotify = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )
            logger.info("Spotify client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client: {e}")
            raise
    
    def search_album(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language = Language.ENGLISH
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Search for official album information on Spotify.
        
        Args:
            artist_name: Artist name to search for
            album_name: Album name to search for
            language: Target language for results (used for search optimization)
            
        Returns:
            Tuple of (clean_artist_name, clean_album_name, track_names) or None if not found
        """
        try:
            # Search for albums
            query = f'artist:"{artist_name}" album:"{album_name}"'
            results = self.spotify.search(
                q=query, 
                type='album', 
                limit=10
            )
            
            if not results['albums']['items']:
                logger.warning(f"No albums found for: {artist_name} - {album_name}")
                return None
            
            # Get the best match (first result)
            album = results['albums']['items'][0]
            album_id = album['id']
            clean_artist_name = album['artists'][0]['name']
            clean_album_name = album['name']
            
            # Get tracks for the album
            tracks_result = self.spotify.album_tracks(album_id)
            track_names = [track['name'] for track in tracks_result['items']]
            
            logger.info(f"Found album: {clean_artist_name} - {clean_album_name} with {len(track_names)} tracks")
            
            return (clean_artist_name, clean_album_name, track_names)
            
        except Exception as e:
            logger.error(f"Spotify search failed for {artist_name} - {album_name}: {e}")
            return None
    
    def get_track_names(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language = Language.ENGLISH
    ) -> Optional[List[str]]:
        """
        Get official track names for an album from Spotify.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            language: Target language for results
            
        Returns:
            List of official track names in order, or None if not found
        """
        result = self.search_album(artist_name, album_name, language)
        if result:
            return result[2]  # Return track names
        return None

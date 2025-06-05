import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional, List, Tuple, Any
from application.interfaces.services.song_name_service_interface import SongNameService
from application.interfaces.services.llm_service_interface import LLMService
from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from domain.entities.models import Language
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

class EnhancedSpotifySongNameService(SongNameService):
    """
    Enhanced implementation for retrieving song names from Spotify API with LLM-optimized search.
    Uses LLM to generate multiple optimized search terms to increase chances of finding albums.
    """
    
    def __init__(
        self, 
        settings: Settings, 
        llm_service: LLMService,
        prompt_service: PromptLoadingService
    ):
        """
        Initialize Enhanced Spotify service.
        
        Args:
            settings: Application settings containing Spotify credentials
            llm_service: LLM service for generating optimized search terms
            prompt_service: Service for loading and rendering prompts
        """
        self.settings = settings
        self.llm_service = llm_service
        self.prompt_service = prompt_service
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
    
    def _generate_search_terms(
        self, 
        artist_name: str, 
        album_name: str, 
        language: Language
    ) -> List[str]:
        """
        Generate optimized search terms using LLM.
        
        Args:
            artist_name: Original artist name
            album_name: Original album name
            language: Target language
            
        Returns:
            List of optimized search queries
        """
        try:
            logger.info(f"Generating optimized search terms for {artist_name} - {album_name}")
            
            # Render search terms prompts
            prompts = self.prompt_service.render_search_terms_prompts(
                artist_name=artist_name,
                album_name=album_name,
                language=language
            )
            
            # Generate search terms using LLM
            search_terms = self.llm_service.generate_search_terms(
                system_prompt=prompts['system'],
                user_prompt=prompts['user']
            )
            
            # Add original search term as fallback
            original_term = f'artist:"{artist_name}" album:"{album_name}"'
            if original_term not in search_terms:
                search_terms.append(original_term)
                
            logger.info(f"Generated {len(search_terms)} search terms")
            return search_terms
            
        except Exception as e:
            logger.warning(f"Failed to generate optimized search terms: {e}")
            # Fall back to original search term
            return [f'artist:"{artist_name}" album:"{album_name}"']
    
    def _execute_search(self, query: str) -> Optional[Tuple[str, str, List[str]]]:
        """
        Execute a single Spotify search with the given query.
        
        Args:
            query: Spotify search query
            
        Returns:
            Tuple of (clean_artist_name, clean_album_name, track_names) or None if not found
        """
        try:
            logger.info(f"Searching Spotify with query: {query}")
            
            # Search for albums
            results = self.spotify.search(
                q=query, 
                type='album', 
                limit=10
            )
            
            if not results['albums']['items']:
                logger.warning(f"No albums found for query: {query}")
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
            logger.error(f"Spotify search failed for query {query}: {e}")
            return None
    
    def search_album(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language = Language.ENGLISH
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Search for official album information on Spotify using LLM-optimized search terms.
        
        Args:
            artist_name: Artist name to search for
            album_name: Album name to search for
            language: Target language for results (used for search optimization)
            
        Returns:
            Tuple of (clean_artist_name, clean_album_name, track_names) or None if not found
        """
        try:
            # Generate multiple search terms using LLM
            search_terms = self._generate_search_terms(artist_name, album_name, language)
            
            # Try each search term until we find a match
            for term in search_terms:
                result = self._execute_search(term)
                if result:
                    return result
            
            logger.warning(f"No albums found after trying {len(search_terms)} search terms")
            return None
            
        except Exception as e:
            logger.error(f"Enhanced Spotify search failed for {artist_name} - {album_name}: {e}")
            return None
    
    def get_track_names(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language = Language.ENGLISH
    ) -> Optional[List[str]]:
        """
        Get official track names for an album from Spotify using LLM-optimized search.
        
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

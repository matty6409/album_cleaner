import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional, List, Tuple, Any
from application.interfaces.services.song_name_service_interface import SongNameService
from application.interfaces.services.llm_service_interface import LLMService
from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from domain.values_objects.language import Language  # Updated import
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger
from opencc import OpenCC
import re

class SpotifySongNameService(SongNameService):
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
        language: Language,
        local_files: List[str] = None
    ) -> List[str]:
        """
        Generate optimized search terms using LLM with smart artist detection.
        
        Args:
            artist_name: Original artist name
            album_name: Original album name
            language: Target language
            local_files: List of local filenames to analyze for artist clues
            
        Returns:
            List of optimized search queries
        """
        try:
            logger.info(f"Generating optimized search terms for {artist_name} - {album_name}")
            
            # Render search terms prompts
            prompts = self.prompt_service.render_search_terms_prompts(
                artist_name=artist_name,
                album_name=album_name,
                language=language,
                local_files=local_files or []
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
    
    def _validate_search_result(self, original_artist: str, original_album: str, found_artist: str, found_album: str) -> bool:
        """
        Validate if the search result is relevant to the requested album.
        
        Args:
            original_artist: Original artist name used for search
            original_album: Original album name used for search
            found_artist: Artist name returned by Spotify
            found_album: Album name returned by Spotify
            
        Returns:
            True if the search result appears to be relevant, False otherwise
        """
        try:
            # Normalize strings for comparison (lowercase, remove special chars)
            def normalize(text):
                return re.sub(r'[^\w\s]', '', text.lower())
            
            orig_artist_norm = normalize(original_artist)
            orig_album_norm = normalize(original_album)
            found_artist_norm = normalize(found_artist)
            found_album_norm = normalize(found_album)
            
            # Check if found artist is completely different (allowing for partial matches)
            if orig_artist_norm != "unknown artist" and not (
                orig_artist_norm in found_artist_norm or 
                found_artist_norm in orig_artist_norm
            ):
                logger.warning(f"Artist mismatch: requested '{original_artist}' but found '{found_artist}'")
                return False
            
            # Check if found album is completely different
            if not (orig_album_norm in found_album_norm or found_album_norm in orig_album_norm):
                # Check if either contains the other
                if len(orig_album_norm) > 3 and len(found_album_norm) > 3:
                    max_len = max(len(orig_album_norm), len(found_album_norm))
                    # Calculate similarity threshold based on length
                    similarity = (
                        len(set(orig_album_norm) & set(found_album_norm)) / 
                        len(set(orig_album_norm) | set(found_album_norm))
                    )
                    
                    if similarity < 0.3:  # Threshold for determining relevance
                        logger.warning(f"Album mismatch: requested '{original_album}' but found '{found_album}' (similarity: {similarity:.2f})")
                        return False
                else:
                    logger.warning(f"Album mismatch: requested '{original_album}' but found '{found_album}'")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating search result: {e}")
            # On error, be permissive and return True to maintain existing behavior
            return True
    
    def _execute_search(self, query: str, original_artist: str = None, original_album: str = None) -> Optional[Tuple[str, str, List[str]]]:
        """
        Execute a single Spotify search with the given query.
        
        Args:
            query: Spotify search query
            original_artist: Original artist name for validation
            original_album: Original album name for validation
            
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
            
            # Validate search result if original info is provided
            if original_artist and original_album:
                if not self._validate_search_result(original_artist, original_album, clean_artist_name, clean_album_name):
                    logger.warning(f"Search result validation failed: '[{clean_artist_name}] {clean_album_name}' is irrelevant to requested '[{original_artist}] {original_album}'")
                    # Try next result if available
                    if len(results['albums']['items']) > 1:
                        logger.info(f"Trying next search result...")
                        for next_album in results['albums']['items'][1:]:
                            next_artist_name = next_album['artists'][0]['name']
                            next_album_name = next_album['name']
                            if self._validate_search_result(original_artist, original_album, next_artist_name, next_album_name):
                                clean_artist_name = next_artist_name
                                clean_album_name = next_album_name
                                album_id = next_album['id']
                                logger.info(f"Found better match: [{clean_artist_name}] {clean_album_name}")
                                break
                        else:
                            logger.warning(f"No relevant search results found for '{original_artist} - {original_album}'")
                            return None
                    else:
                        return None
            
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
        language: Language = Language.ENGLISH,
        local_files: List[str] = None
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Search for official album information on Spotify using LLM-optimized search terms.
        
        Args:
            artist_name: Artist name to search for
            album_name: Album name to search for
            language: Target language for results (used for search optimization)
            local_files: List of local filenames for enhanced search context
            
        Returns:
            Tuple of (clean_artist_name, clean_album_name, track_names) or None if not found
        """
        try:
            # Generate multiple search terms using LLM with local files context
            search_terms = self._generate_search_terms(artist_name, album_name, language, local_files)                # Try each search term until we find a match
            for term in search_terms:
                result = self._execute_search(term, artist_name, album_name)
                if result:
                    # No longer applying OpenCC here - conversion will be done at the final stage
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

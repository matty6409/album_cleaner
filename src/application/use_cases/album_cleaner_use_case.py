import os
import re
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from opencc import OpenCC

from application.interfaces.services.llm_service_interface import LLMService
from application.interfaces.services.song_name_service_interface import SongNameService
from application.interfaces.repositories.file_repository_interface import FileRepositoryInterface
from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from domain.entities.models import Album, Track, ProcessingOptions, ProcessingResult, Language
from infrastructure.logging.logger import logger

class AlbumCleanerUseCase:
    """
    Main use case for cleaning album directories.
    Orchestrates the entire cleaning process using clean architecture principles.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        song_name_service: SongNameService,
        file_repository: FileRepositoryInterface,
        prompt_service: PromptLoadingService
    ):
        """
        Initialize the use case with required services.
        
        Args:
            llm_service: Service for LLM operations (simplified interface)
            song_name_service: Service for official song name retrieval
            file_repository: Repository for file operations
            prompt_service: Service for prompt loading and rendering
        """
        self.llm_service = llm_service
        self.song_name_service = song_name_service
        self.file_repository = file_repository
        self.prompt_service = prompt_service
        self.cc = OpenCC('s2t')  # Simplified to Traditional Chinese converter
    
    def process_albums(self, options: ProcessingOptions) -> List[ProcessingResult]:
        """
        Process all albums in the base directory.
        
        Args:
            options: Processing options
            
        Returns:
            List of processing results for each album
        """
        logger.info(f"Starting album processing with options: {options}")
        
        # Discover albums
        album_dirs = self._discover_albums(options.base_path)
        logger.info(f"Found {len(album_dirs)} albums to process")
        
        results = []
        for album_dir in album_dirs:
            result = self._process_single_album(album_dir, options)
            results.append(result)
            
            if result.success:
                logger.info(f"✅ Successfully processed: {result.album_path}")
            else:
                logger.error(f"❌ Failed to process: {result.album_path} - {result.error_message}")
        
        # Summary
        successful = sum(1 for r in results if r.success)
        logger.info(f"Processing complete: {successful}/{len(results)} albums successful")
        
        return results
    
    def _discover_albums(self, base_path: str) -> List[str]:
        """
        Discover album directories in the base path.
        
        Args:
            base_path: Base directory to scan
            
        Returns:
            List of album directory paths
        """
        album_dirs = []
        
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and self._is_album_directory(item):
                    album_dirs.append(item_path)
        except Exception as e:
            logger.error(f"Error scanning base directory {base_path}: {e}")
        
        return sorted(album_dirs)
    
    def _is_album_directory(self, dir_name: str) -> bool:
        """
        Check if directory name matches album format: [Artist] Album Name
        
        Args:
            dir_name: Directory name to check
            
        Returns:
            True if it matches album format
        """
        return bool(re.match(r'^\[.+\].+', dir_name))
    
    def _extract_artist_and_album(self, dir_name: str) -> Tuple[str, str]:
        """
        Extract artist and album name from directory name.
        
        Args:
            dir_name: Directory name in format [Artist] Album Name
            
        Returns:
            Tuple of (artist_name, album_name)
        """
        match = re.match(r'^\[(.+?)\]\s*(.+)', dir_name)
        if match:
            artist = match.group(1).strip()
            album = match.group(2).strip()
            return artist, album
        
        raise ValueError(f"Invalid album directory format: {dir_name}")
    
    def _process_single_album(
        self, 
        album_path: str, 
        options: ProcessingOptions
    ) -> ProcessingResult:
        """
        Process a single album directory.
        
        Args:
            album_path: Path to the album directory
            options: Processing options
            
        Returns:
            Processing result
        """
        try:
            # Extract artist and album name
            dir_name = os.path.basename(album_path)
            artist_name, album_name = self._extract_artist_and_album(dir_name)
            
            logger.info(f"Processing album: {artist_name} - {album_name}")
            
            # Get local files
            local_files = self.file_repository.list_audio_files(album_path)
            if not local_files:
                return ProcessingResult(
                    album_path=album_path,
                    success=False,
                    error_message="No audio files found"
                )
            
            # Get official track information with language support
            official_data = self._get_official_album_data(artist_name, album_name, options.language)
            if official_data:
                # Use official data when available
                clean_artist, clean_album, official_tracks = official_data
                logger.info(f"Using official data: {len(official_tracks)} tracks from Spotify")
            else:
                # Fallback to LLM-only processing when Spotify fails
                logger.warning(f"No official data found for {artist_name} - {album_name}, falling back to LLM-only cleaning")
                clean_artist, clean_album = artist_name, album_name
                official_tracks = []  # Empty list signals LLM-only mode
            
            # Generate filename mapping using orchestrated approach
            mapping = self._generate_filename_mapping(
                local_files, clean_artist, clean_album, official_tracks, options.language
            )
            
            # Validate mapping (skip official track validation if LLM-only mode)
            self._validate_mapping(mapping, local_files, official_tracks)
            
            # Execute file operations
            files_processed = self._execute_file_operations(
                album_path, mapping, options, clean_artist, clean_album
            )
            
            return ProcessingResult(
                album_path=album_path,
                success=True,
                files_processed=files_processed,
                language_used=options.language
            )
            
        except Exception as e:
            logger.error(f"Error processing album {album_path}: {e}")
            return ProcessingResult(
                album_path=album_path,
                success=False,
                error_message=str(e),
                language_used=options.language
            )
    
    def _get_official_album_data(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Get official album data from song name service.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            language: Target language for results
            
        Returns:
            Tuple of (clean_artist, clean_album, track_names) or None
        """
        try:
            return self.song_name_service.search_album(artist_name, album_name, language)
        except Exception as e:
            logger.error(f"Failed to get official album data: {e}")
            return None
    
    def _generate_filename_mapping(
        self,
        local_files: List[str],
        artist_name: str,
        album_name: str,
        official_tracks: List[str],
        language: Language
    ) -> Dict[str, str]:
        """
        Generate filename mapping using orchestrated approach with prompt service.
        
        Args:
            local_files: List of local filenames
            artist_name: Clean artist name
            album_name: Clean album name
            official_tracks: List of official track names (empty for LLM-only mode)
            language: Target language for processing
            
        Returns:
            Dictionary mapping old filename -> new filename
        """
        for attempt in range(1, 3 + 1):  # Max 3 retries
            try:
                logger.info(f"Generating mapping (attempt {attempt})")
                
                # Step 1: Use prompt service to render the prompts
                rendered_prompts = self.prompt_service.render_album_cleaning_prompts(
                    local_files=local_files,
                    artist_name=artist_name,
                    album_name=album_name,
                    official_tracks=official_tracks,
                    language=language
                )
                
                # Step 2: Use LLM service with pre-rendered prompts
                llm_response = self.llm_service.generate_response(
                    system_prompt=rendered_prompts['system'],
                    user_prompt=rendered_prompts['user']
                )
                
                # Step 3: Parse the LLM response into a mapping
                mapping = self._parse_llm_response(llm_response)
                
                logger.info(f"Successfully generated mapping with {len(mapping)} entries")
                return mapping
                
            except Exception as e:
                logger.warning(f"Mapping generation failed (attempt {attempt}): {e}")
                if attempt == 3:
                    raise
        
        raise RuntimeError("Failed to generate mapping after all retries")
    
    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """
        Parse LLM response into filename mapping.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Dictionary mapping old filename -> new filename
            
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                result = json.loads(response)
                return result
            
            # Try to extract JSON from markdown code block
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                return result
            
            # Try to find JSON-like content
            json_match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                return result
            
            raise ValueError("No valid JSON mapping found in LLM response")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}. Attempted to parse: {response[:200]}...")
            raise ValueError(f"Failed to parse JSON from LLM response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            raise ValueError(f"Unexpected error parsing LLM response: {e}")
    
    def _validate_mapping(
        self,
        mapping: Dict[str, str],
        local_files: List[str],
        official_tracks: List[str]
    ) -> None:
        """
        Validate the filename mapping.
        
        Args:
            mapping: Filename mapping
            local_files: List of local files
            official_tracks: List of official tracks
            
        Raises:
            ValueError: If mapping is invalid
        """
        # Check all files are mapped
        missing_files = set(local_files) - set(mapping.keys())
        if missing_files:
            raise ValueError(f"Missing mappings for files: {missing_files}")
        
        # Extract track numbers from new filenames
        track_numbers = []
        for old_file, new_file in mapping.items():
            match = re.match(r'^(\d+)', new_file)
            if not match:
                raise ValueError(f"New filename doesn't start with track number: {new_file}")
            track_numbers.append(int(match.group(1)))
        
        # Check for duplicates
        if len(set(track_numbers)) != len(track_numbers):
            raise ValueError("Duplicate track numbers in mapping")
        
        # Check count matches (only if we have official tracks)
        if official_tracks and len(track_numbers) != len(official_tracks):
            logger.warning(f"Track count mismatch: {len(track_numbers)} files, {len(official_tracks)} official tracks")
        elif not official_tracks:
            logger.info(f"LLM-only mode: Validated {len(track_numbers)} track mappings without official data")
    
    def _execute_file_operations(
        self,
        album_path: str,
        mapping: Dict[str, str],
        options: ProcessingOptions,
        clean_artist: str,
        clean_album: str
    ) -> int:
        """
        Execute the file operations (copy or rename).
        
        Args:
            album_path: Path to the album directory
            mapping: Filename mapping
            options: Processing options
            clean_artist: Clean artist name
            clean_album: Clean album name
            
        Returns:
            Number of files processed
        """
        files_processed = 0
        
        if options.output_mode == "copy":
            # Create cleaned directory structure
            base_parent = os.path.dirname(album_path)
            cleaned_base = os.path.join(base_parent, "cleaned")
            clean_album_dir = os.path.join(cleaned_base, f"[{clean_artist}] {clean_album}")
            
            self.file_repository.make_dir(clean_album_dir)
            
            # Copy files with new names
            for old_filename, new_filename in mapping.items():
                src = os.path.join(album_path, old_filename)
                
                # Apply Chinese conversion if needed
                if options.language == Language.TRADITIONAL_CHINESE:
                    new_filename = self._convert_to_traditional_chinese(new_filename)
                
                dst = os.path.join(clean_album_dir, new_filename)
                
                self.file_repository.copy_file(src, dst)
                logger.info(f"Copied: {old_filename} → {new_filename}")
                files_processed += 1
                
        else:  # in_place
            # Rename files in place
            for old_filename, new_filename in mapping.items():
                src = os.path.join(album_path, old_filename)
                
                # Apply Chinese conversion if needed
                if options.language == Language.TRADITIONAL_CHINESE:
                    new_filename = self._convert_to_traditional_chinese(new_filename)
                
                dst = os.path.join(album_path, new_filename)
                
                if src != dst:
                    self.file_repository.rename_file(src, dst)
                    logger.info(f"Renamed: {old_filename} → {new_filename}")
                    files_processed += 1
        
        return files_processed
    
    def _convert_to_traditional_chinese(self, filename: str) -> str:
        """
        Convert simplified Chinese characters to traditional Chinese.
        
        Args:
            filename: Filename to convert
            
        Returns:
            Filename with traditional Chinese characters
        """
        # Extract name and extension
        name, ext = os.path.splitext(filename)
        
        # Convert simplified to traditional Chinese
        converted_name = self.cc.convert(name)
        
        # Clean filename of invalid characters
        converted_name = self._clean_filename(converted_name)
        
        return f"{converted_name}{ext}"
    
    def _clean_filename(self, name: str) -> str:
        """
        Remove illegal filesystem characters from filename.
        
        Args:
            name: Filename to clean
            
        Returns:
            Cleaned filename
        """
        return re.sub(r'[<>:"/\\|?*]', '', name)

import os
import re
import json
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING, Union
from opencc import OpenCC

from application.interfaces.services.llm_service_interface import LLMService
from application.interfaces.services.song_name_service_interface import SongNameService
from application.interfaces.repositories.file_repository_interface import FileRepositoryInterface
from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from application.dtos.processing import ProcessingOptions, ProcessingResult
from domain.values_objects.language import Language
from infrastructure.logging.logger import logger
from infrastructure.services.translation.pure_translation_mode import PureTranslationMode

if TYPE_CHECKING:
    from application.interfaces.services.quality_assurance_service_interface import QualityAssuranceService
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
        prompt_service: PromptLoadingService,
        qa_service: Optional['QualityAssuranceService'] = None  # NEW: QA service
    ):
        """
        Initialize the use case with required services.
        
        Args:
            llm_service: Service for LLM operations (simplified interface)
            song_name_service: Service for official song name retrieval
            file_repository: Repository for file operations
            prompt_service: Service for prompt loading and rendering
            qa_service: Optional quality assurance service
        """
        self.llm_service = llm_service
        self.song_name_service = song_name_service
        self.file_repository = file_repository
        self.prompt_service = prompt_service
        self.qa_service = qa_service  # NEW: QA service
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
        logger.info(f"🔍 Found {len(album_dirs)} albums to process")
        
        results = []
        for i, album_dir in enumerate(album_dirs, 1):
            album_name = os.path.basename(album_dir)
            logger.info(f"[{i}/{len(album_dirs)}] Processing: {album_name}")
            
            result = self._process_single_album(album_dir, options)
            results.append(result)
            
            if result.success:
                logger.info(f"✅ Completed: {result.files_processed} files processed")
            else:
                logger.error(f"❌ Failed: {result.error_message}")
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total_files = sum(r.files_processed for r in results if r.success)
        logger.info(f"🎯 Summary: {successful}/{len(results)} albums successful, {total_files} files processed")
        
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
                if os.path.isdir(item_path) and self._is_album_directory(item_path):
                    album_dirs.append(item_path)
        except Exception as e:
            logger.error(f"Error scanning base directory {base_path}: {e}")
        
        return sorted(album_dirs)
    
    def _is_album_directory(self, dir_path: str) -> bool:
        """
        Check if directory contains audio files and should be processed as an album.
        
        Args:
            dir_path: Full path to directory to check
            
        Returns:
            True if it contains audio files and should be processed
        """
        try:
            # Check if directory contains any audio files
            audio_files = self.file_repository.list_audio_files(dir_path)
            return len(audio_files) > 0
        except Exception:
            return False
    
    def _extract_artist_and_album(self, dir_name: str) -> Tuple[str, str]:
        """
        Extract artist and album name from directory name using intelligent parsing.
        
        Args:
            dir_name: Directory name in various formats
            
        Returns:
            Tuple of (artist_name, album_name)
        """
        # Try format: [Artist] Album Name (already clean format)
        match = re.match(r'^\[(.+?)\]\s*(.+)', dir_name)
        if match:
            artist = match.group(1).strip()
            album = match.group(2).strip()
            return artist, album
        
        # Try format: Artist - Album
        if ' - ' in dir_name:
            parts = dir_name.split(' - ', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        # Try format: Artist_Album or Artist.Album
        for separator in ['_', '.']:
            if separator in dir_name:
                parts = dir_name.split(separator, 1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
        
        # Try format: Artist《Album》[Format] (Chinese format)
        match = re.match(r'^(.+?)《(.+?)》', dir_name)
        if match:
            artist = match.group(1).strip()
            album = match.group(2).strip()
            return artist, album
        
        # Try format: ArtistAlbumName (extract from context or use as album name)
        # For single-word directories, treat as album name with unknown artist
        # This will be refined during Spotify search
        return "Unknown Artist", dir_name.strip()
    
    def _process_single_album(
        self, 
        album_path: str, 
        options: ProcessingOptions
    ) -> ProcessingResult:
        """
        Process a single album directory with enhanced retry logic and QA.
        
        Args:
            album_path: Path to the album directory
            options: Processing options
            
        Returns:
            Processing result
        """
        retry_count = 0
        search_attempts = 0
        qa_approved = None
        qa_confidence = None
        
        try:
            # Extract artist and album name
            dir_name = os.path.basename(album_path)
            artist_name, album_name = self._extract_artist_and_album(dir_name)
            
            logger.info(f"🎵 Processing: {artist_name} - {album_name}")
            
            # Get local files
            local_files = self.file_repository.list_audio_files(album_path)
            if not local_files:
                return ProcessingResult(
                    album_path=album_path,
                    success=False,
                    error_message="No audio files found"
                )
            
            logger.info(f"📁 Found {len(local_files)} audio files")
            
            # Check if pure translation mode is enabled
            if options.pure_translation:
                return self._process_pure_translation(album_path, local_files, artist_name, album_name, options)
            
            # Enhanced business logic retry loop
            for business_attempt in range(1, options.max_business_retries + 1):
                try:
                    logger.info(f"Business logic attempt {business_attempt}/{options.max_business_retries}")
                    
                    # Get official track information with enhanced search
                    official_data, search_count = self._get_official_album_data_with_retries(
                        artist_name, album_name, options.language, options.max_search_retries, local_files
                    )
                    search_attempts = search_count
                    
                    if official_data:
                        clean_artist, clean_album, official_tracks = official_data
                        logger.info(f"Using official data: {len(official_tracks)} tracks from Spotify")
                    else:
                        logger.warning(f"No official data found for {artist_name} - {album_name}, falling back to LLM-only cleaning")
                        clean_artist, clean_album = artist_name, album_name
                        official_tracks = []
                    
                    # Generate filename mapping
                    mapping = self._generate_filename_mapping(
                        local_files, clean_artist, clean_album, official_tracks, options.language, options
                    )
                    
                    # Validate basic mapping requirements
                    self._validate_mapping(mapping, local_files, official_tracks)
                    
                    # Enhanced QA Review (if enabled)
                    if options.enable_qa_review and self.qa_service:
                        qa_result = self.qa_service.review_mapping_quality(
                            artist_name=clean_artist,
                            album_name=clean_album,
                            local_files=local_files,
                            proposed_mapping=mapping,
                            official_tracks=official_tracks,
                            target_language=options.language
                        )
                        
                        qa_approved = qa_result.get('approved', False)
                        qa_confidence = qa_result.get('confidence_score', 0.0)
                        
                        logger.info(f"QA Review: Approved={qa_approved}, Confidence={qa_confidence:.2f}")
                        
                        # Check QA approval and confidence threshold
                        if not qa_approved or qa_confidence < options.qa_confidence_threshold:
                            issues = qa_result.get('issues', [])
                            recommendations = qa_result.get('recommendations', [])
                            llm_fallback = qa_result.get('llm_fallback_suggestion', '')
                            
                            error_msg = f"QA review failed (confidence: {qa_confidence:.2f}). Issues: {issues}. Recommendations: {recommendations}"
                            
                            if business_attempt < options.max_business_retries:
                                logger.warning(f"{error_msg}. Retrying...")
                                retry_count += 1
                                continue
                            else:
                                # On final failure, try LLM fallback if suggested
                                if llm_fallback and business_attempt == options.max_business_retries:
                                    logger.info(f"Attempting LLM fallback approach: {llm_fallback}")
                                    try:
                                        fallback_mapping = self._try_llm_fallback(
                                            local_files, clean_artist, clean_album, options.language, llm_fallback
                                        )
                                        if fallback_mapping:
                                            logger.info("LLM fallback succeeded - using fallback mapping")
                                            mapping = fallback_mapping
                                            qa_approved = True  # Override for fallback
                                            qa_confidence = 0.5  # Set moderate confidence for fallback
                                        else:
                                            raise ValueError(error_msg)
                                    except Exception as fallback_error:
                                        logger.error(f"LLM fallback failed: {fallback_error}")
                                        raise ValueError(error_msg)
                                else:
                                    raise ValueError(error_msg)
                    
                    # Execute file operations if all validations pass
                    files_processed = self._execute_file_operations(
                        album_path, mapping, options, clean_artist, clean_album
                    )
                    
                    return ProcessingResult(
                        album_path=album_path,
                        success=True,
                        files_processed=files_processed,
                        language_used=options.language,
                        retry_count=retry_count,
                        qa_approved=qa_approved,
                        qa_confidence=qa_confidence,
                        search_attempts=search_attempts
                    )
                    
                except Exception as e:
                    retry_count += 1
                    if business_attempt < options.max_business_retries:
                        logger.warning(f"Business logic attempt {business_attempt} failed: {e}. Retrying...")
                        continue
                    else:
                        raise e
            
            # If we get here, all business retries failed
            raise RuntimeError(f"All {options.max_business_retries} business logic attempts failed")
            
        except Exception as e:
            logger.error(f"Error processing album {album_path}: {e}")
            return ProcessingResult(
                album_path=album_path,
                success=False,
                error_message=str(e),
                language_used=options.language,
                retry_count=retry_count,
                qa_approved=qa_approved,
                qa_confidence=qa_confidence,
                search_attempts=search_attempts
            )
    
    def _try_llm_fallback(
        self,
        local_files: List[str],
        artist_name: str,
        album_name: str,
        language: Language,
        fallback_suggestion: str
    ) -> Optional[Dict[str, str]]:
        """
        Try an alternative LLM approach when standard mapping fails QA checks.
        This is a last-resort fallback using the QA service's suggestion.
        
        Args:
            local_files: List of local filenames
            artist_name: Clean artist name
            album_name: Clean album name
            language: Target language for processing
            fallback_suggestion: Specific fallback suggestion from QA service
            
        Returns:
            Dictionary mapping old filename -> new filename or None if fallback failed
        """
        try:
            logger.info(f"Attempting LLM fallback with suggestion: {fallback_suggestion}")
            
            # Create a specialized prompt for the fallback approach
            system_prompt = f"""
            You are a music file renaming specialist tasked with creating a clean mapping for filenames.
            
            IMPORTANT CONSTRAINTS:
            - You MUST return a valid JSON mapping with EXACTLY {len(local_files)} entries
            - All new filenames MUST start with a 2-digit track number (01, 02, etc.)
            - Keep original file extensions unchanged
            - Follow this specific approach: {fallback_suggestion}
            """
            
            user_prompt = f"""
            Clean and map these music files for album '{album_name}' by artist '{artist_name}'.
            
            Files to rename:
            {json.dumps(local_files, indent=2)}
            
            Return a JSON object with old filenames as keys and new filenames as values.
            The JSON must be valid and complete, with each file assigned a new name.
            
            Language: {language.value}
            
            Special instructions: {fallback_suggestion}
            """
            
            # Generate fallback mapping using direct LLM call
            llm_response = self.llm_service.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            # Parse the response
            fallback_mapping = self._parse_llm_response(llm_response)
            
            # Validate the mapping
            if not fallback_mapping or len(fallback_mapping) != len(local_files):
                logger.warning(f"LLM fallback produced invalid mapping with {len(fallback_mapping)} entries (expected {len(local_files)})")
                return None
                
            # Check if all required files are mapped
            missing_files = set(local_files) - set(fallback_mapping.keys())
            if missing_files:
                logger.warning(f"LLM fallback mapping is missing {len(missing_files)} files")
                return None
                
            # Always apply Traditional Chinese conversion regardless of language setting
            fallback_mapping = {
                old: self._convert_to_traditional_chinese(new) 
                for old, new in fallback_mapping.items()
            }
            logger.info("Applied Traditional Chinese conversion to fallback mapping (always applied)")
                
            logger.info(f"LLM fallback succeeded with {len(fallback_mapping)} entries")
            return fallback_mapping
            
        except Exception as e:
            logger.error(f"LLM fallback failed: {e}")
            return None
    
    def _get_official_album_data(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language,
        local_files: List[str] = None
    ) -> Optional[Tuple[str, str, List[str]]]:
        """
        Get official album data from song name service.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            language: Target language for results
            local_files: List of local filenames for enhanced search context
            
        Returns:
            Tuple of (clean_artist, clean_album, track_names) or None
        """
        try:
            result = self.song_name_service.search_album(artist_name, album_name, language, local_files)
            return result
        except Exception as e:
            logger.error(f"Failed to get official album data: {e}")
            return None
    
    def _get_official_album_data_with_retries(
        self, 
        artist_name: str, 
        album_name: str,
        language: Language,
        max_search_retries: int,
        local_files: List[str] = None
    ) -> Tuple[Optional[Tuple[str, str, List[str]]], int]:
        """
        Get official album data with enhanced retry logic and QA-suggested alternatives.
        
        Args:
            artist_name: Artist name
            album_name: Album name
            language: Target language
            max_search_retries: Maximum search attempts
            local_files: List of local filenames for enhanced search context
            
        Returns:
            Tuple of (official_data, search_attempts_count)
        """
        search_attempts = 0
        failed_searches = []
        
        # Try original search method first
        original_result = self._get_official_album_data(artist_name, album_name, language, local_files)
        search_attempts += 1
        
        if original_result:
            return original_result, search_attempts
        
        # Record the failed search terms for QA service
        failed_searches.append(f'artist:"{artist_name}" album:"{album_name}"')
        
        # If QA service is available, get alternative search terms
        if self.qa_service and search_attempts < max_search_retries:
            try:
                alternatives = self.qa_service.suggest_search_alternatives(
                    artist_name=artist_name,
                    album_name=album_name,
                    failed_searches=failed_searches,
                    target_language=language
                )
                
                logger.info(f"QA service suggested {len(alternatives)} alternative search terms")
                
                # Try each alternative search term
                for alt_search in alternatives:
                    if search_attempts >= max_search_retries:
                        break
                    
                    try:
                        # Parse the alternative search term and try it
                        logger.info(f"Trying alternative search: {alt_search}")
                        
                        # For now, treat alternatives as direct album names
                        # In a more sophisticated implementation, we'd parse the search syntax
                        alt_result = self._get_official_album_data(artist_name, alt_search, language, local_files)
                        search_attempts += 1
                        
                        if alt_result:
                            logger.info(f"Alternative search succeeded: {alt_search}")
                            return alt_result, search_attempts
                        
                        failed_searches.append(alt_search)
                        
                    except Exception as e:
                        logger.warning(f"Alternative search failed for '{alt_search}': {e}")
                        search_attempts += 1
                        failed_searches.append(alt_search)
                        
            except Exception as e:
                logger.warning(f"Failed to get QA search alternatives: {e}")
        
        logger.warning(f"All {search_attempts} search attempts failed for {artist_name} - {album_name}")
        return None, search_attempts
    
    def _generate_filename_mapping(
        self,
        local_files: List[str],
        artist_name: str,
        album_name: str,
        official_tracks: List[str],
        language: Language,
        options: ProcessingOptions
    ) -> Dict[str, str]:
        """
        Generate filename mapping using orchestrated approach with prompt service.
        
        Args:
            local_files: List of local filenames
            artist_name: Clean artist name
            album_name: Clean album name
            official_tracks: List of official track names (used as reference only)
            language: Target language for processing
            options: Processing options
            
        Returns:
            Dictionary mapping old filename -> new filename
        """
        for attempt in range(1, options.max_retries + 1):  # Use options parameter for consistency
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
                
                # Always apply Traditional Chinese conversion regardless of language setting
                mapping = {
                    old: self._convert_to_traditional_chinese(new) 
                    for old, new in mapping.items()
                }
                logger.info("Applied Traditional Chinese conversion to mapping (always applied)")
                
                logger.info(f"Successfully generated mapping with {len(mapping)} entries")
                return mapping
                
            except Exception as e:
                logger.warning(f"Mapping generation failed (attempt {attempt}): {e}")
                if attempt == options.max_retries:  # Check against options parameter
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
        
        # Relaxed validation for track count mismatches
        if official_tracks and len(track_numbers) != len(official_tracks):
            # Just log a warning but don't treat as a validation error
            logger.warning(f"Track count mismatch: {len(track_numbers)} files, {len(official_tracks)} official tracks")
            logger.info("Allowing mismatch as the official tracks are for reference only")
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
        
        # Always apply Traditional Chinese conversion to artist and album names
        clean_artist = self._convert_to_traditional_chinese(clean_artist)
        clean_album = self._convert_to_traditional_chinese(clean_album)
        logger.info("Applied Traditional Chinese conversion to artist and album names (always applied)")
        
        if options.output_mode == "copy":
            # Create cleaned directory structure at the same level as the original album folder
            album_parent = os.path.dirname(album_path)
            # Go one level up to place "cleaned" folder at the same level as the album's parent folder
            base_parent = os.path.dirname(album_parent)
            cleaned_base = os.path.join(base_parent, "cleaned")
            # Preserve the album's parent folder name in the cleaned structure
            album_parent_name = os.path.basename(album_parent)
            cleaned_album_parent = os.path.join(cleaned_base, album_parent_name)
            self.file_repository.make_dir(cleaned_album_parent)
            clean_album_dir = os.path.join(cleaned_album_parent, f"[{clean_artist}] {clean_album}")
            
            self.file_repository.make_dir(clean_album_dir)
            
            # Copy files with new names
            for old_filename, new_filename in mapping.items():
                src = os.path.join(album_path, old_filename)
                
                # Always apply Chinese conversion automatically when detected
                new_filename = self._convert_to_traditional_chinese(new_filename)
                
                dst = os.path.join(clean_album_dir, new_filename)
                
                self.file_repository.copy_file(src, dst)
                logger.info(f"Copied: {old_filename} → {new_filename}")
                files_processed += 1
                
        else:  # in_place
            # Rename files in place
            for old_filename, new_filename in mapping.items():
                src = os.path.join(album_path, old_filename)
                
                # Always apply Chinese conversion automatically when detected
                new_filename = self._convert_to_traditional_chinese(new_filename)
                
                dst = os.path.join(album_path, new_filename)
                
                if src != dst:
                    self.file_repository.rename_file(src, dst)
                    logger.info(f"Renamed: {old_filename} → {new_filename}")
                    files_processed += 1
        
        return files_processed
    
    def _convert_to_traditional_chinese(self, text_or_filename: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Automatically convert simplified Chinese characters to traditional Chinese when detected.
        Handles filenames, plain text, or lists of strings intelligently.
        
        Args:
            text_or_filename: String, filename, or list of strings to convert
            
        Returns:
            Converted string, filename, or list of strings with traditional Chinese characters
        """
        # Handle list of strings
        if isinstance(text_or_filename, list):
            return [self._convert_to_traditional_chinese(item) for item in text_or_filename]
        
        # Handle single string
        if not isinstance(text_or_filename, str):
            return text_or_filename
            
        # Check if it's a filename (contains extension)
        if '.' in text_or_filename and not text_or_filename.startswith('.'):
            # Extract name and extension
            name, ext = os.path.splitext(text_or_filename)
            
            # Always apply conversion - OpenCC will only change simplified characters
            converted_name = self.cc.convert(name)
            
            # Clean filename of invalid characters
            converted_name = self._clean_filename(converted_name)
            
            return f"{converted_name}{ext}"
        
        # Plain text conversion - OpenCC will only change simplified characters
        return self.cc.convert(text_or_filename)
    
    def _clean_filename(self, name: str) -> str:
        """
        Remove illegal filesystem characters from filename.
        
        Args:
            name: Filename to clean
            
        Returns:
            Cleaned filename
        """
        return re.sub(r'[<>:"/\\|?*]', '', name)
    
    def _process_pure_translation(
        self,
        album_path: str,
        local_files: List[str],
        artist_name: str,
        album_name: str,
        options: ProcessingOptions
    ) -> ProcessingResult:
        """
        Process album using pure translation mode (OpenCC only).
        This mode bypasses all LLM processing and Spotify searches.
        
        Args:
            album_path: Path to the album directory
            local_files: List of local audio files
            artist_name: Extracted artist name
            album_name: Extracted album name
            options: Processing options
            
        Returns:
            ProcessingResult with success status and processed file count
        """
        try:
            logger.info("🔄 Using pure translation mode (OpenCC only)")
            
            # Create pure translation mode processor
            translator = PureTranslationMode()
            
            # Always translate artist and album names to Traditional Chinese
            clean_artist, clean_album = translator.translate_artist_album(artist_name, album_name)
            logger.info("Applied Traditional Chinese conversion in pure translation mode (always applied)")
                
            # Generate mapping using direct translation
            mapping = translator.process_album(album_path, local_files)
            
            # Execute file operations
            files_processed = self._execute_file_operations(
                album_path, mapping, options, clean_artist, clean_album
            )
            
            logger.info(f"✅ Pure translation completed: {files_processed} files processed")
            
            return ProcessingResult(
                album_path=album_path,
                success=True,
                files_processed=files_processed,
                language_used=options.language,
                retry_count=0,
                qa_approved=None,  # No QA in pure translation mode
                qa_confidence=None,  # No QA in pure translation mode
                search_attempts=0   # No search in pure translation mode
            )
        
        except Exception as e:
            logger.error(f"❌ Pure translation failed: {e}")
            return ProcessingResult(
                album_path=album_path,
                success=False,
                error_message=f"Pure translation failed: {e}",
                language_used=options.language
            )

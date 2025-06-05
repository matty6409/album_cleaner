import os
from typing import Optional, List
from infrastructure.persistence.file_repository import FileRepository
from infrastructure.logging.logger import logger
from domain.entities.models import Album, Track
from infrastructure.services.llm_services.perplexity_llm_service import PerplexityLLMService
from infrastructure.services.llm_services.openrouter_deepseek_llm_service import OpenRouterDeepSeekLLMService
from infrastructure.config.settings import Settings
from opencc import OpenCC
import time
import re

class CleanerService:
    """
    Service for cleaning and aligning music file names in album directories using LLMs.
    Handles both in-place and to_new_dir (cleaned folder) operations.
    """
    def __init__(self, prompt_path: str, settings: Settings, to_new_dir: bool = True, llm_provider: str = "perplexity", max_retries: int = 3):
        self.file_repo = FileRepository()
        self.settings = settings
        self.prompt_path = prompt_path
        self.to_new_dir = to_new_dir
        self.max_retries = max_retries
        if llm_provider == "deepseek":
            self.llm_client = OpenRouterDeepSeekLLMService(settings)
        else:
            self.llm_client = PerplexityLLMService(settings)

    def clean_album(self, album_dir: str, singer_name: str = "", language: str = "English") -> None:
        files = self.file_repo.list_audio_files(album_dir)
        album_name = os.path.basename(album_dir)
        if not singer_name:
            singer_name = self._extract_singer_name(album_name)
        expected_track_count = len(files)
        logger.info(f"Processing album: {album_name} with {expected_track_count} tracks (singer: {singer_name})")

        # Retry LLM and validation
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"LLM generation attempt {attempt}")
                rename_map = self.llm_client.get_rename_map(files, album_name, language)
                # Parse LLM output into Track objects
                tracks = self._parse_tracks(rename_map, files)
                # Validate with Album entity
                album = Album(
                    singer_name=singer_name,
                    album_name=album_name,
                    tracks=tracks,
                    expected_track_count=expected_track_count
                )
                logger.info(f"Album validation succeeded on attempt {attempt}")
                break
            except Exception as e:
                logger.warning(f"Validation failed on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Max retries reached for album: {album_name}")
                    return
                time.sleep(1)
        # File operations
        if self.to_new_dir:
            parent_dir = os.path.dirname(album_dir)
            cleaned_dir = os.path.join(parent_dir, "cleaned", album_name)
            self.file_repo.make_dir(cleaned_dir)
            for track in album.tracks:
                self.file_repo.copy_file(
                    os.path.join(album_dir, track.filename),
                    os.path.join(cleaned_dir, f"{track.track_number:02d} {track.name}{os.path.splitext(track.filename)[1]}")
                )
            self._convert_traditional_chinese(cleaned_dir)
            self._rename_album_images(cleaned_dir)
            self._clean_supplementary_files(cleaned_dir)
        else:
            for track in album.tracks:
                src = os.path.join(album_dir, track.filename)
                dst = os.path.join(album_dir, f"{track.track_number:02d} {track.name}{os.path.splitext(track.filename)[1]}")
                if src != dst:
                    self.file_repo.rename_file(src, dst)
            self._convert_traditional_chinese(album_dir)
            self._rename_album_images(album_dir)
            self._clean_supplementary_files(album_dir)

    def _parse_tracks(self, rename_map, files: List[str]) -> List[Track]:
        # Ensure mapping is 1:1 and order is preserved
        mapping = rename_map["old_to_new"] if "old_to_new" in rename_map else rename_map
        tracks = []
        for i, old_name in enumerate(files):
            new_name = mapping.get(old_name)
            if not new_name:
                raise ValueError(f"Missing mapping for file: {old_name}")
            # Extract track number and name from new_name
            try:
                num_str, name_ext = new_name.split(" ", 1)
                track_number = int(num_str)
                name, _ = os.path.splitext(name_ext)
            except Exception:
                raise ValueError(f"Invalid new filename format: {new_name}")
            tracks.append(Track(track_number=track_number, name=name, filename=old_name))
        return tracks

    def _convert_traditional_chinese(self, path: str) -> None:
        cc = OpenCC('s2t')
        for filename in os.listdir(path):
            base, ext = os.path.splitext(filename)
            new_base = cc.convert(base)
            if new_base != base:
                src = os.path.join(path, filename)
                dst = os.path.join(path, f"{self._clean_filename(new_base)}{ext}")
                self.file_repo.rename_file(src, dst)

    def _rename_album_images(self, album_dir: str) -> None:
        mapping = Album.clean_album_images(album_dir)
        for old, new in mapping.items():
            src = os.path.join(album_dir, old)
            dst = os.path.join(album_dir, new)
            if src != dst:
                self.file_repo.rename_file(src, dst)

    def _clean_supplementary_files(self, album_dir: str) -> None:
        """
        Rename or remove non-audio, non-image files in the album folder.
        """
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        audio_exts = set(self.file_repo.AudioFileValidator.AUDIO_EXTENSIONS)
        for f in os.listdir(album_dir):
            ext = os.path.splitext(f)[1].lower()
            if ext not in image_exts and ext not in audio_exts:
                src = os.path.join(album_dir, f)
                new_name = f"supplementary_{self._clean_filename(os.path.splitext(f)[0])}{ext}"
                dst = os.path.join(album_dir, new_name)
                if src != dst:
                    logger.info(f"Renaming supplementary file: {f} -> {new_name}")
                    self.file_repo.rename_file(src, dst)

    def _extract_singer_name(self, album_name: str) -> str:
        # Try to extract [Singer Name] from album folder name
        match = re.match(r"\[(.*?)\]", album_name)
        if match:
            return match.group(1)
        return ""

    def _clean_filename(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '', name) 
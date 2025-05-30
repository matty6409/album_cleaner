import os
from typing import Optional
from infrastructure.file_repository import FileRepository
from infrastructure.llm_client import LLMClient
from domain.models import FileRenameMap
from infrastructure.settings import Settings
from opencc import OpenCC

class CleanerService:
    """
    Service for cleaning and aligning music file names in album directories using LLMs.
    Handles both in-place and to_new_dir (cleaned folder) operations.
    """
    def __init__(self, prompt_path: str, settings: Settings, to_new_dir: bool = True):
        """
        :param prompt_path: Path to the YAML prompt template
        :param settings: Pydantic Settings object
        :param to_new_dir: If True, output to cleaned/ folder; else, rename in place
        """
        self.file_repo = FileRepository()
        self.llm_client = LLMClient(prompt_path, settings)
        self.to_new_dir = to_new_dir

    def clean_album(self, album_dir: str, language: str = "English") -> None:
        """
        Clean and align all audio files in a given album directory.
        :param album_dir: Path to the album directory
        :param language: Language for official track names
        """
        files = self.file_repo.list_audio_files(album_dir)
        album_name = os.path.basename(album_dir)
        rename_map = self.llm_client.get_rename_map(files, album_name, language)
        rename_map = FileRenameMap(**rename_map)

        if self.to_new_dir:
            parent_dir = os.path.dirname(album_dir)
            cleaned_dir = os.path.join(parent_dir, "cleaned", album_name)
            self.file_repo.make_dir(cleaned_dir)
            for old_name in files:
                if old_name in rename_map.old_to_new:
                    new_name = self._clean_filename(rename_map.old_to_new[old_name])
                    self.file_repo.copy_file(
                        os.path.join(album_dir, old_name),
                        os.path.join(cleaned_dir, new_name)
                    )
            self._convert_traditional_chinese(cleaned_dir)
        else:
            for old_name in files:
                if old_name in rename_map.old_to_new:
                    new_name = self._clean_filename(rename_map.old_to_new[old_name])
                    src = os.path.join(album_dir, old_name)
                    dst = os.path.join(album_dir, new_name)
                    if src != dst:
                        self.file_repo.rename_file(src, dst)
            self._convert_traditional_chinese(album_dir)

    def _convert_traditional_chinese(self, path: str) -> None:
        """
        Convert all filenames in a directory to Traditional Chinese if needed.
        :param path: Directory path
        """
        cc = OpenCC('s2t')
        for filename in os.listdir(path):
            base, ext = os.path.splitext(filename)
            new_base = cc.convert(base)
            if new_base != base:
                src = os.path.join(path, filename)
                dst = os.path.join(path, f"{self._clean_filename(new_base)}{ext}")
                self.file_repo.rename_file(src, dst)

    def _clean_filename(self, name: str) -> str:
        """
        Remove illegal characters from filenames.
        :param name: Filename string
        :return: Cleaned filename
        """
        import re
        return re.sub(r'[<>:"/\\|?*]', '', name) 
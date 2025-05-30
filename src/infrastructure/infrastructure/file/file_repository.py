import os
import shutil
from natsort import natsorted
from typing import List

class AudioFileValidator:
    """
    Utility for validating audio file extensions.
    """
    AUDIO_EXTENSIONS = {
        '.dsd', '.dff', '.dsf', '.wav', '.aiff', '.aif',
        '.flac', '.alac', '.dts', '.thd', '.mlp', '.mqa',
        '.tak', '.ape', '.mp3', '.aac', '.m4a', '.ogg', '.wma'
    }

    @staticmethod
    def is_audio_file(filename: str) -> bool:
        """
        Check if a filename is a valid audio file.
        :param filename: Filename string
        :return: True if audio file, else False
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in AudioFileValidator.AUDIO_EXTENSIONS

class FileRepository:
    """
    Repository for file system operations: listing, copying, renaming, and directory creation.
    """
    def list_audio_files(self, directory: str) -> List[str]:
        """
        List all audio files in a directory, sorted naturally.
        :param directory: Directory path
        :return: List of audio filenames
        """
        return natsorted([
            f for f in os.listdir(directory)
            if AudioFileValidator.is_audio_file(f)
        ])

    def copy_file(self, src: str, dst: str) -> None:
        """
        Copy a file from src to dst.
        """
        shutil.copy2(src, dst)

    def rename_file(self, src: str, dst: str) -> None:
        """
        Rename a file from src to dst.
        """
        os.rename(src, dst)

    def make_dir(self, path: str) -> None:
        """
        Create a directory if it does not exist.
        """
        os.makedirs(path, exist_ok=True) 
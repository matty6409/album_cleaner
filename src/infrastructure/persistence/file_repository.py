import os
import shutil
from natsort import natsorted
from typing import List
from application.interfaces.repositories.file_repository_interface import FileRepositoryInterface

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

class FileRepository(FileRepositoryInterface):
    """
    Concrete implementation of file repository for file system operations.
    """
    
    def list_audio_files(self, directory: str) -> List[str]:
        """
        List all audio files in a directory, sorted naturally.
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of audio filenames
        """
        if not os.path.exists(directory):
            return []
            
        return natsorted([
            f for f in os.listdir(directory)
            if AudioFileValidator.is_audio_file(f)
        ])

    def copy_file(self, src: str, dst: str) -> None:
        """
        Copy a file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
        """
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    def rename_file(self, src: str, dst: str) -> None:
        """
        Rename/move a file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
        """
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        os.rename(src, dst)

    def make_dir(self, path: str) -> None:
        """
        Create a directory if it doesn't exist.
        
        Args:
            path: Directory path to create
        """
        os.makedirs(path, exist_ok=True)

    def get_album_directories(self, base_path: str) -> List[str]:
        """
        Get all album directories in the base path.
        
        Args:
            base_path: Base directory to search
            
        Returns:
            List of album directory paths
        """
        album_dirs = []
        if not os.path.exists(base_path):
            return album_dirs
            
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                # Check if directory contains audio files
                if self.list_audio_files(item_path):
                    album_dirs.append(item_path)
        
        return natsorted(album_dirs)

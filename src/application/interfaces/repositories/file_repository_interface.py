from abc import ABC, abstractmethod
from typing import List

class FileRepositoryInterface(ABC):
    """
    Abstract interface for file system operations.
    """
    
    @abstractmethod
    def list_audio_files(self, directory: str) -> List[str]:
        """
        List all audio files in a directory.
        
        Args:
            directory: Directory path to search
            
        Returns:
            List of audio filenames
        """
        pass
    
    @abstractmethod
    def copy_file(self, src: str, dst: str) -> None:
        """
        Copy a file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
        """
        pass
    
    @abstractmethod
    def rename_file(self, src: str, dst: str) -> None:
        """
        Rename/move a file from source to destination.
        
        Args:
            src: Source file path
            dst: Destination file path
        """
        pass
    
    @abstractmethod
    def make_dir(self, path: str) -> None:
        """
        Create a directory if it doesn't exist.
        
        Args:
            path: Directory path to create
        """
        pass
    
    @abstractmethod
    def get_album_directories(self, base_path: str) -> List[str]:
        """
        Get all album directories in the base path.
        
        Args:
            base_path: Base directory to search
            
        Returns:
            List of album directory paths
        """
        pass

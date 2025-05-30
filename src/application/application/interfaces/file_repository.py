from abc import ABC, abstractmethod
from typing import List

class FileRepositoryInterface(ABC):
    @abstractmethod
    def list_audio_files(self, directory: str) -> List[str]:
        pass

    @abstractmethod
    def copy_file(self, src: str, dst: str) -> None:
        pass

    @abstractmethod
    def rename_file(self, src: str, dst: str) -> None:
        pass

    @abstractmethod
    def make_dir(self, path: str) -> None:
        pass

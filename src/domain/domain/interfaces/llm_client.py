from abc import ABC, abstractmethod
from typing import List, Dict

class LLMClientInterface(ABC):
    @abstractmethod
    def get_rename_map(self, files: List[str], album_name: str, language: str) -> Dict[str, Dict[str, str]]:
        """
        Abstract method to get a mapping of old to new filenames from an LLM.
        :param files: List of filenames
        :param album_name: Album name
        :param language: Language for official track names
        :return: Dict with 'old_to_new' mapping
        """
        pass

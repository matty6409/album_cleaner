from domain.interfaces.llm_client import LLMClientInterface
from typing import List, Dict

class BaseLLMClient(LLMClientInterface):
    def get_rename_map(self, files: List[str], album_name: str, language: str) -> Dict[str, Dict[str, str]]:
        raise NotImplementedError("This method should be implemented by subclasses.")

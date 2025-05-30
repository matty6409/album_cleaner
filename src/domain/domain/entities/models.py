from pydantic import BaseModel
from typing import Dict

class RenameSchema(BaseModel):
    """
    Pydantic model for the LLM's rename mapping output.
    """
    old_to_new: Dict[str, str]

class FileRenameMap(BaseModel):
    """
    Pydantic model for direct filename mapping.
    """
    old_to_new: Dict[str, str]  # Direct filename mapping 
"""
Data Transfer Objects (DTOs) for application layer use cases.
"""
from dataclasses import dataclass
from typing import Optional
from domain.values_objects.language import Language


@dataclass
class ProcessingOptions:
    """Options for album processing use case."""
    base_path: str
    language: Language = Language.ENGLISH
    output_mode: str = "copy"  # "copy" or "in_place"
    max_retries: int = 2  # Reduced from 3 since we're more flexible now
    max_business_retries: int = 2  # Reduced from 3 for business logic retries
    max_search_retries: int = 3   # Reduced from 5 for Spotify search attempts
    enable_qa_review: bool = True  # Enable LLM quality assurance
    qa_confidence_threshold: float = 0.6  # Lowered from 0.7 for more flexibility
    pure_translation: bool = False  # Whether to use pure translation mode (OpenCC only)
    
    def __post_init__(self):
        """Validate processing options."""
        if not self.base_path:
            raise ValueError("Base path cannot be empty")
        if self.output_mode not in ["copy", "in_place"]:
            raise ValueError("Output mode must be 'copy' or 'in_place'")
        if self.max_retries < 1:
            raise ValueError("Max retries must be at least 1")
        if self.max_business_retries < 1:
            raise ValueError("Max business retries must be at least 1")
        if self.max_search_retries < 1:
            raise ValueError("Max search retries must be at least 1")
        if not 0.0 <= self.qa_confidence_threshold <= 1.0:
            raise ValueError("QA confidence threshold must be between 0.0 and 1.0")


@dataclass
class ProcessingResult:
    """Result object for album processing use case."""
    album_path: str
    success: bool
    error_message: Optional[str] = None
    files_processed: int = 0
    language_used: Language = Language.ENGLISH
    retry_count: int = 0  # NEW: Track how many retries were needed
    qa_approved: Optional[bool] = None  # NEW: QA approval status
    qa_confidence: Optional[float] = None  # NEW: QA confidence score
    search_attempts: int = 0  # NEW: Track Spotify search attempts

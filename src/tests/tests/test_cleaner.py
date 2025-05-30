import os
import tempfile
import shutil
import pytest
from app.services.cleaner_service import CleanerService
from app.repositories.file_repository import FileRepository

@pytest.fixture
def temp_album_dir() -> str:
    """
    Create a temporary album directory with dummy audio files for testing.
    """
    d = tempfile.mkdtemp()
    album = os.path.join(d, "TestAlbum")
    os.makedirs(album)
    # Create dummy files
    for i in range(1, 4):
        with open(os.path.join(album, f"0{i} - Test Song {i}.flac"), 'w') as f:
            f.write("dummy audio data")
    yield album
    shutil.rmtree(d)

def test_list_audio_files(temp_album_dir: str) -> None:
    """
    Test that FileRepository lists all audio files in a directory.
    """
    repo = FileRepository()
    files = repo.list_audio_files(temp_album_dir)
    assert len(files) == 3
    assert files[0].endswith('.flac')

def test_cleaner_service_init() -> None:
    """
    Test that CleanerService initializes with correct settings.
    """
    service = CleanerService(prompt_path="prompts/cleaner_prompt.yaml", settings=None, to_new_dir=True)
    assert service.to_new_dir is True 
"""
Unit tests for file repository.
Tests file operations, directory management, and audio file detection.
"""
import pytest
import tempfile
import os
import sys
import shutil
from pathlib import Path
from typing import List

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from application.interfaces.repositories.file_repository_interface import FileRepositoryInterface
from infrastructure.repositories.file_repository import FileRepository


class TestFileRepository:
    """Test cases for file repository implementation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def repository(self):
        """Create file repository instance."""
        return FileRepository()
    
    @pytest.fixture
    def sample_album_dir(self, temp_dir):
        """Create sample album directory with audio files."""
        album_path = os.path.join(temp_dir, "[Test Artist] Test Album")
        os.makedirs(album_path)
        
        # Create sample audio files
        audio_files = [
            "01 Track One.flac",
            "02 Track Two.mp3",
            "03 Track Three.wav",
            "04 Track Four.m4a",
            "05 Track Five.dsf"
        ]
        
        for filename in audio_files:
            file_path = os.path.join(album_path, filename)
            with open(file_path, 'w') as f:
                f.write("dummy audio data")
        
        # Create non-audio files (should be ignored)
        non_audio_files = [
            "cover.jpg",
            "folder.jpg", 
            "album.nfo",
            "playlist.m3u",
            ".DS_Store"
        ]
        
        for filename in non_audio_files:
            file_path = os.path.join(album_path, filename)
            with open(file_path, 'w') as f:
                f.write("dummy data")
        
        return album_path

    def test_list_audio_files(self, repository, sample_album_dir):
        """Test listing audio files from directory."""
        audio_files = repository.list_audio_files(sample_album_dir)
        
        assert len(audio_files) == 5
        assert "01 Track One.flac" in audio_files
        assert "02 Track Two.mp3" in audio_files
        assert "03 Track Three.wav" in audio_files
        assert "04 Track Four.m4a" in audio_files
        assert "05 Track Five.dsf" in audio_files
        
        # Ensure non-audio files are not included
        assert "cover.jpg" not in audio_files
        assert "folder.jpg" not in audio_files
        assert "album.nfo" not in audio_files
        assert ".DS_Store" not in audio_files

    def test_list_audio_files_empty_directory(self, repository, temp_dir):
        """Test listing audio files from empty directory."""
        empty_dir = os.path.join(temp_dir, "empty")
        os.makedirs(empty_dir)
        
        audio_files = repository.list_audio_files(empty_dir)
        
        assert audio_files == []

    def test_list_audio_files_nonexistent_directory(self, repository, temp_dir):
        """Test listing audio files from non-existent directory."""
        nonexistent_dir = os.path.join(temp_dir, "does_not_exist")
        
        audio_files = repository.list_audio_files(nonexistent_dir)
        
        assert audio_files == []

    def test_copy_file(self, repository, temp_dir):
        """Test copying files."""
        # Create source file
        src_path = os.path.join(temp_dir, "source.flac")
        with open(src_path, 'w') as f:
            f.write("test audio data")
        
        # Create destination directory
        dest_dir = os.path.join(temp_dir, "destination")
        os.makedirs(dest_dir)
        dest_path = os.path.join(dest_dir, "copied.flac")
        
        repository.copy_file(src_path, dest_path)
        
        # Verify file was copied
        assert os.path.exists(dest_path)
        with open(dest_path, 'r') as f:
            content = f.read()
        assert content == "test audio data"
        
        # Verify source still exists
        assert os.path.exists(src_path)

    def test_copy_file_nonexistent_source(self, repository, temp_dir):
        """Test copying non-existent source file."""
        src_path = os.path.join(temp_dir, "nonexistent.flac")
        dest_path = os.path.join(temp_dir, "destination.flac")
        
        with pytest.raises(FileNotFoundError):
            repository.copy_file(src_path, dest_path)

    def test_rename_file(self, repository, temp_dir):
        """Test renaming files."""
        # Create source file
        old_path = os.path.join(temp_dir, "old_name.flac")
        with open(old_path, 'w') as f:
            f.write("test audio data")
        
        new_path = os.path.join(temp_dir, "new_name.flac")
        
        repository.rename_file(old_path, new_path)
        
        # Verify file was renamed
        assert not os.path.exists(old_path)
        assert os.path.exists(new_path)
        with open(new_path, 'r') as f:
            content = f.read()
        assert content == "test audio data"

    def test_rename_file_nonexistent_source(self, repository, temp_dir):
        """Test renaming non-existent source file."""
        old_path = os.path.join(temp_dir, "nonexistent.flac")
        new_path = os.path.join(temp_dir, "new_name.flac")
        
        with pytest.raises(FileNotFoundError):
            repository.rename_file(old_path, new_path)

    def test_make_dir(self, repository, temp_dir):
        """Test creating directories."""
        new_dir = os.path.join(temp_dir, "new_directory")
        
        repository.make_dir(new_dir)
        
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

    def test_make_dir_nested(self, repository, temp_dir):
        """Test creating nested directories."""
        nested_dir = os.path.join(temp_dir, "level1", "level2", "level3")
        
        repository.make_dir(nested_dir)
        
        assert os.path.exists(nested_dir)
        assert os.path.isdir(nested_dir)

    def test_make_dir_existing(self, repository, temp_dir):
        """Test creating directory that already exists."""
        existing_dir = os.path.join(temp_dir, "existing")
        os.makedirs(existing_dir)
        
        # Should not raise error
        repository.make_dir(existing_dir)
        
        assert os.path.exists(existing_dir)
        assert os.path.isdir(existing_dir)

    def test_get_album_directories(self, repository, temp_dir):
        """Test getting album directories."""
        # Create valid album directories
        album_dirs = [
            "[Artist One] Album One",
            "[Artist Two] Album Two", 
            "[Artist Three] Album Three"
        ]
        
        for dir_name in album_dirs:
            dir_path = os.path.join(temp_dir, dir_name)
            os.makedirs(dir_path)
            # Add audio files to make them valid album directories
            with open(os.path.join(dir_path, "01 Track.mp3"), 'w') as f:
                f.write("dummy audio content")
        
        # Create invalid directories (should be ignored)
        invalid_dirs = [
            "Not An Album",
            "Another Invalid Dir",
            ".hidden"
        ]
        
        for dir_name in invalid_dirs:
            dir_path = os.path.join(temp_dir, dir_name)
            os.makedirs(dir_path)
        
        # Create some files (should be ignored)
        file_path = os.path.join(temp_dir, "some_file.txt")
        with open(file_path, 'w') as f:
            f.write("test")
        
        result = repository.get_album_directories(temp_dir)
        
        assert len(result) == 3
        for album_dir in album_dirs:
            album_path = os.path.join(temp_dir, album_dir)
            assert album_path in result

    def test_get_album_directories_empty(self, repository, temp_dir):
        """Test getting album directories from empty directory."""
        result = repository.get_album_directories(temp_dir)
        
        assert result == []

    def test_get_album_directories_nonexistent(self, repository, temp_dir):
        """Test getting album directories from non-existent directory."""
        nonexistent_dir = os.path.join(temp_dir, "does_not_exist")
        
        result = repository.get_album_directories(nonexistent_dir)
        
        assert result == []

    def test_audio_file_extensions(self, repository, temp_dir):
        """Test that all supported audio extensions are detected."""
        test_dir = os.path.join(temp_dir, "test_extensions")
        os.makedirs(test_dir)
        
        # Test all supported extensions
        supported_extensions = [
            ".flac", ".wav", ".mp3", ".m4a", ".aac", 
            ".ogg", ".wma", ".dsf", ".dff", ".ape"
        ]
        
        for i, ext in enumerate(supported_extensions):
            filename = f"track_{i:02d}{ext}"
            file_path = os.path.join(test_dir, filename)
            with open(file_path, 'w') as f:
                f.write("dummy audio")
        
        audio_files = repository.list_audio_files(test_dir)
        
        assert len(audio_files) == len(supported_extensions)
        for ext in supported_extensions:
            # Check that at least one file with this extension is found
            assert any(file.endswith(ext) for file in audio_files)

    def test_case_insensitive_extensions(self, repository, temp_dir):
        """Test that file extensions are detected case-insensitively."""
        test_dir = os.path.join(temp_dir, "case_test")
        os.makedirs(test_dir)
        
        # Create files with different case extensions
        test_files = [
            "track01.FLAC",
            "track02.Mp3", 
            "track03.WAV",
            "track04.m4A"
        ]
        
        for filename in test_files:
            file_path = os.path.join(test_dir, filename)
            with open(file_path, 'w') as f:
                f.write("dummy audio")
        
        audio_files = repository.list_audio_files(test_dir)
        
        assert len(audio_files) == 4
        for filename in test_files:
            assert filename in audio_files

    def test_copy_file_creates_directories(self, repository, temp_dir):
        """Test that copying creates destination directories if they don't exist."""
        # Create source file
        src_path = os.path.join(temp_dir, "source.flac")
        with open(src_path, 'w') as f:
            f.write("test data")
        
        # Destination in non-existent nested directory
        dest_path = os.path.join(temp_dir, "new", "nested", "dir", "file.flac")
        
        repository.copy_file(src_path, dest_path)
        
        assert os.path.exists(dest_path)
        assert os.path.isdir(os.path.dirname(dest_path))

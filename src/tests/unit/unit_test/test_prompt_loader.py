"""
Unit tests for YAML prompt loader service.
Tests prompt template loading, rendering, and error handling.
"""
import pytest
import tempfile
import os
import sys
import yaml
from typing import Dict, Any
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_dir))

from application.interfaces.services.prompt_loading_service_interface import PromptLoadingService
from infrastructure.services.prompt_loaders.yaml_prompt_loader import YamlPromptLoader
from domain.entities.models import Language


class TestYamlPromptLoader:
    """Test cases for YAML prompt loader implementation."""
    
    @pytest.fixture
    def loader(self):
        """Create YAML prompt loader instance."""
        return YamlPromptLoader()
    
    @pytest.fixture
    def temp_prompt_file(self):
        """Create temporary prompt file for testing."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        
        prompt_content = {
            'system': 'You are a test system. Process {{ item_type }} for {{ user_name }}.',
            'user': 'Please process these items: {{ items }}. Language: {{ language }}'
        }
        
        yaml.dump(prompt_content, temp_file, default_flow_style=False)
        temp_file.close()
        
        yield temp_file.name
        
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def sample_variables(self):
        """Sample variables for template rendering."""
        return {
            'item_type': 'music files',
            'user_name': 'Test User',
            'items': ['file1.mp3', 'file2.mp3'],
            'language': 'English'
        }

    def test_load_prompt_template(self, loader, temp_prompt_file):
        """Test loading prompt template from YAML file."""
        templates = loader.load_prompt_template(temp_prompt_file)
        
        assert 'system' in templates
        assert 'user' in templates
        assert '{{ item_type }}' in templates['system']
        assert '{{ user_name }}' in templates['system']
        assert '{{ items }}' in templates['user']
        assert '{{ language }}' in templates['user']

    def test_load_nonexistent_file(self, loader):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            loader.load_prompt_template('nonexistent_file.yaml')

    def test_load_invalid_yaml(self, loader):
        """Test loading invalid YAML file."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_file.write('invalid: yaml: content: [')
        temp_file.close()
        
        try:
            with pytest.raises(ValueError):
                loader.load_prompt_template(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_render_prompt_basic(self, loader, sample_variables):
        """Test basic prompt rendering."""
        template = 'Hello {{ user_name }}, process {{ item_type }}'
        
        result = loader.render_prompt(template, sample_variables)
        
        assert result == 'Hello Test User, process music files'

    def test_render_prompt_with_list(self, loader, sample_variables):
        """Test rendering template with list variables."""
        template = 'Files to process: {{ items }}'
        
        result = loader.render_prompt(template, sample_variables)
        
        assert 'file1.mp3' in result
        assert 'file2.mp3' in result

    def test_render_prompt_missing_variable(self, loader):
        """Test rendering with missing variables."""
        template = 'Hello {{ missing_variable }}'
        variables = {'other_var': 'value'}
        
        # By default, Jinja2 replaces undefined variables with empty string
        result = loader.render_prompt(template, variables)
        assert result == 'Hello '  # Missing variable becomes empty string

    def test_render_prompt_empty_variables(self, loader):
        """Test rendering with empty variables dict."""
        template = 'Static template with no variables'
        
        result = loader.render_prompt(template, {})
        
        assert result == 'Static template with no variables'

    def test_complex_template_rendering(self, loader):
        """Test rendering complex template with conditionals."""
        template = """
        {% if official_tracks %}
        Use official tracks: {{ official_tracks }}
        {% else %}
        No official tracks available
        {% endif %}
        """
        
        # Test with official tracks
        variables_with_tracks = {'official_tracks': ['Track 1', 'Track 2']}
        result = loader.render_prompt(template, variables_with_tracks)
        assert 'Use official tracks:' in result
        assert 'Track 1' in result
        
        # Test without official tracks
        variables_without_tracks = {'official_tracks': []}
        result = loader.render_prompt(template, variables_without_tracks)
        assert 'No official tracks available' in result

    def test_template_with_loops(self, loader):
        """Test template rendering with loops."""
        template = """
        Files:
        {% for file in files %}
        - {{ file }}
        {% endfor %}
        """
        
        variables = {'files': ['song1.mp3', 'song2.mp3', 'song3.mp3']}
        result = loader.render_prompt(template, variables)
        
        assert '- song1.mp3' in result
        assert '- song2.mp3' in result
        assert '- song3.mp3' in result

    def test_prompt_file_with_missing_sections(self, loader):
        """Test loading prompt file with missing required sections."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        
        # Only include system prompt, missing user prompt
        incomplete_content = {
            'system': 'System prompt only'
        }
        
        yaml.dump(incomplete_content, temp_file, default_flow_style=False)
        temp_file.close()
        
        try:
            with pytest.raises(ValueError):  # Should raise error for missing 'user' key
                loader.load_prompt_template(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_unicode_handling(self, loader):
        """Test handling of Unicode characters in templates."""
        template = 'Artist: {{ artist }}, Album: {{ album }}'
        variables = {
            'artist': '張學友',
            'album': '愛情故事'
        }
        
        result = loader.render_prompt(template, variables)
        
        assert '張學友' in result
        assert '愛情故事' in result

    def test_special_characters_in_template(self, loader):
        """Test handling of special characters in templates."""
        template = 'Process files: {{ files }} with settings: {{ settings }}'
        variables = {
            'files': ['file with spaces.mp3', 'file-with-dashes.mp3', 'file_with_underscores.mp3'],
            'settings': {'language': 'English', 'mode': 'copy'}
        }
        
        result = loader.render_prompt(template, variables)
        
        assert 'file with spaces.mp3' in result
        assert 'file-with-dashes.mp3' in result
        assert 'file_with_underscores.mp3' in result

    def test_nested_yaml_structure(self, loader):
        """Test loading YAML with nested structure."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        
        nested_content = {
            'system': 'System prompt',
            'user': 'User prompt',
            'metadata': {
                'version': '1.0',
                'author': 'Test'
            }
        }
        
        yaml.dump(nested_content, temp_file, default_flow_style=False)
        temp_file.close()
        
        try:
            templates = loader.load_prompt_template(temp_file.name)
            assert 'system' in templates
            assert 'user' in templates
            # Current implementation only returns system and user keys
            assert len(templates) == 2
        finally:
            os.unlink(temp_file.name)

    def test_large_template_file(self, loader):
        """Test loading and rendering large template files."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        
        # Create a large template
        large_system_prompt = """
        You are a comprehensive music file processor. Your task is to analyze and process audio files.
        
        Context:
        - Album: {{ album_name }}
        - Artist: {{ artist_name }}
        - Language: {{ language }}
        - Processing mode: {{ mode }}
        
        Instructions:
        1. Analyze each file carefully
        2. Match to official track names if available
        3. Clean up filenames for consistency
        4. Preserve file extensions
        5. Use proper track numbering
        
        Rules:
        - Always use 2-digit zero-padded numbers
        - Preserve original file extensions
        - Apply language-specific formatting
        - Ensure one-to-one mapping
        """
        
        large_content = {
            'system': large_system_prompt,
            'user': 'Process these {{ file_count }} files: {{ files }}'
        }
        
        yaml.dump(large_content, temp_file, default_flow_style=False)
        temp_file.close()
        
        try:
            templates = loader.load_prompt_template(temp_file.name)
            
            variables = {
                'album_name': 'Test Album',
                'artist_name': 'Test Artist', 
                'language': 'English',
                'mode': 'copy',
                'file_count': 3,
                'files': ['track1.mp3', 'track2.mp3', 'track3.mp3']
            }
            
            system_result = loader.render_prompt(templates['system'], variables)
            user_result = loader.render_prompt(templates['user'], variables)
            
            assert 'Test Album' in system_result
            assert 'Test Artist' in system_result
            assert 'Process these 3 files' in user_result
            assert 'track1.mp3' in user_result
            
        finally:
            os.unlink(temp_file.name)

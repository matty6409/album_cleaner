# Album Cleaner

A CLI tool that intelligently cleans and standardizes music file names in album directories using LLMs (via Perplexity and DeepSeek). The tool accepts albums in various directory formats and outputs them in the standardized `[Artist] Album Name` format, using Spotify API for official album/track information and AI for intelligent file mapping.

## Features

- **Clean Architecture**:
  - Strict separation of domain, application, and infrastructure layers
  - Domain-driven design with rich entities and value objects
  - Dependency inversion through interfaces
  - Clear boundaries between technical and business concerns

- **Service Abstractions**:
  - Plugin architecture with swappable implementations
  - Abstract interfaces for all external services
  - Factory pattern for dependency injection
  - Easy to add new LLM providers or music services

- **Core Features**:
  - Spotify integration with enhanced search capabilities
  - Multiple LLM providers (Perplexity, DeepSeek) for intelligent mapping
  - **LLM-powered Quality Assurance**: Built-in QA reviewer validates results against business rules
  - **Intelligent Retry Logic**: Business logic retries with QA-suggested search alternatives
  - **Agentic Search Enhancement**: QA service suggests alternative search terms when Spotify searches fail
  - English and Traditional Chinese language support with enforced consistency
  - **Automatic Chinese Character Conversion**: Simplified Chinese automatically converted to Traditional Chinese
  - File operations with copy or in-place modes
  - Modern CLI with comprehensive retry and QA configuration options
  - Robust error handling with multiple fallback strategies
  - Streamlined logging with detailed progress tracking

## Architecture

The project follows clean architecture principles with clear separation of concerns:

```
src/
├── application/           # Application Layer (Business Logic)
│   ├── dtos/            # Data Transfer Objects
│   │   └── processing.py # Processing options and results
│   ├── interfaces/       # Abstract service interfaces
│   │   ├── repositories/ # Repository interfaces for file operations
│   │   └── services/    # Service interfaces (LLM, music, prompts)
│   ├── services/        # Application services
│   │   └── cleaner_service.py # Main cleaning orchestration
│   └── use_cases/       # Use case orchestrators
│       └── album_cleaner_use_case.py
├── domain/              # Domain Layer (Core Business Rules)
│   ├── entities/       # Domain Entities
│   │   ├── album.py   # Album entity
│   │   ├── file.py    # File entity
│   │   └── track.py   # Track entity
│   └── values_objects/ # Value Objects (corrected)
│       └── language.py # Language enumeration
├── infrastructure/      # Infrastructure Layer (External Concerns)
│   ├── config/         # Configuration and settings
│   │   └── settings.py # Environment and app settings
│   ├── factories/      # Service factories for DI
│   │   └── service_factory.py # Main factory for dependency injection
│   ├── logging/        # Logging utilities
│   │   └── logger.py   # Centralized logging configuration
│   ├── repositories/   # Repository implementations
│   │   └── file_repository.py # Audio file operations with validation
│   ├── services/       # External service implementations
│   │   ├── llm_services/     # LLM providers (Perplexity, DeepSeek)
│   │   ├── music_services/   # Music services (Spotify)
│   │   ├── prompt_loaders/   # Prompt loading (YAML)
│   │   └── quality_assurance/ # QA service implementations
│   └── utils/          # Utility functions
│       └── file_utils.py # File system utilities
├── presentation/        # Presentation Layer (UI)
│   └── app.py          # Command-line interface
├── prompts/            # YAML prompt templates
└── tests/              # Test suite
    ├── integration/   # Integration tests (end-to-end, fallback tests)
    ├── test_data/    # Sample albums for testing
    └── unit/         # Unit tests

docs/
└── examples/        # Jupyter notebooks with usage examples
```

## Setup

1. Clone the repo
2. Install dependencies:
   ```sh
   poetry install
   ```
3. Set your API keys in a `.env` file:
   ```env
   PERPLEXITY_API_KEY=your-perplexity-key
   OPENROUTER_API_KEY=your-openrouter-key
   SPOTIFY_CLIENT_ID=your-spotify-client-id
   SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
   ```

## Usage

The Album Cleaner accepts music directories in various naming formats and standardizes them to `[Artist] Album Name` format.

### Supported Input Directory Formats:
- `Artist - Album` (most common)
- `Artist《Album》[Format]` (Chinese albums with format tags)
- `Artist_Album` or `Artist.Album` (underscore/dot separated)
- `[Artist] Album` (already in target format)
- `Album Name Only` (treated as album by "Unknown Artist")
- Any directory containing audio files (MP3, FLAC, WAV, etc.)

### Output Format:
All processed albums will be organized as: `[Artist] Album Name/`

```bash
python src/presentation/app.py --base_path /path/to/albums
```

### Core Options:
- `--base_path`: Root directory containing album folders (required)
- `--language`: English or "Traditional Chinese" (default: English)
- `--output_mode`: copy or in_place (default: copy)
- `--llm_provider`: perplexity or deepseek (default: perplexity)
- `--pure_translation`: Use pure translation mode with OpenCC only (bypasses LLM processing, auto-detects Chinese)

### Advanced Options:
- `--max_retries`: Maximum LLM retry attempts (default: 2)
- `--max_business_retries`: Maximum business logic retry attempts (default: 2)
- `--max_search_retries`: Maximum Spotify search retry attempts (default: 3)
- `--enable_qa_review`: Enable LLM quality assurance review (default: True)
- `--disable_qa_review`: Disable LLM quality assurance review
- `--qa_confidence_threshold`: Minimum QA confidence score threshold (default: 0.6)

### Basic Usage:
```bash
# Process albums with default settings
python src/presentation/app.py --base_path src/tests/test_data --llm_provider deepseek

# Process with Traditional Chinese and enhanced retries
python src/presentation/app.py --base_path /path/to/music \
  --language "Traditional Chinese" \
  --max_business_retries 2 \
  --max_search_retries 3 \
  --qa_confidence_threshold 0.6

# Use pure translation mode (OpenCC only, no LLM processing)
# Note: Automatically detects and converts simplified Chinese to traditional
python src/presentation/app.py --base_path /path/to/music \
  --pure_translation
```

This will process albums including English (Adele, BTS) and Chinese (周杰倫) albums. Results will be placed in a `cleaned/` directory with detailed progress logs.

## Processing Flow

1. **Album Discovery**: Scan base directory for any folders containing audio files (MP3, FLAC, WAV, etc.)
2. **Directory Parsing**: Intelligently extract artist and album names from various directory naming conventions
3. **File Analysis**: Extract local audio files and analyze existing track structure
4. **Enhanced Official Data Retrieval**: Multi-retry Spotify search with QA-suggested alternatives
5. **Intelligent LLM Mapping**: Use AI to map local files to official track names with language consistency
6. **Quality Assurance Review**: LLM-powered validation against business rules and language requirements
7. **Business Logic Retries**: Retry entire mapping process if QA approval fails
8. **File Operations**: Execute copy or rename operations to standardized `[Artist] Album Name` format
9. **Automatic Language Conversion**: Apply Traditional Chinese conversion automatically when simplified Chinese is detected

## Expected Input Format

The Album Cleaner accepts directories with various naming conventions:

- **Flexible Album Folders**: 
  - `Artist - Album Name`
  - `Artist《Album Name》[Format]` (Chinese format)
  - `Artist_Album_Name` 
  - `Artist.Album.Name`
  - `[Artist] Album Name` (already clean)
  - Or any directory containing audio files
- **Track Files**: `1. Song Name.ext`, `01 Song Name.ext`, `Song Name.ext`, etc.
- **Supported Audio Formats**: `.flac`, `.wav`, `.mp3`, `.m4a`, `.dsf`, `.aiff`, etc.

The system intelligently parses directory names and uses Spotify + LLM to identify the correct artist and album information.

## Output Format

- **Standardized Directories**: `[Artist] Album Name/` format
- **Standardized Track Names**: `01 Official Track Name.ext`
- **Cleaned Organization**: Results placed in `cleaned/` directory at the same level as your music folder (copy mode)
- **Preserved Extensions**: Original file extensions maintained

### Example Transformation:
```
Before:
├── Jay Chou - Fantasy Plus
│   ├── 01 愛在西元前.mp3
│   └── 02 爸我回來了.mp3
├── Adele_25
│   ├── Hello.mp3
│   └── When We Were Young.mp3

After (in cleaned/Music/ directory):
├── [Jay Chou] Fantasy Plus
│   ├── 01 愛在西元前.mp3
│   └── 02 爸我回來了.mp3
├── [Adele] 25
│   ├── 01 Hello.mp3
│   └── 02 When We Were Young.mp3
```

## Quality Assurance System

The Album Cleaner includes an intelligent QA system that validates results and provides enhancement suggestions:

### **LLM-Powered Validation**
- Reviews all filename mappings against business rules
- Validates language consistency (e.g., ensures Traditional Chinese tracks aren't mapped to English names)
- Checks track numbering, formatting, and completeness
- Provides confidence scores and detailed feedback

### **Intelligent Search Enhancement**
- Suggests alternative search terms when Spotify searches fail
- Analyzes failed searches to recommend better artist/album name variations
- Enables agentic search improvement with multiple retry strategies
- Learns from search patterns to improve success rates

### **Business Logic Retries**
- Automatic retry of entire mapping process when QA approval fails
- Configurable retry thresholds and confidence score requirements
- Detailed feedback about issues and recommendations for improvement
- Prevents low-quality results from being processed

## Processing Modes

### 1. Official Track Mapping with QA (Preferred)
- Enhanced Spotify search with multiple retry strategies
- QA service suggests alternative search terms for failed searches
- Maps local files to official track names with validation
- LLM quality assurance review validates mappings against business rules
- Provides highest accuracy with intelligent fallback options
- Maintains proper track numbering and language consistency

### 2. LLM-Only Cleaning with QA (Fallback)
- Used when Spotify data unavailable after all search attempts
- Pure LLM-based filename cleaning with QA validation
- Still maintains track numbering, structure, and language requirements
- QA service validates results for consistency and formatting
- Works for any language/region with quality enforcement

### 3. Pure Translation Mode (Automatic Chinese Detection)
- Bypasses all LLM processing and Spotify searches
- Uses OpenCC directly to convert filenames from Simplified to Traditional Chinese
- Automatically detects simplified Chinese characters and converts them
- No QA validation or intelligent mapping
- Fastest option for simple S2T Chinese conversion
- Works offline with no API calls

## Testing

Run the tests with:

```bash
poetry run pytest
```

## Dependencies

- **Python 3.12+**
- **spotipy**: Spotify API client
- **langchain**: LLM framework
- **pydantic**: Data validation
- **opencc**: Chinese character conversion
- **natsort**: Natural sorting
- **pyyaml**: YAML processing

## License

MIT License. See [LICENSE](LICENSE) for details.

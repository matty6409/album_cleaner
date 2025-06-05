# Album Cleaner

A CLI and GUI tool to clean and align music file names in album directories using LLMs (via LangChain and Perplexity/DeepSeek). This tool processes music albums in `[Singer Name] Album Name` format, uses Spotify API for official album/track information, and LLM for intelligent mapping.

## Features

- **Clean Architecture**: Separation of application logic from infrastructure concerns
- **Service Abstractions**: Easily swappable implementations for LLM, music services, etc.
- **Spotify Integration**: Official album and track information retrieval
- **LLM Intelligence**: Uses LangChain with Perplexity and DeepSeek models for filename cleaning
- **Language Support**: English and Traditional Chinese (preserves Chinese characters in song names)
- **Processing Modes**: Copy to new directory or in-place renaming
- **Modern CLI**: Clean command-line interface with comprehensive options
- **Robust Error Handling**: Fallback to LLM-only cleaning when Spotify fails
- **Comprehensive Logging**: Detailed logging to `album_cleaner.log`

## Architecture

The project follows clean architecture principles with clear separation of concerns:

```
src/
├── application/           # Application Layer (Business Logic)
│   ├── interfaces/        # Abstract service interfaces
│   └── use_cases/         # Use case orchestrators
├── domain/                # Domain Layer (Business Entities)
│   └── entities/          # Album, Track entities, Language enum
├── infrastructure/        # Infrastructure Layer (External Concerns)
│   ├── llm/               # LLM implementations
│   ├── music/             # Music service implementations
│   ├── prompts/           # Prompt loading implementations
│   ├── file/              # File operation implementations
│   ├── config/            # Configuration
│   └── logging/           # Logging utilities
└── presentation/          # Presentation Layer (UI)
    └── app.py             # Command-line interface
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

## Usage

```bash
python src/presentation/app.py --base_path /path/to/albums
```

Options:
- `--base_path`: Root directory containing album folders
- `--language`: English or "Traditional Chinese" (default: English)
- `--output_mode`: copy or in_place (default: copy)
- `--llm_provider`: perplexity or deepseek (default: perplexity)
- `--max_retries`: Maximum LLM retry attempts (default: 3)

Example using the included test data:
```bash
python src/presentation/app.py --base_path src/tests/test_data
```

This will process the test albums including English (Adele, BTS) and Chinese (周杰倫) albums. Results will be placed in a `cleaned/` directory and logs saved to `album_cleaner.log`.

## Processing Flow

1. **Album Discovery**: Scan base directory for album folders
2. **File Analysis**: Extract local audio files and parse folder name
3. **Official Data Retrieval**: Search Spotify for official album/track information
4. **LLM Mapping**: Use AI to intelligently map local files to official names
5. **Validation**: Ensure all files are mapped correctly
6. **File Operations**: Copy or rename files based on output mode
7. **Chinese Conversion**: Apply Traditional Chinese conversion if needed

## Expected Input Format

- **Album Folders**: `[Artist Name] Album Name`
- **Track Files**: `1. Song Name.ext`, `01 Song Name.ext`, etc.
- **Supported Formats**: `.flac`, `.wav`, `.mp3`, `.m4a`, `.dsf`, etc.

## Output Format

- **Standardized Names**: `01 Official Track Name.ext`
- **Cleaned Directories**: `cleaned/Artist Name - Album Name/` (copy mode)
- **Preserved Extensions**: Original file extensions maintained

## Processing Modes

### 1. Official Track Mapping (Preferred)
- Searches Spotify for album data
- Maps local files to official track names
- Provides highest accuracy and consistency
- Maintains proper track numbering

### 2. LLM-Only Cleaning (Fallback)
- Used when Spotify data unavailable
- Pure LLM-based filename cleaning
- Still maintains track numbering and structure
- Works for any language/region

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

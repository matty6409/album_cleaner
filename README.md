# Album Cleaner

A CLI and GUI tool to clean and align music file names in album directories using LLMs (via LangChain and Perplexity/DeepSeek). All code, tests, prompts, and notebooks are now inside the `src` directory for a fully self-contained project.

## Features
- Uses LangChain with Perplexity and DeepSeek models for filename cleaning
- CLI with argparse for flexible usage
- Modern Streamlit GUI for easy use
- Configurable output: in-place or to a `cleaned/` directory
- Prompt templating with YAML and variable injection
- Clean architecture (domain, application, infrastructure, presentation)
- Progress bars with `tqdm` (CLI) and Streamlit (GUI)
- Logging to `album_cleaner.log`
- Audio metadata editing (with `mutagen`)
- **Automatic language handling**: Chinese/English/phonetic names are mapped and cleaned as needed

## Project Structure
```
src/
  domain/
  application/
  infrastructure/
  presentation/
  prompts/
  tests/
  notebook/
  README.md
  LICENSE
  pyproject.toml
  poetry.lock
  .env
```

## Setup
1. Clone the repo
2. Change directory to `src`:
   ```sh
   cd src
   ```
3. Install dependencies:
   ```sh
   poetry install
   ```
4. Set your API keys in a `.env` file in `src/`:
   ```env
   PERPLEXITY_API_KEY=your-perplexity-key
   DEEPSEEK_API_KEY=your-deepseek-key
   DEEPSEEK_MODEL=deepseek-chat
   ```

## Usage
### CLI
```sh
poetry run python -m presentation.cli --base_path /path/to/albums [--to_new_dir] [--llm_provider perplexity|deepseek]
```
- `--base_path`: Root directory containing album folders
- `--to_new_dir`: If set, cleaned files are saved to `cleaned/` folder; otherwise, files are renamed in place
- `--llm_provider`: Choose which LLM provider to use (default: perplexity)
- **Language is handled automatically based on album/song content**

### GUI
```sh
poetry run streamlit run presentation/gui.py
```
- Use the web interface to select your options and run the cleaner.
- Progress and logs are shown in the app and saved to `album_cleaner.log`.

## Logging & Progress
- All actions and errors are logged to `album_cleaner.log`.
- Progress bars are shown in both CLI and GUI.

## Testing
```sh
poetry run pytest
```

## Notebooks
- Example and exploratory notebooks are in `src/notebook/`.

## License
MIT License. See [LICENSE](LICENSE) for details. 
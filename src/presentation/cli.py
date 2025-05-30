import os
import argparse
from application.use_cases.cleaner_service import CleanerService
from infrastructure.config.settings import Settings

def main() -> None:
    """
    CLI entry point for the Album Cleaner project.
    Parses arguments and runs the cleaning service.
    """
    parser = argparse.ArgumentParser(description="Clean and align music file names in album directories using LLMs.")
    parser.add_argument('--base_path', type=str, required=True, help='Root directory containing album folders')
    parser.add_argument('--to_new_dir', action='store_true', help='If set, save cleaned files to a cleaned/ folder')
    parser.add_argument('--prompt_path', type=str, default='prompts/cleaner_prompt.yaml', help='Path to the prompt YAML file')
    parser.add_argument('--llm_provider', type=str, default='perplexity', choices=['perplexity', 'deepseek'], help='LLM provider to use')
    args = parser.parse_args()

    if not os.path.exists(args.base_path):
        print(f"Path not found: {args.base_path}")
        return

    settings = Settings()
    service = CleanerService(prompt_path=args.prompt_path, settings=settings, to_new_dir=args.to_new_dir, llm_provider=args.llm_provider)
    for album in os.listdir(args.base_path):
        album_path = os.path.join(args.base_path, album)
        if os.path.isdir(album_path):
            print(f"\nProcessing: {album}")
            service.clean_album(album_path)

if __name__ == "__main__":
    main() 
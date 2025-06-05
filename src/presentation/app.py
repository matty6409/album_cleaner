import argparse
import os
import sys
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from domain.entities.models import Language, ProcessingOptions
from infrastructure.factories.service_factory import ServiceFactory, LLMProvider
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

def main():
    """
    Modern CLI entry point for the Album Cleaner project with Language enum support.
    """
    parser = argparse.ArgumentParser(
        description="Clean and align music file names using AI and official music databases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with OpenRouter DeepSeek (default)
  python cli_modern.py --base_path "/path/to/music"
  
  # Use Perplexity instead
  python cli_modern.py --base_path "/path/to/music" --llm_provider perplexity
  
  # Process in Traditional Chinese
  python cli_modern.py --base_path "/path/to/music" --language traditional_chinese
  
  # Rename files in place instead of copying
  python cli_modern.py --base_path "/path/to/music" --output_mode in_place
  
  # Use enhanced search with LLM-optimized search terms
  python cli_modern.py --base_path "/path/to/music" --use_enhanced_search
        """
    )
    
    parser.add_argument(
        '--base_path', 
        type=str, 
        required=False,  # Make optional to allow --list_providers without it
        help='Root directory containing album folders in [Artist] Album format'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        choices=['english', 'traditional_chinese'],
        default='english',
        help='Target language for track names (default: english)'
    )
    
    parser.add_argument(
        '--output_mode',
        type=str,
        choices=['copy', 'in_place'],
        default='copy',
        help='Output mode: copy to cleaned/ folder or rename in place (default: copy)'
    )
    
    parser.add_argument(
        '--llm_provider',
        type=str,
        choices=['perplexity', 'openrouter-deepseek'],
        default='openrouter-deepseek',
        help='LLM provider to use (default: openrouter-deepseek)'
    )
    
    parser.add_argument(
        '--max_retries',
        type=int,
        default=3,
        help='Maximum number of retries for failed operations (default: 3)'
    )
    
    parser.add_argument(
        '--list_providers',
        action='store_true',
        help='List available LLM providers and their configuration status'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--use_enhanced_search',
        action='store_true',
        help='Use LLM to generate optimized search terms for finding albums (default: true)'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # Load settings
    try:
        settings = Settings()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create factory
    factory = ServiceFactory(settings)
    
    # Handle list providers command
    if args.list_providers:
        print("Available LLM Providers:")
        print("=" * 40)
        for provider_name in factory.list_available_providers():
            provider = LLMProvider(provider_name)  # Convert string value to enum
            status = "✅ Configured" if factory.validate_provider_config(provider) else "❌ Not configured"
            print(f"  {provider_name:<20} {status}")
        print("\nConfiguration requirements:")
        print("  perplexity         : PERPLEXITY_API_KEY")
        print("  openrouter-deepseek: OPENROUTER_API_KEY")
        return
    
    # Require base_path for actual processing
    if not args.base_path:
        parser.error("--base_path is required unless using --list_providers")
    
    # Validate base path
    if not os.path.exists(args.base_path):
        logger.error(f"Path not found: {args.base_path}")
        sys.exit(1)
    
    if not os.path.isdir(args.base_path):
        logger.error(f"Path is not a directory: {args.base_path}")
        sys.exit(1)
    
    # Convert language string to enum
    language_map = {
        'english': Language.ENGLISH,
        'traditional_chinese': Language.TRADITIONAL_CHINESE
    }
    language = language_map[args.language]
    
    # Validate provider configuration
    llm_provider_map = {
        'perplexity': LLMProvider.PERPLEXITY,
        'openrouter-deepseek': LLMProvider.OPENROUTER_DEEPSEEK
    }
    llm_provider = llm_provider_map[args.llm_provider]
    
    if not factory.validate_provider_config(llm_provider):
        logger.error(f"LLM provider '{args.llm_provider}' is not properly configured")
        logger.error("Use --list_providers to see configuration requirements")
        sys.exit(1)
        
    # Enable enhanced search if requested
    if args.use_enhanced_search:
        logger.info("Enabling enhanced search with LLM-optimized search terms")
        factory.enable_enhanced_search(llm_provider)
    
    # Create processing options
    options = ProcessingOptions(
        base_path=args.base_path,
        language=language,
        output_mode=args.output_mode,
        max_retries=args.max_retries
    )
    
    # Create use case
    try:
        use_case = factory.create_album_cleaner_use_case(llm_provider)
        logger.info(f"Initialized album cleaner with {args.llm_provider} provider")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        sys.exit(1)
    
    # Process albums
    logger.info(f"Starting album processing in {args.base_path}")
    logger.info(f"Language: {language.value}, Output mode: {args.output_mode}")
    
    try:
        results = use_case.process_albums(options)
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total_files = sum(r.files_processed for r in results if r.success)
        
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Albums processed: {successful}/{len(results)}")
        print(f"Files processed: {total_files}")
        print(f"Language: {language.value}")
        print(f"Output mode: {args.output_mode}")
        print(f"LLM provider: {args.llm_provider}")
        print(f"Enhanced search: {'Enabled' if args.use_enhanced_search or factory.use_enhanced_search else 'Disabled'}")
        
        # Show failed albums
        failed = [r for r in results if not r.success]
        if failed:
            print(f"\nFailed albums ({len(failed)}):")
            for result in failed:
                album_name = os.path.basename(result.album_path)
                print(f"  ❌ {album_name}: {result.error_message}")
        
        print("=" * 60)
        
        if successful == len(results):
            logger.info("🎉 All albums processed successfully!")
            sys.exit(0)
        else:
            logger.warning(f"⚠️  {len(failed)} albums failed to process")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

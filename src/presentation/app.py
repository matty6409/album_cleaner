import os
import sys
import argparse
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from domain.values_objects.language import Language  # Updated import
from application.dtos.processing import ProcessingOptions
from infrastructure.factories.service_factory import ServiceFactory, LLMProvider
from infrastructure.config.settings import Settings
from infrastructure.logging.logger import logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Album Cleaner - Clean and align music file names using LLMs")
    
    parser.add_argument(
        "--base_path", 
        required=True,
        help="Root directory containing album folders"
    )
    
    parser.add_argument(
        "--language", 
        choices=["English", "Traditional Chinese"],
        default="English",
        help="Language for track names (default: English)"
    )
    
    parser.add_argument(
        "--output_mode", 
        choices=["copy", "in_place"],
        default="copy",
        help="Output mode: copy to cleaned/ folder at same level as parent directory or rename in place (default: copy)"
    )
    
    parser.add_argument(
        "--llm_provider", 
        choices=["perplexity", "deepseek"],
        default="perplexity",
        help="LLM provider to use (default: perplexity)"
    )
    
    parser.add_argument(
        "--max_retries", 
        type=int,
        default=2,
        help="Maximum LLM retry attempts (default: 2)"
    )
    
    parser.add_argument(
        "--max_business_retries", 
        type=int,
        default=2,
        help="Maximum business logic retry attempts (default: 2)"
    )
    
    parser.add_argument(
        "--max_search_retries", 
        type=int,
        default=3,
        help="Maximum Spotify search retry attempts (default: 3)"
    )
    
    parser.add_argument(
        "--enable_qa_review", 
        action="store_true",
        default=True,
        help="Enable LLM quality assurance review (default: True)"
    )
    
    parser.add_argument(
        "--disable_qa_review", 
        action="store_true",
        help="Disable LLM quality assurance review"
    )
    
    parser.add_argument(
        "--qa_confidence_threshold", 
        type=float,
        default=0.6,
        help="Minimum QA confidence score threshold (default: 0.6)"
    )
    
    parser.add_argument(
        "--pure_translation", 
        action="store_true",
        help="Use pure translation mode with OpenCC only, bypassing LLM processing"
    )
    
    return parser.parse_args()

def main():
    """
    Modern CLI entry point for the Album Cleaner project with Language enum support.
    """
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Convert arguments to appropriate types
    base_path = args.base_path
    language = Language.TRADITIONAL_CHINESE if args.language == "Traditional Chinese" else Language.ENGLISH
    output_mode = args.output_mode
    llm_provider = LLMProvider.PERPLEXITY if args.llm_provider == "perplexity" else LLMProvider.OPENROUTER_DEEPSEEK
    max_retries = args.max_retries
    max_business_retries = args.max_business_retries
    max_search_retries = args.max_search_retries
    enable_qa_review = args.enable_qa_review and not args.disable_qa_review
    qa_confidence_threshold = args.qa_confidence_threshold
    
    # Configure logging based on verbosity
    log_level = "DEBUG" if hasattr(args, 'verbose') and args.verbose else "INFO"
    
    # Load settings
    try:
        settings = Settings()
        logger.info("Album Cleaner initialized - starting processing")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create factory
    factory = ServiceFactory(settings)
    
    # Require base_path for actual processing
    if not os.path.exists(base_path):
        logger.error(f"Path not found: {base_path}")
        sys.exit(1)
    
    if not os.path.isdir(base_path):
        logger.error(f"Path is not a directory: {base_path}")
        sys.exit(1)
    
    # Validate provider configuration
    if not factory.validate_provider_config(llm_provider):
        logger.error(f"LLM provider '{llm_provider}' is not properly configured")
        logger.error("Use --list_providers to see configuration requirements")
        sys.exit(1)
        
    # Create processing options
    options = ProcessingOptions(
        base_path=base_path,
        language=language,
        output_mode=output_mode,
        max_retries=max_retries,
        max_business_retries=max_business_retries,
        max_search_retries=max_search_retries,
        enable_qa_review=enable_qa_review,
        qa_confidence_threshold=qa_confidence_threshold,
        pure_translation=args.pure_translation
    )
    
    # Create use case
    try:
        use_case = factory.create_album_cleaner_use_case(llm_provider)
        logger.info(f"Initialized album cleaner with {llm_provider} provider")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        sys.exit(1)
    
    # Process albums
    logger.info(f"Starting album processing in {base_path}")
    logger.info(f"Language: {language.value}, Output mode: {output_mode}")
    if args.pure_translation:
        logger.info("Running in PURE TRANSLATION MODE - using OpenCC only, bypassing LLM processing")
    else:
        logger.info(f"QA Review: {'Enabled' if enable_qa_review else 'Disabled'}, Threshold: {qa_confidence_threshold}")
        logger.info(f"Retries - LLM: {max_retries}, Business: {max_business_retries}, Search: {max_search_retries}")
    
    try:
        results = use_case.process_albums(options)
        
        # Summary
        successful = sum(1 for r in results if r.success)
        total_files = sum(r.files_processed for r in results if r.success)
        total_retries = sum(r.retry_count for r in results)
        total_search_attempts = sum(r.search_attempts for r in results)
        qa_approved_count = sum(1 for r in results if r.qa_approved is True)
        
        print("\n" + "=" * 60)
        print("PROCESSING SUMMARY")
        print("=" * 60)
        print(f"Albums processed: {successful}/{len(results)}")
        print(f"Files processed: {total_files}")
        print(f"Language: {language.value}")
        print(f"Output mode: {output_mode}")
        
        if args.pure_translation:
            print(f"Mode: Pure translation (OpenCC only)")
        else:
            print(f"LLM provider: {llm_provider}")
            print(f"Total retries used: {total_retries}")
            print(f"Total search attempts: {total_search_attempts}")
            if enable_qa_review:
                print(f"QA approved albums: {qa_approved_count}/{len(results)}")
        
        # Show failed albums
        failed = [r for r in results if not r.success]
        if failed:
            print(f"\nFailed albums ({len(failed)}):")
            for result in failed:
                album_name = os.path.basename(result.album_path)
                retry_info = f" (retries: {result.retry_count}, searches: {result.search_attempts})"
                print(f"  ❌ {album_name}: {result.error_message}{retry_info}")
        
        # Show QA information for successful albums
        if enable_qa_review and successful > 0:
            print(f"\nQuality Assurance Summary:")
            for result in results:
                if result.success and result.qa_confidence is not None:
                    album_name = os.path.basename(result.album_path)
                    status = "✅" if result.qa_approved else "⚠️"
                    print(f"  {status} {album_name}: Confidence {result.qa_confidence:.2f}")
        
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

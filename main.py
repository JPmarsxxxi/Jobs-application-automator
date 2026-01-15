#!/usr/bin/env python3
"""
Autonomous Job Application Bot
Main Entry Point

Usage:
    python main.py --region uk --test                    # Test mode, UK jobs
    python main.py --region us --platform linkedin       # US jobs, LinkedIn only
    python main.py --schedule                            # Start scheduler (automated runs)
    python main.py --region uk --limit 5                 # UK jobs, max 5 applications
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from modules.core.quality_control_log import get_qc_log
from modules.core.logger import setup_logger, get_logger


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Autonomous Job Application Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --region uk --test                    # Test mode, UK jobs
  %(prog)s --region us --platform linkedin       # US jobs, LinkedIn only
  %(prog)s --schedule                            # Start automated scheduler
  %(prog)s --region uk --limit 5 --dry-run       # Dry run, max 5 jobs
        """,
    )

    # Mode Selection
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--schedule", action="store_true", help="Start scheduler for automated runs"
    )
    mode_group.add_argument(
        "--test", action="store_true", help="Run in test mode (manual approval required)"
    )

    # Region and Platform
    parser.add_argument(
        "--region",
        type=str,
        choices=["uk", "us", "nigeria", "all"],
        default="uk",
        help="Target region for job search",
    )
    parser.add_argument(
        "--platform",
        type=str,
        nargs="+",
        choices=["linkedin", "indeed", "reed", "glassdoor", "efinancial", "jobberman"],
        help="Specific platforms to target (default: all configured for region)",
    )

    # Limits
    parser.add_argument(
        "--limit", type=int, help="Maximum number of applications to submit"
    )

    # Modes
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - generate materials but don't submit applications",
    )
    parser.add_argument(
        "--manual-approval",
        action="store_true",
        default=True,
        help="Require manual approval before each application (default: True)",
    )
    parser.add_argument(
        "--no-manual-approval",
        action="store_true",
        help="Disable manual approval (automatic operation)",
    )

    # Features
    parser.add_argument(
        "--no-networking", action="store_true", help="Disable networking/email features"
    )
    parser.add_argument(
        "--no-screenshots", action="store_true", help="Disable screenshot capture"
    )

    # Debugging
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )

    # Status
    parser.add_argument(
        "--status", action="store_true", help="Check scheduler status"
    )
    parser.add_argument("--stop", action="store_true", help="Stop the scheduler")

    return parser.parse_args()


def validate_environment():
    """Validate that required environment variables and files exist"""
    logger = get_logger()

    # Check user_info.py exists
    user_info_path = project_root / "config" / "user_info.py"
    if not user_info_path.exists():
        logger.error(
            "config/user_info.py not found. Please copy config/user_info.example.py "
            "to config/user_info.py and fill in your details."
        )
        return False

    # Check Ollama connection (will be implemented in Phase 1)
    # For now, just a placeholder
    logger.info("Validating environment...")

    # Check workspace directories exist
    workspace_dir = project_root / "workspace"
    required_dirs = [
        workspace_dir / "portfolio",
        workspace_dir / "generated_materials" / "cvs",
        workspace_dir / "generated_materials" / "cover_letters",
        workspace_dir / "screenshots",
        workspace_dir / "logs",
    ]

    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    logger.info("✓ Environment validation passed")
    return True


def run_single_session(args):
    """Run a single job application session"""
    logger = get_logger()

    logger.info(f"Starting job application session")
    logger.info(f"Region: {args.region.upper()}")
    logger.info(f"Test Mode: {args.test}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Manual Approval: {not args.no_manual_approval}")

    # Initialize quality control log
    qc_log = get_qc_log()
    platforms = args.platform if args.platform else ["linkedin", "indeed"]  # Default for now
    qc_log.start_run(
        mode="TEST" if args.test else "PRODUCTION",
        region=args.region,
        platforms=platforms,
    )

    try:
        # Load user info
        try:
            from config.user_info import USER_INFO, validate_user_info
            validate_user_info()
        except ImportError:
            logger.error("config/user_info.py not found or invalid")
            logger.error("Please copy config/user_info.example.py to config/user_info.py")
            logger.error("and fill in your details")
            return
        except ValueError as e:
            logger.error(f"User info validation failed: {e}")
            return

        # Build configuration
        config = {
            "region": args.region,
            "platforms": args.platform or ["linkedin"],
            "max_jobs": args.limit or 5,
            "user_info": USER_INFO,
            "dry_run": args.dry_run,
            "manual_approval": not args.no_manual_approval,
            "headless": os.getenv("HEADLESS_MODE", "false").lower() == "true",
            "location": USER_INFO.get("location", "United Kingdom"),
            "search_terms": [
                "Data Scientist graduate",
                "Machine Learning Engineer entry level",
            ],
        }

        # Run the job hunt
        from modules.core.orchestrator import run_job_hunt
        result = run_job_hunt(config)

        if result.get("success"):
            logger.info("\n✅ Job hunt session completed successfully!")
        else:
            logger.error(f"\n❌ Job hunt failed: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        logger.warning("\n\nBot interrupted by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=args.debug)


def run_scheduler(args):
    """Start the automated scheduler"""
    logger = get_logger()
    logger.info("Starting automated scheduler...")

    # TODO: Implement in Phase 4
    logger.warning("Scheduler not yet implemented (Phase 4)")
    logger.info("For now, use: python main.py --region <region> --test")


def main():
    """Main entry point"""
    args = parse_arguments()

    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logger(level=log_level, log_to_console=True, log_to_file=True)
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("Autonomous Job Application Bot")
    logger.info("=" * 60)

    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)

    # Handle different modes
    if args.status:
        logger.info("Checking scheduler status...")
        # TODO: Implement
        logger.warning("Status check not yet implemented")

    elif args.stop:
        logger.info("Stopping scheduler...")
        # TODO: Implement
        logger.warning("Scheduler stop not yet implemented")

    elif args.schedule:
        run_scheduler(args)

    else:
        # Single session run
        run_single_session(args)


if __name__ == "__main__":
    main()

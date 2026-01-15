#!/usr/bin/env python3
"""
Test LinkedIn Scraper

Run this to test job scraping functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.scraping.linkedin_scraper import create_linkedin_scraper
from modules.core.logger import setup_logger, get_logger


def main():
    """Test LinkedIn scraper"""
    setup_logger(level="INFO", log_to_console=True, log_to_file=False)
    logger = get_logger()

    logger.info("=" * 60)
    logger.info("LinkedIn Scraper Test")
    logger.info("=" * 60)

    # Create scraper
    scraper = create_linkedin_scraper(
        search_terms=["Data Scientist graduate London"],
        location="United Kingdom",
        max_results=2,  # Just 2 jobs for testing
        headless=False,  # Show browser for debugging
    )

    # Scrape jobs
    logger.info("\nStarting scrape...")
    jobs = scraper.scrape_jobs()

    # Display results
    logger.info("\n" + "=" * 60)
    logger.info(f"Scraped {len(jobs)} jobs")
    logger.info("=" * 60)

    for i, job in enumerate(jobs, 1):
        logger.info(f"\nJob {i}:")
        logger.info(f"  Company: {job.company}")
        logger.info(f"  Title: {job.title}")
        logger.info(f"  Location: {job.location}")
        logger.info(f"  URL: {job.job_url}")
        logger.info(f"  Easy Apply: {job.easy_apply}")
        logger.info(f"  Keywords: {', '.join(job.keywords[:10])}")
        logger.info(f"  Description length: {len(job.description)} chars")

    logger.info("\n✅ Test complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Base Job Scraper

Abstract base class for platform-specific scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
import time

from modules.scraping.job_models import JobPosting, ScraperConfig
from modules.core.logger import get_logger
from modules.utils.helpers import rate_limit_delay


class BaseScraper(ABC):
    """Abstract base class for job board scrapers"""

    def __init__(self, config: ScraperConfig):
        """
        Initialize scraper

        Args:
            config: Scraper configuration
        """
        self.config = config
        self.logger = get_logger()
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.jobs: List[JobPosting] = []

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform name identifier"""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL for the platform"""
        pass

    def start_browser(self):
        """Start Playwright browser"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=self.config.headless
            )
            self.page = self.browser.new_page()

            # Set timeout
            self.page.set_default_timeout(self.config.timeout)

            self.logger.info(f"✓ Browser started for {self.platform_name}")

        except Exception as e:
            self.logger.error(f"Error starting browser: {e}")
            raise

    def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            self.logger.info(f"✓ Browser closed")

        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")

    def wait_for_rate_limit(self):
        """Wait according to platform rate limits"""
        delay = rate_limit_delay(self.platform_name)
        self.logger.debug(f"Rate limit delay: {delay}s")
        time.sleep(delay)

    @abstractmethod
    def build_search_url(self, search_term: str) -> str:
        """
        Build search URL with filters

        Args:
            search_term: Job search term

        Returns:
            Full search URL
        """
        pass

    @abstractmethod
    def extract_job_cards(self) -> List[dict]:
        """
        Extract job cards from search results page

        Returns:
            List of job card elements/data
        """
        pass

    @abstractmethod
    def extract_job_details(self, job_card_data: dict) -> Optional[JobPosting]:
        """
        Extract detailed job information from a job card

        Args:
            job_card_data: Job card element/data

        Returns:
            JobPosting object or None if extraction failed
        """
        pass

    def scrape_jobs(self) -> List[JobPosting]:
        """
        Main scraping method

        Returns:
            List of scraped job postings
        """
        self.logger.info(f"Starting job scrape on {self.platform_name}")
        self.logger.info(f"Search terms: {', '.join(self.config.search_terms)}")
        self.logger.info(f"Max results: {self.config.max_results}")

        try:
            self.start_browser()

            for search_term in self.config.search_terms:
                if len(self.jobs) >= self.config.max_results:
                    self.logger.info(f"Reached max results limit: {self.config.max_results}")
                    break

                self.logger.info(f"Searching for: {search_term}")

                # Navigate to search page
                search_url = self.build_search_url(search_term)
                self.logger.debug(f"URL: {search_url}")

                self.page.goto(search_url)
                self.wait_for_rate_limit()

                # Extract job cards
                job_cards = self.extract_job_cards()
                self.logger.info(f"Found {len(job_cards)} job cards")

                # Extract details from each card
                for i, job_card in enumerate(job_cards):
                    if len(self.jobs) >= self.config.max_results:
                        break

                    self.logger.info(f"Extracting job {i + 1}/{len(job_cards)}")

                    try:
                        job = self.extract_job_details(job_card)
                        if job:
                            self.jobs.append(job)
                            self.logger.info(
                                f"✓ Scraped: {job.company} - {job.title}"
                            )
                        else:
                            self.logger.warning("Failed to extract job details")

                    except Exception as e:
                        self.logger.error(f"Error extracting job: {e}")
                        continue

                    # Rate limiting between jobs
                    if i < len(job_cards) - 1:
                        self.wait_for_rate_limit()

            self.logger.info(f"✓ Scraping complete: {len(self.jobs)} jobs found")
            return self.jobs

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}", exc_info=True)
            return self.jobs

        finally:
            self.close_browser()

    def login_if_required(self):
        """
        Login to platform if required

        Override this method in platform-specific scrapers if login is needed.
        """
        pass

    def handle_popup(self):
        """
        Handle popups/modals that might appear

        Override this method in platform-specific scrapers if needed.
        """
        pass

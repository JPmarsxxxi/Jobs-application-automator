"""
LinkedIn Job Scraper

Scrapes job postings from LinkedIn Jobs with vision-based fallback for company extraction
"""

from typing import List, Optional
import re
import time
from urllib.parse import urlencode
from pathlib import Path
import base64

from modules.scraping.base_scraper import BaseScraper
from modules.scraping.job_models import JobPosting, ScraperConfig
from modules.utils.helpers import generate_job_id, extract_keywords, clean_text
from modules.generation.ollama_client import get_ollama_client


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn Jobs with vision-based fallback"""

    def __init__(self, config: ScraperConfig):
        """Initialize LinkedIn scraper with vision model support"""
        super().__init__(config)
        self.ollama = get_ollama_client()
        self.screenshot_dir = Path("workspace/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    @property
    def platform_name(self) -> str:
        return "linkedin"

    @property
    def base_url(self) -> str:
        return "https://www.linkedin.com/jobs/search"

    def build_search_url(self, search_term: str) -> str:
        """Build LinkedIn search URL with filters"""

        params = {
            "keywords": search_term,
            "location": self.config.location or "United Kingdom",
            "f_TPR": "r604800",  # Past week (7 days in seconds)
            "sortBy": "DD",  # Sort by date (most recent)
        }

        # Add experience level filter if specified
        if self.config.experience_level:
            # LinkedIn experience level codes: 1=Internship, 2=Entry, 3=Associate, 4=Mid-Senior, 5=Director, 6=Executive
            experience_map = {
                "Internship": "1",
                "Entry level": "2",
                "Associate": "3",
                "Mid-Senior level": "4",
                "Director": "5",
                "Executive": "6",
            }
            codes = [experience_map.get(level, "2") for level in self.config.experience_level]
            params["f_E"] = ",".join(codes)

        # Add job type filter if specified
        if self.config.job_type:
            # LinkedIn job type codes: F=Full-time, P=Part-time, C=Contract, T=Temporary, I=Internship
            job_type_map = {
                "Full-time": "F",
                "Part-time": "P",
                "Contract": "C",
                "Temporary": "T",
                "Internship": "I",
            }
            codes = [job_type_map.get(jt, "F") for jt in self.config.job_type]
            params["f_JT"] = ",".join(codes)

        # Add work model filter if specified
        if self.config.work_model:
            # LinkedIn work model codes: 1=On-site, 2=Remote, 3=Hybrid
            work_model_map = {
                "On-site": "1",
                "Remote": "2",
                "Hybrid": "3",
            }
            codes = [work_model_map.get(wm, "1") for wm in self.config.work_model]
            params["f_WT"] = ",".join(codes)

        # Easy apply filter
        if self.config.easy_apply_only:
            params["f_AL"] = "true"

        url = f"{self.base_url}/?{urlencode(params)}"
        return url

    def extract_job_cards(self) -> List[dict]:
        """Extract job cards from LinkedIn search results"""

        try:
            # Wait for job listings to load
            self.page.wait_for_selector("ul.jobs-search__results-list", timeout=10000)

            # Get all job cards
            job_cards = self.page.query_selector_all("li.jobs-search-results__list-item")

            self.logger.debug(f"Found {len(job_cards)} job card elements")

            # Extract basic info from each card
            jobs_data = []
            for card in job_cards:
                try:
                    # Extract job URL and ID
                    link = card.query_selector("a.base-card__full-link")
                    if not link:
                        continue

                    job_url = link.get_attribute("href")
                    if not job_url:
                        continue

                    # Extract job ID from URL
                    job_id_match = re.search(r"/jobs/view/(\d+)", job_url)
                    if not job_id_match:
                        continue

                    job_id = job_id_match.group(1)

                    # Extract basic details
                    title = card.query_selector("h3.base-search-card__title")
                    company = card.query_selector("h4.base-search-card__subtitle")
                    location = card.query_selector("span.job-search-card__location")

                    # Extract company name with vision fallback
                    company_name = "Unknown"
                    if company:
                        company_name = company.inner_text().strip()

                    # If text extraction failed, use vision model
                    if not company_name or company_name == "Unknown" or len(company_name) < 2:
                        self.logger.info(f"Text extraction failed for company, trying vision...")
                        company_name = self._extract_company_with_vision(card, job_id)

                    jobs_data.append({
                        "job_id": job_id,
                        "job_url": job_url,
                        "title": title.inner_text().strip() if title else "Unknown",
                        "company": company_name,
                        "location": location.inner_text().strip() if location else "Unknown",
                        "card_element": card,
                    })

                except Exception as e:
                    self.logger.warning(f"Error extracting job card: {e}")
                    continue

            return jobs_data

        except Exception as e:
            self.logger.error(f"Error extracting job cards: {e}")
            return []

    def _extract_company_with_vision(self, card_element, job_id: str) -> str:
        """
        Extract company name from job card using vision model.

        Args:
            card_element: Playwright element handle for job card
            job_id: Job ID for screenshot naming

        Returns:
            Company name or "Unknown" if extraction fails
        """
        try:
            # Take screenshot of the job card
            screenshot_path = self.screenshot_dir / f"job_card_{job_id}.png"
            card_element.screenshot(path=str(screenshot_path))

            self.logger.debug(f"Screenshot saved: {screenshot_path}")

            # Read screenshot as base64
            with open(screenshot_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Prompt for vision model
            prompt = """Look at this LinkedIn job posting card. Extract ONLY the company name.

Rules:
- Return ONLY the company name, nothing else
- No extra text, no explanations
- If you can't find it, return "Unknown"

Company name:"""

            # Use vision model to extract company name
            company_name = self.ollama.analyze_image(
                image_data=image_data,
                prompt=prompt,
                max_tokens=50
            )

            if company_name:
                # Clean up the response
                company_name = company_name.strip()
                # Remove common prefixes from LLM response
                company_name = company_name.replace("Company name:", "").strip()
                company_name = company_name.replace("The company is", "").strip()
                company_name = company_name.replace("is", "").strip()

                # Validate it's not too long (company names shouldn't be > 100 chars)
                if len(company_name) > 100:
                    self.logger.warning(f"Vision extracted name too long: {company_name[:100]}...")
                    return "Unknown"

                # Validate it's not empty after cleaning
                if len(company_name) < 2:
                    return "Unknown"

                self.logger.info(f"✓ Vision extracted company: {company_name}")
                return company_name

            return "Unknown"

        except Exception as e:
            self.logger.warning(f"Vision extraction failed: {e}")
            return "Unknown"

    def extract_job_details(self, job_card_data: dict) -> Optional[JobPosting]:
        """Extract detailed job information"""

        try:
            # Navigate to job details page
            job_url = job_card_data["job_url"]
            self.logger.debug(f"Opening job: {job_url}")

            self.page.goto(job_url)
            time.sleep(2)  # Wait for page to load

            # Check if job page loaded successfully
            if "Page not found" in self.page.title():
                self.logger.warning("Job page not found")
                return None

            # Extract description
            description = ""
            try:
                # Try main description container
                desc_element = self.page.query_selector("div.show-more-less-html__markup")
                if desc_element:
                    description = clean_text(desc_element.inner_text())
                else:
                    # Try alternative selector
                    desc_element = self.page.query_selector("div.description__text")
                    if desc_element:
                        description = clean_text(desc_element.inner_text())

            except Exception as e:
                self.logger.warning(f"Could not extract description: {e}")

            # Extract additional details
            criteria = {}
            try:
                criteria_items = self.page.query_selector_all("li.description__job-criteria-item")
                for item in criteria_items:
                    header = item.query_selector("h3")
                    value = item.query_selector("span")
                    if header and value:
                        criteria[header.inner_text().strip()] = value.inner_text().strip()
            except Exception as e:
                self.logger.debug(f"Could not extract criteria: {e}")

            # Check for Easy Apply
            easy_apply = False
            try:
                easy_apply_button = self.page.query_selector("button.jobs-apply-button")
                if easy_apply_button:
                    easy_apply = True
            except:
                pass

            # Extract keywords from description
            keywords = extract_keywords(description) if description else []

            # Create JobPosting object
            job = JobPosting(
                job_id=job_card_data["job_id"],
                platform=self.platform_name,
                company=job_card_data["company"],
                title=job_card_data["title"],
                location=job_card_data["location"],
                job_url=job_url,
                description=description,
                job_type=criteria.get("Employment type"),
                work_model=criteria.get("Remote/On-site"),
                keywords=keywords[:20],  # Top 20 keywords
                easy_apply=easy_apply,
                external_apply=not easy_apply,
            )

            return job

        except Exception as e:
            self.logger.error(f"Error extracting job details: {e}")
            return None


def create_linkedin_scraper(
    search_terms: List[str],
    location: str = "United Kingdom",
    max_results: int = 5,
    headless: bool = False,
) -> LinkedInScraper:
    """
    Create a configured LinkedIn scraper

    Args:
        search_terms: List of search terms
        location: Location to search in
        max_results: Maximum number of results
        headless: Run browser in headless mode

    Returns:
        Configured LinkedInScraper instance
    """
    config = ScraperConfig(
        search_terms=search_terms,
        location=location,
        date_posted="past_week",
        sort_by="most_recent",
        max_results=max_results,
        headless=headless,
        experience_level=["Entry level", "Associate"],  # For recent graduates
        job_type=["Full-time"],
    )

    return LinkedInScraper(config)

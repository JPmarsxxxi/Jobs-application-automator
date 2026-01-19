"""
LinkedIn Job Scraper

Scrapes job postings from LinkedIn Jobs with vision-based fallback for company extraction
"""

from typing import List, Optional
import re
import time
import os
import random
from urllib.parse import urlencode
from pathlib import Path

from modules.scraping.base_scraper import BaseScraper
from modules.scraping.job_models import JobPosting, ScraperConfig
from modules.utils.helpers import generate_job_id, extract_keywords, clean_text, human_delay, human_scroll_delay
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

    def _human_like_scroll(self, scroll_amount: int = None, pause: bool = True):
        """
        Human-like scrolling behavior
        """
        if scroll_amount is None:
            scroll_amount = random.randint(300, 800)
        
        # Scroll down
        self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        
        if pause:
            human_scroll_delay()
    
    def _human_like_typing(self, element, text: str):
        """
        Type text with human-like delays between keystrokes
        """
        element.click()  # Focus on element first
        human_delay(0.3, 0.8)  # Pause before typing
        
        for char in text:
            element.type(char, delay=random.uniform(50, 150))
        
        human_delay(0.2, 0.5)  # Pause after typing

    def _dismiss_linkedin_banners(self):
        """
        Dismiss any LinkedIn banners/modals that might interfere with interactions
        """
        banner_selectors = [
            'button[aria-label="Dismiss"]',
            'button[data-control-name*="dismiss"]',
            'button.modal__dismiss',
            'button[data-test-modal-close-btn]',
            'button.artdeco-modal__dismiss',
            'button[aria-label="Close"]',
            'button.msg-overlay-bubble-header__controls button',
            'button[data-tracking-control-name="cookie_consent"]',
            'button[action-type="DENY"]',
        ]

        for selector in banner_selectors:
            try:
                banner = self.page.query_selector(selector)
                if banner and banner.is_visible():
                    banner.click()
                    self.logger.debug(f"Dismissed banner with selector: {selector}")
                    human_delay(0.5, 1.0)
            except:
                continue

    def _parse_linkedin_date(self, date_text: str):
        """
        Parse LinkedIn relative dates like "2 days ago", "1 week ago" to datetime

        Args:
            date_text: LinkedIn date string

        Returns:
            datetime object or None if parsing fails
        """
        from datetime import datetime, timedelta

        try:
            date_text = date_text.lower().strip()
            now = datetime.now()

            # Today/just now
            if 'just now' in date_text or 'today' in date_text:
                return now

            # Parse "X days ago"
            if 'day' in date_text:
                match = re.search(r'(\d+)\s*day', date_text)
                if match:
                    days = int(match.group(1))
                    return now - timedelta(days=days)

            # Parse "X weeks ago"
            if 'week' in date_text:
                match = re.search(r'(\d+)\s*week', date_text)
                if match:
                    weeks = int(match.group(1))
                    return now - timedelta(weeks=weeks)

            # Parse "X months ago"
            if 'month' in date_text:
                match = re.search(r'(\d+)\s*month', date_text)
                if match:
                    months = int(match.group(1))
                    return now - timedelta(days=months*30)  # Approximate

            # Parse "X hours ago"
            if 'hour' in date_text:
                match = re.search(r'(\d+)\s*hour', date_text)
                if match:
                    hours = int(match.group(1))
                    return now - timedelta(hours=hours)

            # Default to now if can't parse
            return now

        except Exception as e:
            self.logger.debug(f"Date parsing failed for '{date_text}': {e}")
            return datetime.now()

    def login_if_required(self):
        """
        Login to LinkedIn if credentials are provided with human-like behavior
        """
        email = os.getenv("LINKEDIN_EMAIL")
        password = os.getenv("LINKEDIN_PASSWORD")

        if not email or not password:
            self.logger.warning("LinkedIn credentials not found in environment variables")
            self.logger.warning("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
            self.logger.warning("Attempting to scrape without login (may not work for job listings)")
            return False

        try:
            self.logger.info("Logging into LinkedIn...")
            
            # Navigate to login page
            self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
            human_delay(2.0, 4.0)  # Random wait after page load

            # Wait for login form and fill credentials with human-like behavior
            try:
                # Find email field
                email_selector = "input#username"
                self.page.wait_for_selector(email_selector, timeout=10000)
                email_input = self.page.locator(email_selector)
                email_input.click()
                human_delay(0.5, 1.0)
                self._human_like_typing(email_input, email)
                self.logger.debug("✓ Email entered")

                # Find password field
                password_selector = "input#password"
                self.page.wait_for_selector(password_selector, timeout=5000)
                password_input = self.page.locator(password_selector)
                password_input.click()
                human_delay(0.5, 1.0)
                self._human_like_typing(password_input, password)
                self.logger.debug("✓ Password entered")

                # Pause before clicking submit (human hesitation)
                human_delay(1.0, 2.5)

                # Click sign in button
                signin_selector = "button[type='submit']"
                self.page.wait_for_selector(signin_selector, timeout=5000)
                submit_button = self.page.locator(signin_selector)
                submit_button.click()
                self.logger.debug("✓ Sign in button clicked")

                # Wait for navigation (either to home page or error)
                human_delay(3.0, 6.0)

                # Check if login was successful
                current_url = self.page.url
                if "challenge" in current_url.lower() or "checkpoint" in current_url.lower():
                    self.logger.warning("⚠️  LinkedIn requires additional verification")
                    self.logger.warning("   Please complete the challenge manually in the browser")
                    self.logger.warning("   Waiting 30 seconds for manual completion...")
                    time.sleep(30)
                    
                elif "login" in current_url.lower():
                    self.logger.error("❌ Login failed - please check credentials")
                    return False
                else:
                    self.logger.info("✓ Login successful")
                    return True

                # Check again after waiting
                current_url = self.page.url
                if "login" not in current_url.lower():
                    self.logger.info("✓ Login successful (after manual verification)")
                    return True
                else:
                    self.logger.error("❌ Login still failed after manual verification")
                    return False

            except Exception as e:
                self.logger.error(f"Error during login form filling: {e}")
                self.logger.warning("You may need to login manually in the browser")
                time.sleep(10)  # Give user time to login manually
                return False

        except Exception as e:
            self.logger.error(f"Error during LinkedIn login: {e}")
            self.logger.warning("Falling back to manual login...")
            time.sleep(10)  # Give user time to login manually if browser is open
            return False

    def extract_job_cards(self) -> List[dict]:
        """Extract job cards from LinkedIn search results with human-like behavior"""

        try:
            # Wait for page to fully load
            human_delay(2.0, 4.0)

            # Scroll multiple times to trigger lazy loading (LinkedIn loads jobs as you scroll)
            # Multiple scroll operations with random intervals
            for i in range(4):
                scroll_amount = random.randint(300, 800)
                self._human_like_scroll(scroll_amount)
                human_delay(1.0, 2.0)  # Wait for content to load
            
            # Try multiple selectors for job listings container (LinkedIn changes frequently)
            container_selectors = [
                "ul.jobs-search__results-list",
                "ul.scaffold-layout__list-container",
                "ul[data-testid='job-search-results-list']",
                "div.jobs-search-results-list",
                "div.scaffold-layout__list-container",
                "ol.jobs-search-results__list",
                "ul.artdeco-list",
            ]
            
            container_found = False
            for selector in container_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    container_found = True
                    self.logger.debug(f"Found job container with selector: {selector}")
                    break
                except:
                    continue
            
            if not container_found:
                self.logger.warning("Job listings container not found - trying to continue anyway")
                # Take a screenshot for debugging
                screenshot_path = "workspace/screenshots/linkedin_debug.png"
                self.page.screenshot(path=screenshot_path, full_page=True)
                self.logger.info(f"Debug screenshot saved to: {screenshot_path}")

            # Try multiple selectors for job cards (LinkedIn uses various class names)
            job_card_selectors = [
                "li.jobs-search-results__list-item",
                "li[data-testid='job-search-result']",
                "li.occludable-update",
                "li.reusable-search__result-container",
                "div.job-search-card",
                "div.job-card-container",
                "li[data-entity-urn*='jobPosting']",
                "div.base-card",
            ]
            
            job_cards = []
            for selector in job_card_selectors:
                try:
                    cards = self.page.query_selector_all(selector)
                    if len(cards) > 0:
                        job_cards = cards
                        self.logger.debug(f"Found {len(job_cards)} job cards with selector: {selector}")
                        break
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue

            self.logger.debug(f"Found {len(job_cards)} job card elements")

            # Extract basic info from each card
            jobs_data = []
            link_selectors = [
                "a.base-card__full-link",
                "a[data-control-id*='jobPosting']",
                "a[href*='/jobs/view/']",
                "a.job-card-container__link",
                "a.job-card-list__title",
            ]
            
            # More comprehensive selectors (LinkedIn changes structure frequently)
            title_selectors = [
                "h3.base-search-card__title",
                "h3.job-card-list__title",
                "h2.job-search-card__title",
                "span.job-search-card__title",
                "a[data-tracking-control-name='job-card-title']",
                ".job-card-search__title",
                "h3.job-card-container__title",
                "h4.base-search-card__title",
                "span.job-card-container__link",
            ]
            
            company_selectors = [
                "h4.base-search-card__subtitle",
                "h4.job-card-container__company-name",
                "span.job-card-container__primary-description",
                "a[data-tracking-control-name='job-card-company']",
                ".job-card-search__company",
                "h4.job-card-container__metadata",
                "span.job-card-container__metadata",
                "a.base-search-card__subtitle-link",
            ]
            
            location_selectors = [
                "span.job-search-card__location",
                "span.job-card-container__metadata-item",
                "li.job-card-container__metadata-item",
                ".job-card-search__location",
                "span.job-card-container__bullet",
                "div.job-card-container__metadata-wrapper span",
            ]
            
            for card in job_cards:
                try:
                    # Extract job URL and ID - try multiple selectors
                    link = None
                    for link_selector in link_selectors:
                        try:
                            link = card.query_selector(link_selector)
                            if link:
                                break
                        except:
                            continue
                    
                    # Try getting link from card directly if selectors failed
                    if not link:
                        # Try finding any link in the card
                        all_links = card.query_selector_all("a")
                        for l in all_links:
                            href = l.get_attribute("href")
                            if href and "/jobs/view/" in href:
                                link = l
                                break
                    
                    if not link:
                        self.logger.debug("Could not find job link in card")
                        continue

                    job_url = link.get_attribute("href")
                    if not job_url:
                        continue
                    
                    # Make sure URL is absolute
                    if job_url.startswith("/"):
                        job_url = f"https://www.linkedin.com{job_url}"

                    # Extract job ID from URL
                    job_id_match = re.search(r"/jobs/view/(\d+)", job_url)
                    if not job_id_match:
                        self.logger.debug(f"Could not extract job ID from URL: {job_url}")
                        continue

                    job_id = job_id_match.group(1)

                    # Extract basic details - try multiple selectors with inner_text fallback
                    title_text = None
                    for title_selector in title_selectors:
                        try:
                            title = card.query_selector(title_selector)
                            if title:
                                title_text = title.inner_text().strip()
                                if title_text:
                                    break
                        except:
                            continue
                    
                    # Fallback: get all text and try to extract title
                    if not title_text:
                        card_text = card.inner_text()
                        # Try to extract title from card text (usually first line)
                        lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                        if lines:
                            title_text = lines[0][:100]  # Limit length
                    
                    company_text = None
                    for company_selector in company_selectors:
                        try:
                            company = card.query_selector(company_selector)
                            if company:
                                company_text = company.inner_text().strip()
                                if company_text:
                                    break
                        except:
                            continue
                    
                    # Fallback: try to extract company from link text or card text
                    if not company_text:
                        try:
                            # Sometimes company is in the subtitle link
                            company_link = card.query_selector("a.base-search-card__subtitle-link")
                            if company_link:
                                company_text = company_link.inner_text().strip()
                        except:
                            pass
                    
                    location_text = None
                    for location_selector in location_selectors:
                        try:
                            location = card.query_selector(location_selector)
                            if location:
                                location_text = location.inner_text().strip()
                                if location_text and location_text not in ["·", "•", "|"]:
                                    break
                        except:
                            continue

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
                        "title": title_text if title_text else "Unknown",
                        "company": company_name,
                        "location": location_text if location_text else "Unknown",
                        "card_element": card,
                    })
                    
                    self.logger.debug(f"Extracted: {title_text or 'Unknown'} at {company_text or 'Unknown'}")

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

            # Prompt for vision model
            prompt = """Look at this LinkedIn job posting card. Extract ONLY the company name.

Rules:
- Return ONLY the company name, nothing else
- No extra text, no explanations
- If you can't find it, return "Unknown"

Company name:"""

            # Use vision model to extract company name
            company_name = self.ollama.analyze_image(
                image_path=str(screenshot_path),
                prompt=prompt
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

    def _extract_from_text_fallback(self, card_text: str) -> dict:
        """
        Extract company and location from raw card text as last resort

        Args:
            card_text: Raw text from job card

        Returns:
            dict with 'company' and 'location' keys
        """
        result = {'company': 'Unknown', 'location': 'Unknown'}

        try:
            lines = [l.strip() for l in card_text.split('\n') if l.strip()]

            # Usually first line is title, second is company, third is location
            if len(lines) >= 2:
                result['company'] = lines[1][:100]  # Limit length

            # Look for location keywords
            location_keywords = ['london', 'uk', 'united kingdom', 'remote', 'hybrid', 'cambridge', 'manchester', 'edinburgh']
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in location_keywords):
                    result['location'] = line[:100]
                    break

            self.logger.debug(f"Text fallback extracted: {result}")

        except Exception as e:
            self.logger.debug(f"Text fallback extraction failed: {e}")

        return result

    def _extract_description_with_retry(self, max_retries: int = 5) -> str:
        """
        Extract job description from detail panel with validation and retries

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            Job description text or fallback message
        """
        description_selectors = [
            'div.description__text',
            'div.show-more-less-html__markup',
            'div[class*="description__text"]',
            'div.jobs-description__content',
            'div.jobs-box__html-content',
            'section[class*="description"]',
            'div[data-test-id*="description"]',
            'div.jobs-description',
            'article.jobs-description__container',
        ]

        for attempt in range(max_retries):
            try:
                # Try each selector
                for selector in description_selectors:
                    try:
                        desc_element = self.page.query_selector(selector)
                        if desc_element:
                            # Wait for element to be visible
                            if desc_element.is_visible():
                                description = clean_text(desc_element.inner_text())

                                # Validate: description should be at least 50 characters
                                if len(description.strip()) > 50:
                                    self.logger.debug(f"Description extracted with selector: {selector}")
                                    return description
                    except Exception as e:
                        self.logger.debug(f"Selector {selector} failed: {e}")
                        continue

                # If no valid description found, wait and retry
                if attempt < max_retries - 1:
                    self.logger.debug(f"Description validation failed, retry {attempt + 1}/{max_retries}")
                    human_delay(0.3, 0.5)

            except Exception as e:
                self.logger.debug(f"Description extraction attempt {attempt + 1} failed: {e}")

        # Final fallback: try to get ANY text from the detail panel
        try:
            detail_panel = self.page.query_selector('div[class*="job"]')
            if detail_panel:
                text = clean_text(detail_panel.inner_text())
                if len(text) > 50:
                    self.logger.warning("Using fallback text extraction for description")
                    return text
        except:
            pass

        self.logger.warning("Could not extract job description")
        return "Description not available"

    def extract_job_details(self, job_card_data: dict) -> Optional[JobPosting]:
        """
        Extract detailed job information by expanding the job panel
        (Panel-based approach - no page navigation)
        """

        try:
            job_url = job_card_data["job_url"]
            card_element = job_card_data["card_element"]

            self.logger.debug(f"Expanding job panel for: {job_card_data['title']}")

            # Dismiss any banners that might interfere with clicking
            self._dismiss_linkedin_banners()

            # Click the job card to expand the detail panel
            try:
                # Try clicking the card element
                card_element.click(timeout=3000)
                self.logger.debug("Clicked job card")
            except Exception as e:
                # Fallback: try JavaScript click
                self.logger.debug(f"Regular click failed, trying JavaScript click: {e}")
                try:
                    card_element.evaluate("el => el.click()")
                except:
                    self.logger.warning("Could not click job card")
                    return None

            # Wait for detail panel to load
            human_delay(1.5, 3.0)

            # Extract description from expanded panel with validation and retries
            description = self._extract_description_with_retry()

            # Extract additional details from panel
            criteria = {}
            try:
                # Try multiple selectors for job criteria
                criteria_selectors = [
                    "li.description__job-criteria-item",
                    "li.jobs-description__list-item",
                    "li[class*='job-criteria']",
                ]

                for selector in criteria_selectors:
                    criteria_items = self.page.query_selector_all(selector)
                    if criteria_items:
                        for item in criteria_items:
                            try:
                                header = item.query_selector("h3")
                                value = item.query_selector("span")
                                if header and value:
                                    criteria[header.inner_text().strip()] = value.inner_text().strip()
                            except:
                                continue
                        break
            except Exception as e:
                self.logger.debug(f"Could not extract criteria: {e}")

            # Check for Easy Apply
            easy_apply = False
            try:
                easy_apply_selectors = [
                    "button.jobs-apply-button",
                    "button[aria-label*='Easy Apply']",
                    "button[data-control-name*='easy_apply']",
                ]
                for selector in easy_apply_selectors:
                    easy_apply_button = self.page.query_selector(selector)
                    if easy_apply_button and easy_apply_button.is_visible():
                        easy_apply = True
                        break
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

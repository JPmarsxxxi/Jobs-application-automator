"""
Adaptive Scraper
Self-healing scraper that learns HTML selectors automatically
"""

import logging
from typing import Optional, List
from playwright.sync_api import Page, ElementHandle

from modules.automation.smart_element_discovery import get_smart_discovery
from modules.automation.selector_cache import get_selector_cache


class AdaptiveScraper:
    """
    Self-healing scraper base class

    How it works:
    1. Try cached selector (fast - ~1ms)
    2. If fails, use SmartElementDiscovery (slow - ~200ms-2s)
    3. Cache newly discovered selector
    4. Next time: use cache again (fast)

    This makes the scraper:
    - Fast after first run
    - Self-healing when websites change
    - Platform-agnostic (works on LinkedIn, Indeed, etc.)
    """

    def __init__(self, page: Page, platform_name: str):
        self.page = page
        self.platform_name = platform_name
        self.logger = logging.getLogger(__name__)

        self.discovery = get_smart_discovery(page)
        self.cache = get_selector_cache()

    def extract_field(
        self,
        element: ElementHandle,
        field_type: str,
        expected_text: Optional[str] = None,
        multiple_selectors: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Extract field value from element (with auto-discovery)

        Args:
            element: Playwright ElementHandle to search within
            field_type: Type of field ("company", "title", "location", etc.)
            expected_text: Optional hint text
            multiple_selectors: Optional list of fallback selectors to try first

        Returns:
            Extracted text or None
        """
        # Step 1: Try cached selector
        cached_selector = self.cache.get(self.platform_name, field_type)
        if cached_selector:
            result = self._try_selector(element, cached_selector)
            if result:
                self.cache.record_success(self.platform_name, field_type)
                self.logger.debug(f"✓ {field_type} extracted via cache: {result[:50]}")
                return result
            else:
                self.cache.record_failure(self.platform_name, field_type)
                self.logger.debug(f"Cached selector failed for {field_type}")

        # Step 2: Try provided fallback selectors (if any)
        if multiple_selectors:
            for selector in multiple_selectors:
                result = self._try_selector(element, selector)
                if result:
                    # Cache this working selector
                    self.cache.set(self.platform_name, field_type, selector)
                    self.logger.debug(f"✓ {field_type} extracted via fallback: {result[:50]}")
                    return result

        # Step 3: Use smart discovery to find selector
        self.logger.info(f"Auto-discovering selector for {field_type}...")
        discovered_selector = self.discovery.discover_selector(element, field_type, expected_text)

        if discovered_selector:
            result = self._try_selector(element, discovered_selector)
            if result:
                # Cache for future use
                self.cache.set(self.platform_name, field_type, discovered_selector)
                self.logger.info(f"✓ {field_type} extracted via discovery: {result[:50]}")
                return result

        # Step 4: All methods failed
        self.logger.warning(f"Could not extract {field_type}")
        return None

    def _try_selector(self, element: ElementHandle, selector: str) -> Optional[str]:
        """Try to extract text using a selector"""
        try:
            target = element.query_selector(selector)
            if target:
                text = target.inner_text().strip()
                if text and len(text) > 0:
                    return text
        except Exception as e:
            self.logger.debug(f"Selector {selector} failed: {e}")

        return None

    def find_button(
        self,
        button_type: str,
        fallback_selectors: Optional[List[str]] = None
    ) -> Optional[ElementHandle]:
        """
        Find button element (e.g., Next, Submit, Easy Apply)

        Args:
            button_type: Button type ("next", "submit", "easy_apply", etc.)
            fallback_selectors: Optional fallback selectors

        Returns:
            ElementHandle or None
        """
        field_key = f"button_{button_type}"

        # Try cached selector
        cached_selector = self.cache.get(self.platform_name, field_key)
        if cached_selector:
            try:
                button = self.page.locator(cached_selector).first
                if button.is_visible():
                    self.cache.record_success(self.platform_name, field_key)
                    return button
                else:
                    self.cache.record_failure(self.platform_name, field_key)
            except:
                self.cache.record_failure(self.platform_name, field_key)

        # Try fallback selectors
        if fallback_selectors:
            for selector in fallback_selectors:
                try:
                    button = self.page.locator(selector).first
                    if button.is_visible():
                        self.cache.set(self.platform_name, field_key, selector)
                        return button
                except:
                    continue

        # Could add smart discovery for buttons here too
        self.logger.warning(f"Could not find {button_type} button")
        return None

    def extract_multiple_fields(
        self,
        element: ElementHandle,
        field_types: List[str]
    ) -> dict:
        """
        Extract multiple fields from an element

        Args:
            element: ElementHandle to extract from
            field_types: List of field types to extract

        Returns:
            Dict mapping field types to extracted values
        """
        results = {}
        for field_type in field_types:
            results[field_type] = self.extract_field(element, field_type)

        return results

    def print_cache_stats(self):
        """Print cache statistics"""
        stats = self.cache.get_stats()

        self.logger.info("\n" + "="*60)
        self.logger.info("SELECTOR CACHE STATISTICS")
        self.logger.info("="*60)
        self.logger.info(f"Total cached selectors: {stats['total_selectors']}")
        self.logger.info(f"\nBy platform:")
        for platform, count in stats['by_platform'].items():
            self.logger.info(f"  {platform}: {count} selectors")

        if stats['most_reliable']:
            self.logger.info(f"\nMost reliable selectors:")
            for item in stats['most_reliable']:
                self.logger.info(
                    f"  {item['key']}: {item['reliability']*100:.1f}% "
                    f"({item['uses']} uses)"
                )
        self.logger.info("="*60 + "\n")


def get_adaptive_scraper(page: Page, platform_name: str) -> AdaptiveScraper:
    """Get AdaptiveScraper instance"""
    return AdaptiveScraper(page, platform_name)

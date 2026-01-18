"""
Company Researcher
Uses DuckDuckGo to research companies for cover letter personalization
"""

import logging
import requests
from typing import Dict, Optional
from bs4 import BeautifulSoup


class CompanyResearcher:
    """Researches companies using DuckDuckGo search"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.search_base_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def research_company(self, company_name: str, job_title: str = "") -> Dict[str, str]:
        """
        Research a company using web search.

        Args:
            company_name: Name of the company
            job_title: Job title (helps refine search)

        Returns:
            Dict with company info: mission, products, recent_news, tech_stack
        """
        if company_name == "Unknown" or not company_name:
            self.logger.warning("Company name is Unknown, skipping research")
            return self._empty_research()

        self.logger.info(f"Researching company: {company_name}")

        research = {
            'mission': self._search_mission(company_name),
            'products': self._search_products(company_name),
            'recent_news': self._search_news(company_name),
            'tech_stack': self._search_tech_stack(company_name, job_title)
        }

        # Log what we found
        found_count = sum(1 for v in research.values() if v != 'N/A')
        self.logger.info(f"✓ Found {found_count}/4 research items for {company_name}")

        return research

    def _search_mission(self, company_name: str) -> str:
        """Search for company mission/about"""
        try:
            query = f"{company_name} company mission about"
            result = self._duckduckgo_search(query, max_results=1)
            if result:
                return result[:300]  # Limit length
            return "N/A"
        except Exception as e:
            self.logger.debug(f"Error searching mission: {e}")
            return "N/A"

    def _search_products(self, company_name: str) -> str:
        """Search for company products/services"""
        try:
            query = f"{company_name} products services what they do"
            result = self._duckduckgo_search(query, max_results=1)
            if result:
                return result[:300]
            return "N/A"
        except Exception as e:
            self.logger.debug(f"Error searching products: {e}")
            return "N/A"

    def _search_news(self, company_name: str) -> str:
        """Search for recent company news"""
        try:
            query = f"{company_name} news 2026 recent"
            result = self._duckduckgo_search(query, max_results=1)
            if result:
                return result[:300]
            return "N/A"
        except Exception as e:
            self.logger.debug(f"Error searching news: {e}")
            return "N/A"

    def _search_tech_stack(self, company_name: str, job_title: str) -> str:
        """Search for company tech stack"""
        try:
            query = f"{company_name} tech stack technologies {job_title}"
            result = self._duckduckgo_search(query, max_results=1)
            if result:
                return result[:300]
            return "N/A"
        except Exception as e:
            self.logger.debug(f"Error searching tech stack: {e}")
            return "N/A"

    def _duckduckgo_search(self, query: str, max_results: int = 1) -> Optional[str]:
        """
        Perform DuckDuckGo search and return snippet.

        Args:
            query: Search query
            max_results: Number of results to extract

        Returns:
            Snippet text or None
        """
        try:
            # DuckDuckGo HTML search
            params = {'q': query}
            response = requests.get(
                self.search_base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            if response.status_code != 200:
                self.logger.debug(f"Search failed with status {response.status_code}")
                return None

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find result snippets
            results = soup.find_all('a', class_='result__snippet', limit=max_results)

            if not results:
                # Try alternative selector
                results = soup.find_all('div', class_='result__snippet', limit=max_results)

            if results:
                # Extract text from first result
                snippet = results[0].get_text(strip=True)
                return snippet if snippet else None

            return None

        except Exception as e:
            self.logger.debug(f"Error in DuckDuckGo search: {e}")
            return None

    def _empty_research(self) -> Dict[str, str]:
        """Return empty research dict"""
        return {
            'mission': 'N/A',
            'products': 'N/A',
            'recent_news': 'N/A',
            'tech_stack': 'N/A'
        }


def get_company_researcher() -> CompanyResearcher:
    """Factory function to create CompanyResearcher instance"""
    return CompanyResearcher()

"""
Selector Cache
Persistent storage for learned HTML selectors
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class SelectorCache:
    """
    Caches discovered selectors to avoid re-learning

    Cache structure:
    {
        "linkedin_company": {
            "selector": "h4.job-card__company-name",
            "last_updated": "2024-01-19T10:30:00",
            "success_count": 15,
            "fail_count": 0
        },
        "linkedin_title": {
            "selector": "a.job-card__title",
            "last_updated": "2024-01-19T10:30:00",
            "success_count": 15,
            "fail_count": 0
        }
    }
    """

    def __init__(self, cache_file: str = "workspace/.selector_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                self.logger.info(f"✓ Loaded {len(cache)} cached selectors from {self.cache_file}")
                return cache
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            self.logger.debug(f"Cache saved to {self.cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")

    def get(self, platform: str, field_type: str) -> Optional[str]:
        """
        Get cached selector

        Args:
            platform: Platform name (linkedin, indeed, etc.)
            field_type: Field type (company, title, location, etc.)

        Returns:
            Selector string or None if not cached
        """
        key = f"{platform}_{field_type}"
        entry = self.cache.get(key)

        if entry:
            selector = entry.get("selector")
            self.logger.debug(f"Cache hit: {key} → {selector}")
            return selector

        self.logger.debug(f"Cache miss: {key}")
        return None

    def set(self, platform: str, field_type: str, selector: str):
        """
        Cache a selector

        Args:
            platform: Platform name
            field_type: Field type
            selector: CSS selector to cache
        """
        key = f"{platform}_{field_type}"

        # Initialize or update entry
        if key in self.cache:
            # Selector changed - reset counters
            if self.cache[key]["selector"] != selector:
                self.logger.info(f"Selector updated: {key} → {selector}")
                self.cache[key] = {
                    "selector": selector,
                    "last_updated": datetime.now().isoformat(),
                    "success_count": 0,
                    "fail_count": 0
                }
        else:
            self.logger.info(f"New selector cached: {key} → {selector}")
            self.cache[key] = {
                "selector": selector,
                "last_updated": datetime.now().isoformat(),
                "success_count": 0,
                "fail_count": 0
            }

        self._save_cache()

    def record_success(self, platform: str, field_type: str):
        """Record successful use of cached selector"""
        key = f"{platform}_{field_type}"
        if key in self.cache:
            self.cache[key]["success_count"] += 1
            if self.cache[key]["success_count"] % 10 == 0:  # Save every 10 successes
                self._save_cache()

    def record_failure(self, platform: str, field_type: str):
        """Record failed use of cached selector"""
        key = f"{platform}_{field_type}"
        if key in self.cache:
            self.cache[key]["fail_count"] += 1
            self.logger.warning(f"Selector failure: {key} (fail count: {self.cache[key]['fail_count']})")

            # If selector fails too often, remove it
            if self.cache[key]["fail_count"] >= 3:
                self.logger.warning(f"Removing unreliable selector: {key}")
                del self.cache[key]
                self._save_cache()

    def clear_platform(self, platform: str):
        """Clear all cached selectors for a platform"""
        keys_to_remove = [k for k in self.cache.keys() if k.startswith(f"{platform}_")]
        for key in keys_to_remove:
            del self.cache[key]

        self.logger.info(f"Cleared {len(keys_to_remove)} selectors for {platform}")
        self._save_cache()

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "total_selectors": len(self.cache),
            "by_platform": self._group_by_platform(),
            "most_reliable": self._get_most_reliable(),
        }

    def _group_by_platform(self) -> Dict[str, int]:
        """Group cached selectors by platform"""
        platforms = {}
        for key in self.cache.keys():
            platform = key.split("_")[0]
            platforms[platform] = platforms.get(platform, 0) + 1
        return platforms

    def _get_most_reliable(self) -> List[Dict]:
        """Get most reliable selectors (highest success rate)"""
        reliable = []
        for key, entry in self.cache.items():
            success = entry.get("success_count", 0)
            fail = entry.get("fail_count", 0)
            total = success + fail

            if total > 0:
                reliability = success / total
                reliable.append({
                    "key": key,
                    "selector": entry["selector"],
                    "reliability": reliability,
                    "uses": total
                })

        return sorted(reliable, key=lambda x: (x["reliability"], x["uses"]), reverse=True)[:5]


# Global cache instance
_cache_instance = None

def get_selector_cache() -> SelectorCache:
    """Get global SelectorCache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SelectorCache()
    return _cache_instance

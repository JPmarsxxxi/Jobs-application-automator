"""
Helper utilities for the job application bot
"""

import re
import time
import random
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import hashlib


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def generate_job_id(company: str, title: str, platform: str) -> str:
    """
    Generate a unique job ID from company, title, and platform

    Args:
        company: Company name
        title: Job title
        platform: Platform name

    Returns:
        Unique job ID hash
    """
    combined = f"{company}_{title}_{platform}_{datetime.now().strftime('%Y%m%d')}"
    return hashlib.md5(combined.encode()).hexdigest()[:12]


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract potential keywords from text (basic version)

    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length

    Returns:
        List of keywords
    """
    # Remove special characters and split into words
    words = re.findall(r"\b[a-zA-Z+#]{" + str(min_length) + r",}\b", text)
    # Convert to lowercase and remove duplicates
    keywords = list(set(word.lower() for word in words))
    return keywords


def rate_limit_delay(platform: str) -> float:
    """
    Get rate limit delay for a platform

    Args:
        platform: Platform name

    Returns:
        Delay in seconds
    """
    delays = {
        "linkedin": 3.0,  # 3 seconds between requests
        "indeed": 2.0,  # 2 seconds
        "reed": 2.5,  # 2.5 seconds
        "glassdoor": 3.0,
        "efinancial": 2.5,
        "jobberman": 2.0,
    }
    return delays.get(platform.lower(), 2.0)


def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """
    Add human-like delay with random variation

    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    import random
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def wait_with_message(seconds: float, message: str = "Waiting"):
    """
    Wait with a progress message

    Args:
        seconds: Seconds to wait
        message: Message to display
    """
    print(f"{message} ({seconds}s)...", end="", flush=True)
    time.sleep(seconds)
    print(" Done")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a timestamp

    Args:
        dt: Datetime object (default: now)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists

    Args:
        path: Directory path

    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def parse_salary(salary_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse salary text into structured format

    Args:
        salary_text: Salary text (e.g., "£30,000 - £40,000 per year")

    Returns:
        Dictionary with salary details or None
    """
    # Remove commas
    salary_text = salary_text.replace(",", "")

    # Try to match salary range
    match = re.search(r"[£$€]?(\d+).*?[£$€]?(\d+)", salary_text)
    if match:
        return {
            "min": int(match.group(1)),
            "max": int(match.group(2)),
            "currency": "GBP" if "£" in salary_text else "USD" if "$" in salary_text else "EUR",
            "period": "year" if "year" in salary_text.lower() else "month",
        }

    # Try to match single salary
    match = re.search(r"[£$€]?(\d+)", salary_text)
    if match:
        return {
            "amount": int(match.group(1)),
            "currency": "GBP" if "£" in salary_text else "USD" if "$" in salary_text else "EUR",
            "period": "year" if "year" in salary_text.lower() else "month",
        }

    return None


def is_valid_email(email: str) -> bool:
    """
    Check if an email address is valid

    Args:
        email: Email address

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def estimate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Estimate reading time in minutes

    Args:
        text: Text to estimate
        words_per_minute: Average reading speed

    Returns:
        Estimated reading time in minutes
    """
    words = len(text.split())
    minutes = max(1, words // words_per_minute)
    return minutes


def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """
    Random delay to simulate human behavior
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


def human_scroll_delay():
    """Delay after scrolling (human-like)"""
    return human_delay(0.5, 1.5)


def human_typing_delay():
    """Delay between keystrokes (human-like)"""
    return random.uniform(0.05, 0.15)
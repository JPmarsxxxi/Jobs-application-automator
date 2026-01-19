"""
Job Data Models

Defines data structures for job information
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class JobPosting:
    """Represents a job posting"""

    # Core identifiers
    job_id: str
    platform: str
    company: str
    title: str

    # Location and URL
    location: str
    job_url: str

    # Details
    description: str
    requirements: Optional[str] = None
    salary: Optional[str] = None

    # Metadata
    posted_date: Optional[str] = None
    application_deadline: Optional[str] = None
    job_type: Optional[str] = None  # Full-time, Part-time, Contract, etc.
    work_model: Optional[str] = None  # Remote, Hybrid, On-site

    # Extracted information
    keywords: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)

    # Visa/sponsorship info
    visa_sponsorship: Optional[bool] = None

    # Application details
    easy_apply: bool = False
    external_apply: bool = False
    application_url: Optional[str] = None

    # Timestamps
    scraped_at: datetime = field(default_factory=datetime.now)

    # Additional data
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "platform": self.platform,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "job_url": self.job_url,
            "description": self.description,
            "requirements": self.requirements,
            "salary": self.salary,
            "posted_date": self.posted_date,
            "application_deadline": self.application_deadline,
            "job_type": self.job_type,
            "work_model": self.work_model,
            "keywords": self.keywords,
            "required_skills": self.required_skills,
            "visa_sponsorship": self.visa_sponsorship,
            "easy_apply": self.easy_apply,
            "external_apply": self.external_apply,
            "application_url": self.application_url,
            "scraped_at": self.scraped_at.isoformat(),
            "raw_data": self.raw_data,
        }

    @property
    def is_recent(self) -> bool:
        """Check if job was posted in last 7 days"""
        if not self.posted_date:
            return True  # Assume recent if no date

        # TODO: Implement date parsing and comparison
        return True

    @property
    def short_description(self) -> str:
        """Get truncated description"""
        if len(self.description) <= 500:
            return self.description
        return self.description[:500] + "..."


@dataclass
class ScraperConfig:
    """Configuration for job scraper"""

    # Search parameters
    search_terms: List[str]
    location: Optional[str] = None
    radius: Optional[int] = None  # miles/km

    # Filters
    date_posted: str = "past_week"  # past_24_hours, past_week, past_month
    experience_level: Optional[List[str]] = None  # Entry, Associate, Mid-Senior, Director, Executive
    job_type: Optional[List[str]] = None  # Full-time, Part-time, Contract, Temporary, Internship
    work_model: Optional[List[str]] = None  # Remote, Hybrid, On-site

    # Special filters
    easy_apply_only: bool = False
    visa_sponsorship: bool = False

    # Sorting
    sort_by: str = "most_recent"  # most_recent, most_relevant

    # Browser control
    keep_browser_open: bool = False  # For Phase 2 application submission

    # Limits
    max_results: int = 20

    # Browser settings
    headless: bool = False
    timeout: int = 30000  # milliseconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "search_terms": self.search_terms,
            "location": self.location,
            "radius": self.radius,
            "date_posted": self.date_posted,
            "experience_level": self.experience_level,
            "job_type": self.job_type,
            "work_model": self.work_model,
            "easy_apply_only": self.easy_apply_only,
            "visa_sponsorship": self.visa_sponsorship,
            "sort_by": self.sort_by,
            "max_results": self.max_results,
            "headless": self.headless,
            "timeout": self.timeout,
        }

"""
Orchestrator

Coordinates the entire job application workflow:
1. Scrape jobs
2. Match projects
3. Generate materials
4. Log everything to quality control log
"""

from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

from modules.scraping.linkedin_scraper import create_linkedin_scraper
from modules.scraping.job_models import JobPosting
from modules.generation.material_generator import create_material_generator
from modules.core.quality_control_log import get_qc_log
from modules.core.logger import get_logger
from modules.generation.ollama_client import get_ollama_client


class JobHuntOrchestrator:
    """Orchestrates the job hunting workflow"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator

        Args:
            config: Configuration dictionary containing:
                - region: Target region (uk, us, etc.)
                - platforms: List of platforms to scrape
                - max_jobs: Maximum number of jobs to process
                - user_info: User information dictionary
                - dry_run: Whether to run in dry-run mode
                - manual_approval: Whether to require manual approval
        """
        self.config = config
        self.logger = get_logger()
        self.qc_log = get_qc_log()
        self.ollama = get_ollama_client()

        # Statistics
        self.stats = {
            "jobs_scraped": 0,
            "cvs_generated": 0,
            "cover_letters_generated": 0,
            "errors": 0,
        }

    def validate_setup(self) -> bool:
        """
        Validate that everything is set up correctly

        Returns:
            True if setup is valid, False otherwise
        """
        self.logger.info("Validating setup...")

        # Check Ollama connection
        if not self.ollama.check_connection():
            self.logger.error("❌ Ollama connection failed")
            return False

        # Check models
        if not self.ollama.check_models():
            self.logger.error("❌ Required models not available")
            return False

        # Check user info
        if not self.config.get("user_info"):
            self.logger.error("❌ User information not provided")
            return False

        # Check portfolio
        portfolio_path = Path("workspace/portfolio/projects_index.json")
        if not portfolio_path.exists():
            self.logger.warning(
                "⚠️  Portfolio not found. Please create workspace/portfolio/projects_index.json"
            )
            self.logger.warning("   You can copy from projects_index.example.json")
            return False

        self.logger.info("✓ Setup validation passed")
        return True

    def scrape_jobs(self, platform: str, search_terms: List[str], max_jobs: int) -> List[JobPosting]:
        """
        Scrape jobs from a platform

        Args:
            platform: Platform name
            search_terms: List of search terms
            max_jobs: Maximum number of jobs to scrape

        Returns:
            List of scraped jobs
        """
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Scraping {platform.upper()}")
        self.logger.info(f"{'='*60}")

        jobs = []

        if platform == "linkedin":
            scraper = create_linkedin_scraper(
                search_terms=search_terms,
                location=self.config.get("location", "United Kingdom"),
                max_results=max_jobs,
                headless=self.config.get("headless", False),
            )
            jobs = scraper.scrape_jobs()

        else:
            self.logger.warning(f"Platform '{platform}' not yet implemented")

        return jobs

    def process_job(self, job: JobPosting) -> Optional[Dict[str, Any]]:
        """
        Process a single job: match projects and generate materials

        Args:
            job: Job posting

        Returns:
            Dictionary containing generated materials or None if failed
        """
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing: {job.company} - {job.title}")
            self.logger.info(f"{'='*60}")

            # Log job to QC log
            self.qc_log.log_job_scraped(
                job_id=job.job_id,
                platform=job.platform,
                company=job.company,
                title=job.title,
                location=job.location,
                job_url=job.job_url,
                description=job.description,
                keywords_extracted=job.keywords,
            )

            # Generate materials
            material_gen = create_material_generator(self.config["user_info"])
            materials = material_gen.generate_materials(job)

            if not materials:
                self.logger.error("Failed to generate materials")
                self.stats["errors"] += 1
                return None

            # Log CV to QC log
            self.qc_log.log_cv_generated(
                job_id=job.job_id,
                company=job.company,
                cv_file_path=materials["cv"]["path"],
                matched_projects=[
                    p.get("project_name", "Unknown")
                    for p in materials["matched_projects"].get("project_scores", [])[:3]
                ],
                cv_content_preview=materials["cv"]["text"],
                ats_score=8.5,  # Placeholder for now
                validation_result=materials["cv"].get("validation"),
            )

            # Log cover letter to QC log
            self.qc_log.log_cover_letter_generated(
                job_id=job.job_id,
                company=job.company,
                cover_letter_file_path=materials["cover_letter"]["path"],
                cover_letter_content=materials["cover_letter"]["text"],
            )

            self.stats["cvs_generated"] += 1
            self.stats["cover_letters_generated"] += 1

            return materials

        except Exception as e:
            self.logger.error(f"Error processing job: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None

    def run(self) -> Dict[str, Any]:
        """
        Run the job hunt workflow

        Returns:
            Dictionary containing run results and statistics
        """
        self.logger.info("\n" + "=" * 60)
        self.logger.info("AUTONOMOUS JOB APPLICATION BOT - PHASE 1")
        self.logger.info("=" * 60)

        # Validate setup
        if not self.validate_setup():
            self.logger.error("Setup validation failed. Please fix errors and try again.")
            return {"success": False, "error": "Setup validation failed"}

        # Initialize quality control log
        mode = "DRY RUN" if self.config.get("dry_run") else "TEST"
        platforms = self.config.get("platforms", ["linkedin"])
        region = self.config.get("region", "uk")

        self.qc_log.start_run(mode=mode, region=region, platforms=platforms)

        # Scrape jobs from each platform
        all_jobs = []
        max_jobs_total = self.config.get("max_jobs", 5)

        for platform in platforms:
            if len(all_jobs) >= max_jobs_total:
                break

            remaining = max_jobs_total - len(all_jobs)
            search_terms = self.config.get("search_terms", ["Data Scientist graduate"])

            jobs = self.scrape_jobs(platform, search_terms, remaining)
            all_jobs.extend(jobs)
            self.stats["jobs_scraped"] += len(jobs)

        self.logger.info(f"\n✓ Total jobs scraped: {len(all_jobs)}")

        if not all_jobs:
            self.logger.warning("No jobs found. Try different search terms or platforms.")
            self.qc_log.finalize_run()
            return {"success": False, "error": "No jobs found"}

        # Process each job
        processed_jobs = []

        for i, job in enumerate(all_jobs, 1):
            self.logger.info(f"\n{'#'*60}")
            self.logger.info(f"JOB {i}/{len(all_jobs)}")
            self.logger.info(f"{'#'*60}")

            materials = self.process_job(job)

            if materials:
                processed_jobs.append({
                    "job": job,
                    "materials": materials,
                })

                # Manual approval if enabled
                if self.config.get("manual_approval", True):
                    self.logger.info("\n" + "-" * 60)
                    self.logger.info("MANUAL APPROVAL REQUIRED")
                    self.logger.info("-" * 60)
                    self.logger.info(f"Job: {job.company} - {job.title}")
                    self.logger.info(f"CV: {materials['cv']['path']}")
                    self.logger.info(f"Cover Letter: {materials['cover_letter']['path']}")
                    self.logger.info("")
                    self.logger.info("Review the generated materials, then:")

                    response = input("Continue to next job? (y/n): ").strip().lower()
                    if response != 'y':
                        self.logger.info("Stopping at user request")
                        break

        # Finalize quality control log
        self.qc_log.finalize_run()

        # Print summary
        self.logger.info("\n" + "=" * 60)
        self.logger.info("RUN COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Jobs Scraped: {self.stats['jobs_scraped']}")
        self.logger.info(f"CVs Generated: {self.stats['cvs_generated']}")
        self.logger.info(f"Cover Letters Generated: {self.stats['cover_letters_generated']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info("=" * 60)
        self.logger.info(f"\n✓ Quality Control Log: workspace/logs/QUALITY_CONTROL_LOG.md")
        self.logger.info("  Review this log to verify quality of generated materials")
        self.logger.info("")

        return {
            "success": True,
            "stats": self.stats,
            "processed_jobs": processed_jobs,
        }


def run_job_hunt(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run job hunt with given configuration

    Args:
        config: Configuration dictionary

    Returns:
        Run results
    """
    orchestrator = JobHuntOrchestrator(config)
    return orchestrator.run()

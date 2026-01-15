"""
Material Generator

Generates ATS-optimized CVs and cover letters for job applications.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from modules.generation.ollama_client import get_ollama_client
from modules.generation.project_matcher import get_project_matcher
from modules.scraping.job_models import JobPosting
from modules.core.logger import get_logger
from modules.utils.helpers import sanitize_filename


class MaterialGenerator:
    """Generates CVs and cover letters"""

    def __init__(
        self,
        user_info: Dict[str, Any],
        output_dir: str = "workspace/generated_materials",
    ):
        """
        Initialize material generator

        Args:
            user_info: User information dictionary
            output_dir: Output directory for generated materials
        """
        self.user_info = user_info
        self.output_dir = Path(output_dir)
        self.logger = get_logger()
        self.ollama = get_ollama_client()
        self.project_matcher = get_project_matcher()

        # Create output directories
        (self.output_dir / "cvs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "cover_letters").mkdir(parents=True, exist_ok=True)

    def format_user_info(self) -> str:
        """Format user information for prompts"""
        info = f"""
Name: {self.user_info.get('name', 'Unknown')}
Email: {self.user_info.get('email', '')}
Phone: {self.user_info.get('phone', '')}
Location: {self.user_info.get('location', '')}
LinkedIn: {self.user_info.get('linkedin', '')}
GitHub: {self.user_info.get('github', '')}

Education:
Current: {self.user_info.get('current_education', '')}
Previous: {self.user_info.get('previous_education', '')}

Experience: {self.user_info.get('years_experience', {}).get('total', 0)} years total

Skills: {', '.join(self.user_info.get('skills', []))}
"""
        return info

    def generate_cv(
        self, job: JobPosting, matched_projects: Dict[str, Any]
    ) -> Optional[Tuple[str, str]]:
        """
        Generate ATS-optimized CV

        Args:
            job: Job posting
            matched_projects: Matched projects from project matcher

        Returns:
            Tuple of (cv_text, cv_file_path) or None if failed
        """
        self.logger.info(f"Generating CV for {job.company} - {job.title}")

        # Read prompt template
        prompt_path = Path("prompts/cv_generation_ats.txt")
        if not prompt_path.exists():
            self.logger.error("CV generation prompt not found")
            return None

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Format matched projects
        project_details = []
        for project_id in matched_projects.get("top_projects", [])[:3]:
            details = self.project_matcher.get_project_details(project_id)
            if details:
                project_details.append(details)

        matched_projects_text = "\n\n".join(project_details)

        # Prepare prompt variables
        variables = {
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "job_description": job.description[:2000],  # Limit length
            "user_info": self.format_user_info(),
            "matched_projects": matched_projects_text,
        }

        # Substitute variables
        prompt = prompt_template
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        # Generate CV
        self.logger.info("Generating CV content with Llama...")

        cv_text = self.ollama.generate_text(
            prompt,
            temperature=0.5,  # Medium creativity
            max_tokens=2000,
        )

        if not cv_text:
            self.logger.error("Failed to generate CV")
            return None

        # Save as .docx
        try:
            safe_company = sanitize_filename(job.company)
            filename = f"{self.user_info['name'].replace(' ', '_')}_CV_{safe_company}_ATS"
            cv_path = self.output_dir / "cvs" / f"{filename}.docx"

            # Create Word document
            doc = Document()

            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.75)
                section.right_margin = Inches(0.75)

            # Add CV content
            for line in cv_text.split("\n"):
                paragraph = doc.add_paragraph(line)
                # Use standard font
                for run in paragraph.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)

            # Save document
            doc.save(cv_path)

            self.logger.info(f"✓ CV saved: {cv_path}")

            return (cv_text, str(cv_path))

        except Exception as e:
            self.logger.error(f"Error saving CV: {e}")
            return None

    def generate_cover_letter(
        self, job: JobPosting, matched_projects: Dict[str, Any]
    ) -> Optional[Tuple[str, str]]:
        """
        Generate cover letter

        Args:
            job: Job posting
            matched_projects: Matched projects from project matcher

        Returns:
            Tuple of (cover_letter_text, file_path) or None if failed
        """
        self.logger.info(f"Generating cover letter for {job.company} - {job.title}")

        # Read prompt template
        prompt_path = Path("prompts/cover_letter_generation.txt")
        if not prompt_path.exists():
            self.logger.error("Cover letter generation prompt not found")
            return None

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Get top project
        top_project_id = matched_projects.get("top_projects", [])[0] if matched_projects.get("top_projects") else None
        top_project_text = ""
        if top_project_id:
            top_project_text = self.project_matcher.get_project_details(top_project_id)

        # Prepare prompt variables
        variables = {
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "job_description": job.description[:1500],
            "user_info": self.format_user_info(),
            "top_project": top_project_text,
        }

        # Substitute variables
        prompt = prompt_template
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        # Generate cover letter
        self.logger.info("Generating cover letter content with Llama...")

        cover_letter_text = self.ollama.generate_text(
            prompt,
            temperature=0.6,  # Slightly more creative
            max_tokens=800,
        )

        if not cover_letter_text:
            self.logger.error("Failed to generate cover letter")
            return None

        # Save as .docx
        try:
            safe_company = sanitize_filename(job.company)
            filename = f"{safe_company}_Cover_Letter"
            cl_path = self.output_dir / "cover_letters" / f"{filename}.docx"

            # Create Word document
            doc = Document()

            # Set margins
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)

            # Add cover letter content
            for line in cover_letter_text.split("\n"):
                paragraph = doc.add_paragraph(line)
                # Use standard font
                for run in paragraph.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)

            # Save document
            doc.save(cl_path)

            self.logger.info(f"✓ Cover letter saved: {cl_path}")

            return (cover_letter_text, str(cl_path))

        except Exception as e:
            self.logger.error(f"Error saving cover letter: {e}")
            return None

    def generate_materials(
        self, job: JobPosting
    ) -> Optional[Dict[str, Any]]:
        """
        Generate all materials for a job application

        Args:
            job: Job posting

        Returns:
            Dictionary containing generated materials and metadata
        """
        self.logger.info("=" * 60)
        self.logger.info(f"Generating materials for: {job.company} - {job.title}")
        self.logger.info("=" * 60)

        # Step 1: Match projects
        matched_projects = self.project_matcher.match_projects(job)

        # Step 2: Generate CV
        cv_result = self.generate_cv(job, matched_projects)
        if not cv_result:
            self.logger.error("CV generation failed")
            return None

        cv_text, cv_path = cv_result

        # Step 3: Generate cover letter
        cl_result = self.generate_cover_letter(job, matched_projects)
        if not cl_result:
            self.logger.error("Cover letter generation failed")
            return None

        cl_text, cl_path = cl_result

        # Return all materials
        return {
            "job_id": job.job_id,
            "company": job.company,
            "title": job.title,
            "matched_projects": matched_projects,
            "cv": {
                "text": cv_text,
                "path": cv_path,
            },
            "cover_letter": {
                "text": cl_text,
                "path": cl_path,
            },
            "generated_at": datetime.now().isoformat(),
        }


def create_material_generator(user_info: Dict[str, Any]) -> MaterialGenerator:
    """
    Create material generator

    Args:
        user_info: User information dictionary

    Returns:
        MaterialGenerator instance
    """
    return MaterialGenerator(user_info)

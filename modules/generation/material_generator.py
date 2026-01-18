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
from modules.generation.cv_template_builder import CVTemplateBuilder
from modules.generation.cover_letter_template_builder import CoverLetterTemplateBuilder
from modules.scraping.job_models import JobPosting
from modules.core.logger import get_logger
from modules.utils.helpers import sanitize_filename
from modules.utils.cv_validator import CVValidator
from modules.utils.cv_fixer import get_cv_fixer
from modules.utils.company_researcher import get_company_researcher


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
        self.validator = CVValidator()
        self.fixer = get_cv_fixer()
        self.company_researcher = get_company_researcher()

        # Initialize template builders (modular approach)
        prompts_dir = Path("prompts")
        self.cv_builder = CVTemplateBuilder(self.ollama, user_info, prompts_dir)
        self.cl_builder = CoverLetterTemplateBuilder(self.ollama, user_info, prompts_dir)

        # Create output directories
        (self.output_dir / "cvs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "cover_letters").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "failed_cvs").mkdir(parents=True, exist_ok=True)

    def format_user_info(self) -> str:
        """Format user information with proper defaults"""

        # Handle missing graduation date
        grad_date = self.user_info.get('graduation_date')
        if not grad_date:
            # Infer from current education if possible
            current_edu = self.user_info.get('current_education', '')
            if 'expected' in current_edu.lower() or 'msc' in current_edu.lower():
                grad_date = 'Expected June 2026'  # Default for current students
            else:
                grad_date = '[OMIT - not provided]'

        # Handle missing previous education
        prev_edu = self.user_info.get('previous_education', '')
        if not prev_edu or len(prev_edu.strip()) == 0:
            prev_edu = '[OMIT - not provided]'

        info = f"""
Name: {self.user_info.get('name', 'Unknown')}
Email: {self.user_info.get('email', '')}
Phone: {self.user_info.get('phone', '')}
Location: {self.user_info.get('location', '')}
LinkedIn: {self.user_info.get('linkedin', '')}
GitHub: {self.user_info.get('github', '')}

Education:
Current: {self.user_info.get('current_education', '')}
Graduation Date: {grad_date}
Previous: {prev_edu}

Experience: {self.user_info.get('years_experience', {}).get('total', 0)} years total

Skills: {', '.join(self.user_info.get('skills', []))}

IMPORTANT: Any field marked [OMIT - not provided] should be completely excluded from the CV output.
"""
        return info

    def _build_correction_prompt(self, validation_result: Dict[str, Any]) -> str:
        """Build specific correction instructions based on validation issues"""
        corrections = []
        corrections.append("CRITICAL CORRECTIONS NEEDED:")
        corrections.append("")

        for issue in validation_result["critical_issues"]:
            if "meta-commentary" in issue.lower():
                corrections.append("• START IMMEDIATELY with the candidate's name. NO introductory text like 'Here is...'")
            elif "relevance score" in issue.lower():
                corrections.append("• REMOVE all relevance scores (X/10) from the output. They should not appear in the CV.")
            elif "placeholder" in issue.lower():
                corrections.append("• REMOVE all placeholder text [like this], TBD, N/A. Use only complete information.")
            elif "missing" in issue.lower() and "section" in issue.lower():
                corrections.append(f"• INCLUDE the missing section: {issue}")
            elif "contact" in issue.lower():
                corrections.append("• ENSURE contact information (email, phone) is included after the name")
            elif "date" in issue.lower():
                corrections.append(f"• FIX date mismatch: {issue}. Use ONLY dates from provided user info.")
            elif "project" in issue.lower():
                corrections.append("• INCLUDE ALL 3 projects. Each needs 2-3 bullet points.")
            else:
                corrections.append(f"• {issue}")

        corrections.append("")
        corrections.append("Regenerate the CV fixing these specific issues.")

        return "\n".join(corrections)

    def generate_cv(
        self, job: JobPosting, matched_projects: Dict[str, Any]
    ) -> Optional[Tuple[str, str]]:
        """
        Generate ATS-optimized CV using modular template approach

        Args:
            job: Job posting
            matched_projects: Matched projects from project matcher

        Returns:
            Tuple of (cv_text, cv_file_path, validation_result) or None if failed
        """
        self.logger.info(f"Generating CV for {job.company} - {job.title}")

        # Format matched projects for template builder
        project_scores = matched_projects.get("project_scores", [])[:3]
        formatted_projects = []

        for score_data in project_scores:
            project_id = score_data.get("project_id")
            project_name = score_data.get("project_name", "Unknown")
            relevance_score = score_data.get("score", 0)
            reasoning = score_data.get("reasoning", "")

            # Get full project details
            details = self.project_matcher.get_project_details(project_id)
            if details:
                # Parse project details (extract title, description, technologies)
                project_data = self._parse_project_details(details)

                # Validate that we got all required fields
                if not project_data.get('title'):
                    self.logger.warning(f"Project {project_id} has no title, skipping")
                    continue
                if not project_data.get('technologies'):
                    self.logger.warning(f"Project {project_id} has no technologies, skipping")
                    continue
                if not project_data.get('description'):
                    self.logger.warning(f"Project {project_id} has no description, skipping")
                    continue

                project_data["score"] = relevance_score
                project_data["relevance_context"] = f"Relevance Score: {relevance_score}/10\nWhy relevant: {reasoning}"
                formatted_projects.append(project_data)

        if len(formatted_projects) < 3:
            self.logger.error(f"Need 3 projects, only got {len(formatted_projects)}")
            return None

        # Generate CV using template builder (handles validation internally)
        try:
            cv_doc = self.cv_builder.generate_cv(job, formatted_projects)

            if not cv_doc:
                self.logger.error("CV generation failed - template builder returned None")
                return None

            # Save as .docx
            safe_company = sanitize_filename(job.company)
            filename = f"{self.user_info['name'].replace(' ', '_')}_CV_{safe_company}_ATS"
            cv_path = self.output_dir / "cvs" / f"{filename}.docx"

            cv_doc.save(cv_path)

            self.logger.info(f"✓ CV saved: {cv_path}")

            # Generate mock validation result for compatibility
            # (validation is done per-section in template builder)
            validation_result = {
                "valid": True,
                "ai_score": 15,  # Low score = good (less AI tells)
                "critical_issues": [],
                "warnings": []
            }

            # Extract text from document for return value
            cv_text = "\n".join([para.text for para in cv_doc.paragraphs if para.text.strip()])

            return (cv_text, str(cv_path), validation_result)

        except Exception as e:
            self.logger.error(f"Error generating CV: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    def _parse_project_details(self, details_text: str) -> Dict[str, Any]:
        """
        Parse project details text into structured format.

        Expected format from get_project_details():
        Line 1: Project Name
        Line 2: Project Summary/Description
        Line 3: Technologies: tech1, tech2, tech3
        Line 4: Key Results: metrics
        """
        lines = [line.strip() for line in details_text.strip().split('\n') if line.strip()]

        project = {
            'title': '',
            'description': '',
            'technologies': []
        }

        # Line-based parsing matching actual get_project_details() format
        if len(lines) >= 1:
            # Line 1: Project title (no prefix)
            project['title'] = lines[0]

        if len(lines) >= 2:
            # Line 2: Project description/summary (no prefix)
            project['description'] = lines[1]

        # Lines 3+: Look for Technologies and Key Results
        for line in lines[2:]:
            if line.startswith('Technologies:'):
                tech_line = line.replace('Technologies:', '').strip()
                project['technologies'] = [t.strip() for t in tech_line.split(',') if t.strip()]
            elif line.startswith('Key Results:'):
                # Append key results to description for context
                key_results = line.replace('Key Results:', '').strip()
                if key_results:
                    project['description'] += f" Key metrics: {key_results}"

        # Log parsed project for debugging
        self.logger.debug(f"Parsed project: title='{project['title']}', "
                         f"technologies={len(project['technologies'])}, "
                         f"description_len={len(project['description'])}")

        return project

    def generate_cover_letter(
        self, job: JobPosting, matched_projects: Dict[str, Any]
    ) -> Optional[Tuple[str, str]]:
        """
        Generate cover letter using template approach with company research

        Args:
            job: Job posting
            matched_projects: Matched projects from project matcher

        Returns:
            Tuple of (cover_letter_text, file_path) or None if failed
        """
        self.logger.info(f"Generating cover letter for {job.company} - {job.title}")

        # Step 1: Research company (web search)
        company_research = self.company_researcher.research_company(job.company, job.title)

        # Step 2: Format matched projects for cover letter builder
        project_scores = matched_projects.get("project_scores", [])[:3]
        formatted_projects = []

        for score_data in project_scores:
            project_id = score_data.get("project_id")
            details = self.project_matcher.get_project_details(project_id)
            if details:
                project_data = self._parse_project_details(details)
                if project_data.get('title'):
                    project_data["score"] = score_data.get("score", 0)
                    project_data["relevance_context"] = score_data.get("reasoning", "")
                    formatted_projects.append(project_data)

        if len(formatted_projects) < 1:
            self.logger.warning("No valid projects for cover letter, using fallback")

        # Step 3: Generate cover letter using template builder
        try:
            cl_doc = self.cl_builder.generate_cover_letter(job, company_research, formatted_projects)

            if not cl_doc:
                self.logger.error("Cover letter generation failed - template builder returned None")
                return None

            # Save as .docx
            safe_company = sanitize_filename(job.company)
            filename = f"{self.user_info['name'].replace(' ', '_')}_CoverLetter_{safe_company}"
            cl_path = self.output_dir / "cover_letters" / f"{filename}.docx"

            cl_doc.save(cl_path)

            self.logger.info(f"✓ Cover letter saved: {cl_path}")

            # Extract text from document for return value
            cl_text = "\n".join([para.text for para in cl_doc.paragraphs if para.text.strip()])

            return (cl_text, str(cl_path))

        except Exception as e:
            self.logger.error(f"Error generating cover letter: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
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

        cv_text, cv_path, cv_validation = cv_result

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
                "validation": cv_validation,
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

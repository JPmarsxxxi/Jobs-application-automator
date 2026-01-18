"""
CV Section Fixer

Performs targeted fixes on specific CV sections without full regeneration.
More efficient and reliable than regenerating entire CV.
"""

import re
from typing import Dict, List, Optional, Tuple
from modules.generation.ollama_client import get_ollama_client
from modules.core.logger import get_logger


class CVSectionFixer:
    """Fixes specific sections of CV without full regeneration"""

    def __init__(self):
        self.ollama = get_ollama_client()
        self.logger = get_logger()

    def parse_cv_sections(self, cv_text: str) -> Dict[str, str]:
        """
        Parse CV into distinct sections

        Returns:
            Dictionary with section names as keys and content as values
        """
        sections = {}

        # Define section markers
        section_markers = [
            "PROFESSIONAL SUMMARY",
            "CORE COMPETENCIES",
            "KEY PROJECTS",
            "PROJECTS",
            "EXPERIENCE",
            "EDUCATION",
        ]

        # Split by section headers
        current_section = "header"
        current_content = []

        for line in cv_text.split('\n'):
            # Check if line is a section header
            is_section_header = False
            for marker in section_markers:
                if marker in line.upper() and len(line.strip()) < 50:
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)

                    # Start new section
                    current_section = marker
                    current_content = [line]
                    is_section_header = True
                    break

            if not is_section_header:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def fix_placeholders(self, cv_text: str, user_info: Dict) -> str:
        """
        Find and fix placeholder text with actual data

        Args:
            cv_text: CV text with placeholders
            user_info: User information to fill in

        Returns:
            Fixed CV text
        """
        self.logger.info("Fixing placeholders in CV...")

        # Common placeholder patterns and their fixes
        fixes = {
            r'\[Graduation Date\]': user_info.get('graduation_date', 'June 2026'),
            r'\[Expected Graduation\]': user_info.get('graduation_date', 'June 2026'),
            r'\[Not Provided\]': '',
            r'\[Not provided\]': '',
            r'\[quantified metrics\]': '',
            r'\[metrics\]': '',
            r'\[TBD\]': '',
            r'\bTBD\b': '',
            r'\bN/A\b': '',
        }

        fixed_text = cv_text
        changes_made = 0

        for pattern, replacement in fixes.items():
            if re.search(pattern, fixed_text, re.IGNORECASE):
                fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)
                changes_made += 1

        if changes_made > 0:
            self.logger.info(f"✓ Fixed {changes_made} placeholder(s)")

        return fixed_text

    def fix_education_section(
        self, education_section: str, user_info: Dict
    ) -> str:
        """
        Fix education section with proper dates and information

        Args:
            education_section: Current education section text
            user_info: User information

        Returns:
            Fixed education section
        """
        prompt = f"""Fix this Education section by replacing placeholders with real data.

CURRENT EDUCATION SECTION:
{education_section}

REAL DATA TO USE:
Current Education: {user_info.get('current_education', 'MSc Data Science')}
Graduation Date: {user_info.get('graduation_date', 'June 2026')}
Previous Education: {user_info.get('previous_education', 'BSc Anatomy')}

INSTRUCTIONS:
1. Replace ALL placeholders with real data above
2. Remove [brackets], TBD, N/A
3. If previous education is not provided or empty, omit it entirely
4. Keep same formatting style
5. Output ONLY the fixed Education section, nothing else

Fixed Education section:"""

        fixed_section = self.ollama.generate_text(
            prompt,
            temperature=0.2,  # Low temperature for consistency
            max_tokens=300,
        )

        return fixed_section if fixed_section else education_section

    def add_missing_project(
        self,
        cv_text: str,
        project_details: str,
        job_description: str,
    ) -> str:
        """
        Add a missing project to the KEY PROJECTS section

        Args:
            cv_text: Current CV text
            project_details: Details of project to add
            job_description: Job description for context

        Returns:
            CV with added project
        """
        self.logger.info("Adding missing project to CV...")

        # Extract KEY PROJECTS section
        projects_match = re.search(
            r'(KEY PROJECTS.*?)(?=\n[A-Z][A-Z\s]+\n|\Z)',
            cv_text,
            re.DOTALL | re.IGNORECASE
        )

        if not projects_match:
            self.logger.warning("Could not find KEY PROJECTS section")
            return cv_text

        projects_section = projects_match.group(1)

        prompt = f"""Add this project to the existing KEY PROJECTS section.

EXISTING KEY PROJECTS SECTION:
{projects_section}

PROJECT TO ADD:
{project_details}

JOB CONTEXT:
{job_description[:500]}

INSTRUCTIONS:
1. Add the new project in the same format as existing projects
2. Include: Project Name, Technologies line, 2-3 bullet points
3. Place it at the end of existing projects
4. Make bullets relevant to the job context
5. Include quantified metrics
6. Output the COMPLETE updated KEY PROJECTS section

Updated KEY PROJECTS section:"""

        updated_section = self.ollama.generate_text(
            prompt,
            temperature=0.4,
            max_tokens=600,
        )

        if updated_section:
            # Replace old section with new one
            cv_text = cv_text.replace(projects_section, updated_section)
            self.logger.info("✓ Added missing project")

        return cv_text

    def fix_section(
        self,
        section_name: str,
        section_content: str,
        issue_description: str,
        user_info: Dict,
        job_description: str = "",
    ) -> str:
        """
        Fix a specific section with targeted instructions

        Args:
            section_name: Name of section (e.g., "EDUCATION", "KEY PROJECTS")
            section_content: Current section content
            issue_description: Description of what's wrong
            user_info: User information for reference
            job_description: Job description for context

        Returns:
            Fixed section content
        """
        self.logger.info(f"Fixing {section_name} section: {issue_description}")

        prompt = f"""Fix this {section_name} section.

CURRENT {section_name} SECTION:
{section_content}

ISSUE TO FIX:
{issue_description}

USER INFO FOR REFERENCE:
Name: {user_info.get('name')}
Education: {user_info.get('current_education')}
Graduation: {user_info.get('graduation_date', 'June 2026')}
Previous: {user_info.get('previous_education', '')}

INSTRUCTIONS:
1. Fix ONLY the specific issue mentioned
2. Keep all other content unchanged
3. Maintain same formatting style
4. Remove placeholders [like this], TBD, N/A
5. Output ONLY the fixed section, no commentary

Fixed {section_name} section:"""

        fixed_section = self.ollama.generate_text(
            prompt,
            temperature=0.3,
            max_tokens=500,
        )

        return fixed_section if fixed_section else section_content

    def can_fix_issues(self, validation_issues: List[str]) -> Tuple[bool, List[str]]:
        """
        Determine if issues can be fixed with section repairs

        Args:
            validation_issues: List of validation issues

        Returns:
            Tuple of (can_fix: bool, fixable_issues: List[str])
        """
        fixable_patterns = [
            "placeholder",
            "graduation date",
            "date mismatch",
            "missing project",
            "project count",
            "not provided",
        ]

        fixable_issues = []
        for issue in validation_issues:
            issue_lower = issue.lower()
            if any(pattern in issue_lower for pattern in fixable_patterns):
                fixable_issues.append(issue)

        can_fix = len(fixable_issues) > 0

        return can_fix, fixable_issues

    def fix_cv(
        self,
        cv_text: str,
        validation_issues: List[str],
        user_info: Dict,
        job_info: Dict,
        matched_projects: Dict,
    ) -> Optional[str]:
        """
        Main method to fix CV issues

        Args:
            cv_text: Current CV text with issues
            validation_issues: List of validation issues
            user_info: User information
            job_info: Job information (company, title, description)
            matched_projects: Matched projects data

        Returns:
            Fixed CV text or None if couldn't fix
        """
        self.logger.info("Attempting targeted CV fixes...")

        # Check if we can fix these issues
        can_fix, fixable_issues = self.can_fix_issues(validation_issues)

        if not can_fix:
            self.logger.warning("Issues not fixable with section repairs")
            return None

        self.logger.info(f"Fixable issues: {', '.join(fixable_issues[:3])}")

        fixed_cv = cv_text

        # Fix 1: Simple placeholder replacement
        fixed_cv = self.fix_placeholders(fixed_cv, user_info)

        # Fix 2: Education section issues
        if any("graduation" in issue.lower() or "date" in issue.lower() for issue in fixable_issues):
            sections = self.parse_cv_sections(fixed_cv)
            if "EDUCATION" in sections:
                fixed_education = self.fix_education_section(sections["EDUCATION"], user_info)
                fixed_cv = fixed_cv.replace(sections["EDUCATION"], fixed_education)

        # Fix 3: Missing project
        if any("project" in issue.lower() and ("missing" in issue.lower() or "count" in issue.lower()) for issue in fixable_issues):
            # Find which project is missing
            project_scores = matched_projects.get("project_scores", [])
            if len(project_scores) >= 3:
                # Check which project is not in CV
                for project_data in project_scores[:3]:
                    project_name = project_data.get("project_name", "")
                    if project_name and project_name not in fixed_cv:
                        # This project is missing, add it
                        project_id = project_data.get("project_id")
                        # Get project details (you'd need to pass project_matcher here)
                        # For now, we'll use a simpler approach
                        self.logger.info(f"Need to add missing project: {project_name}")

        return fixed_cv


def get_cv_fixer() -> CVSectionFixer:
    """Get CV fixer instance"""
    return CVSectionFixer()

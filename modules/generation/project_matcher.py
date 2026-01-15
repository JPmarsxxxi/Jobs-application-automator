"""
Project Matcher

Intelligently matches candidate's projects to job descriptions using LLM.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from modules.generation.ollama_client import get_ollama_client
from modules.scraping.job_models import JobPosting
from modules.core.logger import get_logger


class ProjectMatcher:
    """Matches projects to job descriptions"""

    def __init__(self, portfolio_dir: str = "workspace/portfolio"):
        """
        Initialize project matcher

        Args:
            portfolio_dir: Path to portfolio directory
        """
        self.portfolio_dir = Path(portfolio_dir)
        self.projects = []
        self.logger = get_logger()
        self.ollama = get_ollama_client()

        # Load projects
        self.load_projects()

    def load_projects(self):
        """Load projects from portfolio directory"""
        projects_index_path = self.portfolio_dir / "projects_index.json"

        if not projects_index_path.exists():
            self.logger.warning(
                f"Projects index not found at {projects_index_path}. "
                "Please create it from projects_index.example.json"
            )
            return

        try:
            with open(projects_index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.projects = data.get("projects", [])

            self.logger.info(f"✓ Loaded {len(self.projects)} projects from portfolio")

            # Load detailed descriptions if available
            for project in self.projects:
                project_id = project.get("id")
                md_path = self.portfolio_dir / "projects" / f"{project_id}.md"

                if md_path.exists():
                    with open(md_path, "r", encoding="utf-8") as f:
                        project["detailed_description"] = f.read()

        except Exception as e:
            self.logger.error(f"Error loading projects: {e}")

    def format_projects_for_prompt(self) -> str:
        """
        Format projects for LLM prompt

        Returns:
            Formatted project list
        """
        formatted = []

        for i, project in enumerate(self.projects, 1):
            proj_text = f"""
Project {i}: {project.get('name', 'Unknown')}
ID: {project.get('id', '')}
Summary: {project.get('summary', '')}
Keywords: {', '.join(project.get('keywords', []))}
Tech Stack: {', '.join(project.get('tech_stack', []))}
Key Metrics: {project.get('key_metrics', 'N/A')}
"""
            # Add detailed description if available
            if 'detailed_description' in project:
                proj_text += f"\nDetails: {project['detailed_description'][:500]}..."

            formatted.append(proj_text)

        return "\n---\n".join(formatted)

    def match_projects(
        self, job: JobPosting, top_n: int = 3
    ) -> Dict[str, Any]:
        """
        Match projects to a job posting

        Args:
            job: Job posting to match against
            top_n: Number of top projects to return

        Returns:
            Dictionary containing matched projects and scores
        """
        self.logger.info(f"Matching projects for: {job.company} - {job.title}")

        if not self.projects:
            self.logger.warning("No projects available for matching")
            return {
                "top_projects": [],
                "project_scores": [],
                "error": "No projects loaded"
            }

        # Read prompt template
        prompt_path = Path("prompts/project_matching.txt")
        if not prompt_path.exists():
            self.logger.error("Project matching prompt template not found")
            return {"error": "Prompt template not found"}

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Prepare prompt variables
        variables = {
            "job_description": job.description[:2000],  # Limit length
            "company": job.company,
            "title": job.title,
            "projects": self.format_projects_for_prompt(),
        }

        # Substitute variables
        prompt = prompt_template
        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        # Generate matching analysis
        self.logger.info("Analyzing project matches with Llama...")

        response = self.ollama.generate_text(
            prompt,
            temperature=0.3,  # Lower temperature for more consistent scoring
        )

        if not response:
            self.logger.error("Failed to get LLM response for project matching")
            return {"error": "LLM generation failed"}

        # Parse JSON response
        result = self.ollama.extract_json(response)

        if not result:
            self.logger.error("Failed to parse JSON from LLM response")
            self.logger.debug(f"Raw response: {response[:500]}")
            # Fallback: return all projects with default scores
            return {
                "top_projects": [p["id"] for p in self.projects[:top_n]],
                "project_scores": [
                    {
                        "project_id": p["id"],
                        "project_name": p["name"],
                        "score": 5,
                        "reasoning": "Default match (LLM parsing failed)",
                    }
                    for p in self.projects[:top_n]
                ],
                "fallback": True,
            }

        # Extract top projects
        top_project_ids = result.get("top_projects", [])[:top_n]
        project_scores = result.get("project_scores", [])

        # Sort by score and get top N
        project_scores.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_scores = project_scores[:top_n]

        self.logger.info(f"✓ Matched top {len(top_project_ids)} projects:")
        for score_data in top_scores:
            self.logger.info(
                f"  - {score_data.get('project_name', 'Unknown')} "
                f"(score: {score_data.get('score', 0)}/10)"
            )

        return {
            "top_projects": top_project_ids,
            "project_scores": top_scores,
            "job_analysis": result.get("job_analysis", {}),
            "recommendation": result.get("recommendation", ""),
        }

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project details by ID

        Args:
            project_id: Project ID

        Returns:
            Project dictionary or None
        """
        for project in self.projects:
            if project.get("id") == project_id:
                return project
        return None

    def get_project_details(self, project_id: str) -> str:
        """
        Get formatted project details for CV/cover letter

        Args:
            project_id: Project ID

        Returns:
            Formatted project details
        """
        project = self.get_project_by_id(project_id)
        if not project:
            return ""

        details = f"{project.get('name', 'Unknown Project')}\n"
        details += f"{project.get('summary', '')}\n"
        details += f"Technologies: {', '.join(project.get('tech_stack', []))}\n"
        details += f"Key Results: {project.get('key_metrics', 'N/A')}\n"

        if 'detailed_description' in project:
            details += f"\nDetails:\n{project['detailed_description']}\n"

        return details


# Singleton instance
_project_matcher = None


def get_project_matcher() -> ProjectMatcher:
    """Get or create project matcher singleton"""
    global _project_matcher
    if _project_matcher is None:
        _project_matcher = ProjectMatcher()
    return _project_matcher

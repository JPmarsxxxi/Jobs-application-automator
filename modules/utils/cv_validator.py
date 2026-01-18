"""
CV Validation System

Detects AI tells, quality issues, and ensures professional CV standards.
"""

import re
from typing import Dict, List, Any, Tuple
from collections import Counter


class CVValidator:
    """Validates generated CVs for AI tells and quality issues"""

    # AI clichés to avoid
    AI_CLICHES = [
        "leveraged", "spearheaded", "utilized", "synergized", "orchestrated",
        "facilitated", "strategized", "pioneered", "championed"
    ]

    # Meta-commentary patterns
    META_PATTERNS = [
        r"here is (the|an?)",
        r"i have (generated|created|prepared)",
        r"below is",
        r"please find",
        r"attached is",
        r"this cv",
        r"curriculum vitae for",
    ]

    # Placeholder patterns
    PLACEHOLDER_PATTERNS = [
        r"\[.*?\]",  # [like this]
        r"\{\{.*?\}\}",  # {{like this}} - template markers
        r"\bTBD\b",
        r"\bN/?A\b",  # N/A or NA
        r"\bTODO\b",
        r"\(to be determined\)",
        r"\(insert.*?\)",
        r"not provided",  # Common placeholder phrase
        r"to be confirmed",
        r"\[quantified metrics\]",  # Specific ones seen in errors
        r"\[Graduation Date\]",
        r"\[Expected Graduation\]",
    ]

    # Required sections
    REQUIRED_SECTIONS = [
        "PROFESSIONAL SUMMARY",
        "CORE COMPETENCIES",
        "KEY PROJECTS",
        "EDUCATION"
    ]

    def __init__(self):
        self.critical_issues = []
        self.warnings = []
        self.suggestions = []

    def validate(self, cv_text: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate CV for AI tells and quality issues

        Args:
            cv_text: Generated CV text
            user_info: User information for data validation

        Returns:
            Validation result dictionary
        """
        self.critical_issues = []
        self.warnings = []
        self.suggestions = []

        # Critical checks
        self._check_meta_commentary(cv_text)
        self._check_relevance_scores(cv_text)
        self._check_placeholders(cv_text)
        self._check_required_sections(cv_text)
        self._check_contact_info(cv_text, user_info)
        self._check_dates(cv_text, user_info)
        self._check_project_count(cv_text)

        # Warning checks
        self._check_ai_cliches(cv_text)
        self._check_action_verb_variety(cv_text)
        self._check_quantification(cv_text)

        # Calculate AI score (0-100, higher = more AI-like)
        ai_score = self._calculate_ai_score(cv_text)

        # Valid if no critical issues
        valid = len(self.critical_issues) == 0

        return {
            "valid": valid,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "ai_score": ai_score,
        }

    def _check_meta_commentary(self, cv_text: str):
        """Check for AI meta-commentary"""
        text_lower = cv_text.lower()
        first_100_chars = text_lower[:100]

        for pattern in self.META_PATTERNS:
            if re.search(pattern, first_100_chars, re.IGNORECASE):
                self.critical_issues.append(
                    f"Meta-commentary detected: '{pattern}'. CV should start directly with name, not commentary."
                )
                break

    def _check_relevance_scores(self, cv_text: str):
        """Check for relevance scores in output"""
        score_patterns = [
            r"relevance score[:\s]+\d+/10",
            r"score[:\s]+\d+/10",
            r"\d+/10\s*relevance",
            r"rated \d+/10",
        ]

        for pattern in score_patterns:
            if re.search(pattern, cv_text, re.IGNORECASE):
                self.critical_issues.append(
                    "Relevance scores found in CV output. Scores should be internal only, not visible in CV."
                )
                break

    def _check_placeholders(self, cv_text: str):
        """Check for placeholder text"""
        for pattern in self.PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, cv_text, re.IGNORECASE)
            if matches:
                # Filter out GitHub URLs [URL] which are OK
                real_placeholders = [m for m in matches if "github" not in m.lower() and "url" not in m.lower()]
                if real_placeholders:
                    self.critical_issues.append(
                        f"Placeholder text found: {', '.join(real_placeholders[:3])}. All content should be complete."
                    )
                    break

    def _check_required_sections(self, cv_text: str):
        """Check all required sections are present"""
        missing_sections = []

        for section in self.REQUIRED_SECTIONS:
            if section not in cv_text.upper():
                missing_sections.append(section)

        if missing_sections:
            self.critical_issues.append(
                f"Missing required sections: {', '.join(missing_sections)}"
            )

    def _check_contact_info(self, cv_text: str, user_info: Dict[str, Any]):
        """Check contact information is present"""
        email = user_info.get("email", "")
        phone = user_info.get("phone", "")

        if email and email not in cv_text:
            self.critical_issues.append("Email address missing from CV")

        if phone and phone not in cv_text:
            self.warnings.append("Phone number missing from CV")

    def _check_dates(self, cv_text: str, user_info: Dict[str, Any]):
        """Check dates match user info"""
        # Check graduation date
        expected_grad = user_info.get("graduation_date", "")
        if expected_grad:
            # Extract year
            expected_year = re.search(r"\d{4}", expected_grad)
            if expected_year:
                year = expected_year.group()
                # Check if wrong year appears in education section
                edu_section = self._extract_section(cv_text, "EDUCATION")
                if edu_section:
                    years_in_edu = re.findall(r"\b(20\d{2})\b", edu_section)
                    # Check if any year is significantly different
                    if years_in_edu:
                        for found_year in years_in_edu:
                            if abs(int(found_year) - int(year)) > 1:  # Allow 1 year difference
                                self.critical_issues.append(
                                    f"Date mismatch: Found {found_year} in Education but expected around {year}"
                                )

    def _check_project_count(self, cv_text: str):
        """Check that exactly 3 projects are included"""
        projects_section = self._extract_section(cv_text, "KEY PROJECTS")
        if not projects_section:
            self.critical_issues.append("KEY PROJECTS section missing entirely")
            return

        # Count project titles more accurately
        # Look for lines followed by "Technologies:" line
        lines = projects_section.split('\n')
        project_count = 0

        for i, line in enumerate(lines):
            # Project title is typically followed by Technologies: line
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if next_line.startswith("Technologies:") and len(line.strip()) > 10:
                    if not line.strip().startswith("•") and line.strip() != "KEY PROJECTS":
                        project_count += 1

        if project_count < 3:
            self.critical_issues.append(
                f"Only {project_count} projects found. All 3 provided projects must be included. "
                f"Each project needs: Title line, Technologies line, 2-3 bullet points."
            )

    def _check_ai_cliches(self, cv_text: str):
        """Check for overuse of AI clichés"""
        text_lower = cv_text.lower()
        cliche_counts = {}

        for cliche in self.AI_CLICHES:
            count = text_lower.count(cliche)
            if count > 2:
                cliche_counts[cliche] = count

        if cliche_counts:
            self.warnings.append(
                f"AI clichés overused: {', '.join([f'{k} ({v}x)' for k, v in cliche_counts.items()])}"
            )

    def _check_action_verb_variety(self, cv_text: str):
        """Check for action verb variety"""
        # Extract bullet points
        bullets = re.findall(r'•\s*([A-Z][a-z]+)', cv_text)

        if bullets:
            verb_counts = Counter(bullets)
            overused = {verb: count for verb, count in verb_counts.items() if count > 3}

            if overused:
                self.warnings.append(
                    f"Action verbs overused: {', '.join([f'{k} ({v}x)' for k, v in overused.items()])}"
                )

    def _check_quantification(self, cv_text: str):
        """Check for quantified achievements"""
        projects_section = self._extract_section(cv_text, "KEY PROJECTS")
        if projects_section:
            bullets = [l.strip() for l in projects_section.split('\n') if l.strip().startswith('•')]

            # Check how many bullets have numbers/percentages
            quantified = 0
            for bullet in bullets:
                if re.search(r'\d+[%+]?|\d+,\d+', bullet):
                    quantified += 1

            if bullets and (quantified / len(bullets)) < 0.5:
                self.suggestions.append(
                    f"Only {quantified}/{len(bullets)} project bullets contain metrics. Aim for quantifiable achievements."
                )

    def _calculate_ai_score(self, cv_text: str) -> int:
        """
        Calculate AI detection score (0-100)
        Higher score = more AI-like (bad)
        """
        score = 0

        # Meta-commentary: +40 points
        if any(self._check_pattern(cv_text, p) for p in self.META_PATTERNS):
            score += 40

        # Relevance scores visible: +30 points
        if re.search(r"\d+/10", cv_text):
            score += 30

        # AI clichés: +2 points per occurrence over threshold
        text_lower = cv_text.lower()
        for cliche in self.AI_CLICHES:
            count = text_lower.count(cliche)
            if count > 2:
                score += (count - 2) * 2

        # Lack of specificity: +10 points
        if not re.search(r'\d+[%+]?', cv_text):
            score += 10

        # Generic language: +5 points
        generic_phrases = ["responsible for", "duties include", "worked on", "helped with"]
        for phrase in generic_phrases:
            if phrase in text_lower:
                score += 5

        return min(score, 100)  # Cap at 100

    def _extract_section(self, cv_text: str, section_name: str) -> str:
        """Extract a specific section from CV"""
        pattern = rf"{section_name}(.*?)(?=\n[A-Z][A-Z\s]+\n|$)"
        match = re.search(pattern, cv_text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _check_pattern(self, text: str, pattern: str) -> bool:
        """Check if pattern exists in text"""
        return bool(re.search(pattern, text, re.IGNORECASE))

    def format_validation_report(self, result: Dict[str, Any]) -> str:
        """Format validation result as readable report"""
        report = []
        report.append("=" * 60)
        report.append("CV VALIDATION REPORT")
        report.append("=" * 60)

        if result["valid"]:
            report.append("✅ STATUS: PASSED")
        else:
            report.append("❌ STATUS: FAILED")

        report.append(f"🤖 AI Score: {result['ai_score']}/100 (lower is better)")
        report.append("")

        if result["critical_issues"]:
            report.append("🚨 CRITICAL ISSUES (Must Fix):")
            for issue in result["critical_issues"]:
                report.append(f"  • {issue}")
            report.append("")

        if result["warnings"]:
            report.append("⚠️  WARNINGS:")
            for warning in result["warnings"]:
                report.append(f"  • {warning}")
            report.append("")

        if result["suggestions"]:
            report.append("💡 SUGGESTIONS:")
            for suggestion in result["suggestions"]:
                report.append(f"  • {suggestion}")
            report.append("")

        report.append("=" * 60)

        return "\n".join(report)


def validate_cv(cv_text: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to validate a CV

    Args:
        cv_text: Generated CV text
        user_info: User information

    Returns:
        Validation result dictionary
    """
    validator = CVValidator()
    return validator.validate(cv_text, user_info)

"""
CV Template Structure
Defines the CV template with placeholders for LLM-generated content
"""

def get_cv_template() -> str:
    """
    Returns the CV template with placeholders.

    Placeholders:
    - {{NAME}}: Full name
    - {{EMAIL}}: Email address
    - {{PHONE}}: Phone number
    - {{LINKEDIN}}: LinkedIn URL
    - {{LOCATION}}: City, Country
    - {{PROFESSIONAL_SUMMARY}}: 2-3 sentence summary
    - {{SKILLS_CATEGORIZED}}: Categorized skills (e.g., "Languages: Python, Java...")
    - {{PROJECT_1_TITLE}}: First project title
    - {{PROJECT_1_TECH}}: First project technologies
    - {{PROJECT_1_BULLETS}}: First project bullet points
    - {{PROJECT_2_TITLE}}: Second project title
    - {{PROJECT_2_TECH}}: Second project technologies
    - {{PROJECT_2_BULLETS}}: Second project bullet points
    - {{PROJECT_3_TITLE}}: Third project title
    - {{PROJECT_3_TECH}}: Third project technologies
    - {{PROJECT_3_BULLETS}}: Third project bullet points
    - {{EDUCATION}}: Education section
    - {{CERTIFICATIONS}}: Certifications (if any)
    """

    template = """{{NAME}}
{{EMAIL}} | {{PHONE}} | {{LINKEDIN}} | {{LOCATION}}

PROFESSIONAL SUMMARY
{{PROFESSIONAL_SUMMARY}}

TECHNICAL SKILLS
{{SKILLS_CATEGORIZED}}

KEY PROJECTS

{{PROJECT_1_TITLE}}
Technologies: {{PROJECT_1_TECH}}
{{PROJECT_1_BULLETS}}

{{PROJECT_2_TITLE}}
Technologies: {{PROJECT_2_TECH}}
{{PROJECT_2_BULLETS}}

{{PROJECT_3_TITLE}}
Technologies: {{PROJECT_3_TECH}}
{{PROJECT_3_BULLETS}}

EDUCATION
{{EDUCATION}}

{{CERTIFICATIONS}}"""

    return template


def get_section_order() -> list:
    """Returns the order in which sections should be generated"""
    return [
        'professional_summary',
        'skills_categorized',
        'project_1_bullets',
        'project_2_bullets',
        'project_3_bullets'
    ]


def get_static_sections() -> list:
    """Returns sections that don't need LLM generation (filled from user_info)"""
    return [
        'name',
        'email',
        'phone',
        'linkedin',
        'location',
        'project_1_title',
        'project_1_tech',
        'project_2_title',
        'project_2_tech',
        'project_3_title',
        'project_3_tech',
        'education',
        'certifications'
    ]

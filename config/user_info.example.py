"""
User Information Configuration

Copy this file to user_info.py and fill in your actual details.
NEVER commit user_info.py to version control.
"""

USER_INFO = {
    # Personal Details
    "name": "Your Full Name",
    "email": "your.email@example.com",
    "phone": "Your Phone Number",
    "location": "Your City, Country",

    # Professional Links
    "linkedin": "linkedin.com/in/your-profile",
    "github": "github.com/your-username",
    "portfolio_website": "https://yourwebsite.com",  # Optional

    # Education
    "current_education": "Your Current Degree and Institution",
    "graduation_date": "Expected Month Year",
    "previous_education": "Previous Degree and Institution",
    "gpa": "Your GPA (optional)",

    # Visa Status
    "visa_status": {
        "uk": "student_visa",  # Options: student_visa, work_visa, citizen, sponsorship_needed
        "us": "sponsorship_needed",  # Options: work_visa, citizen, sponsorship_needed
        "nigeria": "citizen",  # Options: citizen, work_permit, sponsorship_needed
    },

    # Work Authorization
    "work_authorization": {
        "uk": {
            "authorized": True,
            "hours_per_week": 20,  # Student visa restrictions
            "requires_sponsorship": False,
        },
        "us": {
            "authorized": False,
            "requires_sponsorship": True,
            "visa_type_seeking": "H1B",
        },
    },

    # Years of Experience
    "years_experience": {
        "total": 1,  # Total professional experience
        "data_science": 1,
        "machine_learning": 1,
        "python": 2,
        "relevant_field": 1,
    },

    # Skills Summary (for quick form filling)
    "skills": [
        "Python",
        "Machine Learning",
        "Data Science",
        "SQL",
        "Statistics",
        # Add your skills here
    ],

    # Preferences
    "job_preferences": {
        "job_types": ["Full-time", "Contract"],  # Options: Full-time, Part-time, Contract, Internship
        "work_models": ["On-site", "Remote", "Hybrid"],
        "willing_to_relocate": True,
        "notice_period": "Immediate",  # or "2 weeks", "1 month", etc.
    },

    # Salary Expectations (optional, be careful with this)
    "salary_expectations": {
        "uk": {
            "minimum": 30000,
            "currency": "GBP",
        },
        "us": {
            "minimum": 80000,
            "currency": "USD",
        },
    },

    # Additional Information (for text fields)
    "about_me": """
    Brief professional summary (2-3 sentences) about your background,
    skills, and what you're looking for. This will be used to fill
    'About Me' or 'Summary' fields in applications.
    """,

    # References (if needed)
    "has_references": True,
    "reference_available_on_request": True,
}

# Validation function
def validate_user_info():
    """Validate that required fields are filled"""
    required_fields = ["name", "email", "phone", "location"]
    for field in required_fields:
        if USER_INFO.get(field) in [None, "", "Your Full Name", "Your City, Country"]:
            raise ValueError(f"Please fill in the '{field}' field in config/user_info.py")
    return True

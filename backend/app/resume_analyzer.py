import re


def analyze_resume(resume_text, resume_skills):
    text = resume_text.lower()

    sections = {
        "summary": [
            "summary",
            "objective",
            "profile"
        ],
        "education": [
            "education",
            "academic"
        ],
        "experience": [
            "experience",
            "work experience",
            "internship"
        ],
        "projects": [
            "projects",
            "project"
        ],
        "skills": [
            "skills",
            "technical skills"
        ],
        "certifications": [
            "certifications",
            "certificates"
        ]
    }

    detected_sections = []

    for section, keywords in sections.items():

        for keyword in keywords:

            if keyword in text:
                detected_sections.append(section)
                break

    detected_sections = list(set(detected_sections))

    suggestions = []
    strengths = []

    # --------------------------------
    # Check important sections
    # --------------------------------

    important_sections = [
        "summary",
        "education",
        "experience",
        "projects",
        "skills"
    ]

    for section in important_sections:

        if section in detected_sections:

            strengths.append(
                f"Your resume contains a {section} section."
            )

        else:

            suggestions.append(
                f"Consider adding a {section} section."
            )

    # --------------------------------
    # Check number of skills
    # --------------------------------

    skill_count = len(resume_skills)

    if skill_count >= 10:

        strengths.append(
            "Your resume contains a good number of technical skills."
        )

    elif skill_count >= 5:

        suggestions.append(
            "Consider adding more relevant technical skills."
        )

    else:

        suggestions.append(
            "Your resume appears to contain very few technical skills."
        )

    # --------------------------------
    # Check resume length
    # --------------------------------

    word_count = len(
        re.findall(
            r"\b\w+\b",
            resume_text
        )
    )

    if word_count >= 300:

        strengths.append(
            "Your resume contains sufficient textual content."
        )

    else:

        suggestions.append(
            "Your resume may be too short. Add relevant projects, achievements, or experience."
        )

    # --------------------------------
    # Calculate score
    # --------------------------------

    section_score = (
        len(
            set(detected_sections)
            & set(important_sections)
        )
        / len(important_sections)
    ) * 60

    skill_score = min(
        skill_count / 10,
        1
    ) * 25

    content_score = min(
        word_count / 500,
        1
    ) * 15

    strength_score = (
        section_score
        + skill_score
        + content_score
    )

    strength_score = round(
        min(strength_score, 100),
        2
    )

    return {
        "strength_score": strength_score,
        "word_count": word_count,
        "skill_count": skill_count,
        "detected_sections": detected_sections,
        "strengths": strengths,
        "suggestions": suggestions
    }
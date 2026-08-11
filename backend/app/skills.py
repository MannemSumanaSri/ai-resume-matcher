# All supported skills are stored in their normalized form.
SKILLS = [
    "python",
    "java",
    "javascript",
    "typescript",

    "react",
    "node.js",
    "express",
    "fastapi",
    "flask",

    "html",
    "css",
    "tailwind",

    "mongodb",
    "mysql",
    "sql",
    "postgresql",

    "git",
    "github",
    "docker",
    "aws",
    "azure",

    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",

    "tensorflow",
    "pytorch",
    "scikit-learn",

    "rest api",
    "jwt",
]


# Different ways of writing the same skill.
SKILL_ALIASES = {
    "python": [
        "python",
        "python3"
    ],

    "javascript": [
        "javascript",
        "java script",
        "js"
    ],

    "typescript": [
        "typescript",
        "ts"
    ],

    "react": [
        "react",
        "reactjs",
        "react.js",
        "react js"
    ],

    "node.js": [
        "node",
        "nodejs",
        "node.js",
        "node js"
    ],

    "express": [
        "express",
        "expressjs",
        "express.js"
    ],

    "mongodb": [
        "mongodb",
        "mongo db",
        "mongo"
    ],

    "mysql": [
        "mysql",
        "my sql"
    ],

    "postgresql": [
        "postgresql",
        "postgres",
        "postgre sql"
    ],

    "scikit-learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn"
    ],

    "machine learning": [
        "machine learning",
        "machine-learning",
        "ml"
    ],

    "deep learning": [
        "deep learning",
        "deep-learning",
        "dl"
    ],

    "natural language processing": [
        "natural language processing",
        "natural-language processing",
        "nlp"
    ],

    "rest api": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "rest-api"
    ],

    "jwt": [
        "jwt",
        "json web token",
        "json web tokens"
    ],

    "git": [
        "git"
    ],

    "github": [
        "github",
        "git hub"
    ],

    "docker": [
        "docker",
        "docker container",
        "docker containers"
    ],

    "aws": [
        "aws",
        "amazon web services"
    ],

    "azure": [
        "azure",
        "microsoft azure"
    ],

    "html": [
        "html",
        "html5"
    ],

    "css": [
        "css",
        "css3"
    ],

    "tailwind": [
        "tailwind",
        "tailwind css"
    ],

    "tensorflow": [
        "tensorflow",
        "tensor flow"
    ],

    "pytorch": [
        "pytorch",
        "py torch"
    ]
}


def normalize_text(text):
    """
    Converts text to lowercase and removes
    unnecessary spaces.
    """

    text = text.lower()

    # Replace new lines and tabs with spaces
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")

    # Remove repeated spaces
    text = " ".join(text.split())

    return text


def extract_skills(text):
    """
    Finds skills in the given text and returns
    them in normalized form.
    """

    text = normalize_text(text)

    found_skills = []

    for normalized_skill, aliases in SKILL_ALIASES.items():

        for alias in aliases:

            if alias in text:
                found_skills.append(normalized_skill)

                # Once we find one alias,
                # no need to check other aliases.
                break

    return sorted(set(found_skills))


def compare_skills(resume_text, job_text):
    """
    Compares skills found in the resume
    with skills required by the job description.
    """

    resume_skills = set(
        extract_skills(resume_text)
    )

    job_skills = set(
        extract_skills(job_text)
    )

    matched_skills = resume_skills.intersection(
        job_skills
    )

    missing_skills = job_skills - resume_skills

    return {
        "resume_skills": sorted(resume_skills),
        "required_skills": sorted(job_skills),
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills)
    }
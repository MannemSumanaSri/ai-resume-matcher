# ============================================================
# AI RESUME MATCHER - COMPLETE SKILL GAP + OLLAMA RECOMMENDER
# ============================================================
#
# FIX:
# The old implementation could ONLY discover skills contained
# in KNOWN_SKILLS.
#
# This version:
#
#   Resume text
#        +
#   Job Description
#        +
#   Existing matcher skills
#        |
#        v
#   Ollama extracts ALL relevant skills from JD
#        |
#        v
#   Normalize + validate extracted skills
#        |
#        v
#   Compare against resume skills
#        |
#        v
#   COMPLETE MISSING SKILLS
#        |
#        v
#   Ollama generates recommendations
#        |
#        v
#   One recommendation for EVERY missing skill
#
# IMPORTANT:
# Ollama is now used for TWO separate tasks:
#
# 1. Skill discovery from the JD
# 2. Personalized recommendations
#
# This removes the limitation of having a small predefined
# KNOWN_SKILLS catalog.
#
# ============================================================

import json
import re
from typing import Dict, List, Optional, Set

import requests


# ============================================================
# OLLAMA CONFIGURATION
# ============================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

OLLAMA_MODEL = "qwen3.5:0.8b"

OLLAMA_TIMEOUT = 120


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    # Programming
    "java script": "javascript",
    "type script": "typescript",

    "cpp": "c++",
    "c plus plus": "c++",

    "c sharp": "c#",

    # Frontend
    "react.js": "react",
    "reactjs": "react",

    "nextjs": "next.js",

    "vue.js": "vue",
    "vuejs": "vue",

    "angular.js": "angular",
    "angularjs": "angular",

    "html5": "html",
    "css3": "css",

    # Backend
    "nodejs": "node.js",
    "node js": "node.js",

    "express.js": "express",
    "expressjs": "express",

    "fast api": "fastapi",

    "springboot": "spring boot",

    "spring framework": "spring",

    "dotnet": ".net",

    # Databases
    "postgres": "postgresql",
    "postgres db": "postgresql",
    "postgres database": "postgresql",

    "mysql database": "mysql",

    "mongo db": "mongodb",
    "mongodb database": "mongodb",

    # APIs
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "restful": "rest api",

    "graphql api": "graphql",

    # Cloud
    "amazon web services": "aws",
    "aws cloud": "aws",

    "aws ec2": "amazon ec2",
    "amazon ec2": "amazon ec2",

    "aws s3": "amazon s3",
    "amazon s3": "amazon s3",

    "aws lambda": "aws lambda",
    "amazon lambda": "aws lambda",

    "google cloud": "gcp",
    "google cloud platform": "gcp",

    "microsoft azure": "azure",

    # DevOps
    "docker containers": "docker",
    "docker containerization": "docker",

    "k8s": "kubernetes",

    "cicd": "ci/cd",
    "ci cd": "ci/cd",
    "ci-cd": "ci/cd",

    # Data
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",

    "ml": "machine learning",

    # Security
    "json web token": "jwt",
    "oauth2": "oauth",

    # Tools
    "git hub": "github",
    "git lab": "gitlab",

}


# ============================================================
# NORMALIZE SKILL
# ============================================================

def normalize_skill(skill: str) -> str:

    if skill is None:
        return ""

    value = str(skill).lower().strip()

    if not value:
        return ""

    value = re.sub(r"\s+", " ", value)

    value = value.strip(
        ".,;:!?()[]{}\"'"
    )

    return SKILL_ALIASES.get(
        value,
        value
    )


# ============================================================
# NORMALIZE SKILL LIST
# ============================================================

def _normalize_skill_list(
    skills: Optional[List[str]]
) -> List[str]:

    result = []

    if not skills:
        return result

    seen = set()

    for skill in skills:

        normalized = normalize_skill(skill)

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)

        result.append(normalized)

    return result


# ============================================================
# JSON EXTRACTION
# ============================================================

def _extract_json(text: str):

    if not text:
        return None

    text = str(text).strip()

    # Remove markdown fences
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # Direct JSON
    try:

        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # JSON array
    start = text.find("[")
    end = text.rfind("]")

    if (
        start != -1
        and end != -1
        and end > start
    ):

        candidate = text[
            start:end + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:
            pass

    # JSON object
    start = text.find("{")
    end = text.rfind("}")

    if (
        start != -1
        and end != -1
        and end > start
    ):

        candidate = text[
            start:end + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:
            pass

    return None


# ============================================================
# CALL OLLAMA HELPER
# ============================================================

def _ollama_generate(
    prompt: str,
    temperature: float = 0.1
) -> Optional[str]:

    payload = {

        "model":
            OLLAMA_MODEL,

        "prompt":
            prompt,

        "stream":
            False,

        "format":
            "json",

        "options": {

            "temperature":
                temperature,

            "top_p":
                0.8,

        }

    }

    try:

        response = requests.post(

            OLLAMA_URL,

            json=payload,

            timeout=OLLAMA_TIMEOUT

        )

        response.raise_for_status()

        data = response.json()

        output = data.get(
            "response",
            ""
        )

        if not output:
            return None

        return output

    except requests.exceptions.ConnectionError:

        print(
            "ERROR: Could not connect to Ollama."
        )

        return None

    except requests.exceptions.Timeout:

        print(
            "ERROR: Ollama request timed out."
        )

        return None

    except requests.exceptions.RequestException as exc:

        print(
            "ERROR: Ollama request failed:",
            str(exc)
        )

        return None

    except Exception as exc:

        print(
            "ERROR:",
            str(exc)
        )

        return None


# ============================================================
# ============================================================
# STEP 1 - AI JOB DESCRIPTION SKILL DISCOVERY
# ============================================================
#
# THIS IS THE IMPORTANT FIX.
#
# We no longer depend on:
#
#     KNOWN_SKILLS = {...}
#
# Instead Ollama reads the complete JD and extracts skills
# dynamically.
#
# Therefore if the JD contains:
#
# Redis
# Kafka
# Terraform
# Jenkins
# Kubernetes
# GraphQL
# Tailwind
# Prisma
# PostgreSQL
# FastAPI
# Azure
#
# they can all be discovered even if they were never placed
# in a predefined Python set.
#
# ============================================================

SKILL_DISCOVERY_PROMPT = """
You are a technical skill extraction engine.

Extract ALL meaningful skills, technologies, tools,
frameworks, programming languages, databases, cloud
platforms, DevOps technologies, security technologies,
libraries, APIs, testing technologies and technical
concepts explicitly required or preferred by the job
description.

IMPORTANT:

1. Read the ENTIRE job description.

2. Do NOT use a predefined skill list.

3. Discover skills dynamically from the text.

4. Include both common and uncommon technologies.

5. Include specific technologies.

6. Include frameworks and libraries.

7. Include databases.

8. Include cloud technologies.

9. Include DevOps tools.

10. Include testing technologies.

11. Include security technologies.

12. Include APIs and protocols when they are actual
technical requirements.

13. Include technical concepts when the JD explicitly
expects them as a skill.

14. Do NOT include generic soft skills such as:
    communication
    leadership
    teamwork
    punctuality
    adaptability

15. Do NOT include job titles.

16. Do NOT include company names.

17. Do NOT invent skills that are not present in the JD.

18. Preserve specific technology names.

19. If multiple technologies are mentioned separately,
return them separately.

20. Return ONLY JSON.

Expected format:

{
  "skills": [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Docker",
    "Kubernetes",
    "AWS",
    "Redis",
    "GraphQL"
  ]
}

JOB DESCRIPTION:

"""


def _discover_jd_skills_with_ai(
    job_description: str
) -> List[str]:

    if not job_description:
        return []

    prompt = (
        SKILL_DISCOVERY_PROMPT
        +
        str(job_description)
    )

    print(
        "\nDiscovering skills dynamically from JD..."
    )

    output = _ollama_generate(
        prompt,
        temperature=0.0
    )

    if not output:

        print(
            "AI skill discovery failed."
        )

        return []

    print(
        "\nAI JD SKILL EXTRACTION:"
    )

    print(
        output
    )

    parsed = _extract_json(
        output
    )

    if parsed is None:
        return []

    # Expected:
    #
    # {
    #   "skills": [...]
    # }

    if isinstance(
        parsed,
        dict
    ):

        skills = parsed.get(
            "skills",
            []
        )

    elif isinstance(
        parsed,
        list
    ):

        skills = parsed

    else:

        skills = []

    if not isinstance(
        skills,
        list
    ):

        return []

    cleaned = []

    seen = set()

    for skill in skills:

        if not isinstance(
            skill,
            str
        ):
            continue

        normalized = normalize_skill(
            skill
        )

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        cleaned.append(
            normalized
        )

    return cleaned


# ============================================================
# STEP 2 - FALLBACK TEXT SKILL DISCOVERY
# ============================================================
#
# AI discovery is primary.
#
# This fallback exists for situations where Ollama is
# unavailable.
#
# It contains common skills only and therefore is NOT the
# main discovery mechanism.
#
# ============================================================

FALLBACK_SKILLS = {

    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",

    "html",
    "css",
    "react",
    "next.js",
    "vue",
    "angular",

    "node.js",
    "express",
    "fastapi",
    "spring",
    "spring boot",
    ".net",

    "rest api",
    "graphql",

    "mongodb",
    "mysql",
    "postgresql",
    "sqlite",
    "redis",

    "aws",
    "azure",
    "gcp",

    "amazon ec2",
    "amazon s3",
    "aws lambda",

    "docker",
    "kubernetes",
    "jenkins",
    "github actions",
    "ci/cd",

    "git",
    "github",
    "gitlab",

    "pandas",
    "numpy",
    "scikit-learn",

    "machine learning",
    "deep learning",

    "jwt",
    "oauth",

    "kafka",
    "rabbitmq",

    "postman",

}


def _skill_present(
    skill: str,
    text: str
) -> bool:

    if not skill or not text:
        return False

    normalized_skill = normalize_skill(
        skill
    )

    normalized_text = str(
        text
    ).lower()

    aliases = [
        normalized_skill
    ]

    for alias, canonical in SKILL_ALIASES.items():

        if canonical == normalized_skill:

            aliases.append(
                alias
            )

    for alias in aliases:

        alias = str(
            alias
        ).lower().strip()

        if not alias:
            continue

        escaped = re.escape(
            alias
        )

        if re.search(
            rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
            normalized_text,
            flags=re.IGNORECASE
        ):

            return True

    return False


def _fallback_extract_job_skills(
    job_description: str
) -> List[str]:

    if not job_description:
        return []

    discovered = []

    ordered = sorted(
        FALLBACK_SKILLS,
        key=len,
        reverse=True
    )

    for skill in ordered:

        if _skill_present(
            skill,
            job_description
        ):

            normalized = normalize_skill(
                skill
            )

            if normalized not in discovered:

                discovered.append(
                    normalized
                )

    return discovered


# ============================================================
# STEP 3 - COMBINE AI + FALLBACK JD SKILLS
# ============================================================

def _extract_job_skills(
    job_description: str
) -> List[str]:

    if not job_description:
        return []

    # --------------------------------------------------------
    # Primary method: AI dynamic discovery
    # --------------------------------------------------------

    ai_skills = (
        _discover_jd_skills_with_ai(
            job_description
        )
    )

    # --------------------------------------------------------
    # Secondary method: deterministic fallback
    # --------------------------------------------------------

    fallback_skills = (
        _fallback_extract_job_skills(
            job_description
        )
    )

    result = []

    seen = set()

    # AI skills first
    for skill in ai_skills:

        normalized = normalize_skill(
            skill
        )

        if (
            normalized
            and normalized not in seen
        ):

            seen.add(
                normalized
            )

            result.append(
                normalized
            )

    # Fallback skills
    for skill in fallback_skills:

        normalized = normalize_skill(
            skill
        )

        if (
            normalized
            and normalized not in seen
        ):

            seen.add(
                normalized
            )

            result.append(
                normalized
            )

    return result


# ============================================================
# STEP 4 - BUILD COMPLETE MISSING SKILLS
# ============================================================

def _build_complete_missing_skills(
    missing_skills: Optional[List[str]],
    resume_skills: Optional[List[str]],
    job_description: str
) -> List[str]:

    normalized_missing = (
        _normalize_skill_list(
            missing_skills
        )
    )

    normalized_resume = set(
        _normalize_skill_list(
            resume_skills
        )
    )

    # --------------------------------------------------------
    # Dynamically discover ALL JD skills
    # --------------------------------------------------------

    job_skills = (
        _extract_job_skills(
            job_description
        )
    )

    complete_missing = []

    # --------------------------------------------------------
    # Existing matcher missing skills
    # --------------------------------------------------------

    for skill in normalized_missing:

        if skill in normalized_resume:
            continue

        if skill not in complete_missing:

            complete_missing.append(
                skill
            )

    # --------------------------------------------------------
    # AI-discovered JD skills
    # --------------------------------------------------------

    for skill in job_skills:

        if skill in normalized_resume:
            continue

        if skill in complete_missing:
            continue

        complete_missing.append(
            skill
        )

    return complete_missing


# ============================================================
# ============================================================
# STEP 5 - RECOMMENDATION PROMPT
# ============================================================
#
# Ollama now receives the COMPLETE dynamically discovered
# missing skill set.
#
# ============================================================

RECOMMENDATION_SYSTEM_PROMPT = """
You are an AI career recommendation engine.

Your job is to generate personalized learning
recommendations for ALL technical skills that are required
or preferred by the job description but are missing from
the candidate's resume.

The application has already created a complete
"missing_skills" list.

IMPORTANT RULES:

1. You MUST recommend every skill in missing_skills.

2. Do NOT recommend skills outside missing_skills.

3. Do NOT recommend skills already present in resume_skills.

4. Do NOT invent candidate experience.

5. Do NOT claim the candidate knows a missing skill.

6. Use the job description to explain why the skill matters.

7. Use the candidate's existing skills to personalize the
   learning path.

8. Every missing skill must receive exactly one
   recommendation.

9. Return ONLY JSON.

10. Return a JSON array.

For every skill provide:

skill
recommendation_type
category
reason
related_skills
topics
learning_path
priority

Priority:

high:
Directly important to the job.

medium:
Useful for the job but less critical.

low:
Useful long-term.

Expected format:

[
  {
    "skill": "terraform",
    "recommendation_type": "missing_skill",
    "category": "DevOps",
    "reason": "Terraform is relevant because the role requires infrastructure automation.",
    "related_skills": ["AWS", "Docker"],
    "topics": [
      "Terraform fundamentals",
      "Providers",
      "Resources",
      "State management"
    ],
    "learning_path": [
      "Learn Terraform fundamentals",
      "Create AWS infrastructure using Terraform",
      "Build a small infrastructure-as-code project"
    ],
    "priority": "high"
  }
]
"""


# ============================================================
# CALL OLLAMA FOR RECOMMENDATIONS
# ============================================================

def _call_ollama(
    missing_skills: List[str],
    resume_skills: Optional[List[str]],
    job_description: str
) -> Optional[List[Dict]]:

    normalized_missing = (
        _normalize_skill_list(
            missing_skills
        )
    )

    if not normalized_missing:
        return []

    normalized_resume = (
        _normalize_skill_list(
            resume_skills
        )
    )

    candidate_data = {

        "missing_skills":
            normalized_missing,

        "resume_skills":
            normalized_resume,

        "job_description":
            job_description or "",

    }

    prompt = (

        RECOMMENDATION_SYSTEM_PROMPT

        + "\n\nCANDIDATE DATA:\n"

        + json.dumps(
            candidate_data,
            indent=2,
            ensure_ascii=False
        )

        + "\n\n"

        + "IMPORTANT: You MUST return one "
          "recommendation for EVERY skill in "
          "missing_skills."

    )

    print(
        "\nGenerating personalized recommendations..."
    )

    output = _ollama_generate(
        prompt,
        temperature=0.2
    )

    if not output:

        return None

    print(
        "\nOLLAMA RECOMMENDATION RESPONSE:"
    )

    print(
        output
    )

    parsed = _extract_json(
        output
    )

    if parsed is None:
        return None

    # Object wrapper
    if isinstance(
        parsed,
        dict
    ):

        if isinstance(
            parsed.get(
                "recommendations"
            ),
            list
        ):

            parsed = parsed[
                "recommendations"
            ]

        elif "skill" in parsed:

            parsed = [
                parsed
            ]

        else:

            parsed = []

    if not isinstance(
        parsed,
        list
    ):

        return None

    return parsed


# ============================================================
# VALIDATE AI RECOMMENDATION
# ============================================================

def _validate_recommendation(
    recommendation: Dict,
    allowed_skills: Set[str]
) -> Optional[Dict]:

    if not isinstance(
        recommendation,
        dict
    ):

        return None

    skill = normalize_skill(
        recommendation.get(
            "skill",
            ""
        )
    )

    if not skill:
        return None

    # --------------------------------------------------------
    # STRICT VALIDATION
    # --------------------------------------------------------

    if skill not in allowed_skills:

        return None

    category = recommendation.get(
        "category",
        "Technical Skill"
    )

    if not isinstance(
        category,
        str
    ):

        category = "Technical Skill"

    category = category.strip()

    if not category:

        category = "Technical Skill"

    reason = recommendation.get(
        "reason",
        ""
    )

    if not isinstance(
        reason,
        str
    ):

        reason = str(
            reason
        )

    reason = reason.strip()

    related_skills = recommendation.get(
        "related_skills",
        []
    )

    if not isinstance(
        related_skills,
        list
    ):

        related_skills = []

    cleaned_related = []

    seen_related = set()

    for item in related_skills:

        if not isinstance(
            item,
            str
        ):
            continue

        value = item.strip()

        if not value:
            continue

        normalized_related = normalize_skill(
            value
        )

        if normalized_related == skill:
            continue

        if value.lower() in seen_related:
            continue

        seen_related.add(
            value.lower()
        )

        cleaned_related.append(
            value
        )

    topics = recommendation.get(
        "topics",
        []
    )

    if not isinstance(
        topics,
        list
    ):

        topics = []

    cleaned_topics = []

    seen_topics = set()

    for item in topics:

        if not isinstance(
            item,
            str
        ):
            continue

        value = item.strip()

        if not value:
            continue

        if value.lower() in seen_topics:
            continue

        seen_topics.add(
            value.lower()
        )

        cleaned_topics.append(
            value
        )

    learning_path = recommendation.get(
        "learning_path",
        []
    )

    if not isinstance(
        learning_path,
        list
    ):

        learning_path = []

    cleaned_learning_path = []

    for item in learning_path:

        if not isinstance(
            item,
            str
        ):
            continue

        value = item.strip()

        if value:

            cleaned_learning_path.append(
                value
            )

    priority = str(
        recommendation.get(
            "priority",
            "medium"
        )
    ).lower().strip()

    if priority not in {
        "high",
        "medium",
        "low"
    }:

        priority = "medium"

    return {

        "skill":
            skill,

        "recommendation_type":
            "missing_skill",

        "category":
            category,

        "reason":
            reason,

        "related_skills":
            cleaned_related,

        "topics":
            cleaned_topics,

        "learning_path":
            cleaned_learning_path,

        "priority":
            priority,

        "source":
            "ollama",

        "ai_generated":
            True,

    }


# ============================================================
# FALLBACK CATEGORY
# ============================================================

def _get_category(
    skill: str
) -> str:

    skill = normalize_skill(
        skill
    )

    cloud = {

        "aws",
        "azure",
        "gcp",
        "amazon ec2",
        "amazon s3",
        "aws lambda",

    }

    devops = {

        "docker",
        "kubernetes",
        "jenkins",
        "github actions",
        "ci/cd",
        "terraform",

    }

    frontend = {

        "react",
        "next.js",
        "vue",
        "angular",
        "html",
        "css",
        "tailwind css",

    }

    backend = {

        "node.js",
        "express",
        "fastapi",
        "spring",
        "spring boot",
        ".net",
        "asp.net",

    }

    database = {

        "mongodb",
        "mysql",
        "postgresql",
        "sqlite",
        "redis",

    }

    api = {

        "rest api",
        "graphql",

    }

    testing = {

        "pytest",
        "jest",
        "vitest",
        "junit",
        "selenium",

    }

    security = {

        "jwt",
        "oauth",
        "oauth2",

    }

    data = {

        "pandas",
        "numpy",
        "scikit-learn",
        "machine learning",
        "deep learning",

    }

    messaging = {

        "kafka",
        "rabbitmq",

    }

    if skill in cloud:
        return "Cloud"

    if skill in devops:
        return "DevOps"

    if skill in frontend:
        return "Frontend"

    if skill in backend:
        return "Backend"

    if skill in database:
        return "Database"

    if skill in api:
        return "API"

    if skill in testing:
        return "Testing"

    if skill in security:
        return "Security"

    if skill in data:
        return "Data / AI"

    if skill in messaging:
        return "Messaging"

    return "Technical Skill"


# ============================================================
# FALLBACK RECOMMENDATION
# ============================================================

def _fallback_recommendation(
    skill: str,
    job_description: str = ""
) -> Dict:

    normalized = normalize_skill(
        skill
    )

    return {

        "skill":
            normalized,

        "recommendation_type":
            "missing_skill",

        "category":
            _get_category(
                normalized
            ),

        "reason":
            (
                f"{normalized} was identified as a "
                "technical skill required or preferred "
                "by the job description but was not "
                "detected in the candidate's resume."
            ),

        "related_skills":
            [],

        "topics": [

            f"{normalized} fundamentals",

            f"{normalized} practical usage",

            f"{normalized} project implementation",

        ],

        "learning_path": [

            f"Learn {normalized} fundamentals",

            f"Practice {normalized} with small examples",

            f"Build a practical project using {normalized}",

        ],

        "priority":
            "medium",

        "source":
            "fallback",

        "ai_generated":
            False,

    }


# ============================================================
# MERGE AI + FALLBACK
# ============================================================

def _merge_recommendations(
    missing_skills: List[str],
    ai_recommendations: Optional[List[Dict]],
    job_description: str = ""
) -> List[Dict]:

    normalized_missing = (
        _normalize_skill_list(
            missing_skills
        )
    )

    allowed = set(
        normalized_missing
    )

    ai_map = {}

    # --------------------------------------------------------
    # Validate AI recommendations
    # --------------------------------------------------------

    for item in (
        ai_recommendations or []
    ):

        clean = _validate_recommendation(
            item,
            allowed
        )

        if clean is None:
            continue

        skill = clean[
            "skill"
        ]

        if skill not in ai_map:

            ai_map[
                skill
            ] = clean

    # --------------------------------------------------------
    # GUARANTEE every missing skill gets a result
    # --------------------------------------------------------

    result = []

    for skill in normalized_missing:

        if skill in ai_map:

            result.append(
                ai_map[
                    skill
                ]
            )

        else:

            result.append(
                _fallback_recommendation(
                    skill,
                    job_description
                )
            )

    # --------------------------------------------------------
    # Sort by priority
    # --------------------------------------------------------

    priority_order = {

        "high":
            0,

        "medium":
            1,

        "low":
            2,

    }

    result.sort(

        key=lambda item:
        priority_order.get(

            item.get(
                "priority",
                "medium"
            ),

            1

        )

    )

    return result


# ============================================================
# MAIN PUBLIC FUNCTION
# ============================================================

def generate_recommendations(
    missing_skills: List[str],
    resume_skills: Optional[List[str]] = None,
    job_description: str = ""
) -> List[Dict]:

    # --------------------------------------------------------
    # If there is no JD and no matcher result, nothing to do
    # --------------------------------------------------------

    if (
        not missing_skills
        and
        not job_description
    ):

        return []

    print(
        "\n============================================"
    )

    print(
        "DYNAMIC SKILL GAP ANALYSIS"
    )

    print(
        "============================================"
    )

    # --------------------------------------------------------
    # Normalize resume
    # --------------------------------------------------------

    normalized_resume = (
        _normalize_skill_list(
            resume_skills
        )
    )

    # --------------------------------------------------------
    # Dynamically discover skills from JD
    # --------------------------------------------------------

    discovered_jd_skills = (
        _extract_job_skills(
            job_description
        )
    )

    print(
        "\nSkills dynamically discovered from JD:"
    )

    print(
        discovered_jd_skills
    )

    # --------------------------------------------------------
    # Build COMPLETE missing list
    # --------------------------------------------------------

    complete_missing = (
        _build_complete_missing_skills(

            missing_skills=
                missing_skills,

            resume_skills=
                normalized_resume,

            job_description=
                job_description,

        )
    )

    print(
        "\nOriginal matcher missing skills:"
    )

    print(
        _normalize_skill_list(
            missing_skills
        )
    )

    print(
        "\nResume skills:"
    )

    print(
        normalized_resume
    )

    print(
        "\nCOMPLETE MISSING SKILLS:"
    )

    print(
        complete_missing
    )

    # --------------------------------------------------------
    # Nothing missing
    # --------------------------------------------------------

    if not complete_missing:

        print(
            "\nNo missing technical skills found."
        )

        return []

    # --------------------------------------------------------
    # Generate AI recommendations
    # --------------------------------------------------------

    ai_recommendations = (
        _call_ollama(

            missing_skills=
                complete_missing,

            resume_skills=
                normalized_resume,

            job_description=
                job_description,

        )
    )

    # --------------------------------------------------------
    # Merge with deterministic fallback
    # --------------------------------------------------------

    final_recommendations = (
        _merge_recommendations(

            missing_skills=
                complete_missing,

            ai_recommendations=
                ai_recommendations,

            job_description=
                job_description,

        )
    )

    print(
        "\n============================================"
    )

    print(
        "FINAL RECOMMENDATIONS"
    )

    print(
        "============================================"
    )

    print(
        "Total missing skills:",
        len(complete_missing)
    )

    print(
        "Total recommendations:",
        len(final_recommendations)
    )

    return final_recommendations


# ============================================================
# SINGLE SKILL API
# ============================================================

def generate_recommendation_for_skill(
    skill: str,
    resume_skills: Optional[List[str]] = None,
    job_description: str = ""
) -> Dict:

    normalized = normalize_skill(
        skill
    )

    if not normalized:

        return _fallback_recommendation(
            skill,
            job_description
        )

    recommendations = (
        generate_recommendations(

            missing_skills=[
                normalized
            ],

            resume_skills=
                resume_skills,

            job_description=
                job_description,

        )
    )

    for recommendation in recommendations:

        if normalize_skill(
            recommendation.get(
                "skill",
                ""
            )
        ) == normalized:

            return recommendation

    return _fallback_recommendation(
        normalized,
        job_description
    )


# ============================================================
# DEBUG
# ============================================================

def debug_skill_gap(
    missing_skills: Optional[List[str]],
    resume_skills: Optional[List[str]],
    job_description: str
) -> Dict:

    normalized_missing = (
        _normalize_skill_list(
            missing_skills
        )
    )

    normalized_resume = (
        _normalize_skill_list(
            resume_skills
        )
    )

    discovered_jd_skills = (
        _extract_job_skills(
            job_description
        )
    )

    complete_missing = (
        _build_complete_missing_skills(

            missing_skills=
                missing_skills,

            resume_skills=
                resume_skills,

            job_description=
                job_description,

        )
    )

    return {

        "original_missing_skills":
            normalized_missing,

        "resume_skills":
            normalized_resume,

        "job_description_skills":
            discovered_jd_skills,

        "complete_missing_skills":
            complete_missing,

        "missing_skill_count":
            len(
                complete_missing
            ),

    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    import pprint

    resume_skills = [

        "Python",
        "JavaScript",
        "React",
        "Node.js",
        "Express",
        "MongoDB",
        "REST API",
        "Git",
        "GitHub",

    ]

    # Imagine matcher only detected two.
    missing_skills = [

        "AWS",
        "Docker",

    ]

    # Notice that the JD contains MANY additional skills
    # that are not in the original missing_skills list.

    job_description = """

    We are looking for a Full Stack Developer.

    Requirements:

    JavaScript
    TypeScript
    React
    Node.js
    Express.js
    MongoDB
    PostgreSQL
    REST APIs
    GraphQL
    Redis
    Kafka
    AWS
    Docker
    Kubernetes
    Terraform
    Jenkins
    GitHub Actions
    Tailwind CSS
    Jest
    OAuth
    JWT

    The candidate should build scalable web applications,
    develop secure APIs, work with relational and NoSQL
    databases, implement automated testing, and deploy
    applications using cloud and container technologies.

    """

    print(
        "\n============================================"
    )

    print(
        "TESTING DYNAMIC AI SKILL DISCOVERY"
    )

    print(
        "============================================"
    )

    # --------------------------------------------------------
    # Debug
    # --------------------------------------------------------

    debug_result = debug_skill_gap(

        missing_skills=
            missing_skills,

        resume_skills=
            resume_skills,

        job_description=
            job_description,

    )

    pprint.pprint(
        debug_result
    )

    # --------------------------------------------------------
    # Generate recommendations
    # --------------------------------------------------------

    recommendations = (
        generate_recommendations(

            missing_skills=
                missing_skills,

            resume_skills=
                resume_skills,

            job_description=
                job_description,

        )
    )

    print(
        "\nFINAL RESULTS:"
    )

    pprint.pprint(
        recommendations
    )
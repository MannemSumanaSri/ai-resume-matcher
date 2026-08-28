import json
import os
import re
from typing import Dict, List, Optional

import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434/api/generate",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3.5:0.8b",
)

OLLAMA_TIMEOUT = int(
    os.getenv(
        "OLLAMA_TIMEOUT",
        "120",
    )
)


def normalize_skill(skill: str) -> str:

    if not skill:
        return ""

    value = str(skill).lower().strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    aliases = {
        "react.js": "react",
        "reactjs": "react",
        "nodejs": "node.js",
        "node js": "node.js",
        "express.js": "express",
        "expressjs": "express",
        "postgres": "postgresql",
        "restful api": "rest api",
        "restful apis": "rest api",
        "rest apis": "rest api",
        "cicd": "ci/cd",
        "ci cd": "ci/cd",
        "ec2": "amazon ec2",
        "aws ec2": "amazon ec2",
        "amazon ec2": "amazon ec2",
        "s3": "amazon s3",
        "aws s3": "amazon s3",
        "amazon s3": "amazon s3",
        "lambda": "aws lambda",
        "aws lambda": "aws lambda",
        "github action": "github actions",
        "github actions": "github actions",
    }

    return aliases.get(
        value,
        value,
    )


def infer_category(skill: str) -> str:

    skill = normalize_skill(skill)

    categories = {
        "aws": "Cloud",
        "amazon ec2": "Cloud",
        "amazon s3": "Cloud",
        "aws lambda": "Cloud",
        "azure": "Cloud",
        "gcp": "Cloud",
        "docker": "DevOps",
        "kubernetes": "DevOps",
        "ci/cd": "DevOps",
        "github actions": "DevOps",
        "python": "Programming",
        "javascript": "Programming",
        "typescript": "Programming",
        "react": "Frontend",
        "angular": "Frontend",
        "node.js": "Backend",
        "express": "Backend",
        "fastapi": "Backend",
        "rest api": "Backend",
        "graphql": "API Development",
        "mongodb": "Database",
        "redis": "Database",
        "postgresql": "Database",
        "mysql": "Database",
        "sql": "Database",
        "git": "Developer Tools",
        "github": "Developer Tools",
        "authentication": "Security",
        "authorization": "Security",
        "oauth": "Security",
    }

    return categories.get(
        skill,
        "Technical Skill",
    )


def _clean_string_list(
    value,
) -> List[str]:

    if not isinstance(
        value,
        list,
    ):
        return []

    result = []

    for item in value:

        if item is None:
            continue

        text = str(
            item
        ).strip()

        if text:
            result.append(
                text
            )

    return result


def _extract_json(
    text: str,
) -> Optional[Dict]:

    if not text:
        return None

    text = text.strip()

    try:

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            dict,
        ):
            return parsed

    except Exception:
        pass

    cleaned = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"```\s*",
        "",
        cleaned,
    ).strip()

    try:

        parsed = json.loads(
            cleaned
        )

        if isinstance(
            parsed,
            dict,
        ):
            return parsed

    except Exception:
        pass

    start = cleaned.find(
        "{"
    )

    end = cleaned.rfind(
        "}"
    )

    if start != -1 and end > start:

        candidate = cleaned[
            start:end + 1
        ]

        try:

            parsed = json.loads(
                candidate
            )

            if isinstance(
                parsed,
                dict,
            ):
                return parsed

        except Exception:
            pass

    return None


def _call_ollama(
    prompt: str,
) -> Optional[str]:

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "num_predict": 800,
        },
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        print("OLLAMA RESPONSE RECEIVED")
        print("Ollama response keys:", list(data.keys()))

        text = data.get("response")

        if text:
            return str(text).strip()

        thinking = data.get("thinking")

        if thinking:
            print(
                "Ollama produced thinking but no final response."
            )
            print(
                "This usually means the model exhausted "
                "its generation limit."
            )

        print(
            "Ollama returned no final response."
        )

        print(
            "Full Ollama response:",
            data
        )

        return None

    except requests.exceptions.ConnectionError:

        print(
            "Could not connect to Ollama at:",
            OLLAMA_URL
        )

        print(
            "Make sure Ollama is running."
        )

        return None

    except requests.exceptions.Timeout:

        print(
            "Ollama request timed out."
        )

        return None

    except Exception as exc:

        print(
            "Ollama request failed:",
            exc
        )

        return None


def _build_prompt(
    skill: str,
    resume_skills: Optional[List[str]],
    job_description: str,
) -> str:

    normalized_skill = normalize_skill(
        skill
    )

    resume = [
        normalize_skill(item)
        for item in (
            resume_skills
            or []
        )
        if normalize_skill(item)
    ]

    jd = (
        job_description
        or ""
    ).strip()

    if len(jd) > 5000:
        jd = jd[:5000]

    return f"""
You are an AI career recommendation engine.

Generate ONE personalized learning recommendation.

The candidate is missing this skill:

{normalized_skill}

Candidate's existing skills:

{json.dumps(resume, ensure_ascii=False)}

Job description:

{jd}

Rules:

1. Recommend ONLY the missing skill: {normalized_skill}
2. Do not add other missing skills.
3. Personalize the recommendation using the candidate's existing skills.
4. Explain why this skill matters for this job.
5. Give practical topics.
6. Give a short ordered learning path.
7. Keep every learning path item short.
8. Return ONLY valid JSON.
9. Do not use markdown.
10. Do not include explanations outside JSON.

Return exactly this JSON structure:

{{
  "skill": "{normalized_skill}",
  "recommendation_type": "missing_skill",
  "category": "string",
  "reason": "string",
  "related_skills": ["string"],
  "topics": ["string", "string", "string"],
  "learning_path": ["string", "string", "string", "string"],
  "priority": "high"
}}
""".strip()


def _validate_ai_result(
    data: Dict,
    expected_skill: str,
) -> Optional[Dict]:

    if not isinstance(
        data,
        dict,
    ):
        return None

    expected = normalize_skill(
        expected_skill
    )

    returned_skill = normalize_skill(
        data.get(
            "skill",
            "",
        )
    )

    if returned_skill != expected:

        print(
            "Ollama returned unexpected skill:",
            returned_skill,
            "expected:",
            expected,
        )

        return None

    category = str(
        data.get(
            "category",
            "",
        )
    ).strip()

    if not category:
        category = infer_category(
            expected
        )

    reason = str(
        data.get(
            "reason",
            "",
        )
    ).strip()

    if not reason:
        reason = (
            f"{expected} is required by the job description "
            "but was not detected in the resume."
        )

    related_skills = _clean_string_list(
        data.get(
            "related_skills",
            [],
        )
    )

    topics = _clean_string_list(
        data.get(
            "topics",
            [],
        )
    )

    learning_path = _clean_string_list(
        data.get(
            "learning_path",
            [],
        )
    )

    priority = str(
        data.get(
            "priority",
            "medium",
        )
    ).lower().strip()

    if priority not in {
        "high",
        "medium",
        "low",
    }:
        priority = "medium"

    return {
        "skill": expected,
        "recommendation_type": "missing_skill",
        "category": category,
        "reason": reason,
        "related_skills": related_skills,
        "topics": topics,
        "learning_path": learning_path,
        "priority": priority,
        "source": "ollama",
        "ai_generated": True,
    }


def generate_recommendation_for_skill(
    skill: str,
    resume_skills: Optional[List[str]] = None,
    job_description: str = "",
) -> Optional[Dict]:

    normalized = normalize_skill(
        skill
    )

    if not normalized:
        return None

    prompt = _build_prompt(
        skill=normalized,
        resume_skills=resume_skills,
        job_description=job_description,
    )

    print(
        f"Generating AI recommendation using Ollama model: "
        f"{OLLAMA_MODEL} for skill: {normalized}"
    )

    raw_response = _call_ollama(
        prompt
    )

    if not raw_response:
        return None

    parsed = _extract_json(
        raw_response
    )

    if parsed is None:

        print(
            "Ollama returned invalid JSON:"
        )

        print(
            raw_response
        )

        return None

    validated = _validate_ai_result(
        parsed,
        normalized,
    )

    if validated is None:
        return None

    return validated


def generate_ai_recommendations(
    missing_skills: List[str],
    resume_skills: Optional[List[str]] = None,
    job_description: str = "",
) -> Optional[List[Dict]]:

    if not missing_skills:
        return []

    normalized_missing = []

    for skill in missing_skills:

        normalized = normalize_skill(
            skill
        )

        if (
            normalized
            and
            normalized not in normalized_missing
        ):
            normalized_missing.append(
                normalized
            )

    if not normalized_missing:
        return []

    recommendations = []

    for skill in normalized_missing:

        recommendation = (
            generate_recommendation_for_skill(
                skill=skill,
                resume_skills=resume_skills,
                job_description=job_description,
            )
        )

        if recommendation is not None:
            recommendations.append(
                recommendation
            )

    if not recommendations:
        return None

    return recommendations


def generate_recommendations(
    missing_skills: List[str],
    resume_skills: Optional[List[str]] = None,
    job_description: str = "",
) -> List[Dict]:

    if not missing_skills:
        return []

    ai_recommendations = (
        generate_ai_recommendations(
            missing_skills=missing_skills,
            resume_skills=resume_skills,
            job_description=job_description,
        )
    )

    if ai_recommendations is None:

        print(
            "Ollama AI recommendations could not be generated."
        )

        return []

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    ai_recommendations.sort(
        key=lambda item:
            priority_order.get(
                item.get(
                    "priority",
                    "medium",
                ),
                1,
            )
    )

    return ai_recommendations


if __name__ == "__main__":

    import pprint

    missing = [
        "docker",
        "kubernetes",
        "redis",
    ]

    resume = [
        "python",
        "javascript",
        "react",
        "node.js",
        "express",
        "mongodb",
        "git",
        "github",
    ]

    jd = """
    We are looking for a Full Stack Developer.

    Required skills include JavaScript, Node.js, Express,
    MongoDB, Docker, Kubernetes and Redis.

    The candidate should be able to build scalable backend
    applications, containerize applications using Docker,
    deploy applications using Kubernetes and use Redis
    for caching and performance optimization.
    """

    result = generate_recommendations(
        missing_skills=missing,
        resume_skills=resume,
        job_description=jd,
    )

    pprint.pprint(
        result,
        sort_dicts=False,
    )
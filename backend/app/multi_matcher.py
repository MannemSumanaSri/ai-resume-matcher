from typing import List

from app.matcher import calculate_similarity
from app.semantic_matcher import calculate_semantic_similarity
from app.skills import compare_skills


def match_multiple_jobs(resume_text: str, jobs: List[dict]):
    results = []

    for index, job in enumerate(jobs):

        job_title = job.get("title", f"Job {index + 1}")
        job_description = job.get("description", "")

        if not job_description.strip():
            continue

        # TF-IDF score
        tfidf_score = calculate_similarity(
            resume_text,
            job_description
        )

        # Semantic score
        try:
            semantic_score = calculate_semantic_similarity(
                resume_text,
                job_description
            )
        except Exception:
            semantic_score = 0

        # Skill matching
        skills = compare_skills(
            resume_text,
            job_description
        )

        matched_count = len(skills["matched_skills"])
        required_count = len(skills["required_skills"])

        if required_count > 0:
            skill_match_score = (
                matched_count / required_count
            ) * 100
        else:
            skill_match_score = 0

        # Final score
        final_score = (
            tfidf_score * 0.20
            + semantic_score * 0.40
            + skill_match_score * 0.40
        )

        results.append({
            "title": job_title,
            "tfidf_score": round(tfidf_score, 2),
            "semantic_score": round(semantic_score, 2),
            "skill_match_score": round(
                skill_match_score, 2
            ),
            "final_match_score": round(
                final_score, 2
            ),
            "matched_skills": skills[
                "matched_skills"
            ],
            "missing_skills": skills[
                "missing_skills"
            ]
        })

    # Highest score first
    results.sort(
        key=lambda x: x["final_match_score"],
        reverse=True
    )

    # Add ranking
    for rank, result in enumerate(
        results,
        start=1
    ):
        result["rank"] = rank

    return results
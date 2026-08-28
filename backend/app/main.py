import json
from functools import lru_cache
from typing import List

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from app.pdf_reader import extract_text_from_pdf
from app.matcher import calculate_similarity
from app.skills import compare_skills
from app.ai_recommendation import generate_recommendations
from app.resume_analyzer import analyze_resume
from app.experience_matcher import match_experience
from app.scoring import (
    calculate_detailed_score,
    calculate_score_from_analysis,
)


MODEL_NAME = "all-MiniLM-L6-v2"
MAX_TEXT_LENGTH = 12000


@lru_cache(maxsize=1)
def get_semantic_model():
    model = SentenceTransformer(MODEL_NAME)

    try:
        model.eval()
    except Exception:
        pass

    return model


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = str(text).strip()

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return text


def calculate_semantic_score(
    resume_text: str,
    job_description: str
) -> float:

    resume_text = clean_text(resume_text)
    job_description = clean_text(job_description)

    if not resume_text or not job_description:
        raise ValueError(
            "Resume text or job description is empty."
        )

    model = get_semantic_model()

    embeddings = model.encode(
        [resume_text, job_description],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    resume_embedding = embeddings[0]
    job_embedding = embeddings[1]

    similarity = float(
        np.dot(
            resume_embedding,
            job_embedding
        )
    )

    similarity = max(
        0.0,
        min(
            1.0,
            similarity
        )
    )

    return round(
        similarity * 100,
        2
    )


def calculate_multiple_semantic_scores(
    resume_text: str,
    job_descriptions: List[str]
) -> List[float]:

    resume_text = clean_text(resume_text)

    if not resume_text:
        raise ValueError(
            "Resume text is empty."
        )

    valid_jobs = [
        clean_text(job)
        for job in job_descriptions
        if clean_text(job)
    ]

    if not valid_jobs:
        raise ValueError(
            "No valid job descriptions were provided."
        )

    model = get_semantic_model()

    texts = [
        resume_text,
        *valid_jobs
    ]

    embeddings = model.encode(
        texts,
        batch_size=min(
            16,
            len(texts)
        ),
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    resume_embedding = embeddings[0]

    job_embeddings = embeddings[1:]

    similarities = np.dot(
        job_embeddings,
        resume_embedding
    )

    return [
        round(
            max(
                0.0,
                min(
                    1.0,
                    float(score)
                )
            ) * 100,
            2
        )
        for score in similarities
    ]


app = FastAPI(
    title="AI Resume & Job Matcher",
    description=(
        "AI-powered resume and job description "
        "matching system with skill recommendations."
    ),
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "AI Resume Matcher API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "semantic_model": MODEL_NAME
    }


def calculate_skill_match_score(
    required_skills,
    matched_skills
):
    if not required_skills:
        return 100.0

    score = (
        len(matched_skills)
        /
        len(required_skills)
    ) * 100

    return round(
        max(
            0.0,
            min(
                100.0,
                score
            )
        ),
        2
    )


def calculate_final_score(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_score=None,
    has_experience_requirements=False
):
    result = calculate_detailed_score(
        tfidf_score=tfidf_score,
        semantic_score=semantic_score,
        skill_match_score=skill_match_score,
        experience_score=experience_score,
        has_experience_requirements=(
            has_experience_requirements
        )
    )

    return result["final_match_score"]


def calculate_complete_score(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_analysis
):
    return calculate_score_from_analysis(
        tfidf_score=tfidf_score,
        semantic_score=semantic_score,
        skill_match_score=skill_match_score,
        experience_analysis=experience_analysis
    )


def get_skill_recommendations(
    missing_skills,
    resume_skills,
    job_description
):
    try:
        recommendations = generate_recommendations(
            missing_skills=missing_skills,
            resume_skills=resume_skills,
            job_description=job_description
        )

        if recommendations is None:
            return []

        return recommendations

    except Exception as e:
        print(
            "Recommendation error:",
            str(e)
        )

        return []


def analyze_match(
    resume_text,
    job_description
):

    tfidf_score = calculate_similarity(
        resume_text,
        job_description
    )

    skills = compare_skills(
        resume_text,
        job_description
    )

    resume_skills = skills.get(
        "resume_skills",
        []
    )

    required_skills = skills.get(
        "required_skills",
        []
    )

    matched_skills = skills.get(
        "matched_skills",
        []
    )

    missing_skills = skills.get(
        "missing_skills",
        []
    )

    skill_match_score = calculate_skill_match_score(
        required_skills,
        matched_skills
    )

    semantic_score = calculate_semantic_score(
        resume_text,
        job_description
    )

    experience_analysis = match_experience(
        resume_text,
        job_description
    )

    score_result = calculate_complete_score(
        tfidf_score=tfidf_score,
        semantic_score=semantic_score,
        skill_match_score=skill_match_score,
        experience_analysis=experience_analysis
    )

    recommendations = get_skill_recommendations(
        missing_skills=missing_skills,
        resume_skills=resume_skills,
        job_description=job_description
    )

    resume_analysis = analyze_resume(
        resume_text,
        resume_skills
    )

    return {
        "tfidf_score": round(
            float(tfidf_score),
            2
        ),

        "semantic_score": round(
            float(semantic_score),
            2
        ),

        "skill_match_score": round(
            float(skill_match_score),
            2
        ),

        "experience_score": score_result.get(
            "experience_score",
            0
        ),

        "final_match_score": score_result.get(
            "final_match_score",
            0
        ),

        "score_weights": score_result.get(
            "score_weights",
            {}
        ),

        "scoring_mode": score_result.get(
            "scoring_mode",
            "content_based"
        ),

        "resume_skills": resume_skills,

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "experience_analysis": (
            experience_analysis
        ),

        "recommendations": recommendations,

        "resume_analysis": resume_analysis
    }


@app.post("/match")
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):

    if not resume.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume file is required."
        )

    if not resume.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported."
        )

    if (
        not job_description
        or
        not job_description.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    try:

        resume_text = extract_text_from_pdf(
            resume.file
        )

        if (
            not resume_text
            or
            not resume_text.strip()
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from "
                    "the uploaded resume."
                )
            )

        result = analyze_match(
            resume_text=resume_text,
            job_description=job_description.strip()
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        print(
            "MATCH ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


class JobInput(BaseModel):
    title: str
    description: str


class MultipleJobsRequest(BaseModel):
    resume_text: str
    jobs: List[JobInput]


@app.post("/match-multiple")
async def match_multiple(
    request: MultipleJobsRequest
):

    resume_text = request.resume_text

    if (
        not resume_text
        or
        not resume_text.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="Resume text cannot be empty."
        )

    if not request.jobs:
        raise HTTPException(
            status_code=400,
            detail="At least one job is required."
        )

    valid_jobs = [
        job
        for job in request.jobs
        if job.description
        and job.description.strip()
    ]

    if not valid_jobs:
        raise HTTPException(
            status_code=400,
            detail="No valid job descriptions were provided."
        )

    semantic_scores = calculate_multiple_semantic_scores(
        resume_text,
        [
            job.description
            for job in valid_jobs
        ]
    )

    results = []

    for index, job in enumerate(valid_jobs):

        job_description = job.description.strip()

        tfidf_score = calculate_similarity(
            resume_text,
            job_description
        )

        skills = compare_skills(
            resume_text,
            job_description
        )

        resume_skills = skills.get(
            "resume_skills",
            []
        )

        required_skills = skills.get(
            "required_skills",
            []
        )

        matched_skills = skills.get(
            "matched_skills",
            []
        )

        missing_skills = skills.get(
            "missing_skills",
            []
        )

        skill_match_score = calculate_skill_match_score(
            required_skills,
            matched_skills
        )

        semantic_score = semantic_scores[index]

        experience_analysis = match_experience(
            resume_text,
            job_description
        )

        score_result = calculate_complete_score(
            tfidf_score=tfidf_score,
            semantic_score=semantic_score,
            skill_match_score=skill_match_score,
            experience_analysis=experience_analysis
        )

        recommendations = get_skill_recommendations(
            missing_skills=missing_skills,
            resume_skills=resume_skills,
            job_description=job_description
        )

        results.append({
            "title": job.title,

            "tfidf_score": round(
                float(tfidf_score),
                2
            ),

            "semantic_score": round(
                float(semantic_score),
                2
            ),

            "skill_match_score": round(
                float(skill_match_score),
                2
            ),

            "experience_score": score_result.get(
                "experience_score",
                0
            ),

            "final_match_score": score_result.get(
                "final_match_score",
                0
            ),

            "score_weights": score_result.get(
                "score_weights",
                {}
            ),

            "scoring_mode": score_result.get(
                "scoring_mode",
                "content_based"
            ),

            "resume_skills": resume_skills,

            "required_skills": required_skills,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills,

            "recommendations": recommendations,

            "experience_analysis": (
                experience_analysis
            )
        })

    results.sort(
        key=lambda x: x["final_match_score"],
        reverse=True
    )

    for rank, result in enumerate(
        results,
        start=1
    ):
        result["rank"] = rank

    return {
        "total_jobs": len(results),
        "results": results
    }


@app.post("/match-multiple-pdf")
async def match_multiple_pdf(
    resume: UploadFile = File(...),
    jobs: str = Form(...)
):

    if not resume.filename:
        raise HTTPException(
            status_code=400,
            detail="Resume file is required."
        )

    if not resume.filename.lower().endswith(
        ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported."
        )

    try:

        resume_text = extract_text_from_pdf(
            resume.file
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    if (
        not resume_text
        or
        not resume_text.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract text from "
                "the uploaded resume."
            )
        )

    try:

        jobs_data = json.loads(
            jobs
        )

    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid jobs JSON format."
        )

    if not isinstance(
        jobs_data,
        list
    ):
        raise HTTPException(
            status_code=400,
            detail="Jobs must be a list."
        )

    if len(jobs_data) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one job is required."
        )

    valid_jobs = []

    for index, job in enumerate(
        jobs_data
    ):

        if not isinstance(
            job,
            dict
        ):
            continue

        title = job.get(
            "title",
            f"Job {index + 1}"
        )

        description = job.get(
            "description",
            ""
        )

        if (
            not description
            or
            not str(description).strip()
        ):
            continue

        valid_jobs.append({
            "title": title,
            "description": str(
                description
            ).strip()
        })

    if not valid_jobs:
        raise HTTPException(
            status_code=400,
            detail="No valid jobs were provided."
        )

    semantic_scores = calculate_multiple_semantic_scores(
        resume_text,
        [
            job["description"]
            for job in valid_jobs
        ]
    )

    results = []

    for index, job in enumerate(
        valid_jobs
    ):

        job_title = job["title"]

        job_description = job[
            "description"
        ]

        tfidf_score = calculate_similarity(
            resume_text,
            job_description
        )

        skills = compare_skills(
            resume_text,
            job_description
        )

        resume_skills = skills.get(
            "resume_skills",
            []
        )

        required_skills = skills.get(
            "required_skills",
            []
        )

        matched_skills = skills.get(
            "matched_skills",
            []
        )

        missing_skills = skills.get(
            "missing_skills",
            []
        )

        skill_match_score = calculate_skill_match_score(
            required_skills,
            matched_skills
        )

        semantic_score = semantic_scores[
            index
        ]

        experience_analysis = match_experience(
            resume_text,
            job_description
        )

        score_result = calculate_complete_score(
            tfidf_score=tfidf_score,
            semantic_score=semantic_score,
            skill_match_score=skill_match_score,
            experience_analysis=experience_analysis
        )

        recommendations = get_skill_recommendations(
            missing_skills=missing_skills,
            resume_skills=resume_skills,
            job_description=job_description
        )

        results.append({
            "title": job_title,

            "tfidf_score": round(
                float(tfidf_score),
                2
            ),

            "semantic_score": round(
                float(semantic_score),
                2
            ),

            "skill_match_score": round(
                float(skill_match_score),
                2
            ),

            "experience_score": score_result.get(
                "experience_score",
                0
            ),

            "final_match_score": score_result.get(
                "final_match_score",
                0
            ),

            "score_weights": score_result.get(
                "score_weights",
                {}
            ),

            "scoring_mode": score_result.get(
                "scoring_mode",
                "content_based"
            ),

            "resume_skills": resume_skills,

            "required_skills": required_skills,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills,

            "recommendations": recommendations,

            "experience_analysis": (
                experience_analysis
            )
        })

    results.sort(
        key=lambda x: x["final_match_score"],
        reverse=True
    )

    for rank, result in enumerate(
        results,
        start=1
    ):
        result["rank"] = rank

    return {
        "total_jobs": len(results),
        "results": results
    }
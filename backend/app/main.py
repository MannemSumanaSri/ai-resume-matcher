import json
from typing import List

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.pdf_reader import extract_text_from_pdf
from app.matcher import calculate_similarity
from app.skills import compare_skills
from app.recommendations import generate_recommendations
from app.resume_analyzer import analyze_resume


# ============================================================
# SEMANTIC MODEL
# ============================================================
# Load the model ONCE when the backend starts.
# Do NOT load it inside every API request.
# This significantly improves matching performance.

print("Loading semantic model...")

semantic_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("Semantic model loaded successfully.")


# ============================================================
# CREATE FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Resume & Job Matcher",
    description="AI-powered resume and job description matching system",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://ai-resume-matcher-55qcinyxa-mannem-sumana-sris-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME ROUTE
# ============================================================

@app.get("/")
def home():
    return {
        "message": "AI Resume Matcher API is running",
        "status": "success"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "semantic_model": "loaded"
    }


# ============================================================
# HELPER FUNCTION
# ============================================================

def calculate_semantic_score(
    resume_text: str,
    job_description: str
):
    """
    Calculate semantic similarity between
    resume and job description.

    The SentenceTransformer model is loaded
    only once when the application starts.
    """

    try:

        embeddings = semantic_model.encode(
            [
                resume_text,
                job_description
            ],
            normalize_embeddings=True
        )

        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        semantic_score = round(
            float(similarity) * 100,
            2
        )

        # Keep the score within 0-100
        semantic_score = max(
            0,
            min(100, semantic_score)
        )

        return semantic_score

    except Exception as e:

        print(
            "Semantic model error:",
            str(e)
        )

        return 0.0


# ============================================================
# HELPER FUNCTION
# ============================================================

def calculate_skill_match_score(
    required_skills,
    matched_skills
):
    """
    Calculate percentage of required skills
    found in the resume.
    """

    if not required_skills:

        return 0.0

    score = (
        len(matched_skills)
        /
        len(required_skills)
    ) * 100

    return round(
        max(0, min(100, score)),
        2
    )


# ============================================================
# HELPER FUNCTION
# ============================================================

def calculate_final_score(
    tfidf_score,
    semantic_score,
    skill_match_score
):
    """
    Final Resume Match Score.

    Weighting:
        TF-IDF        = 15%
        Semantic      = 35%
        Skills        = 50%

    Skills receive the highest weight because
    explicit required technologies are highly
    important for job matching.
    """

    final_score = (
        (tfidf_score * 0.15)
        +
        (semantic_score * 0.35)
        +
        (skill_match_score * 0.50)
    )

    return round(
        max(0, min(100, final_score)),
        2
    )


# ============================================================
# MATCH RESUME WITH ONE JOB DESCRIPTION
# ============================================================

@app.post("/match")
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):

    # --------------------------------------------------------
    # 1. EXTRACT TEXT FROM RESUME PDF
    # --------------------------------------------------------

    resume_text = extract_text_from_pdf(
        resume.file
    )

    if not resume_text or not resume_text.strip():

        return {
            "error": "Could not extract text from the uploaded resume."
        }

    # --------------------------------------------------------
    # 2. TF-IDF SIMILARITY
    # --------------------------------------------------------

    tfidf_score = calculate_similarity(
        resume_text,
        job_description
    )

    # --------------------------------------------------------
    # 3. EXTRACT AND COMPARE SKILLS
    # --------------------------------------------------------

    skills = compare_skills(
        resume_text,
        job_description
    )

    resume_skills = skills[
        "resume_skills"
    ]

    required_skills = skills[
        "required_skills"
    ]

    matched_skills = skills[
        "matched_skills"
    ]

    missing_skills = skills[
        "missing_skills"
    ]

    # --------------------------------------------------------
    # 4. SKILL MATCH SCORE
    # --------------------------------------------------------

    skill_match_score = calculate_skill_match_score(
        required_skills,
        matched_skills
    )

    # --------------------------------------------------------
    # 5. SEMANTIC SIMILARITY
    # --------------------------------------------------------

    semantic_score = calculate_semantic_score(
        resume_text,
        job_description
    )

    # --------------------------------------------------------
    # 6. FINAL MATCH SCORE
    # --------------------------------------------------------

    final_match_score = calculate_final_score(
        tfidf_score,
        semantic_score,
        skill_match_score
    )

    # --------------------------------------------------------
    # 7. AI SKILL RECOMMENDATIONS
    # --------------------------------------------------------

    recommendations = generate_recommendations(
        missing_skills
    )

    # --------------------------------------------------------
    # 8. RESUME STRENGTH ANALYSIS
    # --------------------------------------------------------

    resume_analysis = analyze_resume(
        resume_text,
        resume_skills
    )

    # --------------------------------------------------------
    # 9. RETURN COMPLETE RESULT
    # --------------------------------------------------------

    return {

        "tfidf_score": round(
            tfidf_score,
            2
        ),

        "semantic_score": semantic_score,

        "skill_match_score": skill_match_score,

        "final_match_score": final_match_score,

        "resume_skills": resume_skills,

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "recommendations": recommendations,

        "resume_analysis": resume_analysis
    }


# ============================================================
# MULTIPLE JOB MATCHING MODELS
# ============================================================

class JobInput(BaseModel):

    title: str

    description: str


class MultipleJobsRequest(BaseModel):

    resume_text: str

    jobs: List[JobInput]


# ============================================================
# MATCH RESUME TEXT WITH MULTIPLE JOBS
# ============================================================

@app.post("/match-multiple")
async def match_multiple(
    request: MultipleJobsRequest
):

    resume_text = request.resume_text

    # --------------------------------------------------------
    # VALIDATE RESUME
    # --------------------------------------------------------

    if not resume_text or not resume_text.strip():

        return {
            "error": "Resume text cannot be empty."
        }

    results = []

    # --------------------------------------------------------
    # PROCESS EVERY JOB
    # --------------------------------------------------------

    for index, job in enumerate(
        request.jobs
    ):

        job_title = job.title

        job_description = job.description

        if not job_description.strip():

            continue

        # ----------------------------------------------------
        # TF-IDF
        # ----------------------------------------------------

        tfidf_score = calculate_similarity(
            resume_text,
            job_description
        )

        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        skills = compare_skills(
            resume_text,
            job_description
        )

        required_skills = skills[
            "required_skills"
        ]

        matched_skills = skills[
            "matched_skills"
        ]

        missing_skills = skills[
            "missing_skills"
        ]

        # ----------------------------------------------------
        # SKILL MATCH SCORE
        # ----------------------------------------------------

        skill_match_score = calculate_skill_match_score(
            required_skills,
            matched_skills
        )

        # ----------------------------------------------------
        # SEMANTIC SCORE
        # ----------------------------------------------------

        semantic_score = calculate_semantic_score(
            resume_text,
            job_description
        )

        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        final_match_score = calculate_final_score(
            tfidf_score,
            semantic_score,
            skill_match_score
        )

        # ----------------------------------------------------
        # STORE RESULT
        # ----------------------------------------------------

        results.append({

            "title": job_title,

            "tfidf_score": round(
                tfidf_score,
                2
            ),

            "semantic_score": semantic_score,

            "skill_match_score": skill_match_score,

            "final_match_score": final_match_score,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills
        })

    # --------------------------------------------------------
    # SORT BY SCORE
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["final_match_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # ADD RANK
    # --------------------------------------------------------

    for rank, result in enumerate(
        results,
        start=1
    ):

        result["rank"] = rank

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {

        "total_jobs": len(results),

        "results": results
    }


# ============================================================
# MATCH PDF RESUME WITH MULTIPLE JOBS
# ============================================================

@app.post("/match-multiple-pdf")
async def match_multiple_pdf(
    resume: UploadFile = File(...),
    jobs: str = Form(...)
):

    # --------------------------------------------------------
    # 1. EXTRACT TEXT FROM PDF
    # --------------------------------------------------------

    resume_text = extract_text_from_pdf(
        resume.file
    )

    if not resume_text or not resume_text.strip():

        return {
            "error": "Could not extract text from the uploaded resume."
        }

    # --------------------------------------------------------
    # 2. PARSE JOB JSON
    # --------------------------------------------------------

    try:

        jobs_data = json.loads(
            jobs
        )

    except json.JSONDecodeError:

        return {
            "error": "Invalid jobs JSON format."
        }

    # --------------------------------------------------------
    # 3. VALIDATE JOBS
    # --------------------------------------------------------

    if not isinstance(
        jobs_data,
        list
    ):

        return {
            "error": "Jobs must be a list."
        }

    if len(jobs_data) == 0:

        return {
            "error": "At least one job is required."
        }

    results = []

    # --------------------------------------------------------
    # 4. PROCESS JOBS
    # --------------------------------------------------------

    for index, job in enumerate(
        jobs_data
    ):

        job_title = job.get(
            "title",
            f"Job {index + 1}"
        )

        job_description = job.get(
            "description",
            ""
        )

        if not job_description.strip():

            continue

        # ----------------------------------------------------
        # TF-IDF
        # ----------------------------------------------------

        tfidf_score = calculate_similarity(
            resume_text,
            job_description
        )

        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        skills = compare_skills(
            resume_text,
            job_description
        )

        required_skills = skills[
            "required_skills"
        ]

        matched_skills = skills[
            "matched_skills"
        ]

        missing_skills = skills[
            "missing_skills"
        ]

        # ----------------------------------------------------
        # SKILL SCORE
        # ----------------------------------------------------

        skill_match_score = calculate_skill_match_score(
            required_skills,
            matched_skills
        )

        # ----------------------------------------------------
        # SEMANTIC SCORE
        # ----------------------------------------------------

        semantic_score = calculate_semantic_score(
            resume_text,
            job_description
        )

        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        final_match_score = calculate_final_score(
            tfidf_score,
            semantic_score,
            skill_match_score
        )

        # ----------------------------------------------------
        # STORE RESULT
        # ----------------------------------------------------

        results.append({

            "title": job_title,

            "tfidf_score": round(
                tfidf_score,
                2
            ),

            "semantic_score": semantic_score,

            "skill_match_score": skill_match_score,

            "final_match_score": final_match_score,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills
        })

    # --------------------------------------------------------
    # 5. SORT
    # --------------------------------------------------------

    results.sort(
        key=lambda x: x["final_match_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # 6. ADD RANK
    # --------------------------------------------------------

    for rank, result in enumerate(
        results,
        start=1
    ):

        result["rank"] = rank

    # --------------------------------------------------------
    # 7. RETURN
    # --------------------------------------------------------

    return {

        "total_jobs": len(results),

        "results": results
    }
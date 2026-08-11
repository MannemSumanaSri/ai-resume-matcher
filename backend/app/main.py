from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.pdf_reader import extract_text_from_pdf
from app.matcher import calculate_similarity
from app.skills import compare_skills
from app.recommendations import generate_recommendations
from app.resume_analyzer import analyze_resume


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
    allow_origins=["*"],
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
# MATCH RESUME WITH JOB DESCRIPTION
# ============================================================

@app.post("/match")
async def match_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):

    # --------------------------------------------------------
    # 1. EXTRACT TEXT FROM RESUME PDF
    # --------------------------------------------------------

    resume_text = extract_text_from_pdf(resume.file)

    # Basic validation
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

    resume_skills = skills["resume_skills"]

    required_skills = skills["required_skills"]

    matched_skills = skills["matched_skills"]

    missing_skills = skills["missing_skills"]


    # --------------------------------------------------------
    # 4. SKILL MATCH SCORE
    # --------------------------------------------------------

    if len(required_skills) > 0:

        skill_match_score = (
            len(matched_skills)
            / len(required_skills)
        ) * 100

    else:

        skill_match_score = 0


    skill_match_score = round(
        skill_match_score,
        2
    )


    # --------------------------------------------------------
    # 5. SEMANTIC SIMILARITY
    # --------------------------------------------------------

    semantic_score = 0.0

    try:

        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity

        # Load sentence transformer model
        model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        # Generate embeddings
        embeddings = model.encode(
            [
                resume_text,
                job_description
            ]
        )

        # Calculate cosine similarity
        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]

        # Convert to percentage
        semantic_score = round(
            float(similarity) * 100,
            2
        )

    except Exception as e:

        print(
            "Semantic model error:",
            str(e)
        )

        semantic_score = 0.0


    # --------------------------------------------------------
    # 6. FINAL MATCH SCORE
    # --------------------------------------------------------
    #
    # TF-IDF similarity      -> 20%
    # Semantic similarity    -> 40%
    # Skill matching         -> 40%
    #
    # --------------------------------------------------------

    final_match_score = (
        (tfidf_score * 0.20)
        +
        (semantic_score * 0.40)
        +
        (skill_match_score * 0.40)
    )

    final_match_score = round(
        final_match_score,
        2
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

        # Matching scores
        "tfidf_score": tfidf_score,

        "semantic_score": semantic_score,

        "skill_match_score": skill_match_score,

        "final_match_score": final_match_score,


        # Skill analysis
        "resume_skills": resume_skills,

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,


        # AI recommendations
        "recommendations": recommendations,


        # Resume analysis
        "resume_analysis": resume_analysis
    }
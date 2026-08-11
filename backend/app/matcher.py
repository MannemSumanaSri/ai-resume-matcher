from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_similarity(resume_text, job_description):
    """
    Calculate similarity between resume and job description
    using TF-IDF and cosine similarity.

    Returns:
        float: similarity score between 0 and 100
    """

    # Make sure both inputs are strings
    resume_text = str(resume_text)
    job_description = str(job_description)

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    # Convert resume and job description into TF-IDF vectors
    vectors = vectorizer.fit_transform([
        resume_text,
        job_description
    ])

    # Calculate cosine similarity
    similarity = cosine_similarity(
        vectors[0:1],
        vectors[1:2]
    )[0][0]

    # Convert 0-1 score into percentage
    score = similarity * 100

    return round(score, 2)
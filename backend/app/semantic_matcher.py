from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

# Keep very long documents from creating unnecessary inference work.
# This is character based, not token based, and is only a safety limit.
MAX_TEXT_LENGTH = 12000


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """
    Load the SentenceTransformer model only once.

    The previous implementation created the model inside every
    request/job. This cached singleton avoids repeated model loading.
    """
    model = SentenceTransformer(MODEL_NAME)

    # Better CPU performance for this small model.
    try:
        model.eval()
    except Exception:
        pass

    return model


def clean_text(text: str) -> str:
    """
    Normalize and limit text before embedding.
    """
    if not text:
        return ""

    text = str(text).strip()

    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]

    return text


def calculate_semantic_similarity(
    resume_text: str,
    job_text: str
) -> float:
    """
    Calculate semantic similarity between one resume and one job.
    """

    resume_text = clean_text(resume_text)
    job_text = clean_text(job_text)

    if not resume_text or not job_text:
        return 0.0

    model = get_model()

    embeddings = model.encode(
        [resume_text, job_text],
        batch_size=2,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    similarity = float(
        np.dot(
            embeddings[0],
            embeddings[1]
        )
    )

    # Convert cosine similarity to percentage.
    similarity = max(0.0, min(1.0, similarity))

    return round(similarity * 100, 2)


def calculate_multiple_semantic_similarities(
    resume_text: str,
    job_texts: List[str]
) -> List[float]:
    """
    Calculate semantic similarity between one resume and
    multiple job descriptions in ONE model call.

    This is important for the Find Best Job Matches feature.
    """

    resume_text = clean_text(resume_text)

    if not resume_text:
        return [0.0 for _ in job_texts]

    valid_jobs = [
        clean_text(job)
        for job in job_texts
    ]

    if not valid_jobs:
        return []

    model = get_model()

    texts = [
        resume_text,
        *valid_jobs
    ]

    embeddings = model.encode(
        texts,
        batch_size=min(16, len(texts)),
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
            max(0.0, min(1.0, float(score))) * 100,
            2
        )
        for score in similarities
    ]
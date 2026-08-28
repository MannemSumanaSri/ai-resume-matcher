"""
AI Resume Matcher - Scoring

Centralized scoring logic for:

    - TF-IDF similarity
    - Semantic similarity
    - Skill matching
    - Experience matching

DESIGN:

The final score is primarily driven by actual skill
coverage because technical requirements are the most
direct evidence of whether a candidate matches a job.

Content-based JD:
    Skills       = 70%
    Semantic     = 20%
    TF-IDF       = 10%
    Experience   = 0%

Experience-based JD:
    Skills       = 55%
    Semantic     = 20%
    TF-IDF       = 10%
    Experience   = 15%

IMPORTANT:

There is NO artificial minimum score.

For example:

    60% match -> approximately 60%
    80% match -> approximately 80%
    100% skills + strong content -> high score

This avoids artificially forcing every candidate above
a particular threshold.
"""


from typing import Dict, Optional


# ============================================================
# DEFAULT WEIGHTS
# ============================================================

# Skill matching is the strongest signal because it directly
# measures whether required technologies are present.
CONTENT_BASED_WEIGHTS = {

    "tfidf": 10,

    "semantic": 20,

    "skills": 70,

    "experience": 0,

}


# When the JD explicitly requires experience, experience
# receives its own meaningful contribution.
EXPERIENCE_BASED_WEIGHTS = {

    "tfidf": 10,

    "semantic": 20,

    "skills": 55,

    "experience": 15,

}


# ============================================================
# SAFE NUMBER CONVERSION
# ============================================================

def _safe_float(
    value,
    default: float = 0.0,
) -> float:

    try:

        if value is None:
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return default


# ============================================================
# CLAMP SCORE
# ============================================================

def _clamp_score(
    value,
) -> float:

    value = _safe_float(
        value
    )

    return max(
        0.0,
        min(
            100.0,
            value,
        ),
    )


# ============================================================
# ROUND SCORE
# ============================================================

def _round_score(
    value,
) -> float:

    return round(
        _clamp_score(
            value
        ),
        2,
    )


# ============================================================
# NORMALIZE WEIGHTS
# ============================================================

def normalize_weights(
    weights: Optional[Dict] = None,
) -> Dict:
    """
    Normalize supplied weights so they sum to 100.

    If no weights are supplied, content-based weights
    are returned.
    """

    if not weights:

        return dict(
            CONTENT_BASED_WEIGHTS
        )

    normalized = {

        "tfidf": _safe_float(
            weights.get(
                "tfidf",
                0
            )
        ),

        "semantic": _safe_float(
            weights.get(
                "semantic",
                0
            )
        ),

        "skills": _safe_float(
            weights.get(
                "skills",
                0
            )
        ),

        "experience": _safe_float(
            weights.get(
                "experience",
                0
            )
        ),

    }

    total = sum(
        normalized.values()
    )

    if total <= 0:

        return dict(
            CONTENT_BASED_WEIGHTS
        )

    # Normalize to 100 if the caller supplied another scale.
    if abs(
        total - 100
    ) > 0.0001:

        normalized = {

            key:
                (
                    value / total
                ) * 100

            for key, value
            in normalized.items()

        }

    return normalized


# ============================================================
# DETERMINE SCORING MODE
# ============================================================

def determine_scoring_mode(
    has_experience_requirements: bool,
) -> str:

    if has_experience_requirements:

        return (
            "experience_based"
        )

    return (
        "content_based"
    )


# ============================================================
# GET SCORE WEIGHTS
# ============================================================

def get_score_weights(
    has_experience_requirements: bool,
) -> Dict:

    if has_experience_requirements:

        return dict(
            EXPERIENCE_BASED_WEIGHTS
        )

    return dict(
        CONTENT_BASED_WEIGHTS
    )


# ============================================================
# CALCULATE FINAL SCORE
# ============================================================

def calculate_final_score(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_score=None,
    has_experience_requirements=False,
):
    """
    Calculate the final resume/JD match score.

    All input components are expected to be on a 0-100 scale.

    Content-based JD:

        TF-IDF      10%
        Semantic    20%
        Skills      70%

    Experience-based JD:

        TF-IDF      10%
        Semantic    20%
        Skills      55%
        Experience  15%

    The score is never artificially increased or decreased.
    """

    # --------------------------------------------------------
    # Normalize all component scores
    # --------------------------------------------------------

    tfidf_score = _clamp_score(
        tfidf_score
    )

    semantic_score = _clamp_score(
        semantic_score
    )

    skill_match_score = _clamp_score(
        skill_match_score
    )

    # --------------------------------------------------------
    # Select scoring mode
    # --------------------------------------------------------

    if (
        has_experience_requirements
        and
        experience_score is not None
    ):

        experience_score = _clamp_score(
            experience_score
        )

        weights = (
            EXPERIENCE_BASED_WEIGHTS
        )

    else:

        # Experience is ignored when the JD does not
        # explicitly require experience.
        experience_score = 0.0

        weights = (
            CONTENT_BASED_WEIGHTS
        )

    # --------------------------------------------------------
    # Calculate weighted score
    # --------------------------------------------------------

    tfidf_contribution = (

        tfidf_score
        *
        weights["tfidf"]
        /
        100

    )

    semantic_contribution = (

        semantic_score
        *
        weights["semantic"]
        /
        100

    )

    skill_contribution = (

        skill_match_score
        *
        weights["skills"]
        /
        100

    )

    experience_contribution = (

        experience_score
        *
        weights["experience"]
        /
        100

    )

    final_score = (

        tfidf_contribution

        +

        semantic_contribution

        +

        skill_contribution

        +

        experience_contribution

    )

    return _round_score(
        final_score
    )


# ============================================================
# DETAILED SCORE
# ============================================================

def calculate_detailed_score(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_score=None,
    has_experience_requirements=False,
) -> Dict:
    """
    Return all score components together with the final score.
    """

    # --------------------------------------------------------
    # Normalize component scores
    # --------------------------------------------------------

    tfidf_score = _round_score(
        tfidf_score
    )

    semantic_score = _round_score(
        semantic_score
    )

    skill_match_score = _round_score(
        skill_match_score
    )

    # --------------------------------------------------------
    # Determine scoring mode
    # --------------------------------------------------------

    scoring_mode = (
        determine_scoring_mode(
            has_experience_requirements
        )
    )

    weights = get_score_weights(
        has_experience_requirements
    )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    if (
        has_experience_requirements
        and
        experience_score is not None
    ):

        experience_score = _round_score(
            experience_score
        )

    else:

        experience_score = 0.0

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    final_score = (
        calculate_final_score(

            tfidf_score=
                tfidf_score,

            semantic_score=
                semantic_score,

            skill_match_score=
                skill_match_score,

            experience_score=
                experience_score,

            has_experience_requirements=(
                has_experience_requirements
            ),

        )
    )

    return {

        "tfidf_score":
            tfidf_score,

        "semantic_score":
            semantic_score,

        "skill_match_score":
            skill_match_score,

        "experience_score":
            experience_score,

        "final_match_score":
            final_score,

        "score_weights": {

            key:
                int(
                    round(
                        value
                    )
                )

            for key, value
            in weights.items()

        },

        "scoring_mode":
            scoring_mode,

    }


# ============================================================
# SCORE FROM EXPERIENCE ANALYSIS
# ============================================================

def calculate_score_from_analysis(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_analysis=None,
) -> Dict:
    """
    Convenience function used by main.py.

    Automatically determines whether the JD explicitly
    requires experience.
    """

    # --------------------------------------------------------
    # No experience analysis
    # --------------------------------------------------------

    if not experience_analysis:

        return calculate_detailed_score(

            tfidf_score=
                tfidf_score,

            semantic_score=
                semantic_score,

            skill_match_score=
                skill_match_score,

            experience_score=
                None,

            has_experience_requirements=
                False,

        )

    # --------------------------------------------------------
    # Determine whether experience is actually required
    # --------------------------------------------------------

    has_requirements = bool(

        experience_analysis.get(

            "has_experience_requirements",

            False

        )

    )

    # --------------------------------------------------------
    # Get experience score
    # --------------------------------------------------------

    experience_score = (

        experience_analysis.get(

            "overall_experience_score"

        )

    )

    # If experience is not explicitly required by the JD,
    # it must not influence the final score.
    if not has_requirements:

        experience_score = None

    # --------------------------------------------------------
    # Calculate
    # --------------------------------------------------------

    return calculate_detailed_score(

        tfidf_score=
            tfidf_score,

        semantic_score=
            semantic_score,

        skill_match_score=
            skill_match_score,

        experience_score=
            experience_score,

        has_experience_requirements=
            has_requirements,

    )


# ============================================================
# COMPONENT CONTRIBUTIONS
# ============================================================

def calculate_component_contributions(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_score=None,
    has_experience_requirements=False,
) -> Dict:
    """
    Return the actual contribution of every component.

    Example:

        skills = 90
        skill weight = 70%

        contribution = 63 points

    All contributions together equal the final score.
    """

    weights = get_score_weights(
        has_experience_requirements
    )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    tfidf_score = _clamp_score(
        tfidf_score
    )

    semantic_score = _clamp_score(
        semantic_score
    )

    skill_match_score = _clamp_score(
        skill_match_score
    )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    if (
        has_experience_requirements
        and
        experience_score is not None
    ):

        experience_score = _clamp_score(
            experience_score
        )

    else:

        experience_score = 0.0

    # --------------------------------------------------------
    # Contributions
    # --------------------------------------------------------

    tfidf_contribution = (

        tfidf_score
        *
        weights["tfidf"]
        /
        100

    )

    semantic_contribution = (

        semantic_score
        *
        weights["semantic"]
        /
        100

    )

    skills_contribution = (

        skill_match_score
        *
        weights["skills"]
        /
        100

    )

    experience_contribution = (

        experience_score
        *
        weights["experience"]
        /
        100

    )

    return {

        "tfidf":
            round(
                tfidf_contribution,
                2
            ),

        "semantic":
            round(
                semantic_contribution,
                2
            ),

        "skills":
            round(
                skills_contribution,
                2
            ),

        "experience":
            round(
                experience_contribution,
                2
            ),

    }


# ============================================================
# COMPLETE SCORE RESULT
# ============================================================

def build_score_result(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_analysis=None,
) -> Dict:
    """
    Build the complete score response.
    """

    score = (
        calculate_score_from_analysis(

            tfidf_score=
                tfidf_score,

            semantic_score=
                semantic_score,

            skill_match_score=
                skill_match_score,

            experience_analysis=
                experience_analysis,

        )
    )

    # --------------------------------------------------------
    # Determine experience mode
    # --------------------------------------------------------

    has_experience_requirements = bool(

        experience_analysis

        and

        experience_analysis.get(

            "has_experience_requirements",

            False

        )

    )

    # --------------------------------------------------------
    # Experience score
    # --------------------------------------------------------

    experience_score = None

    if (
        experience_analysis

        and

        has_experience_requirements
    ):

        experience_score = (

            experience_analysis.get(

                "overall_experience_score"

            )

        )

    # --------------------------------------------------------
    # Contributions
    # --------------------------------------------------------

    contributions = (
        calculate_component_contributions(

            tfidf_score=
                tfidf_score,

            semantic_score=
                semantic_score,

            skill_match_score=
                skill_match_score,

            experience_score=
                experience_score,

            has_experience_requirements=(
                has_experience_requirements
            ),

        )
    )

    return {

        **score,

        "score_contributions":
            contributions,

    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def calculate_score(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_score=None,
    has_experience_requirements=False,
):

    return calculate_final_score(

        tfidf_score=
            tfidf_score,

        semantic_score=
            semantic_score,

        skill_match_score=
            skill_match_score,

        experience_score=
            experience_score,

        has_experience_requirements=(
            has_experience_requirements
        ),

    )


def get_final_score(
    tfidf_score,
    semantic_score,
    skill_match_score,
    experience_score=None,
    has_experience_requirements=False,
):

    return calculate_final_score(

        tfidf_score=
            tfidf_score,

        semantic_score=
            semantic_score,

        skill_match_score=
            skill_match_score,

        experience_score=
            experience_score,

        has_experience_requirements=(
            has_experience_requirements
        ),

    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n============================================"
    )

    print(
        "TESTING RESUME MATCH SCORING"
    )

    print(
        "============================================"
    )

    # --------------------------------------------------------
    # Example 1
    #
    # Previously this type of result could produce ~44%.
    #
    # With the new scoring:
    #
    # TF-IDF   = 13
    # Semantic = 39
    # Skills   = 67
    #
    # Score:
    #
    # 13 * 10%
    # + 39 * 20%
    # + 67 * 70%
    #
    # = approximately 52.3
    #
    # Notice:
    # We do NOT artificially force it to 60.
    # The actual skill coverage is still only 67%.
    # --------------------------------------------------------

    result_1 = calculate_detailed_score(

        tfidf_score=13,

        semantic_score=39,

        skill_match_score=67,

        experience_score=None,

        has_experience_requirements=False,

    )

    print(
        "\nPartial skill match:"
    )

    print(
        result_1
    )

    # --------------------------------------------------------
    # Example 2
    #
    # Strong skill match:
    #
    # TF-IDF   = 13
    # Semantic = 39
    # Skills   = 90
    #
    # Score:
    #
    # 13 * 10%
    # + 39 * 20%
    # + 90 * 70%
    #
    # = approximately 71.1
    # --------------------------------------------------------

    result_2 = calculate_detailed_score(

        tfidf_score=13,

        semantic_score=39,

        skill_match_score=90,

        experience_score=None,

        has_experience_requirements=False,

    )

    print(
        "\nStrong skill match:"
    )

    print(
        result_2
    )

    # --------------------------------------------------------
    # Example 3
    #
    # Almost everything matches:
    #
    # Skills = 100
    # --------------------------------------------------------

    result_3 = calculate_detailed_score(

        tfidf_score=13,

        semantic_score=39,

        skill_match_score=100,

        experience_score=None,

        has_experience_requirements=False,

    )

    print(
        "\nComplete skill match:"
    )

    print(
        result_3
    )

    # --------------------------------------------------------
    # Example 4
    #
    # Experience-based JD
    # --------------------------------------------------------

    result_4 = calculate_detailed_score(

        tfidf_score=20,

        semantic_score=60,

        skill_match_score=90,

        experience_score=80,

        has_experience_requirements=True,

    )

    print(
        "\nExperience-based match:"
    )

    print(
        result_4
    )
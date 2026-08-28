"""
Skill extraction and matching engine.

This module preserves the existing skill-matching behavior while improving:

1. Substring false positives
2. Word-boundary matching
3. Phrase matching
4. Skill aliases
5. Canonical skill normalization
6. Expanded skill vocabulary
7. Unknown/unmapped technology detection
8. Evidence-aware compatibility helpers

IMPORTANT:
- Existing compare_skills() behavior is preserved.
- Existing skill names remain available.
- No external ML/NER model is required.
- Matching is deterministic and explainable.
"""

import re
from typing import Dict, List, Optional, Tuple


# ============================================================
# CANONICAL SKILL TAXONOMY
# ============================================================
#
# Every key is the canonical name returned by the system.
#
# Values are aliases / alternate spellings that can appear
# in resumes and job descriptions.
#
# The dictionary is intentionally broad so the system can
# recognize more technologies without changing the API.
# ============================================================

SKILL_ALIASES: Dict[str, List[str]] = {

    # --------------------------------------------------------
    # PROGRAMMING LANGUAGES
    # --------------------------------------------------------

    "python": [
        "python",
        "python 3",
        "python3",
    ],

    "javascript": [
        "javascript",
        "java script",
        "js",
        "ecmascript",
    ],

    "typescript": [
        "typescript",
        "type script",
        "ts",
    ],

    "java": [
        "java",
    ],

    "c": [
        "c",
        "c language",
    ],

    "c++": [
        "c++",
        "cpp",
        "c plus plus",
    ],

    "c#": [
        "c#",
        "c sharp",
        "c-sharp",
    ],

    "go": [
        "golang",
        "go language",
        "go",
    ],

    "rust": [
        "rust",
        "rustlang",
    ],

    "php": [
        "php",
    ],

    "ruby": [
        "ruby",
        "ruby on rails",
    ],

    "kotlin": [
        "kotlin",
    ],

    "swift": [
        "swift",
    ],


    # --------------------------------------------------------
    # FRONTEND
    # --------------------------------------------------------

    "html": [
        "html",
        "html5",
        "hypertext markup language",
    ],

    "css": [
        "css",
        "css3",
        "cascading style sheets",
    ],

    "react": [
        "react",
        "react.js",
        "reactjs",
        "react js",
    ],

    "angular": [
        "angular",
        "angular.js",
        "angularjs",
        "angular js",
    ],

    "vue": [
        "vue",
        "vue.js",
        "vuejs",
        "vue js",
    ],

    "next.js": [
        "next.js",
        "nextjs",
        "next js",
    ],

    "bootstrap": [
        "bootstrap",
    ],

    "tailwind css": [
        "tailwind",
        "tailwind css",
        "tailwindcss",
    ],


    # --------------------------------------------------------
    # BACKEND
    # --------------------------------------------------------

    "node.js": [
        "node.js",
        "nodejs",
        "node js",
        "node",
    ],

    "express": [
        "express",
        "express.js",
        "expressjs",
        "express js",
    ],

    "fastapi": [
        "fastapi",
        "fast api",
        "fast-api",
    ],

    "django": [
        "django",
    ],

    "flask": [
        "flask",
    ],

    "spring": [
        "spring",
        "spring framework",
        "spring boot",
        "springboot",
    ],

    "asp.net": [
        "asp.net",
        "aspnet",
        "asp net",
    ],


    # --------------------------------------------------------
    # APIs
    # --------------------------------------------------------

    "rest api": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "restful services",
        "rest services",
        "rest service",
        "rest web services",
        "rest web service",
    ],

    "graphql": [
        "graphql",
        "graph ql",
    ],

    "grpc": [
        "grpc",
        "g rpc",
    ],

    "websocket": [
        "websocket",
        "web sockets",
        "web socket",
    ],


    # --------------------------------------------------------
    # DATABASES
    # --------------------------------------------------------

    "sql": [
        "sql",
        "structured query language",
    ],

    "mysql": [
        "mysql",
        "my sql",
    ],

    "postgresql": [
        "postgresql",
        "postgres",
        "postgre sql",
        "postgre-sql",
    ],

    "mongodb": [
        "mongodb",
        "mongo db",
        "mongo",
    ],

    "sqlite": [
        "sqlite",
        "sqlite3",
    ],

    "redis": [
        "redis",
    ],

    "oracle": [
        "oracle",
        "oracle database",
    ],

    "microsoft sql server": [
        "sql server",
        "mssql",
        "microsoft sql server",
    ],

    "cassandra": [
        "cassandra",
        "apache cassandra",
    ],

    "dynamodb": [
        "dynamodb",
        "dynamo db",
        "amazon dynamodb",
    ],


    # --------------------------------------------------------
    # CLOUD
    # --------------------------------------------------------

    "aws": [
        "aws",
        "amazon web services",
        "amazon aws",
    ],

    "azure": [
        "azure",
        "microsoft azure",
        "azure cloud",
    ],

    "gcp": [
        "gcp",
        "google cloud",
        "google cloud platform",
    ],

    "heroku": [
        "heroku",
    ],

    "vercel": [
        "vercel",
    ],

    "render": [
        "render",
        "render.com",
    ],


    # --------------------------------------------------------
    # AWS SERVICES
    # --------------------------------------------------------

    "amazon ec2": [
        "ec2",
        "amazon ec2",
        "aws ec2",
    ],

    "amazon s3": [
        "s3",
        "amazon s3",
        "aws s3",
    ],

    "aws lambda": [
        "lambda",
        "aws lambda",
        "amazon lambda",
    ],

    "aws iam": [
        "iam",
        "aws iam",
        "identity and access management",
    ],


    # --------------------------------------------------------
    # DEVOPS / CONTAINERS
    # --------------------------------------------------------

    "docker": [
        "docker",
        "docker container",
        "docker containers",
        "docker engine",
    ],

    "kubernetes": [
        "kubernetes",
        "k8s",
        "kube",
    ],

    "jenkins": [
        "jenkins",
    ],

    "github actions": [
        "github actions",
        "github action",
    ],

    "gitlab ci": [
        "gitlab ci",
        "gitlab-ci",
        "gitlab continuous integration",
    ],

    "ci/cd": [
        "ci/cd",
        "ci cd",
        "continuous integration",
        "continuous deployment",
        "continuous delivery",
    ],


    # --------------------------------------------------------
    # VERSION CONTROL
    # --------------------------------------------------------

    "git": [
        "git",
        "git scm",
        "git version control",
    ],

    "github": [
        "github",
        "git hub",
    ],

    "gitlab": [
        "gitlab",
        "git lab",
    ],

    "bitbucket": [
        "bitbucket",
        "bit bucket",
    ],


    # --------------------------------------------------------
    # AUTHENTICATION / SECURITY
    # --------------------------------------------------------

    "authentication": [
        "authentication",
        "user authentication",
        "application authentication",
    ],

    "authorization": [
        "authorization",
        "user authorization",
        "access authorization",
    ],

    "oauth": [
        "oauth",
        "oauth2",
        "oauth 2",
        "oauth 2.0",
    ],

    "jwt": [
        "jwt",
        "json web token",
        "json web tokens",
    ],

    "role based access control": [
        "role based access control",
        "role-based access control",
        "rbac",
    ],


    # --------------------------------------------------------
    # DATA / AI
    # --------------------------------------------------------

    "machine learning": [
        "machine learning",
        "machine-learning",
        "ml",
    ],

    "deep learning": [
        "deep learning",
        "deep-learning",
        "dl",
    ],

    "nlp": [
        "nlp",
        "natural language processing",
    ],

    "tensorflow": [
        "tensorflow",
        "tensor flow",
    ],

    "pytorch": [
        "pytorch",
        "py torch",
    ],

    "scikit-learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn",
    ],

    "pandas": [
        "pandas",
    ],

    "numpy": [
        "numpy",
        "num py",
    ],

    "sentence transformers": [
        "sentence transformers",
        "sentence-transformers",
        "sentence transformer",
    ],


    # --------------------------------------------------------
    # TESTING
    # --------------------------------------------------------

    "pytest": [
        "pytest",
        "py test",
    ],

    "vitest": [
        "vitest",
        "vi test",
    ],

    "jest": [
        "jest",
    ],

    "postman": [
        "postman",
    ],

    "api testing": [
        "api testing",
        "api test",
        "api tests",
    ],


    # --------------------------------------------------------
    # TOOLS
    # --------------------------------------------------------

    "sqlalchemy": [
        "sqlalchemy",
        "sql alchemy",
    ],

    "fastapi": [
        "fastapi",
        "fast api",
        "fast-api",
    ],

    "uvicorn": [
        "uvicorn",
    ],

    "apscheduler": [
        "apscheduler",
        "apscheduler scheduler",
    ],

    "vercel": [
        "vercel",
    ],

    "render": [
        "render",
        "render.com",
    ],

    "postman": [
        "postman",
    ],

    "insomnia": [
        "insomnia",
    ],
}


# ============================================================
# EXTRA CANONICAL SKILLS
# ============================================================
#
# These are maintained separately so adding new skills later
# does not require rewriting the matching engine.
# ============================================================

ADDITIONAL_SKILLS = {

    "terraform": [
        "terraform",
        "hashicorp terraform",
    ],

    "ansible": [
        "ansible",
    ],

    "prometheus": [
        "prometheus",
    ],

    "grafana": [
        "grafana",
    ],

    "elasticsearch": [
        "elasticsearch",
        "elastic search",
    ],

    "kibana": [
        "kibana",
    ],

    "rabbitmq": [
        "rabbitmq",
        "rabbit mq",
    ],

    "kafka": [
        "kafka",
        "apache kafka",
    ],

    "microservices": [
        "microservices",
        "microservices architecture",
        "microservice architecture",
    ],

    "linux": [
        "linux",
        "linux operating system",
    ],

    "bash": [
        "bash",
        "bash scripting",
    ],

    "powershell": [
        "powershell",
        "power shell",
    ],
}


# Add the additional taxonomy without removing existing skills.
for _skill, _aliases in ADDITIONAL_SKILLS.items():

    if _skill not in SKILL_ALIASES:

        SKILL_ALIASES[
            _skill
        ] = list(_aliases)


# ============================================================
# BACKWARD-COMPATIBLE SKILL DICTIONARY
# ============================================================
#
# Some older code may import SKILLS or SKILL_PATTERNS.
# Keep these names available.
# ============================================================

SKILLS = SKILL_ALIASES


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_whitespace(
    text: str
) -> str:
    """
    Normalize whitespace while preserving the words
    needed for phrase matching.
    """

    if not text:

        return ""

    text = str(text)

    # Normalize common PDF whitespace issues.
    text = text.replace(
        "\u00a0",
        " "
    )

    text = text.replace(
        "\t",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_skill_name(
    skill: str
) -> str:
    """
    Convert an alias/candidate skill name into its
    canonical skill name.
    """

    if not skill:

        return ""

    value = normalize_whitespace(
        skill
    ).lower()

    # Normalize punctuation/spacing variants.
    value = value.replace(
        "–",
        "-"
    )

    value = value.replace(
        "—",
        "-"
    )

    # Direct canonical-name match.
    if value in SKILL_ALIASES:

        return value

    # Alias lookup.
    for canonical, aliases in SKILL_ALIASES.items():

        for alias in aliases:

            if (
                value
                ==
                normalize_whitespace(
                    alias
                ).lower()
            ):

                return canonical

    return value


# ============================================================
# ALIAS LOOKUP
# ============================================================

def get_skill_aliases(
    skill: str
) -> List[str]:
    """
    Return all aliases for a canonical skill.
    """

    canonical = normalize_skill_name(
        skill
    )

    aliases = SKILL_ALIASES.get(
        canonical,
        []
    )

    # Always include canonical name.
    values = [
        canonical
    ] + list(aliases)

    # Deduplicate while preserving order.
    result = []

    seen = set()

    for value in values:

        normalized = normalize_whitespace(
            value
        ).lower()

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        result.append(
            normalized
        )

    return result


# ============================================================
# SAFE PHRASE PATTERN
# ============================================================

def build_skill_pattern(
    alias: str
) -> str:
    """
    Build a regex pattern that performs phrase-aware,
    boundary-aware matching.

    This replaces unsafe logic such as:

        if alias in text:

    with:

        (?<!\\w)alias(?!\\w)

    The negative lookarounds prevent matching a skill
    inside another word.

    Example:

        git        -> matches "git"
        git        -> does not match "digital"
        api        -> matches "API"
        api        -> does not match "capital"
    """

    alias = normalize_whitespace(
        alias
    )

    if not alias:

        return r"(?!x)x"

    # Escape the entire alias first.
    escaped = re.escape(
        alias
    )

    # Permit flexible whitespace between words.
    escaped = escaped.replace(
        r"\ ",
        r"\s+"
    )

    return (
        r"(?<!\w)"
        +
        escaped
        +
        r"(?!\w)"
    )


# ============================================================
# SKILL MATCHING
# ============================================================

def skill_in_text(
    skill: str,
    text: str
) -> bool:
    """
    Check whether a canonical skill is actually present
    in the text.

    IMPORTANT:
    This uses boundary-aware phrase matching and therefore
    avoids the old substring false-positive problem.
    """

    if not skill or not text:

        return False

    normalized_text = normalize_whitespace(
        text
    )

    aliases = get_skill_aliases(
        skill
    )

    # Longest aliases first.
    # This helps phrases such as "rest api" take
    # precedence over shorter terms such as "api".
    aliases.sort(
        key=len,
        reverse=True
    )

    for alias in aliases:

        pattern = build_skill_pattern(
            alias
        )

        if re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE
        ):

            return True

    return False


# ============================================================
# FIND SKILL EVIDENCE
# ============================================================

def find_skill_evidence(
    skill: str,
    text: str,
    context_chars: int = 180
) -> Optional[str]:
    """
    Return a small text window surrounding the first
    reliable occurrence of a skill.

    This is useful for explainable matching and later
    experience/evidence analysis.
    """

    if not skill or not text:

        return None

    normalized_text = normalize_whitespace(
        text
    )

    aliases = get_skill_aliases(
        skill
    )

    aliases.sort(
        key=len,
        reverse=True
    )

    for alias in aliases:

        pattern = build_skill_pattern(
            alias
        )

        match = re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE
        )

        if not match:

            continue

        start = max(
            0,
            match.start()
            -
            context_chars
        )

        end = min(
            len(normalized_text),
            match.end()
            +
            context_chars
        )

        return normalized_text[
            start:end
        ].strip()

    return None


# ============================================================
# EXTRACT SKILLS FROM TEXT
# ============================================================

def extract_skills(
    text: str
) -> List[str]:
    """
    Extract canonical skills from a piece of text.

    The returned list contains canonical skill names,
    not aliases.

    Example:

        "Built RESTful APIs with React.js and Node.js"

    becomes:

        ["react", "node.js", "rest api"]
    """

    if not text:

        return []

    normalized_text = normalize_whitespace(
        text
    )

    found = []

    for skill in SKILL_ALIASES:

        if skill_in_text(
            skill,
            normalized_text
        ):

            found.append(
                skill
            )

    # Remove duplicates.
    return list(
        dict.fromkeys(
            found
        )
    )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def extract_skills_from_text(
    text: str
) -> List[str]:
    """
    Backward-compatible alias.
    """

    return extract_skills(
        text
    )


def get_skills_from_text(
    text: str
) -> List[str]:
    """
    Backward-compatible alias.
    """

    return extract_skills(
        text
    )


# ============================================================
# SKILL EVIDENCE MAP
# ============================================================

def extract_skill_evidence(
    text: str
) -> Dict[str, Dict]:
    """
    Return canonical skills with evidence information.

    Example:

        {
            "python": {
                "found": True,
                "evidence": "Developed backend services using Python..."
            }
        }
    """

    result = {}

    if not text:

        return result

    for skill in SKILL_ALIASES:

        evidence = find_skill_evidence(
            skill,
            text
        )

        result[
            skill
        ] = {

            "found": (
                evidence
                is not None
            ),

            "evidence": evidence
        }

    return result


# ============================================================
# REQUIRED-SKILL EXTRACTION
# ============================================================

def extract_required_skills(
    job_description: str
) -> List[str]:
    """
    Extract skills appearing in a job description.

    This remains deterministic and explainable.

    The method recognizes both canonical names and aliases.
    """

    return extract_skills(
        job_description
    )


# ============================================================
# RESUME-SKILL EXTRACTION
# ============================================================

def extract_resume_skills(
    resume_text: str
) -> List[str]:
    """
    Extract skills from the resume.
    """

    return extract_skills(
        resume_text
    )


# ============================================================
# CANONICAL SKILL SET
# ============================================================

def canonicalize_skills(
    skills: List[str]
) -> List[str]:
    """
    Convert an arbitrary list of skill names/aliases into
    unique canonical skill names.
    """

    result = []

    seen = set()

    for skill in skills or []:

        canonical = normalize_skill_name(
            skill
        )

        if not canonical:

            continue

        if canonical in seen:

            continue

        seen.add(
            canonical
        )

        result.append(
            canonical
        )

    return result


# ============================================================
# COMPARE SKILLS
# ============================================================

def compare_skills(
    resume_text: str,
    job_description: str
) -> Dict:
    """
    Compare resume skills against job requirements.

    Returns the same main structure expected by main.py:

        resume_skills
        required_skills
        matched_skills
        missing_skills

    Additional fields are included for explainability but
    existing callers can continue using the original fields.
    """

    resume_text = (
        resume_text
        or
        ""
    )

    job_description = (
        job_description
        or
        ""
    )

    # --------------------------------------------------------
    # EXTRACT
    # --------------------------------------------------------

    resume_skills = extract_resume_skills(
        resume_text
    )

    required_skills = extract_required_skills(
        job_description
    )

    # --------------------------------------------------------
    # CANONICALIZE
    # --------------------------------------------------------

    resume_skills = canonicalize_skills(
        resume_skills
    )

    required_skills = canonicalize_skills(
        required_skills
    )

    resume_set = set(
        resume_skills
    )

    required_set = set(
        required_skills
    )

    # --------------------------------------------------------
    # MATCH
    # --------------------------------------------------------

    matched_skills = [

        skill

        for skill in required_skills

        if skill in resume_set
    ]

    # --------------------------------------------------------
    # MISSING
    # --------------------------------------------------------

    missing_skills = [

        skill

        for skill in required_skills

        if skill not in resume_set
    ]

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    matched_evidence = {}

    for skill in matched_skills:

        evidence = find_skill_evidence(
            skill,
            resume_text
        )

        matched_evidence[
            skill
        ] = evidence

    missing_evidence = {}

    for skill in missing_skills:

        missing_evidence[
            skill
        ] = None

    # --------------------------------------------------------
    # UNKNOWN TECHNOLOGY TERMS
    # --------------------------------------------------------
    #
    # This is an additional diagnostic mechanism.
    #
    # We do NOT automatically treat arbitrary nouns as skills,
    # because that would create many false positives.
    #
    # Instead, common technology-looking phrases are detected
    # and returned separately so the taxonomy can be expanded.
    # --------------------------------------------------------

    unknown_terms = detect_unknown_technology_terms(
        job_description,
        known_skills=set(
            SKILL_ALIASES.keys()
        )
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    if required_skills:

        skill_match_score = round(

            (
                len(matched_skills)
                /
                len(required_skills)
            )
            *
            100,

            2
        )

    else:

        skill_match_score = 0.0

    return {

        # Existing fields -----------------------------

        "resume_skills": resume_skills,

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        # Existing-style score -----------------------

        "skill_match_score": skill_match_score,

        # New explainability --------------------------

        "matched_skill_evidence": (
            matched_evidence
        ),

        "missing_skill_evidence": (
            missing_evidence
        ),

        # New taxonomy diagnostic ---------------------

        "unknown_skill_candidates": (
            unknown_terms
        )
    }


# ============================================================
# SKILL MATCH SCORE
# ============================================================

def calculate_skill_match_score(
    required_skills: List[str],
    matched_skills: List[str]
) -> float:
    """
    Calculate percentage of required skills matched.
    """

    required = canonicalize_skills(
        required_skills
    )

    matched = canonicalize_skills(
        matched_skills
    )

    if not required:

        return 0.0

    matched_set = set(
        matched
    )

    score = (
        len(
            [
                skill
                for skill in required
                if skill in matched_set
            ]
        )
        /
        len(required)
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


# ============================================================
# EVIDENCE-AWARE SKILL SCORE
# ============================================================

def calculate_evidence_aware_skill_score(
    required_skills: List[str],
    matched_skills: List[str],
    resume_text: str
) -> Dict:
    """
    Compatibility/helper function for evidence-aware scoring.

    It does NOT replace the normal skill score.

    It provides evidence for each matched skill so downstream
    modules can decide whether the evidence is dated, project-
    based, or simply a skills-section mention.
    """

    required = canonicalize_skills(
        required_skills
    )

    matched = canonicalize_skills(
        matched_skills
    )

    matched_set = set(
        matched
    )

    details = []

    for skill in required:

        evidence = find_skill_evidence(
            skill,
            resume_text
        )

        details.append({

            "skill": skill,

            "matched": (
                skill in matched_set
            ),

            "has_evidence": (
                evidence is not None
            ),

            "evidence": evidence
        })

    score = calculate_skill_match_score(
        required,
        matched
    )

    return {

        "skill_match_score": score,

        "details": details
    }


# ============================================================
# UNKNOWN TECHNOLOGY DETECTION
# ============================================================

# Technology-looking words that are useful for identifying
# possible vocabulary gaps.
#
# They are NOT automatically added to the matched skill list.
# That is intentional: otherwise ordinary words could become
# false-positive skills.

TECHNOLOGY_CANDIDATE_PATTERNS = [

    # Product/framework names with characteristic suffixes.
    r"\b[A-Za-z][A-Za-z0-9]*\.js\b",

    r"\b[A-Za-z][A-Za-z0-9]*\.net\b",

    # Common technology categories.
    r"\b[A-Za-z][A-Za-z0-9-]*(?:DB|DBMS)\b",

    # Capitalized technical names.
    r"\b(?:Apache|Amazon|Google|Microsoft|HashiCorp)\s+"
    r"[A-Za-z][A-Za-z0-9.-]+\b",
]


def detect_unknown_technology_terms(
    text: str,
    known_skills: Optional[set] = None
) -> List[str]:
    """
    Identify technology-looking phrases that are not currently
    represented in the taxonomy.

    This is intentionally a diagnostic mechanism rather than
    automatic skill extraction.

    It helps address the fixed-vocabulary limitation without
    introducing uncontrolled false positives.
    """

    if not text:

        return []

    known = set(
        known_skills
        or
        SKILL_ALIASES.keys()
    )

    normalized_text = normalize_whitespace(
        text
    )

    candidates = []

    for pattern in TECHNOLOGY_CANDIDATE_PATTERNS:

        matches = re.findall(
            pattern,
            normalized_text
        )

        for match in matches:

            candidate = (
                match
                if isinstance(
                    match,
                    str
                )
                else
                " ".join(match)
            )

            candidate = normalize_whitespace(
                candidate
            )

            if not candidate:

                continue

            canonical = normalize_skill_name(
                candidate
            )

            if canonical in known:

                continue

            if candidate.lower() in {
                alias.lower()
                for skill in known
                for alias in get_skill_aliases(
                    skill
                )
            }:

                continue

            if candidate not in candidates:

                candidates.append(
                    candidate
                )

    return candidates

# ============================================================
# OPEN-VOCABULARY SKILL DETECTION
# ============================================================
#
# The original system depended entirely on SKILL_ALIASES.
# That creates a fixed-vocabulary limitation:
#
#     New technology not in taxonomy
#              ↓
#          not detected
#
# The functions below provide a deterministic fallback.
#
# Existing taxonomy matching remains the primary mechanism.
# Open-vocabulary detection is used only when a term appears
# in a skill/technology-related context.
#
# This avoids treating every noun in a JD as a skill.
# ============================================================


OPEN_VOCABULARY_CONTEXT_PATTERN = re.compile(
    r"""
    (?:
        skills?
        |
        technologies?
        |
        technology
        |
        tools?
        |
        frameworks?
        |
        libraries
        |
        platforms?
        |
        experience\s+with
        |
        knowledge\s+of
        |
        proficiency\s+in
        |
        expertise\s+in
        |
        familiar(?:ity)?\s+with
        |
        working\s+with
        |
        using
        |
        hands[-\s]?on\s+with
        |
        exposure\s+to
        |
        required
        |
        preferred
        |
        experience
    )
    \s*
    (?:
        (?:in|with|using|of|on|to|:)\s*
    )?
    (?P<value>
        [A-Za-z0-9][A-Za-z0-9+#./_-]*
        (?:
            \s+
            [A-Za-z0-9][A-Za-z0-9+#./_-]*
        ){0,3}
    )
    """,
    re.IGNORECASE | re.VERBOSE
)


# Common natural-language words that must never become
# automatically detected skills.
OPEN_VOCABULARY_STOPWORDS = {
    "and",
    "or",
    "the",
    "with",
    "using",
    "use",
    "used",
    "for",
    "from",
    "into",
    "including",
    "include",
    "required",
    "preferred",
    "experience",
    "knowledge",
    "strong",
    "good",
    "excellent",
    "working",
    "work",
    "development",
    "developer",
    "engineering",
    "engineer",
    "software",
    "application",
    "applications",
    "system",
    "systems",
    "project",
    "projects",
    "candidate",
    "candidates",
    "team",
    "teams",
    "ability",
    "skills",
    "skill",
    "technology",
    "technologies",
    "tools",
    "tool",
    "framework",
    "frameworks",
    "platform",
    "platforms",
    "environment",
    "environments",
    "years",
    "year",
    "months",
    "month",
    "plus",
    "preferred",
    "required",
    "responsibilities",
    "responsibility",
    "requirements",
    "requirement",
}


def _clean_open_vocabulary_candidate(
    candidate: str
) -> str:
    """
    Clean a candidate discovered by the open-vocabulary
    detector.
    """

    if not candidate:
        return ""

    candidate = normalize_whitespace(
        candidate
    )

    candidate = candidate.strip(
        " \t\n\r,;:()[]{}<>\"'"
    )

    # Remove common sentence-ending punctuation.
    candidate = candidate.rstrip(
        ".,;:"
    )

    return candidate


def _looks_like_skill_candidate(
    candidate: str
) -> bool:
    """
    Determine whether a candidate looks sufficiently
    technology-like to be considered by the fallback
    detector.

    This is intentionally conservative.
    """

    if not candidate:
        return False

    normalized = normalize_whitespace(
        candidate
    ).lower()

    if not normalized:
        return False

    words = normalized.split()

    # Entire candidate cannot be a stopword.
    if all(
        word in OPEN_VOCABULARY_STOPWORDS
        for word in words
    ):
        return False

    # Single ordinary words should not automatically
    # become skills.
    if len(words) == 1:

        word = words[0]

        if word in OPEN_VOCABULARY_STOPWORDS:
            return False

        # Very short ordinary words are dangerous.
        if len(word) < 3:
            return False

    # Strong technology indicators.
    technology_indicators = (

        "."
        in normalized

        or
        "/"
        in normalized

        or
        "#"
        in normalized

        or
        "+"
        in normalized

        or
        "-"
        in normalized

        or
        any(
            suffix in normalized
            for suffix in (
                "js",
                "sql",
                "api",
                "db",
                "cloud",
                "framework",
                "sdk",
                "orm",
                "engine",
                "kubernetes",
                "terraform",
            )
        )
    )

    if technology_indicators:
        return True

    # Multi-word candidates are much more likely to be
    # meaningful technologies than isolated generic words.
    if len(words) >= 2:
        return True

    return False


def extract_open_vocabulary_skills(
    job_description: str
) -> List[str]:
    """
    Discover technology/skill candidates that are not
    necessarily present in SKILL_ALIASES.

    Existing taxonomy detection remains unchanged.

    This function only considers text appearing near
    skill-related context such as:

        Skills:
        Technologies:
        Experience with:
        Knowledge of:
        Proficiency in:
        Tools:
        Frameworks:

    Therefore it does not simply treat every noun in the
    job description as a skill.
    """

    if not job_description:
        return []

    text = normalize_whitespace(
        job_description
    )

    candidates = []

    # --------------------------------------------------------
    # 1. Extract terms from explicit skill-context phrases.
    # --------------------------------------------------------

    for match in OPEN_VOCABULARY_CONTEXT_PATTERN.finditer(
        text
    ):

        value = match.group(
            "value"
        )

        value = _clean_open_vocabulary_candidate(
            value
        )

        if not value:
            continue

        # Split comma-separated or semicolon-separated
        # fragments if they survived normalization.
        fragments = re.split(
            r"\s*(?:,|;|\||•)\s*",
            value
        )

        for fragment in fragments:

            fragment = _clean_open_vocabulary_candidate(
                fragment
            )

            if not fragment:
                continue

            if not _looks_like_skill_candidate(
                fragment
            ):
                continue

            canonical = normalize_skill_name(
                fragment
            )

            # If already represented by taxonomy,
            # existing extraction handles it.
            if canonical in SKILL_ALIASES:
                continue

            # Avoid duplicates.
            normalized_candidate = (
                fragment.lower()
            )

            if normalized_candidate in {
                item.lower()
                for item in candidates
            }:
                continue

            candidates.append(
                fragment
            )

    # --------------------------------------------------------
    # 2. Detect explicit technical patterns.
    #
    # Examples:
    #
    #   LangChain
    #   Next.js
    #   .NET
    #   C++
    #   C#
    #   React Native
    #   Spring Boot
    # --------------------------------------------------------

    technical_patterns = [

        r"(?<!\w)\.[A-Za-z][A-Za-z0-9]+",

        r"(?<!\w)[A-Za-z][A-Za-z0-9]*\.(?:js|ts|net|io)",

        r"(?<!\w)[A-Za-z][A-Za-z0-9+#-]*(?:JS|TS|SQL|DB)\b",

        r"(?<!\w)[A-Za-z][A-Za-z0-9+#-]+\+\+",

        r"(?<!\w)[A-Za-z][A-Za-z0-9+#-]+#",

    ]

    for pattern in technical_patterns:

        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE
        ):

            candidate = _clean_open_vocabulary_candidate(
                match.group(0)
            )

            if not candidate:
                continue

            if not _looks_like_skill_candidate(
                candidate
            ):
                continue

            canonical = normalize_skill_name(
                candidate
            )

            if canonical in SKILL_ALIASES:
                continue

            if candidate.lower() not in {
                item.lower()
                for item in candidates
            }:
                candidates.append(
                    candidate
                )

    return candidates


# ============================================================
# OPEN-VOCABULARY CANONICALIZATION
# ============================================================

def canonicalize_open_vocabulary_skill(
    skill: str
) -> str:
    """
    Convert an unknown skill candidate into a stable
    canonical representation.

    Unlike normalize_skill_name(), this does not require
    the skill to exist in SKILL_ALIASES.
    """

    if not skill:
        return ""

    value = normalize_whitespace(
        skill
    ).lower()

    value = value.strip(
        " \t\n\r,;:()[]{}<>\"'"
    )

    return value


# ============================================================
# EXTENDED REQUIRED-SKILL EXTRACTION
# ============================================================

def extract_required_skills_extended(
    job_description: str
) -> List[str]:
    """
    Extract required skills using two layers:

    Layer 1:
        Existing deterministic taxonomy.

    Layer 2:
        Open-vocabulary technology detection.

    This removes the dependency on a completely fixed
    predefined vocabulary.
    """

    if not job_description:
        return []

    # Existing behavior remains the primary source.
    known_skills = extract_required_skills(
        job_description
    )

    known_skills = canonicalize_skills(
        known_skills
    )

    known_set = set(
        known_skills
    )

    # New open-vocabulary fallback.
    unknown_candidates = (
        extract_open_vocabulary_skills(
            job_description
        )
    )

    result = list(
        known_skills
    )

    for candidate in unknown_candidates:

        canonical = (
            canonicalize_open_vocabulary_skill(
                candidate
            )
        )

        if not canonical:
            continue

        if canonical in known_set:
            continue

        result.append(
            canonical
        )

        known_set.add(
            canonical
        )

    return result


# ============================================================
# OPEN-VOCABULARY SKILL MATCHING
# ============================================================

def open_vocabulary_skill_in_text(
    skill: str,
    text: str
) -> bool:
    """
    Match an unknown/open-vocabulary skill using the same
    boundary-aware logic used by the normal taxonomy.

    This is important because limitation 62 must not be
    solved by reintroducing unsafe substring matching.
    """

    if not skill or not text:
        return False

    normalized_text = normalize_whitespace(
        text
    )

    normalized_skill = (
        canonicalize_open_vocabulary_skill(
            skill
        )
    )

    if not normalized_skill:
        return False

    pattern = build_skill_pattern(
        normalized_skill
    )

    return (
        re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE
        )
        is not None
    )


def find_open_vocabulary_skill_evidence(
    skill: str,
    text: str,
    context_chars: int = 180
) -> Optional[str]:
    """
    Return evidence for an open-vocabulary skill.
    """

    if not skill or not text:
        return None

    normalized_text = normalize_whitespace(
        text
    )

    normalized_skill = (
        canonicalize_open_vocabulary_skill(
            skill
        )
    )

    if not normalized_skill:
        return None

    pattern = build_skill_pattern(
        normalized_skill
    )

    match = re.search(
        pattern,
        normalized_text,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    start = max(
        0,
        match.start() - context_chars
    )

    end = min(
        len(normalized_text),
        match.end() + context_chars
    )

    return normalized_text[
        start:end
    ].strip()


# ============================================================
# EXTENDED SKILL COMPARISON
# ============================================================

def compare_skills_extended(
    resume_text: str,
    job_description: str
) -> Dict:
    """
    Extended comparison that supports both:

        1. predefined taxonomy skills
        2. previously unseen technology candidates

    Existing compare_skills() remains untouched for
    backward compatibility.

    This function can be used by main.py to eliminate
    limitation 62.
    """

    resume_text = (
        resume_text
        or
        ""
    )

    job_description = (
        job_description
        or
        ""
    )

    # --------------------------------------------------------
    # Existing taxonomy extraction
    # --------------------------------------------------------

    resume_taxonomy_skills = extract_resume_skills(
        resume_text
    )

    required_taxonomy_skills = extract_required_skills(
        job_description
    )

    resume_taxonomy_skills = canonicalize_skills(
        resume_taxonomy_skills
    )

    required_taxonomy_skills = canonicalize_skills(
        required_taxonomy_skills
    )

    # --------------------------------------------------------
    # Open-vocabulary JD skills
    # --------------------------------------------------------

    open_required_skills = (
        extract_open_vocabulary_skills(
            job_description
        )
    )

    # --------------------------------------------------------
    # Resume open-vocabulary candidates
    #
    # We use the same detector on resume text so an
    # unknown technology can be recognized there too.
    # --------------------------------------------------------

    open_resume_skills = (
        extract_open_vocabulary_skills(
            resume_text
        )
    )

    # --------------------------------------------------------
    # Build canonical lists
    # --------------------------------------------------------

    required_skills = list(
        required_taxonomy_skills
    )

    required_set = set(
        required_skills
    )

    for skill in open_required_skills:

        canonical = (
            canonicalize_open_vocabulary_skill(
                skill
            )
        )

        if not canonical:
            continue

        if canonical in required_set:
            continue

        required_skills.append(
            canonical
        )

        required_set.add(
            canonical
        )

    resume_skills = list(
        resume_taxonomy_skills
    )

    resume_set = set(
        resume_skills
    )

    for skill in open_resume_skills:

        canonical = (
            canonicalize_open_vocabulary_skill(
                skill
            )
        )

        if not canonical:
            continue

        if canonical in resume_set:
            continue

        resume_skills.append(
            canonical
        )

        resume_set.add(
            canonical
        )

    # --------------------------------------------------------
    # Match
    # --------------------------------------------------------

    matched_skills = []

    missing_skills = []

    matched_evidence = {}

    for skill in required_skills:

        # Known taxonomy skill.
        if skill in SKILL_ALIASES:

            matched = skill_in_text(
                skill,
                resume_text
            )

        # Unknown/open-vocabulary skill.
        else:

            matched = (
                open_vocabulary_skill_in_text(
                    skill,
                    resume_text
                )
            )

        if matched:

            matched_skills.append(
                skill
            )

            if skill in SKILL_ALIASES:

                evidence = find_skill_evidence(
                    skill,
                    resume_text
                )

            else:

                evidence = (
                    find_open_vocabulary_skill_evidence(
                        skill,
                        resume_text
                    )
                )

            matched_evidence[
                skill
            ] = evidence

        else:

            missing_skills.append(
                skill
            )

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    if required_skills:

        score = (
            len(matched_skills)
            /
            len(required_skills)
        ) * 100

    else:

        score = 0.0

    # --------------------------------------------------------
    # Identify which skills came from the open vocabulary
    # --------------------------------------------------------

    open_vocabulary_required = [

        skill

        for skill in required_skills

        if skill not in SKILL_ALIASES
    ]

    open_vocabulary_matched = [

        skill

        for skill in matched_skills

        if skill not in SKILL_ALIASES
    ]

    open_vocabulary_missing = [

        skill

        for skill in missing_skills

        if skill not in SKILL_ALIASES
    ]

    return {

        "resume_skills": resume_skills,

        "required_skills": required_skills,

        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "skill_match_score": round(
            score,
            2
        ),

        "matched_skill_evidence": (
            matched_evidence
        ),

        # New information -------------------------------

        "open_vocabulary_required_skills": (
            open_vocabulary_required
        ),

        "open_vocabulary_matched_skills": (
            open_vocabulary_matched
        ),

        "open_vocabulary_missing_skills": (
            open_vocabulary_missing
        ),

        "taxonomy_skill_count": len(
            [
                skill
                for skill in required_skills
                if skill in SKILL_ALIASES
            ]
        ),

        "open_vocabulary_skill_count": len(
            open_vocabulary_required
        ),

        "vocabulary_mode": (
            "hybrid_taxonomy_and_open_vocabulary"
        )
    }
# ============================================================
# TAXONOMY INFORMATION
# ============================================================

def get_skill_taxonomy() -> Dict[str, List[str]]:
    """
    Return a copy of the current taxonomy.

    Returning a copy prevents accidental mutation of the
    global dictionary by other modules.
    """

    return {
        skill: list(aliases)
        for skill, aliases
        in SKILL_ALIASES.items()
    }


def get_all_canonical_skills() -> List[str]:
    """
    Return all canonical skill names.
    """

    return list(
        SKILL_ALIASES.keys()
    )


def is_known_skill(
    skill: str
) -> bool:
    """
    Check whether a skill/alias belongs to the taxonomy.
    """

    canonical = normalize_skill_name(
        skill
    )

    return (
        canonical
        in
        SKILL_ALIASES
    )


# ============================================================
# ADD SKILL TO TAXONOMY AT RUNTIME
# ============================================================

def register_skill(
    canonical_name: str,
    aliases: Optional[List[str]] = None
) -> str:
    """
    Add a new canonical skill and aliases to the in-memory
    taxonomy.

    This does not persist to a database.

    It gives the application a clean extension point for a
    future database-backed skill ontology.
    """

    canonical = normalize_whitespace(
        canonical_name
    ).lower()

    if not canonical:

        raise ValueError(
            "canonical_name cannot be empty"
        )

    if canonical not in SKILL_ALIASES:

        SKILL_ALIASES[
            canonical
        ] = []

    if aliases:

        for alias in aliases:

            alias_value = normalize_whitespace(
                alias
            ).lower()

            if not alias_value:

                continue

            if alias_value not in SKILL_ALIASES[
                canonical
            ]:

                SKILL_ALIASES[
                    canonical
                ].append(
                    alias_value
                )

    return canonical


# ============================================================
# LEGACY PATTERN MAP
# ============================================================
#
# Older code can still import SKILL_PATTERNS.
#
# We generate it from the canonical taxonomy instead of
# maintaining a second independent dictionary.
# ============================================================

SKILL_PATTERNS: Dict[str, List[str]] = {

    skill: [
        build_skill_pattern(alias)
        for alias
        in get_skill_aliases(skill)
    ]

    for skill
    in SKILL_ALIASES
}


# ============================================================
# LEGACY FUNCTION
# ============================================================

def get_skill_pattern(
    skill: str
) -> List[str]:
    """
    Backward-compatible access to regex patterns.
    """

    canonical = normalize_skill_name(
        skill
    )

    return SKILL_PATTERNS.get(
        canonical,
        [
            build_skill_pattern(
                canonical
            )
        ]
    )


# ============================================================
# TEST / DEBUG
# ============================================================

if __name__ == "__main__":

    test_resume = """
    Developed web applications using Python, React.js,
    Node.js and RESTful APIs.

    Used Git and GitHub for version control.

    Worked with PostgreSQL and MongoDB.

    Docker and AWS are planned for future deployment.
    """

    test_jd = """
    We require Python, React, REST APIs, Docker and AWS.
    Git experience is preferred.
    """

    print(
        "RESUME SKILLS:"
    )

    print(
        extract_skills(
            test_resume
        )
    )

    print(
        "\nREQUIRED SKILLS:"
    )

    print(
        extract_required_skills(
            test_jd
        )
    )

    print(
        "\nCOMPARISON:"
    )

    comparison = compare_skills(
        test_resume,
        test_jd
    )

    print(
        comparison
    )

    print(
        "\nFALSE POSITIVE TEST:"
    )

    print(
        "git in digital =",
        skill_in_text(
            "git",
            "digital transformation"
        )
    )

    print(
        "git in GitHub =",
        skill_in_text(
            "git",
            "GitHub"
        )
    )

    print(
        "python in Python developer =",
        skill_in_text(
            "python",
            "Python developer"
        )
    )

    print(
        "api in capital =",
        skill_in_text(
            "api",
            "capital investment"
        )
    )
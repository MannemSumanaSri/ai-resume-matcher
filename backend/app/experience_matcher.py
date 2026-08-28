"""
AI Resume Matcher - Experience Matcher

Date-range + skill-evidence based experience matching.

Important principle:

A skill appearing in a resume does NOT automatically mean
the candidate has X years of experience with that skill.

Example:

    "Python" in Technical Skills
        -> skill evidence
        -> NOT automatically 3 years

    "Python | Jan 2024 - Jan 2026"
        -> dated evidence
        -> approximately 2 years

    "Built a Python project"
        -> project evidence
        -> demonstrates usage
        -> no invented years

This prevents inflated experience claims.
"""

import re
from datetime import date
from typing import Dict, List, Optional, Tuple


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_PATTERNS = {

    "python": [
        r"\bpython\b",
    ],

    "javascript": [
        r"\bjavascript\b",
        r"\bjava\s*script\b",
    ],

    "typescript": [
        r"\btypescript\b",
    ],

    "react": [
        r"\breact\b",
        r"\breact\.js\b",
        r"\breactjs\b",
    ],

    "node.js": [
        r"\bnode\.?js\b",
        r"\bnodejs\b",
        r"\bnode\s+js\b",
    ],

    "express": [
        r"\bexpress\.?js\b",
        r"\bexpressjs\b",
        r"\bexpress\b",
    ],

    "fastapi": [
        r"\bfastapi\b",
        r"\bfast\s*api\b",
    ],

    "django": [
        r"\bdjango\b",
    ],

    "flask": [
        r"\bflask\b",
    ],

    "html": [
        r"\bhtml\b",
        r"\bhtml5\b",
    ],

    "css": [
        r"\bcss\b",
        r"\bcss3\b",
    ],

    "sql": [
        r"\bsql\b",
    ],

    "mysql": [
        r"\bmysql\b",
    ],

    "postgresql": [
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ],

    "mongodb": [
        r"\bmongodb\b",
        r"\bmongo\s*db\b",
    ],

    "aws": [
        r"\baws\b",
        r"\bamazon web services\b",
    ],

    "azure": [
        r"\bazure\b",
        r"\bmicrosoft azure\b",
    ],

    "docker": [
        r"\bdocker\b",
    ],

    "kubernetes": [
        r"\bkubernetes\b",
        r"\bk8s\b",
    ],

    "git": [
        r"\bgit\b",
    ],

    "github": [
        r"\bgithub\b",
    ],

    "rest api": [
        r"\brestful?\s+apis?\b",
        r"\brest\s+apis?\b",
        r"\brest\s+endpoints?\b",
    ],

    "api": [
        r"\bapi\b",
        r"\bapis\b",
    ],

    "oauth": [
        r"\boauth\b",
        r"\boauth2\b",
    ],

    "jwt": [
        r"\bjwt\b",
        r"\bjson web token\b",
    ],

    "authentication": [
        r"\bauthentication\b",
    ],

    "authorization": [
        r"\bauthorization\b",
        r"\brole[- ]based authorization\b",
    ],
}


# ============================================================
# MONTH PARSING
# ============================================================

MONTHS = {
    "january": 1,
    "jan": 1,

    "february": 2,
    "feb": 2,

    "march": 3,
    "mar": 3,

    "april": 4,
    "apr": 4,

    "may": 5,

    "june": 6,
    "jun": 6,

    "july": 7,
    "jul": 7,

    "august": 8,
    "aug": 8,

    "september": 9,
    "sep": 9,
    "sept": 9,

    "october": 10,
    "oct": 10,

    "november": 11,
    "nov": 11,

    "december": 12,
    "dec": 12,
}


# ============================================================
# NORMALIZE
# ============================================================

def normalize_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = str(text)

    text = text.replace(
        "\u2013",
        "-"
    )

    text = text.replace(
        "\u2014",
        "-"
    )

    text = text.replace(
        "\u2212",
        "-"
    )

    return text


# ============================================================
# PARSE DATE
# ============================================================

def parse_month_year(
    month_text: str,
    year_text: str,
) -> Optional[date]:

    month_key = (
        month_text
        .lower()
        .strip()
    )

    month = MONTHS.get(
        month_key
    )

    if not month:
        return None

    try:

        year = int(
            year_text
        )

        return date(
            year,
            month,
            1,
        )

    except (
        ValueError,
        TypeError,
    ):

        return None


# ============================================================
# DATE RANGE PATTERNS
# ============================================================

DATE_RANGE_PATTERNS = [

    # May 2025 - Aug 2025
    re.compile(
        r"(?P<start_month>"
        r"January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
        r")"
        r"\s+"
        r"(?P<start_year>\d{4})"
        r"\s*[-–—]\s*"
        r"(?P<end_month>"
        r"January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
        r")"
        r"\s+"
        r"(?P<end_year>\d{4})",
        re.IGNORECASE,
    ),

    # May 2025 - Present
    re.compile(
        r"(?P<start_month>"
        r"January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
        r")"
        r"\s+"
        r"(?P<start_year>\d{4})"
        r"\s*[-–—]\s*"
        r"(?P<end>Present|Current|Now)",
        re.IGNORECASE,
    ),

    # 2024 - 2026
    re.compile(
        r"(?P<start_year>\d{4})"
        r"\s*[-–—]\s*"
        r"(?P<end_year>\d{4})"
    ),

    # 2024 - Present
    re.compile(
        r"(?P<start_year>\d{4})"
        r"\s*[-–—]\s*"
        r"(?P<end>Present|Current|Now)",
        re.IGNORECASE,
    ),
]


# ============================================================
# EXTRACT DATE RANGES
# ============================================================

def extract_date_ranges(
    text: str,
) -> List[Dict]:

    text = normalize_text(
        text
    )

    results = []

    for pattern in DATE_RANGE_PATTERNS:

        for match in pattern.finditer(
            text
        ):

            groups = match.groupdict()

            start = None
            end = None

            # Month + year -> month + year
            if (
                groups.get(
                    "start_month"
                )
                and groups.get(
                    "start_year"
                )
            ):

                start = parse_month_year(
                    groups[
                        "start_month"
                    ],
                    groups[
                        "start_year"
                    ],
                )

            # Month + year -> Present
            if (
                start
                and groups.get(
                    "end"
                )
            ):

                end = date.today()

            # Month + year -> month + year
            elif (
                start
                and groups.get(
                    "end_month"
                )
                and groups.get(
                    "end_year"
                )
            ):

                end = parse_month_year(
                    groups[
                        "end_month"
                    ],
                    groups[
                        "end_year"
                    ],
                )

            # Year -> year
            elif (
                groups.get(
                    "start_year"
                )
                and groups.get(
                    "end_year"
                )
            ):

                try:

                    start = date(
                        int(
                            groups[
                                "start_year"
                            ]
                        ),
                        1,
                        1,
                    )

                    end = date(
                        int(
                            groups[
                                "end_year"
                            ]
                        ),
                        1,
                        1,
                    )

                except ValueError:

                    continue

            # Year -> Present
            elif (
                groups.get(
                    "start_year"
                )
                and groups.get(
                    "end"
                )
            ):

                try:

                    start = date(
                        int(
                            groups[
                                "start_year"
                            ]
                        ),
                        1,
                        1,
                    )

                    end = date.today()

                except ValueError:

                    continue

            if (
                not start
                or not end
            ):

                continue

            if end < start:

                continue

            results.append({

                "start": start,

                "end": end,

                "raw": match.group(
                    0
                ),

                "start_position": (
                    match.start()
                ),

                "end_position": (
                    match.end()
                ),
            })

    # Remove duplicates
    unique = []

    seen = set()

    for item in results:

        key = (
            item["start"],
            item["end"],
        )

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            item
        )

    unique.sort(
        key=lambda item: (
            item["start_position"]
        )
    )

    return unique


# ============================================================
# MONTH DIFFERENCE
# ============================================================

def months_between(
    start: date,
    end: date,
) -> int:

    months = (
        (end.year - start.year)
        * 12
        +
        (end.month - start.month)
    )

    if months < 0:
        return 0

    return months


# ============================================================
# SKILL DETECTION
# ============================================================

def skill_in_text(
    skill: str,
    text: str,
) -> bool:

    patterns = SKILL_PATTERNS.get(
        skill,
        [
            rf"\b{re.escape(skill)}\b"
        ],
    )

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):

            return True

    return False


# ============================================================
# EXTRACT SKILLS FROM TEXT
# ============================================================

def skills_in_text(
    text: str,
) -> List[str]:

    if not text:
        return []

    found = []

    for skill in SKILL_PATTERNS:

        if skill_in_text(
            skill,
            text,
        ):

            found.append(
                skill
            )

    return found


# ============================================================
# EXPERIENCE REQUIREMENT EXTRACTION
# ============================================================

def extract_experience_requirements(
    job_description: str,
) -> List[Dict]:
    """
    Extract explicit years-of-experience requirements from a job
    description.

    Supported examples:

        3 years of Python experience
        3+ years of Python
        3+ years of professional experience with Python
        2+ years of experience with React
        2+ years of experience developing REST APIs
        Python - 3 years
        React: 2 years
        Python (3+ years)
        minimum of 3 years experience with Python
        at least 2 years in React

    Only explicit numeric duration requirements are extracted.
    """

    text = normalize_text(job_description)
    # Normalize common plural/alias forms before requirement extraction.
    text = re.sub(r"\bRESTful\s+APIs\b", "RESTful API", text, flags=re.IGNORECASE)
    text = re.sub(r"\bREST\s+APIs\b", "REST API", text, flags=re.IGNORECASE)
    text = re.sub(r"\bReact\.js\b", "React", text, flags=re.IGNORECASE)
    text = re.sub(r"\bNode\.js\b", "Node.js", text, flags=re.IGNORECASE)
    requirements = []

    experience_skills = [
        "machine learning",
        "restful api",
        "rest api",
        "javascript",
        "typescript",
        "postgresql",
        "mongodb",
        "kubernetes",
        "fastapi",
        "docker",
        "python",
        "react.js",
        "react",
        "node.js",
        "nodejs",
        "express",
        "django",
        "flask",
        "java",
        "c++",
        "c#",
        "mysql",
        "sql",
        "aws",
        "azure",
        "git",
        "graphql",
        "nlp",
    ]

    experience_skills = sorted(
        experience_skills,
        key=len,
        reverse=True,
    )

    skill_pattern = "|".join(
        re.escape(skill)
        for skill in experience_skills
    )

    def add_requirement(
        skill: str,
        years: float,
    ) -> None:
        skill = normalize_skill_name(skill)

        if not skill or years <= 0:
            return

        requirements.append({
            "skill": skill,
            "required_years": years,
        })

    # ------------------------------------------------------------
    # 1. Duration followed by normal experience wording.
    #
    # Examples:
    #   3 years of Python experience
    #   3+ years Python experience
    #   3 years experience with Python
    #   3 years experience in Python
    # ------------------------------------------------------------
    pattern_direct = re.compile(
        r"(?P<years>\d+(?:\.\d+)?)"
        r"\s*\+?\s*(?:years?|yrs?)"
        r"\s*(?:of\s+)?"
        r"(?:experience\s+)?"
        r"(?:with|in|using|on)?\s*"
        r"(?P<skill>"
        + skill_pattern +
        r")"
        r"\b",
        re.IGNORECASE,
    )

    for match in pattern_direct.finditer(text):
        add_requirement(
            match.group("skill"),
            float(match.group("years")),
        )

    # ------------------------------------------------------------
    # 2. Natural-language professional experience.
    #
    # This is the form that the previous implementation missed:
    #
    #   3+ years of professional experience with Python
    #   2+ years of hands-on experience with React
    #   2 years of relevant experience in AWS
    # ------------------------------------------------------------
    pattern_professional = re.compile(
        r"(?P<years>\d+(?:\.\d+)?)"
        r"\s*\+?\s*(?:years?|yrs?)"
        r"\s+"
        r"(?:of\s+)?"
        r"(?:professional|hands?[- ]on|commercial|relevant|"
        r"practical|industry|software|development|engineering)"
        r"\s+"
        r"experience"
        r"\s*(?:with|in|using|on|developing|building)?\s*"
        r"(?P<skill>"
        + skill_pattern +
        r")"
        r"\b",
        re.IGNORECASE,
    )

    for match in pattern_professional.finditer(text):
        add_requirement(
            match.group("skill"),
            float(match.group("years")),
        )

    # ------------------------------------------------------------
    # 3. Experience + action wording.
    #
    #   2+ years of experience developing REST APIs
    #   3 years building Python applications
    # ------------------------------------------------------------
    pattern_action = re.compile(
        r"(?P<years>\d+(?:\.\d+)?)"
        r"\s*\+?\s*(?:years?|yrs?)"
        r"\s+(?:of\s+)?"
        r"(?:experience\s+)?"
        r"(?:developing|building|designing|working\s+with|"
        r"using|programming\s+with|proficiency\s+with|"
        r"proficiency\s+in)"
        r"\s+"
        r"(?P<skill>"
        + skill_pattern +
        r")"
        r"\b",
        re.IGNORECASE,
    )

    for match in pattern_action.finditer(text):
        add_requirement(
            match.group("skill"),
            float(match.group("years")),
        )

    # ------------------------------------------------------------
    # 4. Skill followed by duration.
    #
    #   Python - 3 years
    #   React: 2 years
    #   Python (3+ years)
    # ------------------------------------------------------------
    pattern_skill_first = re.compile(
        r"(?P<skill>"
        + skill_pattern +
        r")"
        r"\s*(?:\(|\[)?\s*"
        r"[:\-–—]?\s*"
        r"(?P<years>\d+(?:\.\d+)?)"
        r"\s*\+?\s*(?:years?|yrs?)"
        r"(?:\)|\])?",
        re.IGNORECASE,
    )

    for match in pattern_skill_first.finditer(text):
        add_requirement(
            match.group("skill"),
            float(match.group("years")),
        )

    # ------------------------------------------------------------
    # 5. Minimum / at-least wording.
    #
    #   minimum of 3 years experience with Python
    #   at least 2 years experience in React
    # ------------------------------------------------------------
    pattern_minimum = re.compile(
        r"(?:minimum\s+of|at\s+least|minimum)"
        r"\s+"
        r"(?P<years>\d+(?:\.\d+)?)"
        r"\s*\+?\s*(?:years?|yrs?)"
        r"\s+(?:of\s+)?"
        r"(?:professional\s+)?"
        r"(?:experience\s+)?"
        r"(?:with|in|using|on|developing|building)\s+"
        r"(?P<skill>"
        + skill_pattern +
        r")"
        r"\b",
        re.IGNORECASE,
    )

    for match in pattern_minimum.finditer(text):
        add_requirement(
            match.group("skill"),
            float(match.group("years")),
        )

    # ------------------------------------------------------------
    # Deduplicate and keep the strongest explicit requirement.
    # ------------------------------------------------------------
    unique = {}

    for requirement in requirements:
        skill = requirement["skill"]
        existing = unique.get(skill)

        if (
            existing is None
            or requirement["required_years"]
            > existing["required_years"]
        ):
            unique[skill] = requirement

    return list(unique.values())


# ============================================================
# NORMALIZE SKILL NAME
# ============================================================

def normalize_skill_name(
    skill: str,
) -> str:

    value = (
        skill
        .lower()
        .strip()
    )

    aliases = {

        "react.js": "react",

        "reactjs": "react",

        "nodejs": "node.js",

        "node js": "node.js",

        "node.js": "node.js",

        "express.js": "express",

        "expressjs": "express",

        "postgres": "postgresql",

        "restful api": "rest api",

        "rest apis": "rest api",

    }

    return aliases.get(
        value,
        value,
    )


# ============================================================
# EXPERIENCE EVIDENCE
# ============================================================
# ============================================================
# SECTION-AWARE EXPERIENCE FILTERING
# ============================================================

SECTION_HEADINGS = [
    "summary", "profile", "objective", "education",
    "academic background", "technical skills", "skills",
    "experience", "work experience", "professional experience",
    "employment", "work history", "internship", "internships",
    "volunteer experience", "projects", "project experience",
    "certifications", "achievements", "courses",
]

PROFESSIONAL_EXPERIENCE_SECTIONS = {
    "experience", "work experience", "professional experience",
    "employment", "work history", "internship", "internships",
    "volunteer experience",
}

NON_PROFESSIONAL_SECTIONS = {
    "education", "academic background", "technical skills", "skills",
    "projects", "project experience", "certifications",
    "achievements", "courses", "summary", "profile", "objective",
}

def _canonical_heading(value: str) -> str:
    value = re.sub(r"[^a-zA-Z ]+", " ", value or "")
    return re.sub(r"\s+", " ", value).strip().lower()

def _find_section_context(
    text: str,
    position: int,
) -> Tuple[Optional[str], int, int]:
    """Find the resume section containing a character position."""
    if not text:
        return None, 0, len(text)

    heading_pattern = re.compile(
        r"(?im)^\s*(?:[-•*|]+\s*)?(?P<heading>"
        + "|".join(re.escape(h) for h in SECTION_HEADINGS)
        + r")\s*[:\-]?\s*$"
    )
    headings = []
    for match in heading_pattern.finditer(text):
        headings.append((
            match.start(),
            match.end(),
            _canonical_heading(match.group("heading")),
        ))

    # PDF extraction sometimes joins a heading to the next text.
    # Use loose heading detection only when line-based detection found none.
    if not headings:
        loose_pattern = re.compile(
            r"\b(" + "|".join(re.escape(h) for h in SECTION_HEADINGS) + r")\b",
            re.IGNORECASE,
        )
        for match in loose_pattern.finditer(text):
            headings.append((
                match.start(), match.end(),
                _canonical_heading(match.group(1)),
            ))

    if not headings:
        return None, 0, len(text)

    headings.sort(key=lambda item: item[0])
    previous = None
    next_heading_start = len(text)
    for item in headings:
        if item[0] <= position:
            previous = item
        else:
            next_heading_start = item[0]
            break

    if previous is None:
        return None, 0, next_heading_start
    return previous[2], previous[1], next_heading_start

def _is_professional_date_range(text: str, date_range: Dict) -> bool:
    """Only professional/work sections can generate experience years."""
    section, _, _ = _find_section_context(
        text, date_range["start_position"]
    )

    if section in PROFESSIONAL_EXPERIENCE_SECTIONS:
        return True
    if section in NON_PROFESSIONAL_SECTIONS:
        return False

    # Conservative fallback for flattened PDF text.
    start = max(0, date_range["start_position"] - 350)
    end = min(len(text), date_range["end_position"] + 350)
    nearby = text[start:end].lower()

    professional_markers = (
        "work experience", "professional experience", "experience",
        "employment", "work history", "internship", "internships",
        "open source contributor", "volunteer experience",
    )
    non_professional_markers = (
        "education", "bachelor", "master", "degree", "university",
        "college", "coursework", "projects", "certifications",
        "certification",
    )
    has_professional = any(x in nearby for x in professional_markers)
    has_non_professional = any(x in nearby for x in non_professional_markers)
    if has_non_professional and not has_professional:
        return False
    return has_professional


def extract_resume_experience(
    resume_text: str,
) -> List[Dict]:
    text = normalize_text(
        resume_text
    )

    date_ranges = extract_date_ranges(
        text
    )

    results = []

    for date_range in date_ranges:
        # Education/project/certification dates are evidence of dates,
        # but they are NOT professional experience.
        if not _is_professional_date_range(
            text,
            date_range,
        ):
            continue

        start = date_range["start"]
        end = date_range["end"]

        months = months_between(
            start,
            end,
        )

        if months <= 0:
            continue

        section, section_start, section_end = _find_section_context(
            text,
            date_range["start_position"],
        )

        position = date_range["start_position"]
        line_start = max(
            section_start,
            position - 500,
        )
        line_end = min(
            section_end,
            date_range["end_position"] + 1800,
        )

        evidence_text = text[line_start:line_end]
        skills = skills_in_text(evidence_text)

        if not skills:
            continue

        for skill in skills:
            results.append({
                "skill": skill,
                "years": round(months / 12, 2),
                "months": months,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "evidence": evidence_text.strip(),
                "date_range": date_range["raw"],
                "evidence_type": "dated_experience",
                "section": section,
            })

    return results


# ============================================================
# NON-DATED SKILL EVIDENCE
# ============================================================

def extract_nondated_skill_evidence(
    resume_text: str,
) -> List[Dict]:

    """
    Detect skills used in projects/certifications/skills
    but DO NOT convert them into years.

    This solves the false claim problem.
    """

    text = normalize_text(
        resume_text
    )

    date_ranges = extract_date_ranges(
        text
    )

    dated_text_ranges = []

    for item in date_ranges:

        start = max(
            0,
            item[
                "start_position"
            ] - 500,
        )

        end = min(
            len(text),
            item[
                "end_position"
            ] + 1800,
        )

        dated_text_ranges.append(
            (
                start,
                end,
            )
        )

    skills = skills_in_text(
        text
    )

    results = []

    for skill in skills:

        # If it has dated evidence, don't duplicate
        # that evidence here.
        has_dated = False

        for start, end in dated_text_ranges:

            segment = text[
                start:end
            ]

            if skill_in_text(
                skill,
                segment,
            ):

                has_dated = True

                break

        if has_dated:
            continue

        # Find a representative occurrence.
        pattern_list = SKILL_PATTERNS.get(
            skill,
            []
        )

        evidence = None

        for pattern in pattern_list:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:

                start = max(
                    0,
                    match.start() - 250,
                )

                end = min(
                    len(text),
                    match.end() + 500,
                )

                evidence = text[
                    start:end
                ].strip()

                break

        results.append({

            "skill": skill,

            "years": 0,

            "months": 0,

            "start": None,

            "end": None,

            "evidence": evidence,

            "date_range": None,

            "evidence_type": (
                "undated_resume_evidence"
            ),
        })

    return results


# ============================================================
# MATCH EXPERIENCE
# ============================================================

def match_experience(
    resume_text: str,
    job_description: str,
) -> Dict:

    requirements = (
        extract_experience_requirements(
            job_description
        )
    )

    # --------------------------------------------------------
    # NO EXPERIENCE REQUIREMENT
    # --------------------------------------------------------

    if not requirements:

        resume_experience = (
            extract_resume_experience(
                resume_text
            )
        )

        return {

            "overall_experience_score": None,

            "experience_requirements": [],

            "has_experience_requirements": False,

            "message": (
                "No explicit experience requirements "
                "were found in the job description."
            ),

            "resume_experience": (
                resume_experience
            ),

            "required_experience": [],
        }

    # --------------------------------------------------------
    # EXTRACT DATED EXPERIENCE
    # --------------------------------------------------------

    dated_experience = (
        extract_resume_experience(
            resume_text
        )
    )

    nondated_evidence = (
        extract_nondated_skill_evidence(
            resume_text
        )
    )

    # Combine for returned resume evidence.
    resume_experience = (
        dated_experience
        +
        nondated_evidence
    )

    # --------------------------------------------------------
    # CALCULATE EACH REQUIREMENT
    # --------------------------------------------------------

    requirement_results = []

    match_percentages = []

    for requirement in requirements:

        skill = requirement[
            "skill"
        ]

        required_years = float(
            requirement[
                "required_years"
            ]
        )

        # ----------------------------------------------------
        # DATED EVIDENCE ONLY COUNTS TOWARD YEARS.
        # ----------------------------------------------------

        matching_evidence = [

            item

            for item in dated_experience

            if normalize_skill_name(
                item["skill"]
            )
            ==
            normalize_skill_name(
                skill
            )
        ]

        detected_months = 0

        best_evidence = None

        for evidence in matching_evidence:

            detected_months += int(
                evidence.get(
                    "months",
                    0
                )
            )

            if best_evidence is None:

                best_evidence = evidence

            elif evidence.get(
                "months",
                0
            ) > best_evidence.get(
                "months",
                0
            ):

                best_evidence = evidence

        # Avoid counting overlapping date ranges twice.
        detected_months = min(
            detected_months,
            120,
        )

        detected_years = round(
            detected_months / 12,
            2,
        )

        if required_years <= 0:

            match_percentage = 100.0

        else:

            match_percentage = (
                detected_years
                /
                required_years
            ) * 100

            match_percentage = min(
                100,
                match_percentage,
            )

        match_percentages.append(
            match_percentage
        )

        # ----------------------------------------------------
        # NON-DATED EVIDENCE
        # ----------------------------------------------------

        non_dated = [

            item

            for item in nondated_evidence

            if normalize_skill_name(
                item["skill"]
            )
            ==
            normalize_skill_name(
                skill
            )
        ]

        if best_evidence:

            evidence_text = (
                best_evidence[
                    "evidence"
                ]
            )

            date_range = (
                best_evidence[
                    "date_range"
                ]
            )

            has_evidence = True

        elif non_dated:

            evidence_text = (
                non_dated[0].get(
                    "evidence"
                )
            )

            date_range = None

            # Skill is demonstrated, but no years
            # can safely be claimed.
            has_evidence = True

        else:

            evidence_text = None

            date_range = None

            has_evidence = False

        requirement_results.append({

            "skill": skill,

            "required_years": required_years,

            "detected_years": detected_years,

            "match_percentage": round(
                match_percentage,
                2,
            ),

            "has_evidence": has_evidence,

            "evidence": evidence_text,

            "date_range": date_range,
        })

    # --------------------------------------------------------
    # OVERALL EXPERIENCE SCORE
    # --------------------------------------------------------

    if match_percentages:

        overall_score = (
            sum(match_percentages)
            /
            len(match_percentages)
        )

    else:

        overall_score = 0.0

    return {

        "overall_experience_score": round(
            max(
                0,
                min(
                    100,
                    overall_score,
                )
            ),
            2,
        ),

        "experience_requirements": (
            requirement_results
        ),

        "has_experience_requirements": True,

        "message": (
            "Experience was compared using "
            "dated resume evidence. Undated "
            "project/skill evidence demonstrates "
            "skill usage but is not converted into "
            "years of experience."
        ),

        "resume_experience": (
            resume_experience
        ),

        "required_experience": requirements,
    }


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def calculate_experience_match(
    resume_text: str,
    job_description: str,
) -> Dict:

    return match_experience(
        resume_text,
        job_description,
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    resume = """
    Technical Skills:
    Python, React.js, JavaScript, REST APIs

    Experience:
    GirlScript Summer of Code
    May 2025 - Aug 2025

    Contributed to open source projects using
    JavaScript, HTML and Git.

    Projects:
    AI Resume Matcher
    Built using Python, FastAPI and React.js.
    """

    jd = """
    We require 3 years of Python experience
    and 2 years of React experience.
    """

    result = match_experience(
        resume,
        jd,
    )

    import json

    print(
        json.dumps(
            result,
            indent=2,
        )
    )
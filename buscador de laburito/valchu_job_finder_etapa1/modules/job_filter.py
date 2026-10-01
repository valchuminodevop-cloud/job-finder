import re


# ============================================================
# CONFIGURACIÓN
# ============================================================

EXCLUDED_TERMS = [
    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "staff",
    "manager",
    "director",
    "head of",
    "vp ",
    "vice president",
    "tier iii",
    "tier iv",
    "level iii",
    "level iv",
    "architect",
    "engineering manager",
]


PREFERRED_TERMS = [
    "junior",
    "jr.",
    "jr ",
    "entry level",
    "entry-level",
    "intern",
    "internship",
    "trainee",
    "associate",
    "graduate",
]


TARGET_ROLE_TERMS = [
    "web developer",
    "frontend developer",
    "front-end developer",
    "frontend",
    "front end",
    "software developer",
    "software engineer",
    "developer",
    "it support",
    "technical support",
    "technical support specialist",
    "help desk",
    "service desk",
    "qa",
    "qa tester",
    "quality assurance",
    "cybersecurity",
    "cyber security",
    "security analyst",
    "it intern",
    "technology intern",
]


# Skills relacionadas con el perfil.
SKILL_WEIGHTS = {

    "html": 8,

    "css": 8,

    "javascript": 10,

    "react": 10,

    "python": 10,

    "sql": 7,

    "git": 6,

    "github": 5,

    "vs code": 3,

    "networking": 8,

    "linux": 7,

    "it support": 8,

    "technical support": 8,

    "customer support": 5,

    "cybersecurity": 10,

    "cyber security": 10,

    "tryhackme": 8,

    "qa": 7,

    "testing": 6,
}


# ============================================================
# UTILIDADES
# ============================================================

def normalize_text(text):
    """
    Convierte un texto a minúsculas
    y elimina espacios innecesarios.
    """

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(text).lower().strip()
    )


def get_job_text(job):
    """
    Une título, descripción, empresa y skills
    para analizar la oferta.
    """

    title = job.get(
        "title",
        ""
    )

    description = job.get(
        "description",
        ""
    )

    company = job.get(
        "company",
        ""
    )

    requirements = job.get(
        "requirements",
        ""
    )

    location = job.get(
        "location",
        ""
    )

    skills = job.get(
        "skills",
        []
    )

    if isinstance(
        skills,
        list
    ):

        skills_text = " ".join(
            str(skill)
            for skill in skills
        )

    else:

        skills_text = str(
            skills
        )

    return normalize_text(
        f"""
        {title}
        {description}
        {requirements}
        {company}
        {location}
        {skills_text}
        """
    )


# ============================================================
# EXCLUSIONES
# ============================================================

def is_excluded(job):
    """
    Devuelve True si el puesto parece estar
    fuera del nivel buscado.
    """

    title = normalize_text(
        job.get(
            "title",
            ""
        )
    )

    for term in EXCLUDED_TERMS:

        if term in title:
            return True

    return False


# ============================================================
# DETECTAR ROLE
# ============================================================

def is_target_role(job):
    """
    Determina si el puesto pertenece a alguna
    de las áreas buscadas.
    """

    text = get_job_text(
        job
    )

    for term in TARGET_ROLE_TERMS:

        if term in text:
            return True

    return False


# ============================================================
# SKILLS
# ============================================================

def find_matching_skills(job):
    """
    Devuelve las skills que aparecen
    en la oferta.
    """

    text = get_job_text(
        job
    )

    matches = []

    for skill in SKILL_WEIGHTS:

        if skill in text:

            matches.append(
                skill
            )

    return matches


# ============================================================
# MATCH SCORE
# ============================================================

def calculate_match_score(job):
    """
    Calcula un porcentaje aproximado
    de compatibilidad.
    """

    title = normalize_text(
        job.get(
            "title",
            ""
        )
    )

    text = get_job_text(
        job
    )

    score = 0

    # --------------------------------------------------------
    # ROLE
    # --------------------------------------------------------

    role_match = False

    for term in TARGET_ROLE_TERMS:

        if term in title:

            role_match = True

            break

    if role_match:

        score += 20

    # --------------------------------------------------------
    # SENIORITY
    # --------------------------------------------------------

    for term in PREFERRED_TERMS:

        if term in title:

            score += 15

            break

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------

    matched_skills = []

    for skill, weight in SKILL_WEIGHTS.items():

        if skill in text:

            matched_skills.append(
                skill
            )

            score += weight

    # --------------------------------------------------------
    # CUSTOMER SERVICE
    # --------------------------------------------------------

    customer_terms = [

        "customer support",

        "customer service",

        "technical support",

        "help desk",

        "service desk",

    ]

    if any(
        term in text
        for term in customer_terms
    ):

        score += 5

    # --------------------------------------------------------
    # REMOTO
    # --------------------------------------------------------

    remote_terms = [

        "remote",

        "work from home",

        "worldwide",

        "anywhere",

        "latam",

        "latin america",

        "americas",

        "argentina",

    ]

    if any(
        term in text
        for term in remote_terms
    ):

        score += 5

    # --------------------------------------------------------
    # LIMITAR SCORE
    # --------------------------------------------------------

    score = min(
        score,
        100
    )

    return (
        score,
        matched_skills
    )


# ============================================================
# FILTRO PRINCIPAL
# ============================================================

def filter_jobs(
    jobs,
    minimum_score=60
):
    """
    Filtra los trabajos y devuelve
    únicamente aquellos que tengan
    suficiente compatibilidad.

    Parámetros:

        jobs:
            lista de trabajos

        minimum_score:
            score mínimo requerido

    Retorna:

        lista de trabajos filtrados
    """

    filtered_jobs = []

    # Seguridad:
    # si por alguna razón jobs no es una lista,
    # devolvemos una lista vacía.

    if not isinstance(
        jobs,
        list
    ):

        return filtered_jobs

    for job in jobs:

        # ----------------------------------------------------
        # Seguridad
        # ----------------------------------------------------

        if not isinstance(
            job,
            dict
        ):

            continue

        # ----------------------------------------------------
        # 1. EXCLUIR SENIOR / LEAD / MANAGER
        # ----------------------------------------------------

        if is_excluded(
            job
        ):

            continue

        # ----------------------------------------------------
        # 2. COMPROBAR ROLE
        # ----------------------------------------------------

        if not is_target_role(
            job
        ):

            continue

        # ----------------------------------------------------
        # 3. CALCULAR SCORE
        # ----------------------------------------------------

        score, matched_skills = (
            calculate_match_score(
                job
            )
        )

        # ----------------------------------------------------
        # 4. GUARDAR INFORMACIÓN DEL MATCH
        # ----------------------------------------------------

        job["match_score"] = score

        job["matched_skills"] = (
            matched_skills
        )

        # ----------------------------------------------------
        # 5. FILTRO FINAL
        # ----------------------------------------------------

        if score >= minimum_score:

            filtered_jobs.append(
                job
            )

    # --------------------------------------------------------
    # ORDENAR
    # --------------------------------------------------------

    filtered_jobs.sort(

        key=lambda job:
            job.get(
                "match_score",
                0
            ),

        reverse=True
    )

    return filtered_jobs


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

def print_filtered_jobs(
    jobs
):
    """
    Muestra los trabajos filtrados
    en la terminal.
    """

    if not jobs:

        print(
            "\nNo se encontraron "
            "trabajos compatibles."
        )

        return

    print()
    print(
        "=" * 70
    )

    print(
        "TRABAJOS COMPATIBLES"
    )

    print(
        "=" * 70
    )

    for index, job in enumerate(
        jobs,
        start=1
    ):

        title = job.get(
            "title",
            "Sin título"
        )

        company = job.get(
            "company",
            "Empresa desconocida"
        )

        location = job.get(
            "location",
            "Sin ubicación"
        )

        url = job.get(
            "url",
            "Sin URL"
        )

        score = job.get(
            "match_score",
            0
        )

        matched_skills = job.get(
            "matched_skills",
            []
        )

        print()
        print(
            f"#{index}"
        )

        print(
            f"Título: {title}"
        )

        print(
            f"Empresa: {company}"
        )

        print(
            f"Ubicación: {location}"
        )

        print(
            f"Match: {score}%"
        )

        if matched_skills:

            print(
                "Skills encontradas: "
                + ", ".join(
                    matched_skills
                )
            )

        print(
            f"URL: {url}"
        )

    print()
    print(
        "=" * 70
    )

    print(
        f"TOTAL DE MATCHES: "
        f"{len(jobs)}"
    )

    print(
        "=" * 70
    )
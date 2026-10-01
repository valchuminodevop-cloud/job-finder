import json
import re
from html import unescape
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET


# ============================================================
# CONFIGURACIÓN
# ============================================================

REMOTEOK_URL = "https://remoteok.com/api"

WWR_URL = "https://weworkremotely.com/remote-jobs.rss"

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/154.0 Safari/537.36"
)


# ============================================================
# SITIOS QUE REQUIEREN PAGO PARA POSTULARSE
# ============================================================
#
# IMPORTANTE:
#
# Esta lista es para sitios/plataformas donde la postulación
# puede requerir pagar créditos, membresía o una tarifa.
#
# Si más adelante agregamos una fuente que permita aplicar
# gratis, podemos sacarla de esta lista.
#
# ============================================================

PAID_APPLICATION_DOMAINS = [

    # Freelance / marketplaces donde pueden requerirse
    # créditos o pagos para enviar propuestas.
    "upwork.com",
    "workana.com",

    # Agregamos acá otros dominios solamente cuando
    # confirmemos que cobrar es obligatorio para postularse.
]


# ============================================================
# FRASES QUE INDICAN PAGO OBLIGATORIO
# ============================================================
#
# Estas frases se buscan en:
#
# - título
# - descripción
# - requisitos
# - instrucciones de aplicación
# - URL
#
# Somos deliberadamente estrictos con las frases que dicen
# que hay que pagar para aplicar.
#
# ============================================================

PAID_APPLICATION_TERMS = [

    # Inglés
    "pay to apply",
    "paid to apply",
    "payment required to apply",
    "payment is required to apply",
    "fee required to apply",
    "application fee",
    "application fee required",
    "fee to apply",
    "fee is required",
    "must pay to apply",
    "must pay to submit",
    "must purchase to apply",
    "purchase required to apply",
    "membership required to apply",
    "subscription required to apply",
    "paid membership required",
    "credits required to apply",
    "credits required to submit",
    "buy credits to apply",
    "purchase credits to apply",
    "pay a fee to apply",
    "pay a fee to submit",
    "pay before applying",
    "payment before applying",

    # Español
    "pagar para postular",
    "pagar para postularse",
    "pago para postular",
    "pago para postularse",
    "tarifa de postulación",
    "tarifa para postular",
    "tarifa para postularse",
    "pago obligatorio",
    "pago requerido",
    "membresía obligatoria",
    "membresia obligatoria",
    "suscripción obligatoria",
    "suscripcion obligatoria",
    "créditos para postular",
    "creditos para postular",
    "comprar créditos para postular",
    "comprar creditos para postular",
]


# ============================================================
# HTTP
# ============================================================

def download_url(
    url,
    accept="*/*"
):
    """
    Descarga contenido desde una URL pública.
    """

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept
        }
    )

    with urlopen(
        request,
        timeout=30
    ) as response:

        return response.read()


# ============================================================
# LIMPIAR HTML
# ============================================================

def strip_html(text):
    """
    Convierte HTML en texto simple.
    """

    if not text:
        return ""

    text = unescape(
        str(text)
    )

    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"</p\s*>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# NORMALIZAR LISTA
# ============================================================

def normalize_list(value):

    if value is None:
        return []

    if isinstance(
        value,
        list
    ):

        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    if isinstance(
        value,
        str
    ):

        parts = re.split(
            r"[,|;/]",
            value
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    return [
        str(value)
    ]


# ============================================================
# UBICACIÓN
# ============================================================

def normalize_location(
    location
):

    if location is None:
        return ""

    if isinstance(
        location,
        list
    ):

        return ", ".join(
            str(item)
            for item in location
        )

    return str(
        location
    ).strip()


# ============================================================
# DOMINIO DE UNA URL
# ============================================================

def get_domain(url):

    if not url:
        return ""

    url = str(
        url
    ).lower().strip()

    # Eliminar protocolo.
    url = re.sub(
        r"^https?://",
        "",
        url
    )

    # Eliminar www.
    url = re.sub(
        r"^www\.",
        "",
        url
    )

    # Quedarnos con dominio.
    domain = url.split(
        "/"
    )[0]

    # Eliminar puerto.
    domain = domain.split(
        ":"
    )[0]

    return domain


# ============================================================
# COMPROBAR DOMINIO
# ============================================================

def is_paid_application_domain(
    url
):
    """
    Comprueba si la URL pertenece a un sitio
    que hemos marcado como plataforma con pago
    necesario para postularse.
    """

    domain = get_domain(
        url
    )

    if not domain:
        return False

    for blocked_domain in PAID_APPLICATION_DOMAINS:

        blocked_domain = (
            blocked_domain.lower()
        )

        if (
            domain == blocked_domain
            or domain.endswith(
                "." + blocked_domain
            )
        ):

            return True

    return False


# ============================================================
# DETECTAR PAGO OBLIGATORIO
# ============================================================

def requires_payment_to_apply(
    job
):
    """
    Determina si una oferta parece requerir
    un pago para poder postularse.

    Devuelve:

        True  -> bloquear oferta

        False -> permitir oferta
    """

    if not isinstance(
        job,
        dict
    ):
        return False

    # --------------------------------------------------------
    # URLs
    # --------------------------------------------------------

    urls = [

        job.get(
            "url",
            ""
        ),

        job.get(
            "apply_url",
            ""
        ),

        job.get(
            "application_url",
            ""
        ),
    ]

    # --------------------------------------------------------
    # 1. DOMINIO BLOQUEADO
    # --------------------------------------------------------

    for url in urls:

        if is_paid_application_domain(
            url
        ):

            return True

    # --------------------------------------------------------
    # 2. TEXTO DE LA OFERTA
    # --------------------------------------------------------

    title = job.get(
        "title",
        ""
    )

    description = job.get(
        "description",
        ""
    )

    requirements = job.get(
        "requirements",
        ""
    )

    application_instructions = job.get(
        "application_instructions",
        ""
    )

    combined_text = " ".join(
        [

            str(title),

            str(description),

            str(requirements),

            str(application_instructions),

            " ".join(
                str(url)
                for url in urls
                if url
            )
        ]
    ).lower()

    combined_text = re.sub(
        r"\s+",
        " ",
        combined_text
    ).strip()

    # --------------------------------------------------------
    # 3. BUSCAR FRASES EXPLÍCITAS
    # --------------------------------------------------------

    for term in PAID_APPLICATION_TERMS:

        if term.lower() in combined_text:

            return True

    # --------------------------------------------------------
    # 4. PATRONES MÁS ESTRICTOS
    # --------------------------------------------------------
    #
    # Estos patrones intentan detectar frases como:
    #
    # "You must purchase 10 credits to apply"
    #
    # "A $5 application fee is required"
    #
    # pero NO deberían bloquear frases como:
    #
    # "salary: $5000"
    #
    # porque eso no tiene relación con pagar para aplicar.
    #

    payment_patterns = [

        r"\bmust\s+(?:pay|purchase|buy)\b[^.]{0,60}\bto\s+(?:apply|submit)\b",

        r"\bpay(?:ing)?\s+(?:a\s+)?(?:\$?\d+\s+)?(?:application\s+)?fee\s+to\s+(?:apply|submit)\b",

        r"\b(?:buy|purchase)\s+(?:\d+\s+)?credits?\s+to\s+(?:apply|submit)\b",

        r"\bapplication\s+fee\b[^.]{0,40}\brequired\b",

        r"\b(?:membership|subscription)\s+(?:is\s+)?required\s+to\s+apply\b",

    ]

    for pattern in payment_patterns:

        match = re.search(
            pattern,
            combined_text,
            flags=re.IGNORECASE
        )

        if match:

            print(f"   motivo: ...{match.group(0)}...")

            return True


# ============================================================
# UBICACIÓN ACEPTABLE
# ============================================================

def is_allowed_location(
    location,
    description=""
):

    combined = (
        f"{location} {description}"
    ).lower()

    # --------------------------------------------------------
    # ACEPTADAS
    # --------------------------------------------------------

    allowed_terms = [

        "worldwide",

        "world wide",

        "anywhere in the world",

        "global",

        "latam",

        "latin america",

        "américa latina",

        "america latina",

        "americas",

        "the americas",

        "south america",

        "argentina",

        "remote - argentina",

        "remote argentina"
    ]

    if any(
        term in combined
        for term in allowed_terms
    ):

        return True

    # --------------------------------------------------------
    # BLOQUEADAS
    # --------------------------------------------------------

    blocked_terms = [

        "usa only",

        "us only",

        "united states only",

        "u.s. only",

        "canada only",

        "europe only",

        "uk only",

        "australia only"
    ]

    if any(
        term in combined
        for term in blocked_terms
    ):

        return False

    # --------------------------------------------------------
    # REMOTO GENÉRICO
    # --------------------------------------------------------

    remote_terms = [

        "remote",

        "remotely",

        "work from home",

        "work-from-home"
    ]

    if any(
        term in combined
        for term in remote_terms
    ):

        return True

    return False


# ============================================================
# REMOTE OK
# ============================================================

def fetch_remoteok():

    jobs = []

    try:

        raw = download_url(
            REMOTEOK_URL,
            accept="application/json"
        )

        data = json.loads(
            raw.decode(
                "utf-8",
                errors="replace"
            )
        )

    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        OSError
    ) as error:

        print(
            f"[RemoteOK] Error: {error}"
        )

        return []

    if not isinstance(
        data,
        list
    ):

        return []

    for item in data:

        if not isinstance(
            item,
            dict
        ):
            continue

        if not item.get(
            "position"
        ):
            continue

        title = (
            item.get(
                "position"
            )
            or item.get(
                "title"
            )
            or ""
        )

        company = (
            item.get(
                "company"
            )
            or "Empresa no especificada"
        )

        description = (
            item.get(
                "description"
            )
            or ""
        )

        location = normalize_location(
            item.get(
                "location"
            )
        )

        tags = normalize_list(
            item.get(
                "tags"
            )
        )

        url = (
            item.get(
                "url"
            )
            or ""
        )

        apply_url = (
            item.get(
                "apply_url"
            )
            or url
        )

        job_id = (

            str(
                item.get(
                    "id"
                )
            )

            if item.get(
                "id"
            )

            else apply_url
        )

        if not location:

            location = (
                "Remote / Worldwide"
            )

        # ----------------------------------------------------
        # CREAR OFERTA
        # ----------------------------------------------------

        job = {

            "id":
                f"remoteok-{job_id}",

            "title":
                title.strip(),

            "company":
                str(company).strip(),

            "location":
                location,

            "remote":
                True,

            "employment_type":
                (
                    item.get(
                        "employment_type"
                    )
                    or "Remote"
                ),

            "source":
                "RemoteOK",

            "url":
                url,

            "apply_url":
                apply_url,

            "description":
                strip_html(
                    description
                ),

            "requirements":
                strip_html(
                    description
                ),

            "skills":
                tags,

            "salary_min":
                item.get(
                    "salary_min"
                ),

            "salary_max":
                item.get(
                    "salary_max"
                ),

            "date_posted":
                (
                    item.get(
                        "date"
                    )
                    or ""
                )
        }

        # ----------------------------------------------------
        # FILTRO DE PAGO
        # ----------------------------------------------------

        if requires_payment_to_apply(
            job
        ):

            print(
                "[BLOQUEADA - PAGO] "
                f"{title} — {company}"
            )

            continue

        # ----------------------------------------------------
        # FILTRO GEOGRÁFICO
        # ----------------------------------------------------

        if not is_allowed_location(
            location,
            description
        ):

            continue

        jobs.append(
            job
        )

    return jobs


# ============================================================
# WE WORK REMOTELY
# ============================================================

def fetch_weworkremotely():

    jobs = []

    try:

        raw = download_url(
            WWR_URL,
            accept=(
                "application/rss+xml, "
                "application/xml, "
                "text/xml"
            )
        )

        root = ET.fromstring(
            raw
        )

    except (
        HTTPError,
        URLError,
        TimeoutError,
        ET.ParseError,
        OSError
    ) as error:

        print(
            f"[WWR] Error: {error}"
        )

        return []

    items = root.findall(
        ".//item"
    )

    for item in items:

        def get_text(tag):

            element = item.find(
                tag
            )

            if element is None:
                return ""

            return (
                element.text
                or ""
            ).strip()

        title_raw = get_text(
            "title"
        )

        link = get_text(
            "link"
        )

        description_raw = get_text(
            "description"
        )

        guid = get_text(
            "guid"
        )

        pub_date = get_text(
            "pubDate"
        )

        description = strip_html(
            description_raw
        )

        # ----------------------------------------------------
        # EMPRESA / TÍTULO
        # ----------------------------------------------------

        company = ""

        title = title_raw

        if ":" in title_raw:

            parts = title_raw.split(
                ":",
                1
            )

            first = parts[0].strip()

            second = parts[1].strip()

            company = first

            title = second

        if not company:

            company = (
                "Empresa no especificada"
            )

        # ----------------------------------------------------
        # UBICACIÓN
        # ----------------------------------------------------

        location = "Remote"

        description_lower = (
            description.lower()
        )

        location_patterns = [

            "worldwide",

            "anywhere in the world",

            "latam",

            "latin america",

            "south america",

            "argentina",

            "americas",

            "usa only",

            "us only",

            "united states only"
        ]

        detected_locations = []

        for pattern in location_patterns:

            if pattern in description_lower:

                detected_locations.append(
                    pattern
                )

        if detected_locations:

            location = ", ".join(
                dict.fromkeys(
                    detected_locations
                )
            )

        # ----------------------------------------------------
        # CREAR OFERTA
        # ----------------------------------------------------

        job_id = (
            guid
            or link
            or title_raw
        )

        job = {

            "id":
                f"wwr-{job_id}",

            "title":
                title,

            "company":
                company,

            "location":
                location,

            "remote":
                True,

            "employment_type":
                "Remote",

            "source":
                "We Work Remotely",

            "url":
                link,

            "apply_url":
                link,

            "description":
                description,

            "requirements":
                description,

            "skills":
                [],

            "date_posted":
                pub_date
        }

        # ----------------------------------------------------
        # FILTRO DE PAGO
        # ----------------------------------------------------

        if requires_payment_to_apply(
            job
        ):

            print(
                "[BLOQUEADA - PAGO] "
                f"{title} — {company}"
            )

            continue

        # ----------------------------------------------------
        # FILTRO GEOGRÁFICO
        # ----------------------------------------------------

        if not is_allowed_location(
            location,
            description
        ):

            continue

        jobs.append(
            job
        )

    return jobs


# ============================================================
# TODAS LAS FUENTES
# ============================================================
from datetime import datetime, timezone
GETONBOARD_URL = "https://www.getonbrd.com/api/v0/search/jobs"

GETONBOARD_QUERIES = [
    "junior",
    "trainee",
    "frontend",
    "soporte",
    "qa",
    "ciberseguridad",
]

GETONBOARD_ALLOWED_COUNTRIES = {"remote", "argentina", "latam", "worldwide"}


def fetch_getonboard():

    jobs = {}

    for query in GETONBOARD_QUERIES:

        try:
            raw = download_url(
                f"{GETONBOARD_URL}?query={query}&per_page=30&expand[]=company",
                accept="application/json"
            )
            data = json.loads(raw.decode("utf-8", errors="replace"))

        except (HTTPError, URLError, TimeoutError,
                json.JSONDecodeError, OSError) as error:

            print(f"[GetOnBoard] Error con '{query}': {error}")
            continue

        for item in data.get("data", []) or []:

            attrs = item.get("attributes", {})

            rel = lambda key: (
                (attrs.get(key) or {}).get("data") or {}
            ).get("id")

            # Niveles: 4 en adelante = senior, se descarta
            seniority = rel("seniority")

            if seniority is not None and int(seniority) >= 4:
                continue

            # Ubicación: solo remoto / Argentina / LATAM
            countries = attrs.get("countries") or []
            countries_lower = {str(c).lower() for c in countries}

            if not countries_lower & GETONBOARD_ALLOWED_COUNTRIES:
                continue

            title = attrs.get("title") or attrs.get("name") or ""

            description = " ".join(
                strip_html(attrs.get(key, ""))
                for key in ("description", "functions", "desirable")
            ).strip()

            company_data = (attrs.get("company") or {}).get("data") or {}

            company = (
                (company_data.get("attributes") or {}).get("name")
                or "Empresa no especificada"
            )

            published = attrs.get("published_at")
            date_posted = ""

            if isinstance(published, (int, float)):
                date_posted = datetime.fromtimestamp(
                    published, tz=timezone.utc
                ).date().isoformat()

            url = (item.get("links") or {}).get("public_url", "")

            job = {
                "id": f"getonboard-{item.get('id')}",
                "title": title.strip(),
                "company": company,
                "location": ", ".join(countries),
                "remote": "remote" in countries_lower,
                "employment_type": "Full-time",
                "source": "Get on Board",
                "url": url,
                "apply_url": url,
                "description": description,
                "requirements": description,
                "skills": [],
                "date_posted": date_posted,
            }

            jobs[job["id"]] = job

    return list(jobs.values())

def fetch_all_sources():

    all_jobs = []

    print()

    print(
        "=" * 70
    )

    print(
        "DESCARGANDO OFERTAS REALES"
    )

    print(
        "=" * 70
    )

    print()

    # --------------------------------------------------------
    # REMOTE OK
    # --------------------------------------------------------

    print(
        "→ Consultando RemoteOK..."
    )

    remoteok_jobs = (
        fetch_remoteok()
    )

    print(
        f"  RemoteOK: "
        f"{len(remoteok_jobs)} ofertas "
        "válidas"
    )

    all_jobs.extend(
        remoteok_jobs
    )

    # --------------------------------------------------------
    # WE WORK REMOTELY
    # --------------------------------------------------------
    print("→ Consultando Get on Board...")

    getonboard_jobs = fetch_getonboard()

    print(f"  Get on Board: {len(getonboard_jobs)} ofertas válidas")

    all_jobs.extend(getonboard_jobs)
    print(
        "→ Consultando "
        "We Work Remotely..."
    )

    wwr_jobs = (
        fetch_weworkremotely()
    )

    print(
        f"  We Work Remotely: "
        f"{len(wwr_jobs)} ofertas "
        "válidas"
    )

    all_jobs.extend(
        wwr_jobs
    )
    # --------------------------------------------------------
    # GET ON BOARD
    # --------------------------------------------------------

    print(
        "→ Consultando Get on Board..."
    )

    getonboard_jobs = fetch_getonboard()

    print(
        f"  Get on Board: "
        f"{len(getonboard_jobs)} ofertas "
        "válidas"
    )

    all_jobs.extend(
        getonboard_jobs
    )
    # --------------------------------------------------------
    # DEDUPLICACIÓN BÁSICA
    # --------------------------------------------------------

    unique_jobs = {}

    for job in all_jobs:

        job_id = (
            job.get("id")
            or job.get("url")
        )

        if job_id:

            unique_jobs[
                str(job_id)
            ] = job

    all_jobs = list(
        unique_jobs.values()
    )

    print()

    print(
        f"Total de ofertas válidas: "
        f"{len(all_jobs)}"
    )

    print()

    return all_jobs
from flask import Flask, render_template, jsonify
from pathlib import Path
from datetime import datetime
import json
import traceback

from modules.job_filter import filter_jobs
from job_searcher import update_jobs


# ============================================================
# CONFIGURACIÓN
# ============================================================

app = Flask(__name__)

BASE_DIR = Path(
    __file__
).resolve().parent

PROFILE_FILE = (
    BASE_DIR / "profile.json"
)

JOBS_FILE = (
    BASE_DIR / "data" / "jobs.json"
)

MATCHES_FILE = (
    BASE_DIR / "data" / "matches.json"
)


# ============================================================
# JSON
# ============================================================

def load_json(
    file_path,
    default=None
):

    if default is None:
        default = {}

    try:

        if not file_path.exists():
            return default

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError
    ):

        return default


def save_json(
    file_path,
    data
):

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# CARGAR OFERTAS
# ============================================================

def get_jobs_from_file():

    data = load_json(
        JOBS_FILE,
        default=[]
    )

    if isinstance(
        data,
        list
    ):
        return data

    if isinstance(
        data,
        dict
    ):

        jobs = data.get(
            "jobs",
            []
        )

        if isinstance(
            jobs,
            list
        ):
            return jobs

    return []


# ============================================================
# SCORE MÍNIMO
# ============================================================

def get_minimum_score():

    profile = load_json(
        PROFILE_FILE,
        default={}
    )

    if not isinstance(
        profile,
        dict
    ):
        return 60

    possible_keys = [
        "minimum_match_score",
        "min_match_score",
        "minimum_score",
        "min_score"
    ]

    for key in possible_keys:

        value = profile.get(
            key
        )

        if value is not None:

            try:
                return int(value)

            except (
                TypeError,
                ValueError
            ):
                pass

    # Tu filtro actual tiene 60 como
    # valor predeterminado.
    return 60


# ============================================================
# UBICACIÓN
# ============================================================

def detect_location_scope(
    location
):

    if location is None:
        return "Sin especificar"

    text = str(
        location
    ).strip()

    if not text:
        return "Sin especificar"

    upper = text.upper()

    if any(
        term in upper
        for term in [
            "WORLDWIDE",
            "WORLD WIDE",
            "ANYWHERE",
            "GLOBAL"
        ]
    ):
        return "Worldwide"

    if any(
        term in upper
        for term in [
            "ARGENTINA",
            "BUENOS AIRES",
            "CÓRDOBA",
            "CORDOBA",
            "ROSARIO",
            "MENDOZA"
        ]
    ):
        return "Argentina"

    if any(
        term in upper
        for term in [
            "LATAM",
            "LATIN AMERICA",
            "AMERICA LATINA"
        ]
    ):
        return "LATAM"

    if any(
        term in upper
        for term in [
            "AMERICAS",
            "THE AMERICAS",
            "NORTH AMERICA",
            "SOUTH AMERICA"
        ]
    ):
        return "Americas"

    if any(
        term in upper
        for term in [
            "REMOTE",
            "REMOTO",
            "REMOTA"
        ]
    ):
        return "Remote"

    return text


# ============================================================
# PREPARAR OFERTA
# ============================================================

def prepare_job_for_web(
    job
):

    if not isinstance(
        job,
        dict
    ):
        job = {}

    title = (
        job.get("title")
        or job.get("name")
        or "Oferta sin título"
    )

    company = (
        job.get("company")
        or job.get("company_name")
        or "Empresa no especificada"
    )

    location = (
        job.get("location")
        or "Ubicación no especificada"
    )

    if isinstance(
        location,
        list
    ):

        location = ", ".join(
            str(item)
            for item in location
        )

    url = (
        job.get("url")
        or job.get("apply_url")
        or job.get("link")
        or "#"
    )

    source = (
        job.get("source")
        or "Fuente desconocida"
    )

    employment_type = (
        job.get("employment_type")
        or "No especificado"
    )

    remote = job.get(
        "remote",
        False
    )

    if isinstance(
        remote,
        str
    ):

        remote = remote.lower() in [
            "true",
            "1",
            "yes",
            "si",
            "sí",
            "remote",
            "remoto",
            "remota"
        ]

    score = (
        job.get("match_score")
        or job.get("score")
        or 0
    )

    try:

        score = float(
            score
        )

    except (
        TypeError,
        ValueError
    ):

        score = 0

    score = max(
        0,
        min(
            100,
            score
        )
    )

    if score.is_integer():
        score = int(score)

    matched_skills = (
        job.get("matched_skills")
        or []
    )

    if isinstance(
        matched_skills,
        str
    ):

        matched_skills = [
            matched_skills
        ]

    if not isinstance(
        matched_skills,
        list
    ):

        matched_skills = []

    location_scope = (
        job.get("location_scope")
        or detect_location_scope(
            location
        )
    )

    prepared = dict(
        job
    )

    prepared.update({

        "title":
            str(title),

        "company":
            str(company),

        "location":
            str(location),

        "url":
            str(url),

        "source":
            str(source),

        "employment_type":
            str(employment_type),

        "remote":
            bool(remote),

        "match_score":
            score,

        "matched_skills":
            matched_skills,

        "location_scope":
            str(location_scope)
    })

    return prepared


# ============================================================
# EJECUTAR FILTRO
# ============================================================

def run_filter():

    jobs = get_jobs_from_file()

    # IMPORTANTE:
    # Usamos el filtro tal como está implementado
    # actualmente.
    #
    # No pasamos minimum_score porque queremos
    # evitar incompatibilidades entre versiones.

    filtered_jobs = filter_jobs(
        jobs
    )

    if not isinstance(
        filtered_jobs,
        list
    ):

        filtered_jobs = []

    web_jobs = [
        prepare_job_for_web(job)
        for job in filtered_jobs
    ]

    result = {

        "generated_at":
            datetime.now().isoformat(),

        "minimum_match_score":
            get_minimum_score(),

        "total_input_jobs":
            len(jobs),

        "total_eligible_jobs":
            len(web_jobs),

        "jobs":
            web_jobs
    }

    save_json(
        MATCHES_FILE,
        result
    )

    return web_jobs


# ============================================================
# RESULTADOS EXISTENTES
# ============================================================

def get_existing_matches():

    data = load_json(
        MATCHES_FILE,
        default={}
    )

    if not isinstance(
        data,
        dict
    ):
        return []

    jobs = data.get(
        "jobs",
        []
    )

    if not isinstance(
        jobs,
        list
    ):
        return []

    return [
        prepare_job_for_web(
            job
        )
        for job in jobs
    ]


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route("/")
def index():

    try:

        # Si no existe matches.json,
        # generamos los primeros resultados.
        if not MATCHES_FILE.exists():

            run_filter()

        jobs = (
            get_existing_matches()
        )

        error_message = None

    except Exception as error:

        jobs = (
            get_existing_matches()
        )

        error_message = str(
            error
        )

        print()
        print("=" * 70)
        print("ERROR EN EL DASHBOARD")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70)
        print()

    total_jobs = len(
        jobs
    )

    high_matches = [
        job
        for job in jobs
        if job.get(
            "match_score",
            0
        ) >= 80
    ]

    remote_jobs = [
        job
        for job in jobs
        if job.get(
            "remote"
        ) is True
    ]

    minimum_score = (
        get_minimum_score()
    )

    total_input_jobs = len(
        get_jobs_from_file()
    )

    data = {

        "generated_at":
            datetime.now().isoformat(),

        "minimum_match_score":
            minimum_score,

        "total_input_jobs":
            total_input_jobs,

        "total_eligible_jobs":
            len(jobs),

        "jobs":
            jobs
    }

    return render_template(

        "index.html",

        jobs=jobs,

        total_jobs=
            total_jobs,

        high_matches=
            len(high_matches),

        remote_jobs=
            len(remote_jobs),

        minimum_score=
            minimum_score,

        generated_at=
            datetime.now().strftime(
                "%d/%m/%Y %H:%M"
            ),

        error_message=
            error_message,

        data=
            data
    )


# ============================================================
# ACTUALIZAR
# ============================================================

@app.route(
    "/refresh",
    methods=["POST"]
)
def refresh():

    try:

        print()
        print(
            "🌐 Descargando ofertas nuevas..."
        )

        # 1. Descargar fuentes reales.
        update_jobs()

        # 2. Filtrar.
        jobs = run_filter()

        return jsonify({

            "success":
                True,

            "message":
                "Ofertas reales actualizadas correctamente.",

            "total_jobs":
                len(jobs)
        })

    except Exception as error:

        print()
        print("=" * 70)
        print("ERROR AL ACTUALIZAR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70)
        print()

        return jsonify({

            "success":
                False,

            "message":
                str(error)

        }), 500


# ============================================================
# API
# ============================================================

@app.route(
    "/api/jobs"
)
def api_jobs():

    try:

        jobs = (
            get_existing_matches()
        )

        return jsonify({

            "success":
                True,

            "total":
                len(jobs),

            "jobs":
                jobs
        })

    except Exception as error:

        return jsonify({

            "success":
                False,

            "message":
                str(error),

            "jobs":
                []

        }), 500


# ============================================================
# SERVIDOR
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("VALCHU JOB FINDER")
    print("=" * 70)
    print()
    print(
        "Dashboard:"
    )
    print(
        "http://127.0.0.1:5000/"
    )
    print()
    print(
        "Para actualizar las ofertas:"
    )
    print(
        "presioná el botón "
        "'Actualizar ofertas' en la página."
    )
    print()
    print("=" * 70)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
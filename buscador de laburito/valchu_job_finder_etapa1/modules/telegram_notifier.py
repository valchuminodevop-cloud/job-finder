import json
import os
import html
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SEEN_JOBS_FILE = BASE_DIR / "data" / "seen_jobs.json"

load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ============================================================
# VALIDAR CONFIGURACIÓN
# ============================================================

def validate_telegram_config():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "Falta TELEGRAM_BOT_TOKEN en el archivo .env"
        )

    if not TELEGRAM_CHAT_ID:
        raise ValueError(
            "Falta TELEGRAM_CHAT_ID en el archivo .env"
        )


# ============================================================
# IDENTIFICAR OFERTA
# ============================================================

def get_job_id(job):
    """
    Genera un identificador estable para evitar
    mandar la misma oferta dos veces.
    """

    job_id = job.get("id")

    if job_id:
        return str(job_id)

    url = job.get("url")

    if url:
        return str(url)

    title = job.get("title", "")
    company = job.get("company", "")

    return f"{title}|{company}".lower()


# ============================================================
# OFERTAS YA ENVIADAS
# ============================================================

def load_seen_jobs():
    if not SEEN_JOBS_FILE.exists():
        return set()

    try:
        with open(
            SEEN_JOBS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return set(
            data.get("sent_jobs", [])
        )

    except (json.JSONDecodeError, OSError):
        return set()


def save_seen_jobs(seen_jobs):

    SEEN_JOBS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data = {
        "sent_jobs": sorted(seen_jobs)
    }

    with open(
        SEEN_JOBS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# ENVIAR MENSAJE A TELEGRAM
# ============================================================

def send_telegram_message(message):

    validate_telegram_config()

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }).encode("utf-8")

    request = Request(
        url,
        data=payload,
        method="POST"
    )

    with urlopen(
        request,
        timeout=20
    ) as response:

        response_data = response.read().decode(
            "utf-8"
        )

    result = json.loads(response_data)

    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram rechazó el mensaje: {result}"
        )

    return result


# ============================================================
# FORMATEAR OFERTA
# ============================================================

def format_job_message(job):

    title = html.escape(
        str(job.get("title", "Sin título"))
    )

    company = html.escape(
        str(job.get("company", "Empresa no especificada"))
    )

    location = html.escape(
        str(job.get("location", "No especificada"))
    )

    score = job.get(
        "match_score",
        0
    )

    skills = job.get(
        "matched_skills",
        []
    )

    if isinstance(skills, list):
        skills_text = ", ".join(
            str(skill)
            for skill in skills
        )
    else:
        skills_text = str(skills)

    skills_text = html.escape(
        skills_text or "No especificadas"
    )

    url = (
        job.get("apply_url")
        or job.get("url")
        or ""
    )

    url = html.escape(
        str(url),
        quote=True
    )

    message = (
        "💼 <b>NUEVA OFERTA COMPATIBLE</b>\n\n"
        f"🎯 <b>{title}</b>\n"
        f"🏢 {company}\n"
        f"📍 {location}\n"
        f"📊 Match: <b>{score}%</b>\n"
        f"🛠 Skills: {skills_text}\n\n"
    )

    if url:
        message += (
            f'🔗 <a href="{url}">POSTULARME</a>\n'
        )

    message += (
        "\n🤖 <i>Encontrada por Valchu Job Finder</i>"
    )

    return message


# ============================================================
# ENVIAR UNA OFERTA
# ============================================================

def send_job_to_telegram(job):

    message = format_job_message(job)

    send_telegram_message(message)


# ============================================================
# ENVIAR OFERTAS NUEVAS
# ============================================================

def send_new_jobs_to_telegram(jobs):

    validate_telegram_config()

    seen_jobs = load_seen_jobs()

    new_jobs = []

    for job in jobs:

        job_id = get_job_id(job)

        # Nunca enviar ejemplos
        url = str(
            job.get("url", "")
        ).lower()

        if "example.com" in url:
            continue

        if job_id in seen_jobs:
            continue

        try:

            send_job_to_telegram(job)

            seen_jobs.add(job_id)

            new_jobs.append(job)

            print(
                f"✓ Telegram: enviada → "
                f"{job.get('title', 'Sin título')}"
            )

        except Exception as error:

            print(
                f"❌ Error enviando a Telegram: "
                f"{error}"
            )

    save_seen_jobs(seen_jobs)

    return new_jobs
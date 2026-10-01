import json
from pathlib import Path
from datetime import datetime

from modules.job_sources import fetch_all_sources
from modules.telegram_notifier import send_new_jobs_to_telegram


# ============================================================
# VALCHU JOB FINDER
# Job matching engine
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

PROFILE_FILE = BASE_DIR / "profile.json"
OUTPUT_FILE = BASE_DIR / "job_matches.json"
import json

from modules.job_sources import fetch_all_sources
from modules.job_filter import filter_jobs

SEEN_FILE = BASE_DIR / "data" / "seen_jobs.json"


def load_json(path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def main():
    profile = load_json(PROFILE_FILE, {})
    min_score = profile.get("job_preferences", {}).get("minimum_match_score", 60)

    # 1. Buscar
    jobs = fetch_all_sources()
    print(f"Ofertas descargadas: {len(jobs)}")

    # 2. Filtrar y puntuar
    matches = filter_jobs(jobs, minimum_score=min_score)
    print(f"Ofertas compatibles: {len(matches)}")
    # 3. Guardar resultados
    save_json(OUTPUT_FILE, matches)

    # 4. Enviar a Telegram (el notificador filtra las ya vistas)
    send_new_jobs_to_telegram(matches)


if __name__ == "__main__":
    main()
import re
import unicodedata
from copy import deepcopy
from typing import Any


def normalize_text(value: Any) -> str:
    """Lowercase, remove accents and normalize whitespace."""
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().lower()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return []


def normalize_job(job: dict) -> dict:
    """
    Return a copy with a predictable schema.
    Does not mutate the original source object.
    """
    if not isinstance(job, dict):
        raise TypeError("Cada oferta debe ser un objeto JSON.")

    normalized = deepcopy(job)
    normalized["id"] = str(job.get("id") or job.get("job_id") or "").strip()
    normalized["source"] = str(job.get("source") or "manual").strip().lower()
    normalized["title"] = str(job.get("title") or "").strip()
    normalized["company"] = str(job.get("company") or "").strip()
    normalized["location"] = str(job.get("location") or "").strip()
    normalized["description"] = str(job.get("description") or "").strip()
    normalized["requirements"] = str(job.get("requirements") or "").strip()
    normalized["employment_type"] = str(job.get("employment_type") or "").strip()
    normalized["seniority"] = str(job.get("seniority") or "").strip()
    normalized["url"] = str(job.get("url") or job.get("apply_url") or "").strip()

    skills = job.get("skills", [])
    if isinstance(skills, str):
        skills = [part.strip() for part in re.split(r"[,;\n]", skills) if part.strip()]
    normalized["skills"] = as_list(skills)

    # A source can provide a normalized scope; otherwise the filter infers it.
    normalized["location_scope"] = str(job.get("location_scope") or "").strip().upper()
    normalized["remote"] = bool(job.get("remote", False))
    return normalized

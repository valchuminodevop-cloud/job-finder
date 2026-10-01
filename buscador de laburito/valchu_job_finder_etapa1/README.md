# Valchu Job Finder — Etapa 1

Esta etapa consolida el formato de ofertas, el filtro geográfico y el motor de compatibilidad.
Todavía no integra fuentes externas, `seen_jobs.json`, notificaciones, automatización ni cartas con IA.

## Estructura

```text
bot buscador de laburito/
├── data/
│   ├── jobs.json          # Tus ofertas actuales (conservar)
│   └── matches.json       # Se genera automáticamente
├── modules/
│   ├── __init__.py
│   ├── job_normalizer.py
│   └── job_filter.py
├── tests/
│   └── test_filter.py
├── profile.json           # Tu perfil actual (conservar)
├── job_searcher.py
└── .gitignore
```

## Requisitos

Python 3.10 o superior. No se necesitan paquetes externos para esta etapa.

## Instalación / reemplazo

1. Hacé una copia de seguridad de tu carpeta actual.
2. Conservá tu `profile.json` y `data/jobs.json`.
3. Copiá `modules/job_normalizer.py`, `modules/job_filter.py` y `modules/__init__.py`.
4. Reemplazá `job_searcher.py` por el de esta etapa.
5. Creá `tests/test_filter.py` y `.gitignore`.
6. No copies archivos `.pyc` ni `__pycache__`.

## Ejecutar

Desde la terminal de VS Code, ubicada en la carpeta raíz:

```powershell
python job_searcher.py
```

## Ejecutar tests

```powershell
python -m unittest discover -s tests -v
```

## Cómo se clasifican las ubicaciones

- `ARGENTINA`, `LATAM`, `AMERICAS`, `WORLDWIDE`: elegible.
- `Remote` sin región confirmada: va a `review_jobs`, no se acepta automáticamente.
- Restricción explícita como `US only`: va a `rejected_jobs`.

La detección por texto es heurística. Revisá las ofertas clasificadas como elegibles antes de postularte, especialmente si dicen `Americas`, porque cada empresa puede definir ese término de manera distinta.

## Contrato de una oferta

Campos normalizados: `id`, `source`, `title`, `company`, `location`, `remote`,
`location_scope`, `employment_type`, `seniority`, `description`, `requirements`,
`skills`, `url`.

Los campos adicionales originales se conservan.

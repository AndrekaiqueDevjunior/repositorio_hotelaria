#!/usr/bin/env python3
"""
Bootstrap comum para executar seeds em ambiente local com segurança.

Uso recomendado:
    cd backend
    python seeds/seed_quartos.py

Opcionalmente, force o arquivo de ambiente:
    SEED_ENV_FILE=backend/.env.test python backend/seeds/seed_quartos.py

Proteção:
    - Se detectar ambiente de produção, aborta por padrão.
    - Para permitir explicitamente, use SEED_ALLOW_PROD=true.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def _mask_database_url(url: str) -> str:
    if not url:
        return "NOT_SET"
    try:
        parsed = urlparse(url)
        if parsed.password:
            masked_netloc = f"{parsed.username}:****@{parsed.hostname}:{parsed.port}"
            return f"{parsed.scheme}://{masked_netloc}{parsed.path}"
        return url
    except Exception:
        return "INVALID_URL"


def _resolve_env_files(backend_dir: Path, project_dir: Path) -> list[Path]:
    explicit = os.getenv("SEED_ENV_FILE", "").strip()
    candidates: list[Path] = []

    if explicit:
        explicit_path = Path(explicit)
        if not explicit_path.is_absolute():
            explicit_path = project_dir / explicit_path
        candidates.append(explicit_path)

    candidates.extend(
        [
            backend_dir / ".env.dev",
            backend_dir / ".env.local",
            backend_dir / ".env.test",
            backend_dir / ".env",
            project_dir / ".env",
        ]
    )

    unique_candidates: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_candidates.append(candidate)
    return unique_candidates


def bootstrap_seed_environment() -> Path | None:
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parents[1]
    project_dir = backend_dir.parent

    backend_dir_str = str(backend_dir)
    if backend_dir_str not in sys.path:
        sys.path.insert(0, backend_dir_str)

    env_loaded: Path | None = None
    if not os.getenv("DATABASE_URL"):
        for env_file in _resolve_env_files(backend_dir, project_dir):
            if env_file.exists():
                load_dotenv(env_file, override=False)
                env_loaded = env_file
                break

    database_url = os.getenv("DATABASE_URL", "")
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    allow_prod = os.getenv("SEED_ALLOW_PROD", "").strip().lower() == "true"

    print("[SEED] Bootstrap inicializado")
    print(f"[SEED] Backend dir: {backend_dir}")
    print(f"[SEED] Env file: {env_loaded if env_loaded else 'process environment'}")
    print(f"[SEED] DATABASE_URL: {_mask_database_url(database_url)}")
    print(f"[SEED] ENVIRONMENT: {environment or 'undefined'}")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL não definida. Configure a variável ou use SEED_ENV_FILE com um .env válido."
        )

    if environment == "production" and not allow_prod:
        raise RuntimeError(
            "Seed bloqueado: ENVIRONMENT=production. "
            "Use um arquivo dev/test com SEED_ENV_FILE ou defina SEED_ALLOW_PROD=true conscientemente."
        )

    return env_loaded

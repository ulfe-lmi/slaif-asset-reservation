from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.management.base import CommandError


def database_url_from_env() -> str:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise CommandError("DATABASE_URL is required.")
    return database_url


def postgres_command_parts(database_url: str) -> tuple[list[str], dict[str, str]]:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
        raise CommandError("DATABASE_URL must be a PostgreSQL URL.")
    command = ["--host", parsed.hostname]
    if parsed.port:
        command += ["--port", str(parsed.port)]
    if parsed.username:
        command += ["--username", unquote(parsed.username)]
    database_name = unquote(parsed.path.strip("/"))
    if not database_name:
        raise CommandError("DATABASE_URL must include a database name.")
    command += ["--dbname", database_name]

    env = os.environ.copy()
    if parsed.password:
        env["PGPASSWORD"] = unquote(parsed.password)
    return command, env


def ensure_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise CommandError(f"{name} is required on PATH.")
    return path


def run_postgres_tool(command: list[str], *, env: dict[str, str]) -> None:
    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise CommandError(
            "PostgreSQL tool failed; see operator logs without database credentials."
        )


def require_parent_directory(path: Path) -> None:
    if not path.parent.exists():
        raise CommandError("Output directory does not exist.")

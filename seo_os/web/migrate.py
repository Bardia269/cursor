"""Migrations de schéma (Alembic) pilotées depuis le code : `seo-os db-upgrade`."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from .db import database_url

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def alembic_config(url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", url or database_url())
    return cfg


def upgrade(url: str | None = None) -> None:
    command.upgrade(alembic_config(url), "head")


def revision(message: str, url: str | None = None) -> None:
    command.revision(alembic_config(url), message=message, autogenerate=True)

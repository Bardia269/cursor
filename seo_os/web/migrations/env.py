"""Environnement Alembic : la cible est seo_os.web.models, l'URL vient de DATABASE_URL."""

from alembic import context
from seo_os.web.db import database_url, make_engine
from seo_os.web.models import Base

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = config.attributes.get("connection")
    if connectable is None:
        engine = make_engine(config.get_main_option("sqlalchemy.url") or database_url())
        try:
            with engine.connect() as connection:
                _run(connection)
        finally:
            engine.dispose()
    else:
        _run(connectable)


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

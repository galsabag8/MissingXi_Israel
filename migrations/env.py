import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from models import db # Imports db (SQLAlchemy instance)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Link the SQLAlchemy models metadata
target_metadata = db.Model.metadata

def get_db_url():
    """
    Retrieves the database URL, prioritizing the DATABASE_URL environment variable.
    """
    # 1. Try to get the live DB URL from environment variables
    url = os.environ.get("DATABASE_URL")
    
    # 2. If not found, fall back to the URL set in alembic.ini (if running locally)
    if not url:
         url = config.get_main_option("sqlalchemy.url")
         # Sanity check for the default placeholder in alembic.ini
         if url == "driver://user:pass@localhost/dbname":
             # This fallback must match the default local dev setup or your specific setup.
             url = "postgresql://postgres:password@localhost:5432/top10game"
             
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # 1. Resolve the URL explicitly
    db_url = get_db_url()
    
    # 2. CRITICAL FIX: Create a separate configuration dictionary.
    # We must overwrite the 'sqlalchemy.url' key that Alembic reads from the .ini file.
    alembic_config_section = config.get_section(config.config_ini_section, {})
    alembic_config_section['sqlalchemy.url'] = db_url # <-- FORCE the URL here
    
    connectable = engine_from_config(
        alembic_config_section, # Pass the modified config section
        prefix="sqlalchemy.",
        # We don't need 'url=db_url' here anymore, as it's in the config dict
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
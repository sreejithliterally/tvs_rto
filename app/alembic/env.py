from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
import models
from alembic import context
from dotenv import load_dotenv
from pathlib import Path

# Adjust the path according to your project structure
env_path = Path("C:/Users/HP/Desktop/tvs_rto/.env")
load_dotenv(dotenv_path=env_path)

# Verify if the environment variables are loaded
database_username = os.getenv("database_username")
database_password = os.getenv("database_password")
database_hostname = os.getenv("database_hostname")
database_port = os.getenv("database_port")
database_name = os.getenv("database_name")

# Print the values to debug
print(f"database_username: {database_username}")
print(f"database_password: {database_password}")
print(f"database_hostname: {database_hostname}")
print(f"database_port: {database_port}")
print(f"database_name: {database_name}")

# Construct the database URL
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{database_username}:{database_password}@{database_hostname}:{database_port}/{database_name}"
)
print(f"Constructed DATABASE_URL: {SQLALCHEMY_DATABASE_URL}")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = models.Base.metadata

# Set SQLAlchemy URL from environment variables
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
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
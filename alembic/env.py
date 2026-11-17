
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database.connection import Base, engine
from app.models.order_model import Order
from app.models.order_item_model import OrderItem

# Alembic configuration
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Connect Alembic to our application database
database_url = engine.url.render_as_string(hide_password=False)
config.set_main_option(
    "sqlalchemy.url",
    database_url.replace("%", "%%")
)

# Load SQLAlchemy model metadata
target_metadata = Base.metadata


def run_migrations_offline():
    # Run migrations without creating a database connection
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,#Placeholder mattum show pannama, actual value-ah SQL query-la display panna help pannum.
        literal_binds=True, #Converts SQL parameter placeholders into actual values when Alembic generates SQL in offline mode.VALUES (:user_id, :total_amount); instaed VALUES (101, 2500.00);
        dialect_opts={"paramstyle": "named"}, #? or %s madhiri symbols use pannama, :user_id madhiri meaningful parameter names use panna sollrom.
        compare_type=True 
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Create a database connection for migrations
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}), #alembic.ini file-la sqlalchemy.-nu start aagura settings-ah identify panni, database engine create panna use panrom. and returns it as a Python dictionary.
        prefix="sqlalchemy.",
        poolclass=pool.NullPool # not need continue connection QueuePool-na connection-ah save panni next time reuse pannum. NullPool-na connection use pannitu release pannumbodhu close pannidum. Alembic migration-ku NullPool use panrom because long-term connection reuse thevai illa.
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

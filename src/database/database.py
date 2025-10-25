import os
from pathlib import Path

from sqlmodel import create_engine

_DATABASE_NAME = "database.db"


# Create an engine that stores data in the local directory's database.db file.
db_file = Path(os.path.dirname(__file__)).joinpath(_DATABASE_NAME)

# Checking threads is handled by FastAPI's dependency automatically.
DB_ENGINE = create_engine(
    f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
)

from pathlib import Path

from sqlalchemy import create_engine

from sqlalchemy.orm import declarative_base

from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

COURSE_CATALOG_PATH = DATA_DIR / "rice_course_pages.json"

DATABASE_URL = "postgresql://postgres:rIyaVNToyEKqcBzFWcZwzgWRAcPmRljy@zephyr.proxy.rlwy.net:28482/railway"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine

)

Base = declarative_base()

def get_course_catalog_path() -> Path:

    return COURSE_CATALOG_PATH
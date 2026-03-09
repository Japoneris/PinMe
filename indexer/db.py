"""Database setup: engine, session factory, and table creation."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models import Base


def init_db(db_path: str = "pintme.db") -> sessionmaker:
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def get_session(db_path: str = "pintme.db") -> Session:
    SessionLocal = init_db(db_path)
    return SessionLocal()

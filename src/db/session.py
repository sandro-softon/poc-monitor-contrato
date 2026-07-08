from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import Config

engine = create_engine(Config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(engine)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

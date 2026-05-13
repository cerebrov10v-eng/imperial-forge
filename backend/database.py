"""
Imperial Forge V10 — Base de datos SQLite (WAL)
Tablas: forge_jobs, forge_assets
"""
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime, Float
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager

from backend.config import DB_PATH, DB_URL

logger = logging.getLogger("imperial_forge.db")

# Garantizar directorio
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)

# Activar WAL mode
with engine.connect() as conn:
    conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    conn.exec_driver_sql("PRAGMA synchronous=NORMAL")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class ForgeJob(Base):
    __tablename__ = "forge_jobs"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type     = Column(String, nullable=False)   # video|audio|landing|ads|master
    status       = Column(String, default="queued") # queued|processing|done|failed
    source       = Column(String, default="api")
    brief_data   = Column(Text)                     # JSON serializado
    result_urls  = Column(Text)                     # JSON con URLs de outputs
    error        = Column(Text)
    created_at   = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_s   = Column(Float)                    # tiempo de procesamiento


class ForgeAsset(Base):
    __tablename__ = "forge_assets"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    job_id     = Column(String, nullable=False)
    asset_type = Column(String)  # video|audio|image|landing|ad
    local_path = Column(String)
    remote_url = Column(String)
    platform   = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Imperial Forge DB — WAL OK")


@contextmanager
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

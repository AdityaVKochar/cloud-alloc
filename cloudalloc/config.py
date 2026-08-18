from __future__ import annotations

import os
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///cloudalloc-dev.sqlite3"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    ARTIFACT_DIR = os.getenv("ARTIFACT_DIR", str(Path("artifacts").resolve()))
    JSON_SORT_KEYS = False


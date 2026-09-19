"""Test environment bootstrap.

`app.core.config` builds `Settings()` at import time and requires DATABASE_URL,
so the suite could not be run with a bare `pytest`. Set the defaults before any
application module is imported.
"""

import os

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://gcr:gcr_test@localhost:5432/gcr_test")
os.environ.setdefault("CORS_ORIGINS", "*")

import importlib

import pytest

import app.config as app_config
from app.database.connection import normalize_database_url


def test_database_url_normalizes_railway_postgres_scheme():
    assert (
        normalize_database_url("postgres://user:pass@host:5432/db")
        == "postgresql://user:pass@host:5432/db"
    )


def test_runtime_config_requires_production_secrets(monkeypatch):
    monkeypatch.setenv("CLOCKLY_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db")
    monkeypatch.delenv("CLOCKLY_SECRET_KEY", raising=False)
    monkeypatch.delenv("CLOCKLY_DEFAULT_ADMIN_PASSWORD", raising=False)

    config = importlib.reload(app_config)
    with pytest.raises(RuntimeError, match="CLOCKLY_DEFAULT_ADMIN_PASSWORD"):
        config.validate_runtime_config()

    monkeypatch.setenv("CLOCKLY_ENV", "development")
    monkeypatch.setenv("CLOCKLY_SECURE_COOKIES", "false")
    monkeypatch.setenv("CLOCKLY_DOCS_ENABLED", "true")
    monkeypatch.delenv("CLOCKLY_TRUSTED_HOSTS", raising=False)
    importlib.reload(app_config)


def test_runtime_config_requires_explicit_production_hosts(monkeypatch):
    monkeypatch.setenv("CLOCKLY_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/test_db")
    monkeypatch.setenv("CLOCKLY_SECRET_KEY", "production-secret-key-with-enough-entropy")
    monkeypatch.setenv("CLOCKLY_DEFAULT_ADMIN_PASSWORD", "StrongInitialPassword123")
    monkeypatch.setenv("CLOCKLY_SECURE_COOKIES", "true")
    monkeypatch.setenv("CLOCKLY_DOCS_ENABLED", "false")
    monkeypatch.delenv("CLOCKLY_TRUSTED_HOSTS", raising=False)

    config = importlib.reload(app_config)
    with pytest.raises(RuntimeError, match="CLOCKLY_TRUSTED_HOSTS"):
        config.validate_runtime_config()

    monkeypatch.setenv("CLOCKLY_TRUSTED_HOSTS", "clockly.example.com")
    config = importlib.reload(app_config)
    config.validate_runtime_config()

    monkeypatch.setenv("CLOCKLY_ENV", "development")
    monkeypatch.setenv("CLOCKLY_SECURE_COOKIES", "false")
    monkeypatch.setenv("CLOCKLY_DOCS_ENABLED", "true")
    monkeypatch.delenv("CLOCKLY_TRUSTED_HOSTS", raising=False)
    importlib.reload(app_config)

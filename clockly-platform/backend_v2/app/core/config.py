from functools import lru_cache
from typing import Any

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment driven settings for the standalone API backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="ClockLy API", validation_alias="CLOCKLY_APP_NAME")
    environment: str = Field(default="development", validation_alias=AliasChoices("CLOCKLY_ENV", "ENVIRONMENT"))
    debug: bool = Field(default=False, validation_alias="CLOCKLY_DEBUG")
    database_url: str = Field(
        default="postgresql+psycopg://clockly:clockly@localhost:5432/clockly",
        validation_alias=AliasChoices("DATABASE_URL", "CLOCKLY_DATABASE_URL"),
    )
    secret_key: str = Field(default="change-me-in-production", validation_alias="CLOCKLY_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="CLOCKLY_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, validation_alias="CLOCKLY_ACCESS_TOKEN_MINUTES")
    refresh_token_expire_days: int = Field(default=30, validation_alias="CLOCKLY_REFRESH_TOKEN_DAYS")
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        validation_alias="CLOCKLY_CORS_ALLOWED_ORIGINS",
    )
    trusted_hosts: list[str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver"],
        validation_alias="CLOCKLY_TRUSTED_HOSTS",
    )

    @field_validator("cors_allowed_origins", "trusted_hosts", mode="before")
    @classmethod
    def parse_csv_list(cls, value: Any) -> Any:
        if isinstance(value, str):
            if not value.strip():
                return []
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        clean = value.strip()
        if clean.startswith("postgres://"):
            return "postgresql+psycopg://" + clean.removeprefix("postgres://")
        if clean.startswith("postgresql://"):
            return "postgresql+psycopg://" + clean.removeprefix("postgresql://")
        return clean

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment.lower() == "production":
            if self.secret_key in {"", "change-me-in-production"}:
                raise ValueError("CLOCKLY_SECRET_KEY must be set in production.")
            if "*" in self.cors_allowed_origins:
                raise ValueError("CLOCKLY_CORS_ALLOWED_ORIGINS cannot contain '*' in production.")
            if not self.trusted_hosts or "*" in self.trusted_hosts:
                raise ValueError("CLOCKLY_TRUSTED_HOSTS must be explicit in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


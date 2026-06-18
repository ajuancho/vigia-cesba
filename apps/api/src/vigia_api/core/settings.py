from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://vigia:vigia@localhost:5432/vigia"
    redis_url: str = "redis://localhost:6379/0"
    api_cors_origins: str = "http://localhost:3000"

    # Fase 2 — auth (placeholders; se activan al construir el módulo de auth).
    auth_secret: str = "dev-only-change-me"
    auth_jwt_alg: str = "HS256"
    auth_jwt_ttl_seconds: int = 60 * 60 * 24  # 24h
    auth_enabled: bool = False  # False = modo demo abierto

    # Free trial: días de uso pleno desde la creación del workspace. Al vencer,
    # los endpoints gated devuelven 402 trial_expired salvo plan != "free".
    trial_days: int = 30

    # Cuando se define, todas las queries a `norma` se acotán a esta jurisdicción
    # sin necesidad de filtros en el frontend. Permite desplegar la misma
    # codebase como instancia CABA ("CABA") o nacional (vacío = sin restricción).
    # Env var: VIGIA_JURISDICCION_SCOPE
    vigia_jurisdiccion_scope: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


def get_settings() -> Settings:
    return Settings()

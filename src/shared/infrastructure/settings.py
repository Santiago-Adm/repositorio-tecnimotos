"""Configuración de la aplicación vía variables de entorno."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="development")
    api_version: str = Field(default="0.1.0")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    database_url: str = Field(default="postgresql+asyncpg://tecnimotos:tecnimotos@localhost:5432/tecnimotos")
    database_url_sync: str = Field(default="postgresql://tecnimotos:tecnimotos@localhost:5432/tecnimotos")

    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_params_db: str = Field(default="redis://localhost:6379/1")
    redis_notifications_db: str = Field(default="redis://localhost:6379/2")

    jwt_private_key_path: str = Field(default="./keys/private.pem")
    jwt_public_key_path: str = Field(default="./keys/public.pem")
    jwt_algorithm: str = Field(default="RS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    fernet_key: str = Field(default="")

    whatsapp_api_token: str = Field(default="")
    whatsapp_phone_number_id: str = Field(default="")

    sms_provider: str = Field(default="twilio")
    sms_api_key: str = Field(default="")
    sms_account_sid: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    return Settings()

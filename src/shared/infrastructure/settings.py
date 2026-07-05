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

    # Sin default (R23/incidente de seguridad 2026-07-04): la app debe fallar
    # al arrancar si no están configuradas, no degradar silenciosamente a una
    # credencial de desarrollo conocida y pública.
    database_url: str
    database_url_sync: str

    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_params_db: str = Field(default="redis://localhost:6379/1")
    redis_notifications_db: str = Field(default="redis://localhost:6379/2")

    jwt_private_key_path: str = Field(default="./keys/private.pem")
    jwt_public_key_path: str = Field(default="./keys/public.pem")
    jwt_algorithm: str = Field(default="RS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    fernet_key: str = Field(default="")

    # Pieza de verificación profunda (2026-07-05) — 07-criterios-seguridad-
    # ejecutables.md §2.1 exige Argon2id + pepper; el código usaba PBKDF2 sin
    # pepper (hallazgo real, corregido). El pepper es un secreto de servidor
    # separado de la sal (que sí vive en cada hash) — nunca en la base de datos.
    argon2_pepper: str = Field(default="")

    superadmin_bootstrap_key: str = Field(default="")

    whatsapp_api_token: str = Field(default="")
    whatsapp_phone_number_id: str = Field(default="")

    sms_provider: str = Field(default="twilio")
    sms_api_key: str = Field(default="")
    sms_account_sid: str = Field(default="")

    r2_account_id: str = Field(default="")
    r2_endpoint: str = Field(default="")
    r2_bucket_name: str = Field(default="")
    r2_public_url: str = Field(default="")
    r2_access_key_id: str = Field(default="")
    r2_secret_access_key: str = Field(default="")

    # MFA por correo — ADR-011. Resend HTTP API (Railway no da SMTP propio).
    resend_api_key: str = Field(default="")
    mfa_email_from: str = Field(default="Tecnimotos <onboarding@resend.dev>")


@lru_cache
def get_settings() -> Settings:
    return Settings()

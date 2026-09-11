from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    db_host: str = "aws-0-us-east-1.pooler.supabase.com"
    db_port: int = 6543
    db_name: str = "postgres"
    db_user: str = "app_backend.relglfpyctcldlbgsjdn"
    db_password: str  # obligatoria: sin default. La app no arranca sin ella.

    supabase_jwks_uri: str = (
        "https://relglfpyctcldlbgsjdn.supabase.co/auth/v1/.well-known/jwks.json"
    )
    supabase_issuer: str = "https://relglfpyctcldlbgsjdn.supabase.co/auth/v1"


settings = Settings()

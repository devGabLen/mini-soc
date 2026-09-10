from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Los defaults aquí abajo son los datos reales de tu proyecto Supabase
    (relglfpyctcldlbgsjdn), igual que quedaron calibrados en la versión Java.
    La DB_PASSWORD es la del rol `app_backend` creado en sql/02_security_rls.sql.

    Antes de usar esto en producción o subirlo a un repo compartido, rota esa
    contraseña y quita el default de aquí, dejando la variable de entorno como
    obligatoria (sin valor por defecto).
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Conexión vía Supavisor (connection pooler) en vez de la conexión directa:
    # db.<ref>.supabase.co suele resolver solo a IPv6, y muchas redes/VMs
    # (como la tuya) no tienen salida IPv6 -> "Network is unreachable".
    # El pooler sí es accesible por IPv4. Puerto 6543 = modo transacción,
    # que encaja con nuestro patrón de "una transacción corta por request".
    db_host: str = "aws-0-us-east-1.pooler.supabase.com"
    db_port: int = 6543
    db_name: str = "postgres"
    db_user: str = "app_backend.relglfpyctcldlbgsjdn"
    db_password: str

    # Este proyecto de Supabase firma sus JWT con ES256 (asimétrico) -
    # confirmado inspeccionando un token real emitido por /auth/v1/token.
    # Por eso se valida contra el endpoint JWKS público, sin secreto compartido.
    supabase_jwks_uri: str = (
        "https://relglfpyctcldlbgsjdn.supabase.co/auth/v1/.well-known/jwks.json"
    )
    supabase_issuer: str = "https://relglfpyctcldlbgsjdn.supabase.co/auth/v1"


settings = Settings()

"""
Equivalente Python de SecurityConfig.java + SupabaseJwtAuthConverter.java.

Valida la firma del JWT contra el endpoint JWKS público del proyecto (ES256),
sin necesidad de compartir ningún secreto. PyJWKClient cachea las claves
públicas automáticamente, evitando pegarle al endpoint JWKS en cada request.
"""

from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .config import settings

bearer_scheme = HTTPBearer(auto_error=True)
_jwk_client = jwt.PyJWKClient(settings.supabase_jwks_uri)


class CurrentUser(BaseModel):
    sub: str  # uuid del usuario, coincide con auth.uid() en Postgres
    email: Optional[str] = None
    soc_role: Optional[str] = None  # profiles.role, sincronizado en app_metadata


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials

    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            issuer=settings.supabase_issuer,
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from exc

    app_metadata = payload.get("app_metadata") or {}

    return CurrentUser(
        sub=payload["sub"],
        email=payload.get("email"),
        soc_role=app_metadata.get("role"),
    )

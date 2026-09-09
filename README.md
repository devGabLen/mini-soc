# mini-soc

CiberSecurity monitoring app

Backend Python / FastAPI.

Reemplazo del backend Java: misma arquitectura, mismo Supabase, sin ningún
cambio en `sql/01_schema_ddl.sql` ni `sql/02_security_rls.sql` — el diseño
de RLS es agnóstico al lenguaje del backend.

## Instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configurar (opcional)

Los defaults en `app/config.py` ya apuntan a tu proyecto Supabase real. Si
quieres sobreescribirlos, copia `.env.example` a `.env` y edítalo.

## Arrancar

```bash
uvicorn app.main:app --reload --port 8080
```

## Probar

```bash
# 1. Login contra Supabase Auth para obtener un JWT (ver conversación previa
#    para el curl exacto de /auth/v1/token?grant_type=password)

# 2. Pegarle al endpoint de prueba
curl http://localhost:8080/api/v1/profiles/me \
  -H "Authorization: Bearer <access_token>"
```

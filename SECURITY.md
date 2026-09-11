# Postura de seguridad — mini-soc

Resumen del hardening aplicado en la Fase 5, y del diseño de seguridad
acumulado desde la Fase 1.

## Roles de Postgres (principio de menor privilegio, uno por "actor")

| Rol | Puede | No puede |
|---|---|---|
| `app_backend` | CRUD en `incidents`/`alerts`/`profiles`, filtrado por RLS según el usuario autenticado | DDL, tocar `network_logs` en escritura, bypass de RLS |
| `sensor_ingest` | Solo `INSERT` en `network_logs` | Leer nada, tocar cualquier otra tabla |
| `correlation_engine` | Leer `network_logs`, insertar en `alerts`, leer/actualizar su checkpoint | Tocar `incidents`/`profiles`, DDL |
| `anon` / `authenticated` (nativos de Supabase) | Nada (revocado explícitamente) | — |

Ninguno de los tres roles de aplicación tiene `BYPASSRLS`, `SUPERUSER`,
`CREATEDB` ni `CREATEROLE`.

## Rotación de credenciales (2026-09-10)

Las contraseñas originales de `app_backend`, `sensor_ingest` y
`correlation_engine` quedaron expuestas en texto plano durante el desarrollo
(compartidas en una sesión de chat para poder configurar los `.env`
locales). Se rotaron las tres como parte del hardening de la Fase 5
(migración `09_rotate_all_service_passwords`). Las nuevas contraseñas
**no están en ningún archivo de este repositorio** — viven únicamente en
los `.env` locales de cada máquina (excluidos de git vía `.gitignore`).

**Lección para el futuro**: nunca pegar una contraseña real en un chat, log,
o ticket, aunque sea "solo para configurar algo rápido". Si pasa, rotarla
en cuanto se pueda, como se hizo aquí.

## RLS

Las 4 tablas de `public` (`profiles`, `incidents`, `alerts`, `network_logs`)
tienen RLS activo, con políticas independientes por operación (nunca
`FOR ALL`), verificadas con `get_advisors` en cada fase — 0 advertencias de
seguridad pendientes, salvo una:

## Limitación aceptada

**Leaked Password Protection**: Supabase solo la ofrece en el plan Pro.
En el plan gratuito de este proyecto queda deshabilitada. Es una limitación
conocida del plan, no un descuido — documentada aquí para que quede
explícito que fue una decisión informada, no un hueco que se pasó por alto.
Si este proyecto llegara a producción con usuarios reales, esto debería
revisarse (upgrade de plan, o validación propia contra una lista de
contraseñas filtradas conocidas antes de pasarlas a Supabase Auth).

## Pendientes de higiene de secretos (recordatorio)

- Los `.env.example` de `app/`, `ingest/` y `correlate/` tienen placeholders,
  no contraseñas reales — cada quien debe completar su propio `.env` (nunca
  commitearlo).
- El backend (`app/config.py`) ya no arranca con una contraseña por defecto
  hardcodeada: si falta `DB_PASSWORD`, falla explícitamente en vez de usar
  un valor silencioso.

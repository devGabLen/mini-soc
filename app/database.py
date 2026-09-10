"""
Equivalente Python de RlsConnectionAspect.java: el puente entre la identidad
ya validada del JWT y las políticas RLS de Postgres.

ADVERTENCIA DE SEGURIDAD (no es cosmético):
El tercer argumento de set_config DEBE ser `true` (is_local). Eso hace que
Postgres descarte ese valor al terminar la transacción, incluso si la
conexión física vuelve al pool de psycopg y se reutiliza para otro usuario
en la siguiente petición. Usar `false`, o ejecutar esto fuera de una
transacción real, filtraría la identidad de un usuario hacia la petición de
otro usuario en una conexión reciclada del pool.

`pool.connection()` de psycopg3 ya envuelve todo en una transacción real:
hace commit al salir del bloque `with` sin errores, y rollback si hay una
excepción — por eso basta con hacer el set_config al inicio del bloque.
"""

from fastapi import Depends
from psycopg_pool import ConnectionPool

from .config import settings
from .security import CurrentUser, get_current_user

conninfo = (
    f"host={settings.db_host} port={settings.db_port} "
    f"dbname={settings.db_name} user={settings.db_user} "
    f"password={settings.db_password}"
)

pool = ConnectionPool(
    conninfo,
    min_size=1,
    max_size=10,
    open=True,
    kwargs={"prepare_threshold": None},  # ver ingest/tshark_ingest.py: incompatibilidad
    # conocida entre prepared statements de psycopg y el pooler de Supabase en modo
    # transacción (puerto 6543) -> DuplicatePreparedStatement bajo uso repetido.
)


def get_db_conn(current_user: CurrentUser = Depends(get_current_user)):
    """
    Dependencia de FastAPI: primero resuelve el JWT (get_current_user),
    y con ese resultado fija el contexto de RLS antes de entregar la
    conexión al endpoint. Úsala en los routers como:
        conn: Connection = Depends(get_db_conn)
    """
    with pool.connection() as conn:
        conn.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (current_user.sub,),
        )
        yield conn

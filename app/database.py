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
    kwargs={"prepare_threshold": None},
)


def get_db_conn(current_user: CurrentUser = Depends(get_current_user)):
    with pool.connection() as conn:
        conn.execute(
            "select set_config('request.jwt.claim.sub', %s, true)",
            (current_user.sub,),
        )
        yield conn

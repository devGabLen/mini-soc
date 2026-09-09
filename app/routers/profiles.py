from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from ..database import get_db_conn
from ..schemas import ProfileResponse
from ..security import CurrentUser, get_current_user

router = APIRouter(prefix="/api/v1/profiles", tags=["profiles"])


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    conn: Connection = Depends(get_db_conn),
) -> ProfileResponse:
    # Filtro explícito por user_id: RLS ya restringe qué filas son visibles,
    # pero un admin ve TODOS los perfiles por política, así que sin este
    # WHERE un admin podría recibir el perfil de otra persona en su /me.
    row = conn.execute(
        """
        select id, email, full_name, role, created_at
        from public.profiles
        where user_id = %s
        """,
        (current_user.sub,),
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    return ProfileResponse(
        id=row[0],
        email=row[1],
        full_name=row[2],
        role=row[3],
        created_at=row[4],
    )

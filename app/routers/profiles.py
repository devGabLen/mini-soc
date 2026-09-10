from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

import psycopg
from ..database import get_db_conn
from ..schemas import ProfileResponse, RoleUpdateRequest
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


@router.patch("/{profile_id}/role", response_model=ProfileResponse)
def update_profile_role(
    profile_id: str,
    body: RoleUpdateRequest,
    conn: Connection = Depends(get_db_conn),
) -> ProfileResponse:
    """
    Cambia el rol de OTRO usuario. No hay ninguna validación de "eres admin"
    aquí en Python: la política profiles_update_any_by_admin y el trigger
    private.prevent_role_escalation ya lo garantizan en Postgres. Si quien
    llama no es admin, esto simplemente no afecta ninguna fila.
    """
    try:
        row = conn.execute(
            """
            update public.profiles
            set role = %s
            where id = %s
            returning id, email, full_name, role, created_at
            """,
            (body.role, profile_id),
        ).fetchone()
    except psycopg.errors.RaiseException as exc:
        # El trigger prevent_role_escalation lanza esta excepción cuando
        # quien llama no es admin pero de alguna forma la fila sí era visible.
        raise HTTPException(
            status_code=403,
            detail="No tienes permisos para modificar el rol de este usuario.",
        ) from exc

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Perfil no encontrado o sin permisos para modificarlo.",
        )

    return ProfileResponse(
        id=row[0],
        email=row[1],
        full_name=row[2],
        role=row[3],
        created_at=row[4],
    )

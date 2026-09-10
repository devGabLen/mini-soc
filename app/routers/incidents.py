"""
Endpoints de incidents. Nótese lo que NO hace este archivo: no valida "¿puede
este usuario ver/crear/editar este incidente?" en Python. Esa autorización
fina ya la hace Postgres vía RLS (sql/02_security_rls.sql), usando la
identidad que RlsConnectionAspect (database.get_db_conn) ya propagó. El
backend solo traduce HTTP <-> SQL y decide qué código de estado devolver
según lo que Postgres permitió o bloqueó.
"""

from typing import List
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection
from psycopg.rows import dict_row

from ..database import get_db_conn
from ..schemas import IncidentCreateRequest, IncidentResponse, IncidentUpdateRequest

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


def _row_to_response(row: dict) -> IncidentResponse:
    return IncidentResponse(
        id=row["id"],
        title=row["title"],
        severity=row["severity"],
        status=row["status"],
        assigned_to=row["assigned_to"],
        tlp=row["tlp"],
        pap=row["pap"],
        created_at=row["created_at"],
        acknowledged_at=row["acknowledged_at"],
        closed_at=row["closed_at"],
    )


@router.get("/mttr", response_model=dict)
def get_mttr(conn: Connection = Depends(get_db_conn)) -> dict:
    """
    MTTR promedio (en segundos) y tiempo medio de reconocimiento, sobre los
    incidentes CERRADOS visibles para este usuario (RLS filtra el resto).
    Ver docs/ARQUITECTURA_FASE1.md para la explicación de por qué se separan
    acknowledged_at (primera respuesta) de closed_at (resolución real).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            select
                extract(epoch from avg(closed_at - created_at)),
                extract(epoch from avg(acknowledged_at - created_at))
            from public.incidents
            where closed_at is not null
            """
        )
        mttr_seconds, ack_seconds = cur.fetchone()

    return {
        "mttr_seconds": mttr_seconds,
        "time_to_acknowledge_seconds": ack_seconds,
    }


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: Connection = Depends(get_db_conn),
) -> List[IncidentResponse]:
    # Sin WHERE: RLS ya filtra. Si el usuario no es SOC staff, esto
    # simplemente devuelve una lista vacía, no un error.
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            select id, title, severity, status, assigned_to, tlp, pap,
                   created_at, acknowledged_at, closed_at
            from public.incidents
            order by created_at desc
            limit %s offset %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()

    return [_row_to_response(r) for r in rows]


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    body: IncidentCreateRequest, conn: Connection = Depends(get_db_conn)
) -> IncidentResponse:
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                insert into public.incidents (title, description, severity, assigned_to, tlp, pap)
                values (%s, %s, %s, %s, %s, %s)
                returning id, title, severity, status, assigned_to, tlp, pap,
                          created_at, acknowledged_at, closed_at
                """,
                (
                    body.title,
                    body.description,
                    body.severity,
                    body.assigned_to,
                    body.tlp,
                    body.pap,
                ),
            )
            row = cur.fetchone()
    except psycopg.errors.InsufficientPrivilege as exc:
        # La política incidents_insert_soc_staff bloqueó el INSERT
        # (el usuario autenticado no es analyst/manager/admin).
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear incidentes.",
        ) from exc

    return _row_to_response(row)


@router.patch("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: UUID,
    body: IncidentUpdateRequest,
    conn: Connection = Depends(get_db_conn),
) -> IncidentResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No enviaste ningún campo para actualizar.")

    set_clause = ", ".join(f"{field} = %s" for field in updates)
    values = list(updates.values()) + [incident_id]

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            update public.incidents
            set {set_clause}
            where id = %s
            returning id, title, severity, status, assigned_to, tlp, pap,
                      created_at, acknowledged_at, closed_at
            """,
            values,
        )
        row = cur.fetchone()

    if row is None:
        # RLS bloqueó la fila (no es tu incidente asignado ni eres manager/admin)
        # O el incidente no existe. Por diseño, no se distingue entre ambos casos
        # aquí para no filtrar información sobre qué incidentes existen.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado o sin permisos para modificarlo.",
        )

    return _row_to_response(row)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: UUID, conn: Connection = Depends(get_db_conn)) -> None:
    with conn.cursor() as cur:
        cur.execute("delete from public.incidents where id = %s returning id", (incident_id,))
        deleted = cur.fetchone()

    if deleted is None:
        # Igual que en update: RLS solo deja borrar a un admin (política
        # incidents_delete_admin_only). 0 filas = no existe o no tienes permiso.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado o sin permisos para eliminarlo.",
        )

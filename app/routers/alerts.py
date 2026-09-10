"""
alerts es de solo lectura + creación desde la API. A propósito no hay
PATCH/DELETE: ni siquiera existen políticas RLS para esas operaciones sobre
esta tabla (ver sql/02_security_rls.sql) — es inmutabilidad forense, no un
descuido. Si algún día hace falta "corregir" una alerta, eso se modela como
un nuevo registro/comentario en incidents, no como editar la evidencia
original.
"""

from typing import List

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection
from psycopg.rows import dict_row

from ..database import get_db_conn
from ..schemas import AlertCreateRequest, AlertResponse

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


def _row_to_response(row: dict) -> AlertResponse:
    return AlertResponse(
        id=row["id"],
        incident_id=row["incident_id"],
        category=row["category"],
        mitre_tactic=row["mitre_tactic"],
        severity=row["severity"],
        description=row["description"],
        src_ip=str(row["src_ip"]),
        dst_ip=str(row["dst_ip"]),
        has_payload=row["payload"] is not None,
        occurred_at=row["occurred_at"],
        detected_at=row["detected_at"],
    )


@router.get("", response_model=List[AlertResponse])
def list_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conn: Connection = Depends(get_db_conn),
) -> List[AlertResponse]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            select id, incident_id, category, mitre_tactic, severity, description,
                   src_ip, dst_ip, payload, occurred_at, detected_at
            from public.alerts
            order by detected_at desc
            limit %s offset %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()

    return [_row_to_response(r) for r in rows]


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    body: AlertCreateRequest, conn: Connection = Depends(get_db_conn)
) -> AlertResponse:
    try:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                insert into public.alerts
                    (incident_id, category, mitre_tactic, severity, description,
                     src_ip, dst_ip, occurred_at)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
                returning id, incident_id, category, mitre_tactic, severity, description,
                          src_ip, dst_ip, payload, occurred_at, detected_at
                """,
                (
                    body.incident_id,
                    body.category,
                    body.mitre_tactic,
                    body.severity,
                    body.description,
                    body.src_ip,
                    body.dst_ip,
                    body.occurred_at,
                ),
            )
            row = cur.fetchone()
    except psycopg.errors.InsufficientPrivilege as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para registrar alertas.",
        ) from exc

    return _row_to_response(row)


@router.get("/mttd", response_model=dict)
def get_mttd(conn: Connection = Depends(get_db_conn)) -> dict:
    """
    MTTD promedio (en segundos) sobre las alertas visibles para este usuario,
    tal como se explicó en docs/ARQUITECTURA_FASE1.md.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            select extract(epoch from avg(detected_at - occurred_at))
            from public.alerts
            """
        )
        (avg_seconds,) = cur.fetchone()

    return {"mttd_seconds": avg_seconds}

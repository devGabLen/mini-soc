from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# --- profiles ---------------------------------------------------------------


UserRole = Literal["admin", "soc_manager", "analyst_tier2", "analyst_tier1", "viewer"]


class RoleUpdateRequest(BaseModel):
    role: UserRole


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime


# --- incidents ---------------------------------------------------------------

TlpLevel = Literal["RED", "AMBER_STRICT", "AMBER", "GREEN", "CLEAR"]
PapLevel = Literal["RED", "AMBER", "GREEN", "WHITE"]


class IncidentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=4000)
    severity: int = Field(..., ge=1, le=4)
    assigned_to: Optional[UUID] = None
    tlp: TlpLevel
    pap: PapLevel


class IncidentUpdateRequest(BaseModel):
    # Todos opcionales: PATCH parcial. Solo se actualizan los campos enviados.
    status: Optional[
        Literal["open", "in_progress", "contained", "closed", "false_positive"]
    ] = None
    severity: Optional[int] = Field(None, ge=1, le=4)
    assigned_to: Optional[UUID] = None
    acknowledged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    severity: int
    status: str
    assigned_to: Optional[UUID] = None
    tlp: str
    pap: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


# --- alerts --------------------------------------------------------------

MitreCategory = Literal[
    "reconocimiento",
    "entrega_ataque",
    "explotacion",
    "compromiso_sistema",
    "conciencia_ambiental",
]


class AlertCreateRequest(BaseModel):
    incident_id: Optional[UUID] = None
    category: MitreCategory
    mitre_tactic: Optional[str] = Field(None, max_length=20)
    severity: int = Field(..., ge=1, le=4)
    description: Optional[str] = Field(None, max_length=4000)
    src_ip: str
    dst_ip: str
    occurred_at: datetime


class AlertResponse(BaseModel):
    id: UUID
    incident_id: Optional[UUID] = None
    category: str
    mitre_tactic: Optional[str] = None
    severity: int
    description: Optional[str] = None
    src_ip: str
    dst_ip: str
    has_payload: bool
    occurred_at: datetime
    detected_at: datetime

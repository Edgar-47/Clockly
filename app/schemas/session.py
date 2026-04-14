"""
app/schemas/session.py

Pydantic models for attendance session HTTP requests.
"""

from pydantic import BaseModel


class ClockPunchForm(BaseModel):
    """Employee clock in/out from the kiosk."""
    employee_id: int
    password: str
    entry_type: str          # "entrada" | "salida"
    exit_note: str = ""
    incident_type: str = ""


class AdminCloseSessionForm(BaseModel):
    """Admin forcefully closes an active session."""
    reason: str

"""Location safety API routes for patient devices and caregiver clients."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.location_safety import LocationSafetyService

router = APIRouter(prefix="/api/location", tags=["location-safety"])
service = LocationSafetyService()


class LocationUpdateRequest(BaseModel):
    """Normalized location payload uploaded by Android or another patient device."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float | None = Field(default=None, ge=0)
    address_text: str | None = None
    source: str | None = None


class SafeZoneRequest(BaseModel):
    """Circular safe zone payload configured by a caregiver client."""

    label: str = "家庭安全区域"
    center_latitude: float = Field(ge=-90, le=90)
    center_longitude: float = Field(ge=-180, le=180)
    radius_meters: float = Field(gt=0)
    enabled: bool = True


@router.post("/{patient_id}")
async def update_patient_location(patient_id: str, payload: LocationUpdateRequest):
    """Save latest location, evaluate safe-zone status, and return alert if needed."""
    try:
        return service.update_patient_location(patient_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{patient_id}/safe-zone")
async def save_safe_zone(patient_id: str, payload: SafeZoneRequest):
    """Create or update the patient's caregiver-defined safe zone."""
    try:
        safe_zone = service.save_safe_zone(patient_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "ok",
        "patient_id": safe_zone.patient_id,
        "safe_zone": safe_zone.to_dict(),
    }


@router.get("/{patient_id}/status")
async def get_location_status(patient_id: str):
    """Return caregiver-facing latest location, safe-zone state, and summary."""
    try:
        return service.get_location_status(patient_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{patient_id}/alerts")
async def list_location_alerts(patient_id: str, limit: int = 20):
    """Return recent location risk alerts for one patient."""
    try:
        alerts = service.list_alerts(patient_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "patient_id": patient_id,
        "alerts": [alert.to_dict() for alert in alerts],
    }

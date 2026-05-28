"""Backend location safety service for future Android patient-device uploads.

The service stores the latest patient location, stores one circular safe zone,
evaluates whether the patient is inside that zone, and records alerts when a
reported point is outside the enabled safe zone. Map SDK concerns stay on the
client side; this backend only accepts normalized latitude/longitude payloads.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt
from typing import Any

from app.database import get_connection
from app.models.location import LocationAlert, PatientLocation, SafeZone

EARTH_RADIUS_METERS = 6_371_000
OUT_OF_SAFE_ZONE = "OUT_OF_SAFE_ZONE"
HIGH = "HIGH"


@dataclass(slots=True)
class LocationEvaluation:
    """Result of evaluating one location against a safe zone."""

    inside_safe_zone: bool | None
    distance_meters: float | None
    alert: LocationAlert | None = None
    safe_zone_missing: bool = False


class LocationSafetyService:
    """Persistence and safety evaluation service for location data."""

    def calculate_distance_meters(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two WGS84 points using Haversine."""
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        rlat1 = radians(lat1)
        rlat2 = radians(lat2)

        a = sin(delta_lat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(delta_lon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return EARTH_RADIUS_METERS * c

    def evaluate_location(
        self,
        patient_location: PatientLocation,
        safe_zone: SafeZone | None,
    ) -> LocationEvaluation:
        """Evaluate one location and return an optional unsaved alert."""
        if safe_zone is None or not safe_zone.enabled:
            return LocationEvaluation(
                inside_safe_zone=None,
                distance_meters=None,
                alert=None,
                safe_zone_missing=safe_zone is None,
            )

        distance_meters = self.calculate_distance_meters(
            patient_location.latitude,
            patient_location.longitude,
            safe_zone.center_latitude,
            safe_zone.center_longitude,
        )
        inside_safe_zone = distance_meters <= safe_zone.radius_meters
        alert = None

        if not inside_safe_zone:
            alert = LocationAlert(
                patient_id=patient_location.patient_id,
                alert_type=OUT_OF_SAFE_ZONE,
                severity=HIGH,
                message=(
                    f"患者已离开【{safe_zone.label}】，距离中心约 "
                    f"{round(distance_meters)} 米。建议立即联系患者或附近家属。"
                ),
                latitude=patient_location.latitude,
                longitude=patient_location.longitude,
                distance_meters=distance_meters,
                created_at=_now_text(),
                resolved=False,
            )

        return LocationEvaluation(
            inside_safe_zone=inside_safe_zone,
            distance_meters=distance_meters,
            alert=alert,
            safe_zone_missing=False,
        )

    def update_patient_location(
        self,
        patient_id: str,
        location_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Store latest location and evaluate safe-zone status."""
        location = PatientLocation(
            patient_id=_clean_patient_id(patient_id),
            latitude=float(location_payload["latitude"]),
            longitude=float(location_payload["longitude"]),
            accuracy=_optional_float(location_payload.get("accuracy")),
            address_text=_optional_text(location_payload.get("address_text")),
            source=_optional_text(location_payload.get("source")),
            timestamp=_now_text(),
        )
        self._save_patient_location(location)

        safe_zone = self.get_safe_zone(location.patient_id)
        evaluation = self.evaluate_location(location, safe_zone)
        saved_alert = self._save_location_alert(evaluation.alert) if evaluation.alert else None

        return {
            "patient_id": location.patient_id,
            "inside_safe_zone": evaluation.inside_safe_zone,
            "distance_meters": _rounded_distance(evaluation.distance_meters),
            "safe_zone_missing": evaluation.safe_zone_missing,
            "alert": saved_alert.to_dict() if saved_alert else None,
            "latest_location": location.to_dict(),
        }

    def get_location_status(self, patient_id: str) -> dict[str, Any]:
        """Return caregiver-facing status for one patient."""
        normalized_patient_id = _clean_patient_id(patient_id)
        latest_location = self.get_latest_location(normalized_patient_id)
        safe_zone = self.get_safe_zone(normalized_patient_id)
        latest_alert = self.get_latest_alert(normalized_patient_id)

        if latest_location is None:
            return {
                "patient_id": normalized_patient_id,
                "latest_location": None,
                "safe_zone": safe_zone.to_dict() if safe_zone else None,
                "inside_safe_zone": None,
                "distance_meters": None,
                "safe_zone_missing": safe_zone is None,
                "latest_alert": latest_alert.to_dict() if latest_alert else None,
                "caregiver_summary": "暂未获取到患者定位信息。",
            }

        evaluation = self.evaluate_location(latest_location, safe_zone)
        return {
            "patient_id": normalized_patient_id,
            "latest_location": latest_location.to_dict(),
            "safe_zone": safe_zone.to_dict() if safe_zone else None,
            "inside_safe_zone": evaluation.inside_safe_zone,
            "distance_meters": _rounded_distance(evaluation.distance_meters),
            "safe_zone_missing": evaluation.safe_zone_missing,
            "latest_alert": latest_alert.to_dict() if latest_alert else None,
            "caregiver_summary": build_caregiver_summary(
                latest_location,
                safe_zone,
                evaluation,
            ),
        }

    def save_safe_zone(self, patient_id: str, payload: dict[str, Any]) -> SafeZone:
        """Create or update the active safe zone for one patient."""
        normalized_patient_id = _clean_patient_id(patient_id)
        safe_zone = SafeZone(
            patient_id=normalized_patient_id,
            label=_optional_text(payload.get("label")) or "家庭安全区域",
            center_latitude=float(payload["center_latitude"]),
            center_longitude=float(payload["center_longitude"]),
            radius_meters=max(1.0, float(payload["radius_meters"])),
            enabled=bool(payload.get("enabled", True)),
            updated_at=_now_text(),
        )

        with closing(get_connection()) as connection:
            connection.execute(
                """
                INSERT INTO safe_zones (
                    patient_id, label, center_latitude, center_longitude,
                    radius_meters, enabled, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(patient_id) DO UPDATE SET
                    label = excluded.label,
                    center_latitude = excluded.center_latitude,
                    center_longitude = excluded.center_longitude,
                    radius_meters = excluded.radius_meters,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    safe_zone.patient_id,
                    safe_zone.label,
                    safe_zone.center_latitude,
                    safe_zone.center_longitude,
                    safe_zone.radius_meters,
                    1 if safe_zone.enabled else 0,
                    safe_zone.updated_at,
                ),
            )
            connection.commit()

        return safe_zone

    def get_latest_location(self, patient_id: str) -> PatientLocation | None:
        """Return the latest location for one patient."""
        with closing(get_connection()) as connection:
            row = connection.execute(
                "SELECT * FROM patient_locations WHERE patient_id = ?",
                (_clean_patient_id(patient_id),),
            ).fetchone()
        return PatientLocation.from_row(row) if row else None

    def get_safe_zone(self, patient_id: str) -> SafeZone | None:
        """Return the configured safe zone for one patient."""
        with closing(get_connection()) as connection:
            row = connection.execute(
                "SELECT * FROM safe_zones WHERE patient_id = ?",
                (_clean_patient_id(patient_id),),
            ).fetchone()
        return SafeZone.from_row(row) if row else None

    def list_alerts(self, patient_id: str, limit: int = 20) -> list[LocationAlert]:
        """Return recent location alerts for one patient."""
        safe_limit = max(1, min(limit, 100))
        with closing(get_connection()) as connection:
            rows = connection.execute(
                """
                SELECT * FROM location_alerts
                WHERE patient_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (_clean_patient_id(patient_id), safe_limit),
            ).fetchall()
        return [LocationAlert.from_row(row) for row in rows]

    def get_latest_alert(self, patient_id: str) -> LocationAlert | None:
        """Return the latest unresolved or recent alert for one patient."""
        alerts = self.list_alerts(patient_id, limit=1)
        return alerts[0] if alerts else None

    def _save_patient_location(self, location: PatientLocation) -> None:
        """Upsert the latest patient location."""
        with closing(get_connection()) as connection:
            connection.execute(
                """
                INSERT INTO patient_locations (
                    patient_id, latitude, longitude, accuracy,
                    address_text, source, timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(patient_id) DO UPDATE SET
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    accuracy = excluded.accuracy,
                    address_text = excluded.address_text,
                    source = excluded.source,
                    timestamp = excluded.timestamp
                """,
                (
                    location.patient_id,
                    location.latitude,
                    location.longitude,
                    location.accuracy,
                    location.address_text,
                    location.source,
                    location.timestamp,
                ),
            )
            connection.commit()

    def _save_location_alert(self, alert: LocationAlert | None) -> LocationAlert | None:
        """Persist an alert generated during safe-zone evaluation."""
        if alert is None:
            return None

        with closing(get_connection()) as connection:
            connection.execute(
                """
                INSERT INTO location_alerts (
                    patient_id, alert_type, severity, message, latitude,
                    longitude, distance_meters, created_at, resolved
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    alert.patient_id,
                    alert.alert_type,
                    alert.severity,
                    alert.message,
                    alert.latitude,
                    alert.longitude,
                    alert.distance_meters,
                    alert.created_at,
                    1 if alert.resolved else 0,
                ),
            )
            connection.commit()
            row = connection.execute(
                "SELECT * FROM location_alerts WHERE id = last_insert_rowid()"
            ).fetchone()

        return LocationAlert.from_row(row)


def build_caregiver_summary(
    latest_location: PatientLocation | None,
    safe_zone: SafeZone | None,
    evaluation: LocationEvaluation,
) -> str:
    """Build a short Chinese caregiver summary for location status."""
    if latest_location is None:
        return "暂未获取到患者定位信息。"

    if safe_zone is None:
        return "暂未设置安全区域，请家属先设置家庭或常去地点。"

    if evaluation.distance_meters is None:
        return "暂未设置安全区域，请家属先设置家庭或常去地点。"

    distance_text = str(round(evaluation.distance_meters))
    update_time = _format_time_for_summary(latest_location.timestamp)

    if evaluation.inside_safe_zone:
        return (
            f"患者目前位于【{safe_zone.label}】内，距离中心约 "
            f"{distance_text} 米，最后更新时间为 {update_time}。"
        )

    return (
        f"风险提醒：患者已离开【{safe_zone.label}】，距离中心约 "
        f"{distance_text} 米。建议立即联系患者或附近家属。"
    )


def _now_text() -> str:
    """Return an ISO-like timestamp string for persistence."""
    return datetime.now().isoformat(timespec="seconds")


def _clean_patient_id(patient_id: str) -> str:
    """Normalize patient identifiers coming from apps or devices."""
    normalized = str(patient_id or "").strip()
    if not normalized:
        raise ValueError("patient_id is required")
    return normalized


def _optional_float(value: Any) -> float | None:
    """Convert optional numeric payload values."""
    if value in (None, ""):
        return None
    return float(value)


def _optional_text(value: Any) -> str | None:
    """Convert optional text payload values."""
    text = str(value or "").strip()
    return text or None


def _rounded_distance(value: float | None) -> float | None:
    """Round distances for stable caregiver-facing responses."""
    if value is None:
        return None
    return round(value, 1)


def _format_time_for_summary(timestamp: str) -> str:
    """Return HH:MM when possible, otherwise the raw timestamp."""
    if "T" in timestamp:
        return timestamp.split("T", 1)[1][:5]
    return timestamp[:5] if timestamp else "未知时间"

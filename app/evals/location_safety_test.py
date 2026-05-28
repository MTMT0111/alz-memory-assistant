"""Lightweight checks for the location safety backend module.

Run with:
    python -m app.evals.location_safety_test

The script uses a throwaway patient id and removes its rows afterwards so it
can be run in a local development database without polluting demo data.
"""

from __future__ import annotations

import asyncio
from contextlib import closing

from app.database import get_connection
from app.init_db import initialize_database
from app.models.location import PatientLocation, SafeZone
from app.routes.location import LocationUpdateRequest, SafeZoneRequest
from app.routes.location import get_location_status, list_location_alerts
from app.routes.location import save_safe_zone, update_patient_location
from app.services.location_safety import LocationSafetyService

TEST_PATIENT_ID = "__location_safety_test__"


def _cleanup() -> None:
    """Remove test rows from the persistent SQLite database."""
    with closing(get_connection()) as connection:
        connection.execute("DELETE FROM location_alerts WHERE patient_id = ?", (TEST_PATIENT_ID,))
        connection.execute("DELETE FROM patient_locations WHERE patient_id = ?", (TEST_PATIENT_ID,))
        connection.execute("DELETE FROM safe_zones WHERE patient_id = ?", (TEST_PATIENT_ID,))
        connection.commit()


def run_checks() -> None:
    """Run service-level and API-level checks."""
    initialize_database()
    _cleanup()

    service = LocationSafetyService()
    home_zone = SafeZone(
        patient_id=TEST_PATIENT_ID,
        label="家庭安全区域",
        center_latitude=28.0,
        center_longitude=120.7,
        radius_meters=500,
        enabled=True,
    )

    same_point_distance = service.calculate_distance_meters(28.0, 120.7, 28.0, 120.7)
    assert same_point_distance < 0.1, "same-point distance should be close to 0"

    nearby_location = PatientLocation(
        patient_id=TEST_PATIENT_ID,
        latitude=28.0001,
        longitude=120.7001,
        accuracy=20,
        source="AMap",
        timestamp="2026-04-28T10:32:00",
    )
    nearby_eval = service.evaluate_location(nearby_location, home_zone)
    assert nearby_eval.inside_safe_zone is True, "nearby location should be inside safe zone"
    assert nearby_eval.alert is None, "inside safe zone should not create alert"

    far_location = PatientLocation(
        patient_id=TEST_PATIENT_ID,
        latitude=28.01,
        longitude=120.71,
        accuracy=20,
        source="AMap",
        timestamp="2026-04-28T10:32:00",
    )
    far_eval = service.evaluate_location(far_location, home_zone)
    assert far_eval.inside_safe_zone is False, "far location should be outside safe zone"
    assert far_eval.alert is not None, "outside safe zone should create alert"
    assert far_eval.alert.severity == "HIGH", "outside safe zone alert severity should be HIGH"

    missing_zone_eval = service.evaluate_location(nearby_location, None)
    assert missing_zone_eval.safe_zone_missing is True, "missing safe zone should be explicit"
    assert missing_zone_eval.alert is None, "missing safe zone should not create alert"

    missing_zone_response = asyncio.run(
        update_patient_location(
            TEST_PATIENT_ID,
            LocationUpdateRequest(
                latitude=28.0001,
                longitude=120.7001,
                accuracy=20,
                source="AMap",
            ),
        )
    )
    assert missing_zone_response["safe_zone_missing"] is True
    assert missing_zone_response["alert"] is None

    zone_response = asyncio.run(
        save_safe_zone(
            TEST_PATIENT_ID,
            SafeZoneRequest(
                label="家庭安全区域",
                center_latitude=28.0,
                center_longitude=120.7,
                radius_meters=500,
                enabled=True,
            ),
        )
    )
    assert zone_response["status"] == "ok"

    location_response = asyncio.run(
        update_patient_location(
            TEST_PATIENT_ID,
            LocationUpdateRequest(
                latitude=28.0001,
                longitude=120.7001,
                accuracy=20,
                address_text="温州市某某路附近",
                source="AMap",
            ),
        )
    )
    assert location_response["inside_safe_zone"] is True

    status_response = asyncio.run(get_location_status(TEST_PATIENT_ID))
    assert "患者目前位于【家庭安全区域】内" in status_response["caregiver_summary"]

    outside_response = asyncio.run(
        update_patient_location(
            TEST_PATIENT_ID,
            LocationUpdateRequest(
                latitude=28.01,
                longitude=120.71,
                accuracy=20,
                source="AMap",
            ),
        )
    )
    assert outside_response["inside_safe_zone"] is False
    assert outside_response["alert"]["severity"] == "HIGH"

    alerts_response = asyncio.run(list_location_alerts(TEST_PATIENT_ID))
    assert len(alerts_response["alerts"]) >= 1

    _cleanup()
    print("location safety checks passed")


if __name__ == "__main__":
    run_checks()

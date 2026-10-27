import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "Gridbricks" in data["app"]
    assert "/docs" in data["docs"]


@patch("app.api.routes.elexon_client.ping_health", new_callable=AsyncMock)
def test_health_endpoint(mock_ping):
    mock_ping.return_value = True
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["elexon_live_accessible"] is True
    assert "data_points_cached" in data


def test_metadata_endpoint():
    resp = client.get("/api/v1/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert "FUELHH" in data["dataset_actual"]
    assert "WINDFOR" in data["dataset_forecast"]
    assert len(data["supported_cutoff_presets"]) >= 4


def test_analysis_summary_endpoint():
    resp = client.get("/api/v1/analysis/summary?start_date=2026-01-01&end_date=2026-01-07&cutoff_preset=DA_1100")
    assert resp.status_code == 200
    data = resp.json()
    assert "summary" in data
    assert "procurementImpact" in data
    assert data["summary"]["totalIntervals"] == 168  # 7 days * 24 hours
    assert data["summary"]["matchedIntervals"] > 0
    assert data["summary"]["maeMW"] is not None


def test_analysis_timeseries_endpoint():
    resp = client.get("/api/v1/analysis/timeseries?start_date=2026-01-01&end_date=2026-01-02&cutoff_preset=DA_1100")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 48  # 2 days * 24 hours
    first = data[0]
    assert "timestamp" in first
    assert "actualMW" in first
    assert "forecastMW" in first


def test_analysis_daily_endpoint():
    resp = client.get("/api/v1/analysis/daily?start_date=2026-01-01&end_date=2026-01-05&cutoff_preset=DA_1100")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert data[0]["date"] == "2026-01-01"
    assert data[0]["matchedIntervals"] == 24


def test_analysis_diurnal_endpoint():
    resp = client.get("/api/v1/analysis/diurnal?start_date=2026-01-01&end_date=2026-01-07&cutoff_preset=DA_1100")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 24
    assert data[0]["hourOfDay"] == 0
    assert data[23]["hourOfDay"] == 23


def test_analysis_errors_endpoint():
    resp = client.get("/api/v1/analysis/errors?start_date=2026-01-01&end_date=2026-01-07&cutoff_preset=DA_1100")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 9
    assert any("Accurate" in b["label"] for b in data)


def test_forecast_table_pagination():
    resp = client.get("/api/v1/analysis/forecast-table?start_date=2026-01-01&end_date=2026-01-02&page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 48
    assert data["page"] == 1
    assert data["pageSize"] == 10
    assert len(data["items"]) == 10
    item = data["items"][0]
    assert "deliveryInterval" in item
    assert "status" in item


def test_export_csv_endpoint():
    resp = client.get("/api/v1/analysis/export-csv?start_date=2026-01-01&end_date=2026-01-02&cutoff_preset=DA_1100")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    content = resp.text
    assert "Delivery Interval (UTC)" in content
    assert "Actual Wind Generation (MW)" in content


def test_invalid_date_range():
    resp = client.get("/api/v1/analysis/summary?start_date=2026-01-10&end_date=2026-01-05")
    assert resp.status_code == 400
    assert "start_date must be less than or equal to end_date" in resp.json()["detail"]


def test_invalid_date_format():
    resp = client.get("/api/v1/analysis/summary?start_date=invalid-date&end_date=2026-01-05")
    assert resp.status_code == 400
    assert "Dates must be in YYYY-MM-DD format" in resp.json()["detail"]

"""test_telemetry.py - OTel collector + Jaeger telemetry chain tests"""
import pytest
import requests
import time

BASE_URL = "http://localhost:5000"
OTEL_COLLECTOR_URL = "http://localhost:4318"
JAEGER_URL = "http://localhost:16686"

def test_otel_collector_http_reachable():
    try:
        r = requests.get(OTEL_COLLECTOR_URL + "/", timeout=5)
        assert r.status_code in (200, 404, 405)
    except requests.exceptions.ConnectionError:
        pytest.skip("otel-collector not running on :4318")

def test_send_telemetry_otel_sent_flag():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"otel_flag_test","session_id":"otel-flag"})
    assert r.status_code == 200
    assert r.json()["otel_sent"] == 1, "otel_sent must be 1 - span was queued for export"

def test_send_telemetry_returns_32char_trace_id():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"trace_id_test","session_id":"trace-test"})
    d = r.json()
    assert "trace_id" in d
    assert len(d["trace_id"]) == 32, f"trace_id must be 32 hex chars: {d['trace_id']!r}"

def test_send_telemetry_returns_16char_span_id():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"span_id_test","session_id":"span-test"})
    d = r.json()
    assert "span_id" in d
    assert len(d["span_id"]) == 16, f"span_id must be 16 hex chars: {d['span_id']!r}"

def test_ltm_save_button_click_otel_chain():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"ltm_save_btn_click","session_id":"otel-save-btn","source":"ui_button"})
    d = r.json()
    assert d["otel_sent"] == 1
    assert d["trace_id"] != ""
    assert d["db_row_id"] > 0

def test_ltm_recall_button_click_otel_chain():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"ltm_recall_btn_click","session_id":"otel-recall-btn","source":"ui_button"})
    d = r.json()
    assert d["otel_sent"] == 1
    assert d["trace_id"] != ""

def test_drag_db_footprint_click_otel_chain():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"drag_db_footprint_click","session_id":"otel-drag","source":"ui_button"})
    d = r.json()
    assert d["otel_sent"] == 1
    assert d["trace_id"] != ""
    assert d["db_row_id"] > 0

def test_ltm_save_api_otel_chain():
    r = requests.post(BASE_URL + "/api/ltm/save",
                      json={"session_id":"otel-ltm-save","content":"OTel chain test"})
    d = r.json()
    assert d.get("otel_sent") == 1
    assert d.get("trace_id","") != ""

def test_jaeger_reachable():
    try:
        r = requests.get(JAEGER_URL + "/api/services", timeout=5)
        assert r.status_code == 200
        services = r.json().get("data", [])
        assert isinstance(services, list)
    except requests.exceptions.ConnectionError:
        pytest.skip("Jaeger not running on :16686")

def test_jaeger_has_ltm_service_after_send():
    requests.post(BASE_URL + "/api/ltm/save",
                  json={"session_id":"jaeger-svc","content":"jaeger test"})
    time.sleep(2)
    try:
        r = requests.get(JAEGER_URL + "/api/services", timeout=5)
        services = r.json().get("data", [])
        assert len(services) > 0, "Jaeger must have at least one service after span sent"
    except requests.exceptions.ConnectionError:
        pytest.skip("Jaeger not running")

def test_telemetry_db_row_matches_api_trace_id():
    sid = "tel-match-test"
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry",
                      json={"event":"match_test","session_id":sid})
    api_trace_id = r.json()["trace_id"]
    rows = requests.get(BASE_URL + "/api/db/query",
                        params={"table":"telemetry_events","session_id":sid}).json()
    assert len(rows) > 0
    assert rows[0]["trace_id"] == api_trace_id, "DB trace_id must match API response trace_id"

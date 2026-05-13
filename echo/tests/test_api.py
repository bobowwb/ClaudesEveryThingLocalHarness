"""test_api.py - Pure API tests for LTM Chat UI (no Selenium required)"""
import pytest
import requests
import time

BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    r = requests.get(BASE_URL + "/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_chat_route_serves_html():
    r = requests.get(BASE_URL + "/chat")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")
    assert "loadDbFootprint" in r.text

def test_root_route_serves_html():
    r = requests.get(BASE_URL + "/")
    assert r.status_code == 200
    assert "loadDbFootprint" in r.text

def test_ltm_save_returns_id():
    r = requests.post(BASE_URL + "/api/ltm/save", json={"session_id":"api-test","content":"API test memory"})
    assert r.status_code == 200
    d = r.json()
    assert "id" in d
    assert d["id"] > 0

def test_ltm_save_returns_trace_id():
    r = requests.post(BASE_URL + "/api/ltm/save", json={"session_id":"api-test","content":"trace test"})
    d = r.json()
    assert "trace_id" in d
    assert len(d["trace_id"]) == 32

def test_ltm_save_returns_otel_sent_1():
    r = requests.post(BASE_URL + "/api/ltm/save", json={"session_id":"api-test","content":"otel test"})
    assert r.json().get("otel_sent") == 1

def test_ltm_recall_returns_list():
    sid = "recall-api-test"
    requests.post(BASE_URL + "/api/ltm/save", json={"session_id":sid,"content":"recall me"})
    r = requests.get(BASE_URL + "/api/ltm/recall", params={"session_id":sid})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["content"] == "recall me"

def test_chat_message_stored():
    sid = "chat-api-test"
    r = requests.post(BASE_URL + "/api/chat/message", json={"session_id":sid,"role":"user","content":"hello api"})
    assert r.status_code in (200, 201)
    assert "id" in r.json()

def test_send_telemetry_returns_otel_ids():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"event":"test_event","session_id":"tel-api-test"})
    assert r.status_code == 200
    d = r.json()
    assert d["otel_sent"] == 1
    assert len(d["trace_id"]) == 32
    assert len(d["span_id"]) == 16
    assert d["db_row_id"] > 0

def test_send_telemetry_ltm_save_btn_click():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"event":"ltm_save_btn_click","session_id":"btn-test","source":"ui_button"})
    assert r.status_code == 200
    assert r.json()["otel_sent"] == 1

def test_send_telemetry_ltm_recall_btn_click():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"event":"ltm_recall_btn_click","session_id":"btn-test","source":"ui_button"})
    assert r.status_code == 200
    assert r.json()["otel_sent"] == 1

def test_send_telemetry_drag_db_footprint_click():
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"event":"drag_db_footprint_click","session_id":"drag-test","source":"ui_button"})
    assert r.status_code == 200
    d = r.json()
    assert d["otel_sent"] == 1
    assert d["trace_id"] != ""

def test_db_telemetry_endpoint_returns_rows():
    requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"event":"db_tel_test","session_id":"dbtel"})
    r = requests.get(BASE_URL + "/api/db/telemetry")
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list) and len(rows) > 0
    assert all(f in rows[0] for f in ("id","session_id","event_type","trace_id","otel_sent","created_at"))

def test_db_tables_endpoint():
    r = requests.get(BASE_URL + "/api/db/tables")
    assert r.status_code == 200
    tables = r.json()
    for t in ("ltm_memories", "chat_history", "telemetry_events", "sessions"):
        assert t in tables

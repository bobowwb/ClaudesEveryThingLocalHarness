"""test_db.py - SQL DB footprint tests for all tables"""
import pytest
import requests
import time

BASE_URL = "http://localhost:5000"

def test_ltm_memories_table_exists():
    r = requests.get(BASE_URL + "/api/db/tables")
    assert "ltm_memories" in r.json()

def test_chat_history_table_exists():
    assert "chat_history" in requests.get(BASE_URL + "/api/db/tables").json()

def test_telemetry_events_table_exists():
    assert "telemetry_events" in requests.get(BASE_URL + "/api/db/tables").json()

def test_sessions_table_exists():
    assert "sessions" in requests.get(BASE_URL + "/api/db/tables").json()

def test_sql_ltm_memories_row_on_ltm_save():
    sid = "db-ltm-test"
    requests.post(BASE_URL + "/api/ltm/save", json={"session_id":sid,"content":"SQL ltm test"})
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"ltm_memories","session_id":sid}).json()
    assert len(rows) > 0
    assert rows[0]["content"] == "SQL ltm test"
    assert rows[0]["session_id"] == sid

def test_sql_chat_history_row_on_message():
    sid = "db-chat-test"
    requests.post(BASE_URL + "/api/chat/message", json={"session_id":sid,"role":"user","content":"SQL chat test"})
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"chat_history","session_id":sid}).json()
    assert len(rows) > 0
    assert rows[0]["content"] == "SQL chat test"
    assert rows[0]["role"] == "user"

def test_sql_telemetry_row_on_send_telemetry():
    sid = "db-tel-test"
    requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"session_id":sid,"event":"ltm_save"})
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"telemetry_events","session_id":sid}).json()
    assert len(rows) > 0
    assert rows[0]["otel_sent"] == 1
    assert rows[0]["trace_id"] != ""
    assert rows[0]["event_type"] == "ltm_save"

def test_sql_all_tables_footprint_full_ltm_scenario():
    sid = "db-full-scenario"
    requests.post(BASE_URL + "/api/ltm/save", json={"session_id":sid,"content":"Full scenario"})
    requests.get(BASE_URL + "/api/ltm/recall", params={"session_id":sid})
    requests.post(BASE_URL + "/api/chat/message", json={"session_id":sid,"role":"user","content":"msg"})
    requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"session_id":sid,"event":"ltm_recall_btn_click"})
    time.sleep(0.3)
    for tbl in ("ltm_memories","chat_history","telemetry_events"):
        rows = requests.get(BASE_URL + "/api/db/query", params={"table":tbl,"session_id":sid}).json()
        assert len(rows) > 0, f"{tbl} must have rows after full scenario"

def test_sql_telemetry_otel_sent_always_1():
    sid = "db-otel-sent"
    requests.post(BASE_URL + "/api/ltm/save", json={"session_id":sid,"content":"otel check"})
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"telemetry_events","session_id":sid}).json()
    assert all(r["otel_sent"] == 1 for r in rows), "All telemetry rows must have otel_sent=1"

def test_sql_telemetry_trace_id_stored():
    sid = "db-trace-check"
    r = requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"session_id":sid,"event":"trace_check"})
    trace_id = r.json()["trace_id"]
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"telemetry_events","session_id":sid}).json()
    assert len(rows) > 0
    assert rows[0]["trace_id"] == trace_id

def test_sql_ltm_save_btn_click_footprint():
    sid = "db-save-btn"
    requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"session_id":sid,"event":"ltm_save_btn_click","source":"ui_button"})
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"telemetry_events","session_id":sid}).json()
    assert any(r["event_type"] == "ltm_save_btn_click" for r in rows)

def test_sql_drag_db_footprint_click_footprint():
    sid = "db-drag-btn"
    requests.post(BASE_URL + "/api/ltm/send-telemetry", json={"session_id":sid,"event":"drag_db_footprint_click","source":"ui_button"})
    rows = requests.get(BASE_URL + "/api/db/query", params={"table":"telemetry_events","session_id":sid}).json()
    assert any(r["event_type"] == "drag_db_footprint_click" for r in rows)

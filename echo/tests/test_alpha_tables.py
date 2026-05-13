"""test_alpha_tables.py - Alpha plan OTel AppFnd table footprint tests
Mirrors HDB SYSTEM schema: LTM4D_MEMORY_TRACES, LTM4D_SPANS, LTM_ALPHA_*
"""
import pytest
import requests
import time

BASE_URL = "http://localhost:5000"

ALPHA_TABLES = [
    "ltm4d_memory_traces",
    "ltm4d_spans",
    "ltm_alpha_memories",
    "ltm_alpha_events",
    "ltm_alpha_appfnd_logs",
    "ltm_alpha_graph_nodes",
    "ltm_alpha_graph_edges",
]

def test_alpha_tables_endpoint_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert r.status_code == 200
    tables = r.json()
    assert isinstance(tables, list)

def test_all_alpha_tables_in_db():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    tables = r.json()
    for t in ALPHA_TABLES:
        assert t in tables, f"Alpha table missing from DB: {t}"

def test_ltm4d_memory_traces_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm4d_memory_traces" in r.json()

def test_ltm4d_spans_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm4d_spans" in r.json()

def test_ltm_alpha_memories_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm_alpha_memories" in r.json()

def test_ltm_alpha_events_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm_alpha_events" in r.json()

def test_ltm_alpha_appfnd_logs_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm_alpha_appfnd_logs" in r.json()

def test_ltm_alpha_graph_nodes_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm_alpha_graph_nodes" in r.json()

def test_ltm_alpha_graph_edges_table_exists():
    r = requests.get(BASE_URL + "/api/alpha/tables")
    assert "ltm_alpha_graph_edges" in r.json()

def test_alpha_event_api_writes_alpha_tables():
    sid = "alpha-event-test"
    r = requests.post(BASE_URL + "/api/alpha/event",
                      json={"session_id":sid,"event":"ltm_save_btn_click","source":"ui_button"})
    assert r.status_code == 200
    d = r.json()
    assert d["otel_sent"] == 1
    assert d["alpha_row_id"] > 0
    assert len(d["trace_id"]) == 32

def test_alpha_event_populates_ltm_alpha_events():
    sid = "alpha-evt-sql"
    requests.post(BASE_URL + "/api/alpha/event",
                  json={"session_id":sid,"event":"alpha_test_event","source":"test"})
    r = requests.get(BASE_URL + "/api/alpha/query",
                     params={"table":"ltm_alpha_events","session_id":sid})
    rows = r.json()
    assert len(rows) > 0, "ltm_alpha_events must have row after /api/alpha/event"
    assert rows[0]["event_type"] == "alpha_test_event"
    assert rows[0]["otel_sent"] == 1

def test_alpha_event_populates_ltm4d_memory_traces():
    sid = "alpha-trace-sql"
    r = requests.post(BASE_URL + "/api/alpha/event",
                      json={"session_id":sid,"event":"trace_footprint_test","source":"test"})
    trace_id = r.json()["trace_id"]
    rows = requests.get(BASE_URL + "/api/alpha/query",
                        params={"table":"ltm4d_memory_traces","session_id":sid}).json()
    assert len(rows) > 0, "ltm4d_memory_traces must have row after alpha event"
    assert rows[0]["trace_id"] == trace_id

def test_alpha_event_populates_ltm4d_spans():
    sid = "alpha-span-sql"
    r = requests.post(BASE_URL + "/api/alpha/event",
                      json={"session_id":sid,"event":"span_footprint_test","source":"test"})
    span_id = r.json()["span_id"]
    rows = requests.get(BASE_URL + "/api/alpha/query",
                        params={"table":"ltm4d_spans","session_id":sid}).json()
    assert len(rows) > 0, "ltm4d_spans must have row after alpha event"
    assert rows[0]["span_id"] == span_id
    assert rows[0]["otel_exported"] == 1

def test_alpha_event_populates_appfnd_logs():
    sid = "alpha-log-sql"
    requests.post(BASE_URL + "/api/alpha/event",
                  json={"session_id":sid,"event":"appfnd_log_test","source":"test"})
    rows = requests.get(BASE_URL + "/api/alpha/query",
                        params={"table":"ltm_alpha_appfnd_logs","session_id":sid}).json()
    assert len(rows) > 0, "ltm_alpha_appfnd_logs must have row after alpha event"
    assert "ALPHA" in rows[0]["message"]

def test_alpha_full_ltm_scenario_all_tables():
    sid = "alpha-full-scenario"
    # Fire multiple alpha events to populate all tables
    for evt in ("ltm_save_btn_click", "ltm_recall_btn_click", "drag_db_footprint_click"):
        requests.post(BASE_URL + "/api/alpha/event",
                      json={"session_id":sid,"event":evt,"source":"ui_button"})
    time.sleep(0.3)
    # Verify footprint in all alpha event tables
    for table in ("ltm_alpha_events","ltm4d_memory_traces","ltm4d_spans","ltm_alpha_appfnd_logs"):
        rows = requests.get(BASE_URL + "/api/alpha/query",
                            params={"table":table,"session_id":sid}).json()
        assert len(rows) > 0, f"{table} must have rows after full alpha LTM scenario"

def test_alpha_query_endpoint_works_for_all_tables():
    """Verify /api/alpha/query works for every alpha table."""
    for table in ALPHA_TABLES:
        r = requests.get(BASE_URL + "/api/alpha/query", params={"table":table})
        assert r.status_code == 200, f"/api/alpha/query?table={table} must return 200"
        assert isinstance(r.json(), list), f"{table} query must return a list"

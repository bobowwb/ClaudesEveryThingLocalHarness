import sqlite3, json, os

DB_PATH     = os.environ.get("DB_PATH",     os.path.join(os.path.dirname(os.path.abspath(__file__)), "ltm_chat.db"))
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    with get_connection() as conn:
        with open(SCHEMA_PATH) as f:
            conn.executescript(f.read())

def save_ltm_memory(session_id, content, tags=""):
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO ltm_memories (session_id,content,tags) VALUES (?,?,?)", (session_id,content,tags))
        conn.execute("INSERT INTO sessions(id) VALUES(?) ON CONFLICT(id) DO UPDATE SET last_active=datetime('now')", (session_id,))
        return cur.lastrowid

def recall_ltm_memories(session_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM ltm_memories WHERE session_id=? ORDER BY created_at DESC", (session_id,)).fetchall()
        return [dict(r) for r in rows]

def save_chat_message(session_id, role, content):
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO chat_history (session_id,role,content) VALUES (?,?,?)", (session_id,role,content))
        conn.execute("INSERT INTO sessions(id) VALUES(?) ON CONFLICT(id) DO UPDATE SET last_active=datetime('now')", (session_id,))
        return cur.lastrowid

def get_chat_history(session_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM chat_history WHERE session_id=? ORDER BY created_at ASC", (session_id,)).fetchall()
        return [dict(r) for r in rows]

def save_telemetry_event(session_id, event_type, trace_id="", span_id="", payload=None, otel_sent=0):
    with get_connection() as conn:
        cur = conn.execute("INSERT INTO telemetry_events (session_id,event_type,trace_id,span_id,payload,otel_sent) VALUES (?,?,?,?,?,?)", (session_id, event_type, trace_id, span_id, json.dumps(payload or {}), otel_sent))
        return cur.lastrowid

def query_telemetry_by_session(session_id):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM telemetry_events WHERE session_id=? ORDER BY created_at DESC", (session_id,)).fetchall()
        return [dict(r) for r in rows]

def get_all_telemetry():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM telemetry_events ORDER BY created_at DESC LIMIT 200").fetchall()
        return [dict(r) for r in rows]

def list_tables():
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [r["name"] for r in rows]

def query_table(table, session_id=None):
    allowed = {"ltm_memories","chat_history","telemetry_events","sessions"}
    if table not in allowed:
        return []
    with get_connection() as conn:
        if session_id:
            rows = conn.execute(f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid DESC", (session_id,)).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]

def count_rows(table, session_id=None):
    allowed = {"ltm_memories","chat_history","telemetry_events","sessions"}
    if table not in allowed:
        return 0
    with get_connection() as conn:
        if session_id:
            row = conn.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE session_id=?", (session_id,)).fetchone()
        else:
            row = conn.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()
        return row["cnt"] if row else 0


# ── Alpha Plan OTel AppFnd table helpers ──────────────────────────────────

ALPHA_TABLES = {"ltm4d_memory_traces","ltm4d_spans","ltm_alpha_memories","ltm_alpha_events","ltm_alpha_appfnd_logs","ltm_alpha_graph_nodes","ltm_alpha_graph_edges"}

def save_ltm4d_trace(session_id, trace_id, operation_name, service_name="ltm-chat-service", attributes=None, status="OK"):
    import json
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO ltm4d_memory_traces (trace_id,session_id,service_name,operation_name,status,attributes) VALUES (?,?,?,?,?,?)",
            (trace_id, session_id, service_name, operation_name, status, json.dumps(attributes or {})))
        return cur.lastrowid

def save_ltm4d_span(session_id, span_id, trace_id, operation_name, parent_span_id="", service_name="ltm-chat-service", attributes=None, otel_exported=0):
    import json
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO ltm4d_spans (span_id,trace_id,parent_span_id,session_id,operation_name,service_name,attributes,otel_exported) VALUES (?,?,?,?,?,?,?,?)",
            (span_id, trace_id, parent_span_id, session_id, operation_name, service_name, json.dumps(attributes or {}), otel_exported))
        return cur.lastrowid

def save_alpha_memory(session_id, content, memory_key="", trace_id="", importance=1.0, tags=""):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO ltm_alpha_memories (session_id,content,memory_key,trace_id,importance,tags) VALUES (?,?,?,?,?,?)",
            (session_id, content, memory_key, trace_id, importance, tags))
        return cur.lastrowid

def save_alpha_event(session_id, event_type, trace_id="", span_id="", event_source="ui_button", payload=None, otel_sent=0):
    import json
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO ltm_alpha_events (session_id,event_type,event_source,trace_id,span_id,payload,otel_sent) VALUES (?,?,?,?,?,?,?)",
            (session_id, event_type, event_source, trace_id, span_id, json.dumps(payload or {}), otel_sent))
        return cur.lastrowid

def save_alpha_appfnd_log(session_id, message, log_level="INFO", trace_id="", span_id="", attributes=None):
    import json
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO ltm_alpha_appfnd_logs (session_id,log_level,message,trace_id,span_id,attributes) VALUES (?,?,?,?,?,?)",
            (session_id, log_level, message, trace_id, span_id, json.dumps(attributes or {})))
        return cur.lastrowid

def save_alpha_graph_node(session_id, node_id, label, node_type="memory", content="", trace_id="", weight=1.0):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO ltm_alpha_graph_nodes (node_id,session_id,node_type,label,content,trace_id,weight) VALUES (?,?,?,?,?,?,?)",
            (node_id, session_id, node_type, label, content, trace_id, weight))
        return cur.lastrowid

def save_alpha_graph_edge(session_id, edge_id, source_node_id, target_node_id, relation_type="related", trace_id="", weight=1.0):
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO ltm_alpha_graph_edges (edge_id,session_id,source_node_id,target_node_id,relation_type,trace_id,weight) VALUES (?,?,?,?,?,?,?)",
            (edge_id, session_id, source_node_id, target_node_id, relation_type, trace_id, weight))
        return cur.lastrowid

def list_all_tables():
    """Returns all tables including alpha tables."""
    with get_connection() as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [r["name"] for r in rows]

def query_alpha_table(table, session_id=None):
    all_tables = {"ltm4d_memory_traces","ltm4d_spans","ltm_alpha_memories","ltm_alpha_events","ltm_alpha_appfnd_logs","ltm_alpha_graph_nodes","ltm_alpha_graph_edges","ltm_memories","chat_history","telemetry_events","sessions"}
    if table not in all_tables:
        return []
    with get_connection() as conn:
        if session_id:
            rows = conn.execute(f"SELECT * FROM {table} WHERE session_id=? ORDER BY rowid DESC", (session_id,)).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]

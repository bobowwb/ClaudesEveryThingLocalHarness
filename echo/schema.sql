-- LTM Chat UI Database Schema
CREATE TABLE IF NOT EXISTS ltm_memories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    created_at  DATETIME DEFAULT (datetime('now')),
    tags        TEXT    DEFAULT ''
);
CREATE TABLE IF NOT EXISTS chat_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    role        TEXT    NOT NULL CHECK(role IN ('user','assistant','system')),
    content     TEXT    NOT NULL,
    created_at  DATETIME DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS telemetry_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    trace_id    TEXT    DEFAULT '',
    span_id     TEXT    DEFAULT '',
    payload     TEXT    DEFAULT '{}',
    otel_sent   INTEGER DEFAULT 0,
    created_at  DATETIME DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    created_at  DATETIME DEFAULT (datetime('now')),
    last_active DATETIME DEFAULT (datetime('now')),
    meta        TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_ltm_session   ON ltm_memories(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_session  ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_telem_session ON telemetry_events(session_id);

-- =================================================================
-- LTM ALPHA PLAN - OTel AppFnd (Application Foundation) Tables
-- Mirrors HDB SYSTEM schema: LTM4D_MEMORY_TRACES, LTM4D_SPANS, etc.
-- =================================================================

-- LTM4D_MEMORY_TRACES: Full OTel trace records (alpha/4D plan)
CREATE TABLE IF NOT EXISTS ltm4d_memory_traces (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id        TEXT    NOT NULL UNIQUE,
    session_id      TEXT    NOT NULL,
    service_name    TEXT    DEFAULT 'ltm-chat-service',
    operation_name  TEXT    NOT NULL,
    start_time      DATETIME NOT NULL DEFAULT (datetime('now')),
    end_time        DATETIME,
    duration_ms     INTEGER DEFAULT 0,
    status          TEXT    DEFAULT 'OK',
    attributes      TEXT    DEFAULT '{}',
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- LTM4D_SPANS: Individual OTel spans within a trace (alpha/4D plan)
CREATE TABLE IF NOT EXISTS ltm4d_spans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    span_id         TEXT    NOT NULL,
    trace_id        TEXT    NOT NULL,
    parent_span_id  TEXT    DEFAULT '',
    session_id      TEXT    NOT NULL,
    operation_name  TEXT    NOT NULL,
    service_name    TEXT    DEFAULT 'ltm-chat-service',
    start_time      DATETIME NOT NULL DEFAULT (datetime('now')),
    end_time        DATETIME,
    duration_ms     INTEGER DEFAULT 0,
    status          TEXT    DEFAULT 'OK',
    attributes      TEXT    DEFAULT '{}',
    events          TEXT    DEFAULT '[]',
    otel_exported   INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- LTM_ALPHA_MEMORIES: Alpha-plan LTM memories (structured for AppFnd)
CREATE TABLE IF NOT EXISTS ltm_alpha_memories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL,
    memory_key      TEXT    DEFAULT '',
    content         TEXT    NOT NULL,
    embedding_ref   TEXT    DEFAULT '',
    importance      REAL    DEFAULT 1.0,
    decay_factor    REAL    DEFAULT 0.99,
    access_count    INTEGER DEFAULT 0,
    last_accessed   DATETIME DEFAULT (datetime('now')),
    tags            TEXT    DEFAULT '',
    trace_id        TEXT    DEFAULT '',
    plan_version    TEXT    DEFAULT 'alpha',
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- LTM_ALPHA_EVENTS: AppFnd telemetry events for alpha plan
CREATE TABLE IF NOT EXISTS ltm_alpha_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL,
    event_type      TEXT    NOT NULL,
    event_source    TEXT    DEFAULT 'ui_button',
    trace_id        TEXT    DEFAULT '',
    span_id         TEXT    DEFAULT '',
    payload         TEXT    DEFAULT '{}',
    otel_sent       INTEGER DEFAULT 0,
    otel_collector  TEXT    DEFAULT 'http://localhost:4318',
    plan_version    TEXT    DEFAULT 'alpha',
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- LTM_ALPHA_APPFND_LOGS: Application Foundation layer logs
CREATE TABLE IF NOT EXISTS ltm_alpha_appfnd_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL,
    log_level       TEXT    DEFAULT 'INFO' CHECK(log_level IN ('DEBUG','INFO','WARN','ERROR')),
    logger_name     TEXT    DEFAULT 'ltm-appfnd',
    message         TEXT    NOT NULL,
    trace_id        TEXT    DEFAULT '',
    span_id         TEXT    DEFAULT '',
    attributes      TEXT    DEFAULT '{}',
    plan_version    TEXT    DEFAULT 'alpha',
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- LTM_ALPHA_GRAPH_NODES: Alpha memory graph nodes
CREATE TABLE IF NOT EXISTS ltm_alpha_graph_nodes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id         TEXT    NOT NULL UNIQUE,
    session_id      TEXT    NOT NULL,
    node_type       TEXT    DEFAULT 'memory',
    label           TEXT    NOT NULL,
    content         TEXT    DEFAULT '',
    embedding_ref   TEXT    DEFAULT '',
    weight          REAL    DEFAULT 1.0,
    trace_id        TEXT    DEFAULT '',
    plan_version    TEXT    DEFAULT 'alpha',
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- LTM_ALPHA_GRAPH_EDGES: Alpha memory graph edges
CREATE TABLE IF NOT EXISTS ltm_alpha_graph_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    edge_id         TEXT    NOT NULL UNIQUE,
    session_id      TEXT    NOT NULL,
    source_node_id  TEXT    NOT NULL,
    target_node_id  TEXT    NOT NULL,
    relation_type   TEXT    DEFAULT 'related',
    weight          REAL    DEFAULT 1.0,
    trace_id        TEXT    DEFAULT '',
    plan_version    TEXT    DEFAULT 'alpha',
    created_at      DATETIME DEFAULT (datetime('now'))
);

-- Indexes for alpha tables
CREATE INDEX IF NOT EXISTS idx_ltm4d_traces_session  ON ltm4d_memory_traces(session_id);
CREATE INDEX IF NOT EXISTS idx_ltm4d_traces_trace    ON ltm4d_memory_traces(trace_id);
CREATE INDEX IF NOT EXISTS idx_ltm4d_spans_session   ON ltm4d_spans(session_id);
CREATE INDEX IF NOT EXISTS idx_ltm4d_spans_trace     ON ltm4d_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_alpha_mem_session     ON ltm_alpha_memories(session_id);
CREATE INDEX IF NOT EXISTS idx_alpha_events_session  ON ltm_alpha_events(session_id);
CREATE INDEX IF NOT EXISTS idx_alpha_events_trace    ON ltm_alpha_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_alpha_logs_session    ON ltm_alpha_appfnd_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_alpha_nodes_session   ON ltm_alpha_graph_nodes(session_id);
CREATE INDEX IF NOT EXISTS idx_alpha_edges_session   ON ltm_alpha_graph_edges(session_id);

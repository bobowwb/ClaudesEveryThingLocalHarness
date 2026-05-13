import os
import logging

logger = logging.getLogger(__name__)

# SAP HANA DB connection defaults - SYSTEM/manager
HDB_HOST   = os.environ.get("HDB_HOST",   "localhost")
HDB_PORT   = int(os.environ.get("HDB_PORT",   "30015"))
HDB_USER   = os.environ.get("HDB_USER",   "SYSTEM")
HDB_PASS   = os.environ.get("HDB_PASS",   "manager")
HDB_SCHEMA = os.environ.get("HDB_SCHEMA", "SYSTEM")

_conn = None

def get_hdb_connection():
    """Get or create HANA DB connection. Returns None if hdbcli not available."""
    global _conn
    try:
        import hdbcli.dbapi as hdb
    except ImportError:
        logger.warning("[HDB] hdbcli not installed - HANA DB features disabled. pip install hdbcli")
        return None
    try:
        if _conn is None:
            logger.info("[HDB] Connecting to HANA DB %s:%s as %s", HDB_HOST, HDB_PORT, HDB_USER)
            _conn = hdb.connect(address=HDB_HOST, port=HDB_PORT, user=HDB_USER, password=HDB_PASS)
            logger.info("[HDB] Connected to HANA DB")
        return _conn
    except Exception as e:
        logger.error("[HDB] Connection failed: %s", e)
        _conn = None
        return None

def hdb_ping():
    """Ping HANA DB with SELECT 1 FROM DUMMY. Returns True if connected."""
    conn = get_hdb_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM DUMMY")
        result = cur.fetchone()[0]
        return result == 1
    except Exception as e:
        logger.error("[HDB] ping failed: %s", e)
        return False

def hdb_sql_count(table, schema=None, where=""):
    """Execute SELECT COUNT(*) FROM schema.table WHERE ..."""
    conn = get_hdb_connection()
    if not conn:
        return -1
    s = schema or HDB_SCHEMA
    q = f"SELECT COUNT(*) FROM \"{s}\".\"{table}\""
    if where:
        q += f" WHERE {where}"
    try:
        cur = conn.cursor()
        cur.execute(q)
        return cur.fetchone()[0]
    except Exception as e:
        logger.error("[HDB] COUNT failed %s.%s: %s", s, table, e)
        return -1

def hdb_write_trace(trace_id, session_id, operation_name, status="OK", attributes="{}"):
    """Write a trace row to HDB SYSTEM.LTM4D_MEMORY_TRACES."""
    conn = get_hdb_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO \"SYSTEM\".\"LTM4D_MEMORY_TRACES\" "
            "(TRACE_ID,SESSION_ID,OPERATION_NAME,STATUS,ATTRIBUTES) VALUES (?,?,?,?,?)",
            (trace_id, session_id, operation_name, status, attributes))
        conn.commit()
        logger.info("[HDB] wrote trace %s to LTM4D_MEMORY_TRACES", trace_id)
        return True
    except Exception as e:
        logger.error("[HDB] write trace failed: %s", e)
        return False

def hdb_write_span(span_id, trace_id, session_id, operation_name, otel_exported=1):
    """Write a span row to HDB SYSTEM.LTM4D_SPANS."""
    conn = get_hdb_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO \"SYSTEM\".\"LTM4D_SPANS\" "
            "(SPAN_ID,TRACE_ID,SESSION_ID,OPERATION_NAME,OTEL_EXPORTED) VALUES (?,?,?,?,?)",
            (span_id, trace_id, session_id, operation_name, otel_exported))
        conn.commit()
        logger.info("[HDB] wrote span %s to LTM4D_SPANS", span_id)
        return True
    except Exception as e:
        logger.error("[HDB] write span failed: %s", e)
        return False

def list_hdb_tables(schema=None):
    """List all tables in HDB schema."""
    conn = get_hdb_connection()
    if not conn:
        return []
    s = schema or HDB_SCHEMA
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT TABLE_NAME FROM SYS.TABLES WHERE SCHEMA_NAME=\x27{s}\x27 ORDER BY TABLE_NAME")
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        logger.error("[HDB] list_tables failed: %s", e)
        return []

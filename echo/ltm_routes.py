import json, logging
from flask import Blueprint, request, jsonify
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import db_helper as db
from otel_setup import get_tracer, span_to_ids

logger = logging.getLogger(__name__)
ltm_bp = Blueprint("ltm", __name__)

def _emit_span(event_type, session_id, extra=None):
    """Create OTel span, export to otel-collector, return ids+otel_sent flag."""
    tracer = get_tracer()
    ids = {"trace_id": "", "span_id": ""}
    otel_sent = 0
    with tracer.start_as_current_span(event_type) as span:
        span.set_attribute("session.id", str(session_id))
        span.set_attribute("event.type", str(event_type))
        if extra:
            for k, v in extra.items():
                span.set_attribute(f"ltm.{k}", str(v))
        ids = span_to_ids(span)
        span.set_status(Status(StatusCode.OK))
        otel_sent = 1
        logger.info("[TELEMETRY] event=%s session=%s trace=%s span=%s", event_type, session_id, ids["trace_id"], ids["span_id"])
    return ids, otel_sent

# POST /api/ltm/send-telemetry  <-- FIXED endpoint (was broken before)
@ltm_bp.route("/api/ltm/send-telemetry", methods=["POST"])
def send_telemetry():
    body       = request.get_json(force=True) or {}
    session_id = body.get("session_id", "anonymous")
    event_type = body.get("event", body.get("event_type", "ltm_event"))
    extra      = {k: v for k, v in body.items() if k not in ("session_id", "event", "event_type")}
    ids, otel_sent = _emit_span(event_type, session_id, extra)
    row_id = db.save_telemetry_event(
        session_id=session_id, event_type=event_type,
        trace_id=ids["trace_id"], span_id=ids["span_id"],
        payload=body, otel_sent=otel_sent)
    return jsonify({"status": "ok", "event_type": event_type, "session_id": session_id,
                    "trace_id": ids["trace_id"], "span_id": ids["span_id"],
                    "otel_sent": otel_sent, "db_row_id": row_id}), 200

# POST /api/ltm/save
@ltm_bp.route("/api/ltm/save", methods=["POST"])
def ltm_save():
    body       = request.get_json(force=True) or {}
    session_id = body.get("session_id", "anonymous")
    content    = body.get("content", "")
    tags       = body.get("tags", "")
    row_id = db.save_ltm_memory(session_id, content, tags)
    ids, otel_sent = _emit_span("ltm_save", session_id, {"content_len": len(content), "row_id": row_id})
    db.save_telemetry_event(session_id, "ltm_save", ids["trace_id"], ids["span_id"], {"action": "ltm_save", "row_id": row_id}, otel_sent)
    return jsonify({"status": "ok", "id": row_id, "trace_id": ids["trace_id"], "otel_sent": otel_sent}), 200

# GET /api/ltm/recall
@ltm_bp.route("/api/ltm/recall", methods=["GET"])
def ltm_recall():
    session_id = request.args.get("session_id", "anonymous")
    memories   = db.recall_ltm_memories(session_id)
    ids, otel_sent = _emit_span("ltm_recall", session_id, {"count": len(memories)})
    db.save_telemetry_event(session_id, "ltm_recall", ids["trace_id"], ids["span_id"], {"action": "ltm_recall", "count": len(memories)}, otel_sent)
    return jsonify(memories), 200

# POST /api/chat/message
@ltm_bp.route("/api/chat/message", methods=["POST"])
def chat_message():
    body       = request.get_json(force=True) or {}
    session_id = body.get("session_id", "anonymous")
    role       = body.get("role", "user")
    content    = body.get("content", "")
    row_id = db.save_chat_message(session_id, role, content)
    ids, otel_sent = _emit_span("chat_message", session_id, {"role": role, "row_id": row_id})
    db.save_telemetry_event(session_id, "chat_message", ids["trace_id"], ids["span_id"], {"action": "chat_message", "role": role}, otel_sent)
    return jsonify({"status": "ok", "id": row_id}), 200

# GET /api/db/tables
@ltm_bp.route("/api/db/tables", methods=["GET"])
def db_tables():
    tables = db.list_tables()
    return jsonify(tables), 200

# GET /api/db/query
@ltm_bp.route("/api/db/query", methods=["GET"])
def db_query():
    table      = request.args.get("table", "")
    session_id = request.args.get("session_id", None)
    rows = db.query_table(table, session_id)
    return jsonify(rows), 200

# GET /api/db/telemetry  - returns all recent telemetry for UI #dbfp div
@ltm_bp.route("/api/db/telemetry", methods=["GET"])
def db_telemetry():
    rows = db.get_all_telemetry()
    return jsonify(rows), 200


@ltm_bp.route("/api/alpha/tables",methods=["GET"])
def alpha_tables():
    return jsonify(db.list_all_tables()),200

@ltm_bp.route("/api/alpha/query",methods=["GET"])
def alpha_query():
    t=request.args.get("table",""); sid=request.args.get("session_id",None)
    return jsonify(db.query_alpha_table(t,sid)),200

@ltm_bp.route("/api/alpha/event",methods=["POST"])
def alpha_event():
    body=request.get_json(force=True) or {}
    sid=body.get("session_id","anon"); evt=body.get("event",body.get("event_type","alpha_event")); src=body.get("source","ui_button")
    extra={k:v for k,v in body.items() if k not in("session_id","event","event_type","source")}
    ids,otel_sent=_emit_span(evt,sid,extra)
    ar=db.save_alpha_event(session_id=sid,event_type=evt,trace_id=ids["trace_id"],span_id=ids["span_id"],event_source=src,payload=body,otel_sent=otel_sent)
    db.save_ltm4d_trace(session_id=sid,trace_id=ids["trace_id"],operation_name=evt,attributes=extra)
    db.save_ltm4d_span(session_id=sid,span_id=ids["span_id"],trace_id=ids["trace_id"],operation_name=evt,attributes=extra,otel_exported=otel_sent)
    db.save_alpha_appfnd_log(session_id=sid,message="[ALPHA] "+evt+" src="+src,log_level="INFO",trace_id=ids["trace_id"],span_id=ids["span_id"])
    return jsonify({"status":"ok","event_type":evt,"session_id":sid,"trace_id":ids["trace_id"],"span_id":ids["span_id"],"otel_sent":otel_sent,"alpha_row_id":ar}),200


# ── HDB (SAP HANA) status routes ──────────────────────────────────────────

@ltm_bp.route("/api/hdb/ping",methods=["GET"])
def hdb_ping_route():
    """Ping SAP HANA DB with SELECT 1 FROM DUMMY. Returns connection status."""
    try:
        import hdb_helper as hdb
        ok = hdb.hdb_ping()
        tables = hdb.list_hdb_tables() if ok else []
        return jsonify({"status":"ok" if ok else "error","connected":ok,"user":hdb.HDB_USER,"host":hdb.HDB_HOST,"port":hdb.HDB_PORT,"schema":hdb.HDB_SCHEMA,"tables":tables}),200
    except Exception as e:
        return jsonify({"status":"error","connected":False,"error":str(e)}),200

@ltm_bp.route("/api/hdb/tables",methods=["GET"])
def hdb_tables_route():
    """List all tables in HDB SYSTEM schema."""
    try:
        import hdb_helper as hdb
        tables = hdb.list_hdb_tables()
        return jsonify({"tables":tables,"count":len(tables),"schema":hdb.HDB_SCHEMA}),200
    except Exception as e:
        return jsonify({"tables":[],"error":str(e)}),200

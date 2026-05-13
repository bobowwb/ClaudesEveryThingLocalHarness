# LTM Chat UI - Test Suite

## Structure

| File | Tests | Description |
|------|-------|-------------|
| `conftest.py` | fixtures | Shared pytest fixtures (driver, base_url, api) |
| `test_api.py` | 14 | Pure API tests - no browser required |
| `test_db.py` | 11 | SQL footprint tests for all DB tables |
| `test_telemetry.py` | 11 | OTel-collector + Jaeger telemetry chain tests |(if need just docker pull image)
| `test_ui.py` | 12 | Selenium browser UI tests |
| `test_chat_ui.py` | 31 | Full integration test suite (all of the above) |

**Total: 79 tests** across 5 modules

## Running Tests

```bash
# Install deps
pip install pytest selenium requests

# Run all tests
cd echo
pytest tests/ -v

# Run only API tests (no Selenium needed)
pytest tests/test_api.py -v

# Run only DB tests
pytest tests/test_db.py -v

# Run only telemetry tests
pytest tests/test_telemetry.py -v

# Run only UI tests (needs Chrome + chromedriver)
pytest tests/test_ui.py -v
```

## Prerequisites

- Flask app running: `python app.py` (localhost:5000)
- otel-collector running: port 4318 (OTLP/HTTP)
- Jaeger running: port 16686 (UI), 14250 (gRPC)
- Chrome + ChromeDriver for UI tests

## Test Categories

### API Tests (`test_api.py`)
- Health endpoint
- `/` and `/chat` routes serve HTML with `loadDbFootprint`
- LTM save/recall with OTel trace_id verification
- All button click telemetry events: `ltm_save_btn_click`, `ltm_recall_btn_click`, `drag_db_footprint_click`
- `/api/db/telemetry` returns rows with required fields

### DB Tests (`test_db.py`)
- All 4 tables exist: `ltm_memories`, `chat_history`, `telemetry_events`, `sessions`
- SQL queries verify row footprint after each LTM scenario
- `otel_sent=1` verified in DB for all telemetry rows
- `trace_id` stored in DB matches API response

### Telemetry Tests (`test_telemetry.py`)
- otel-collector port 4318 reachable (skip if not running)
- `otel_sent=1` flag always set
- `trace_id` = 32 hex chars, `span_id` = 16 hex chars
- Jaeger service appears after span sent
- DB `trace_id` matches API `trace_id` (end-to-end verification)

### UI Tests (`test_ui.py`)
- All buttons exist: `ltmSaveBtn`, `ltmRecallBtn`, `dragDbFpBtn`
- `#dbfp` div exists
- After `ltmSaveBtn` click: `#dbfp` must NOT show `"No records."`
- After `dragDbFpBtn` click: `#dbfp` populated with telemetry records
- `#statusBar` updates after actions

## Key Diagnostic

If `#dbfp` shows `"No records."` after any LTM button click:
1. Check Flask server is running: `curl http://localhost:5000/health`
2. Check `/api/ltm/send-telemetry` returns `otel_sent=1`
3. Check `/api/db/telemetry` returns rows
4. Check otel-collector logs for incoming spans
5. Open DevTools Console - look for `[LTM-UI]` prefixed logs

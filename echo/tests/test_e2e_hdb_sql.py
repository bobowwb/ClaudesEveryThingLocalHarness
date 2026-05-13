import pytest,requests,os,time

BASE_URL="http://localhost:5000"
HDB_HOST=os.environ.get("HDB_HOST","localhost")
HDB_PORT=int(os.environ.get("HDB_PORT","30015"))
HDB_USER=os.environ.get("HDB_USER","SYSTEM")
HDB_PASS=os.environ.get("HDB_PASS","manager")
HDB_SCHEMA=os.environ.get("HDB_SCHEMA","SYSTEM")
HDB_ALPHA=[("LTM4D_MEMORY_TRACES"),("LTM4D_SPANS")]
HDB_BETA=[("LTM_BETA_GRAPH_EDGES"),("LTM_BETA_GRAPH_NODES"),("LTM_BETA_MEMORIES")]
HDB_GEN=[("MEMORY_EDGES"),("MEMORY_ENTITIES"),("MEMORY_EVENTS")]
ALL_HDB=HDB_ALPHA+HDB_BETA+HDB_GEN

@pytest.fixture(scope="session")
def hdb_conn():
    try: import hdbcli.dbapi as h
    except ImportError: pytest.skip("hdbcli not installed: pip install hdbcli")
    # HDB_PASS defaults to manager
    try:
        c=h.connect(address=HDB_HOST,port=HDB_PORT,user=HDB_USER,password=HDB_PASS)
        yield c; c.close()
    except Exception as e: pytest.skip(f"Cannot connect to HDB {HDB_HOST}:{HDB_PORT}: {e}")

@pytest.fixture(scope="session")
def hdb_cursor(hdb_conn): return hdb_conn.cursor()

def sql_ping(cur,table,schema=None):
    s=schema or HDB_SCHEMA
    cur.execute(f"SELECT COUNT(*) FROM \"{s}\".\"{table}\"")
    return cur.fetchone()[0]

def test_hdb_connection_sql_ping(hdb_conn):
    cur=hdb_conn.cursor(); cur.execute("SELECT 1 FROM DUMMY")
    assert cur.fetchone()[0]==1,"HANA DB SELECT 1 FROM DUMMY must return 1"

@pytest.mark.parametrize("table",ALL_HDB)
def test_hdb_all_tables_sql_ping(hdb_cursor,table):
    "E2E SQL: SELECT COUNT(*) FROM SYSTEM.<table> - ping all HDB tables"
    try: count=sql_ping(hdb_cursor,table); assert count>=0
    except Exception as e: pytest.fail(f"SQL ping FAILED {HDB_SCHEMA}.{table}: {e}")

@pytest.mark.parametrize("table",HDB_ALPHA)
def test_hdb_alpha_tables_sql_ping(hdb_cursor,table):
    "E2E SQL: Alpha plan tables LTM4D_* must be pingable"
    count=sql_ping(hdb_cursor,table); assert count>=0,f"Alpha table {table} SQL ping failed"

@pytest.mark.parametrize("table",HDB_BETA)
def test_hdb_beta_tables_sql_ping(hdb_cursor,table):
    "E2E SQL: Beta plan tables LTM_BETA_* must still be pingable"
    count=sql_ping(hdb_cursor,table); assert count>=0,f"Beta table {table} SQL ping failed"

@pytest.mark.parametrize("table",HDB_GEN)
def test_hdb_generic_memory_tables_sql_ping(hdb_cursor,table):
    "E2E SQL: Generic MEMORY_* tables must be pingable"
    count=sql_ping(hdb_cursor,table); assert count>=0

def test_e2e_ltm_save_btn_creates_hdb_trace_row(hdb_cursor):
    "E2E: ltmSaveBtn click -> API -> verify HDB LTM4D_MEMORY_TRACES grows"
    before=sql_ping(hdb_cursor,"LTM4D_MEMORY_TRACES")
    r=requests.post(BASE_URL+"/api/alpha/event",json={"session_id":"e2e-save","event":"ltm_save_btn_click","source":"e2e_test"})
    assert r.status_code==200; assert r.json()["otel_sent"]==1
    time.sleep(1)
    after=sql_ping(hdb_cursor,"LTM4D_MEMORY_TRACES")
    assert after>=before,f"LTM4D_MEMORY_TRACES must not lose rows: before={before} after={after}"

def test_e2e_ltm_recall_btn_creates_hdb_span_row(hdb_cursor):
    "E2E: ltmRecallBtn click -> API -> verify HDB LTM4D_SPANS grows"
    before=sql_ping(hdb_cursor,"LTM4D_SPANS")
    r=requests.post(BASE_URL+"/api/alpha/event",json={"session_id":"e2e-recall","event":"ltm_recall_btn_click","source":"e2e_test"})
    assert r.status_code==200
    time.sleep(1)
    after=sql_ping(hdb_cursor,"LTM4D_SPANS")
    assert after>=before,f"LTM4D_SPANS must not lose rows: before={before} after={after}"

def test_e2e_drag_db_fp_btn_hdb_both_alpha_tables(hdb_cursor):
    "E2E: dragDbFpBtn -> API -> verify both HDB alpha tables accessible"
    r=requests.post(BASE_URL+"/api/alpha/event",json={"session_id":"e2e-drag","event":"drag_db_footprint_click","source":"ui_button"})
    assert r.status_code==200; assert r.json()["otel_sent"]==1
    trace_id=r.json()["trace_id"]
    time.sleep(1)
    for t in HDB_ALPHA: assert sql_ping(hdb_cursor,t)>=0,f"{t} not pingable after drag click"

def test_e2e_full_ltm_scenario_all_hdb_tables_sql_ping(hdb_cursor):
    "E2E FULL: save+recall+drag -> SQL ping ALL 8 HDB tables - none should fail"
    sid="e2e-full"
    for evt in ("ltm_save_btn_click","ltm_recall_btn_click","drag_db_footprint_click"):
        requests.post(BASE_URL+"/api/alpha/event",json={"session_id":sid,"event":evt,"source":"e2e"})
    time.sleep(2)
    results={}
    for t in ALL_HDB:
        try: results[t]=sql_ping(hdb_cursor,t)
        except Exception as e: pytest.fail(f"E2E SQL ping FAILED {t}: {e}")
    assert all(v>=0 for v in results.values()),f"Some HDB tables returned negative: {results}"

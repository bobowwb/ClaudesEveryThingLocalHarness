import pytest, requests, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

BASE_URL="http://localhost:5000"
OTEL_COLLECTOR_URL="http://localhost:4318"
JAEGER_URL="http://localhost:16686"

@pytest.fixture(scope="session")
def driver():
    o=Options()
    for a in ("--headless","--no-sandbox","--disable-dev-shm-usage"): o.add_argument(a)
    d2=webdriver.Chrome(options=o); d2.implicitly_wait(10); yield d2; d2.quit()

@pytest.fixture(scope="session")
def base_url(): return BASE_URL


def test_page_loads(driver,base_url):
    driver.get(base_url)
    assert driver.find_element(By.TAG_NAME,"body").is_displayed()

def test_send_message(driver,base_url):
    driver.get(base_url)
    inp=driver.find_element(By.ID,"userInput")
    inp.clear();inp.send_keys("hello world")
    driver.find_element(By.ID,"sendBtn").click()
    time.sleep(1)
    assert "hello" in driver.find_element(By.ID,"chatBox").text.lower()

def test_ltm_save_button_exists(driver,base_url):
    driver.get(base_url); assert driver.find_element(By.ID,"ltmSaveBtn").is_displayed()

def test_ltm_recall_button_exists(driver,base_url):
    driver.get(base_url); assert driver.find_element(By.ID,"ltmRecallBtn").is_displayed()

def test_ltm_save_api(base_url):
    r=requests.post(base_url+"/api/ltm/save",json={"session_id":"ts","content":"Test memory"})
    assert r.status_code==200
    assert "id" in r.json() or "status" in r.json()


def test_ltm_recall_api(base_url):
    r=requests.get(base_url+"/api/ltm/recall",params={"session_id":"ts"})
    assert r.status_code==200
    assert isinstance(r.json(),(list,dict))

def test_ltm_save_persists(base_url):
    sid="p001"
    requests.post(base_url+"/api/ltm/save",json={"session_id":sid,"content":"Persistent"})
    r=requests.get(base_url+"/api/ltm/recall",params={"session_id":sid})
    mems=r.json() if isinstance(r.json(),list) else [r.json()]
    assert any("Persistent" in str(m) for m in mems)

def test_ltm_recall_ui(driver,base_url):
    driver.get(base_url)
    driver.find_element(By.ID,"ltmRecallBtn").click()
    time.sleep(1)
    assert driver.find_element(By.ID,"ltmPanel").is_displayed()

def test_chat_history_stored(base_url):
    r=requests.post(base_url+"/api/chat/message",json={"session_id":"ht","role":"user","content":"hi"})
    assert r.status_code in (200,201)

def test_telemetry_endpoint_exists(base_url):
    r=requests.post(base_url+"/api/ltm/send-telemetry",json={"event":"test","session_id":"ts"})
    assert r.status_code in (200,202,204)


def test_telemetry_returns_otel_ids(base_url):
    r=requests.post(base_url+"/api/ltm/send-telemetry",json={"event":"otel_test","session_id":"oi"})
    d=r.json()
    assert "trace_id" in d and "span_id" in d
    assert len(d["trace_id"])==32 and len(d["span_id"])==16

def test_otel_collector_reachable():
    try:
        r=requests.get(OTEL_COLLECTOR_URL+"/",timeout=5)
        assert r.status_code in (200,404,405)
    except requests.exceptions.ConnectionError:
        pytest.skip("otel-collector not running")

def test_otel_collector_receives_span_on_ltm_save(base_url):
    r=requests.post(base_url+"/api/ltm/save",json={"session_id":"os","content":"OTel"})
    d=r.json()
    assert d.get("otel_sent")==1
    assert d.get("trace_id","")!=""

def test_otel_collector_receives_span_on_send_telemetry(base_url):
    r=requests.post(base_url+"/api/ltm/send-telemetry",json={"session_id":"ot","event":"ltm_save_btn_click","source":"test"})
    d=r.json()
    assert d["otel_sent"]==1 and d["trace_id"]!="" and d["db_row_id"]>0

def test_jaeger_reachable():
    try:
        r=requests.get(JAEGER_URL+"/api/services",timeout=5)
        assert r.status_code==200
    except requests.exceptions.ConnectionError:
        pytest.skip("Jaeger not running")


def test_db_ltm_table_exists(base_url):
    r=requests.get(base_url+"/api/db/tables")
    assert r.status_code==200 and "ltm_memories" in r.json()

def test_db_chat_history_table_exists(base_url):
    assert "chat_history" in requests.get(base_url+"/api/db/tables").json()

def test_db_telemetry_table_exists(base_url):
    assert "telemetry_events" in requests.get(base_url+"/api/db/tables").json()

def test_sql_ltm_memories_row_on_save(base_url):
    sid="sql-ltm"
    requests.post(base_url+"/api/ltm/save",json={"session_id":sid,"content":"SQL footprint"})
    rows=requests.get(base_url+"/api/db/query",params={"table":"ltm_memories","session_id":sid}).json()
    assert len(rows)>0 and rows[0]["content"]=="SQL footprint"

def test_sql_chat_history_row_on_message(base_url):
    sid="sql-chat"
    requests.post(base_url+"/api/chat/message",json={"session_id":sid,"role":"user","content":"SQL chat"})
    rows=requests.get(base_url+"/api/db/query",params={"table":"chat_history","session_id":sid}).json()
    assert len(rows)>0 and rows[0]["content"]=="SQL chat"

def test_sql_telemetry_events_row_on_send_telemetry(base_url):
    sid="sql-tel"
    requests.post(base_url+"/api/ltm/send-telemetry",json={"session_id":sid,"event":"ltm_save"})
    rows=requests.get(base_url+"/api/db/query",params={"table":"telemetry_events","session_id":sid}).json()
    assert len(rows)>0
    assert rows[0]["otel_sent"]==1 and rows[0]["trace_id"]!=""

def test_sql_all_tables_footprint_after_ltm_scenario(base_url):
    sid="sql-full"
    requests.post(base_url+"/api/ltm/save",json={"session_id":sid,"content":"Full"})
    requests.get(base_url+"/api/ltm/recall",params={"session_id":sid})
    requests.post(base_url+"/api/chat/message",json={"session_id":sid,"role":"user","content":"msg"})
    requests.post(base_url+"/api/ltm/send-telemetry",json={"session_id":sid,"event":"ltm_recall_btn_click"})
    time.sleep(0.5)
    for tbl in ("ltm_memories","chat_history","telemetry_events"):
        r=requests.get(base_url+"/api/db/query",params={"table":tbl,"session_id":sid})
        assert len(r.json())>0,f"{tbl} must have rows"


def test_sql_telemetry_otel_sent_flag_on_ltm_save(base_url):
    sid="otel-sent"
    requests.post(base_url+"/api/ltm/save",json={"session_id":sid,"content":"otel flag"})
    rows=requests.get(base_url+"/api/db/query",params={"table":"telemetry_events","session_id":sid}).json()
    assert len(rows)>0 and all(row["otel_sent"]==1 for row in rows)

def test_ui_dbfp_not_no_records_after_ltm_click(driver,base_url):
    driver.get(base_url)
    driver.find_element(By.ID,"ltmSaveBtn").click()
    time.sleep(2)
    text=driver.find_element(By.ID,"dbfp").text.strip()
    assert text!="No records.","#dbfp shows No records. after ltmSaveBtn - telemetry chain BROKEN. Check /api/ltm/send-telemetry otel_sent=1 otel-collector:4318 DB written"

def test_ui_dbfp_shows_records_after_recall_click(driver,base_url):
    driver.get(base_url)
    driver.find_element(By.ID,"ltmRecallBtn").click()
    time.sleep(2)
    text=driver.find_element(By.ID,"dbfp").text.strip()
    assert text!="No records.","#dbfp No records after ltmRecallBtn - chain broken"

def test_db_telemetry_endpoint_returns_list(base_url):
    requests.post(base_url+"/api/ltm/send-telemetry",json={"event":"dbfp_feed","session_id":"dbfp"})
    r=requests.get(base_url+"/api/db/telemetry")
    assert r.status_code==200
    data=r.json()
    assert isinstance(data,list) and len(data)>0
    for field in ("id","session_id","event_type","trace_id","otel_sent","created_at"):
        assert field in data[0],f"missing field {field}"

def test_otel_collector_api_call_on_ltm_save_btn(base_url):
    r=requests.post(base_url+"/api/ltm/send-telemetry",json={"session_id":"osb","event":"ltm_save_btn_click","source":"test"})
    d=r.json()
    assert d["otel_sent"]==1 and d["trace_id"]!="" and d["db_row_id"]>0

def test_otel_collector_api_call_on_ltm_recall_btn(base_url):
    r=requests.post(base_url+"/api/ltm/send-telemetry",json={"session_id":"orb","event":"ltm_recall_btn_click","source":"test"})
    d=r.json()
    assert d["otel_sent"]==1 and d["trace_id"]!=""

def test_ltm_save_span_in_jaeger(base_url):
    sid="jaeger-span"
    requests.post(base_url+"/api/ltm/save",json={"session_id":sid,"content":"Jaeger span test"})
    time.sleep(2)
    try:
        r=requests.get(JAEGER_URL+"/api/traces",params={"service":"ltm-chat-service","limit":5},timeout=5)
        assert r.status_code==200
        traces=r.json().get("data",[])
        assert len(traces)>0
    except requests.exceptions.ConnectionError:
        pytest.skip("Jaeger not available")


def test_drag_db_footprint_btn_triggers_api_call(driver,base_url):
    driver.get(base_url)
    driver.find_element(By.ID,"dragDbFpBtn").click()
    time.sleep(2)
    dbfp=driver.find_element(By.ID,"dbfp")
    text=dbfp.text.strip()
    assert text!="No records." and text!="Click Drag DB Footprint.","dragDbFpBtn click must call API and populate #dbfp - got: "+repr(text)

def test_drag_db_footprint_btn_sends_telemetry(base_url):
    sid="drag-fp-test"
    r=requests.post(base_url+"/api/ltm/send-telemetry",json={"session_id":sid,"event":"drag_db_footprint_click","source":"ui_button"})
    assert r.status_code==200
    d=r.json()
    assert d["otel_sent"]==1
    assert d["trace_id"]!=""
    rows=requests.get(base_url+"/api/db/query",params={"table":"telemetry_events","session_id":sid}).json()
    assert len(rows)>0
    assert any(r["event_type"]=="drag_db_footprint_click" for r in rows)


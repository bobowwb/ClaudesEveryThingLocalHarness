import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://localhost:5000"
OTEL_COLLECTOR_URL = "http://localhost:4318"
JAEGER_URL = "http://localhost:16686"

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def otel_url():
    return OTEL_COLLECTOR_URL

@pytest.fixture(scope="session")
def jaeger_url():
    return JAEGER_URL

@pytest.fixture(scope="session")
def driver():
    o = Options()
    o.add_argument("--headless")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    d = webdriver.Chrome(options=o)
    d.implicitly_wait(10)
    yield d
    d.quit()

@pytest.fixture
def api(base_url):
    class API:
        def post(self, path, **kwargs):
            return requests.post(base_url + path, **kwargs)
        def get(self, path, **kwargs):
            return requests.get(base_url + path, **kwargs)
    return API()


import os as _os
HDB_HOST=_os.environ.get("HDB_HOST","localhost")
HDB_PORT=int(_os.environ.get("HDB_PORT","30015"))
HDB_USER=_os.environ.get("HDB_USER","SYSTEM")
HDB_PASS=_os.environ.get("HDB_PASS","manager")
HDB_SCHEMA=_os.environ.get("HDB_SCHEMA","SYSTEM")

@pytest.fixture(scope="session")
def hdb_conn():
    try: import hdbcli.dbapi as hdb
    except ImportError: pytest.skip("hdbcli not installed: pip install hdbcli")
    try:
        c=hdb.connect(address=HDB_HOST,port=HDB_PORT,user=HDB_USER,password=HDB_PASS)
        yield c; c.close()
    except Exception as e: pytest.skip(f"Cannot connect to HANA {HDB_HOST}:{HDB_PORT} SYSTEM/manager: {e}")

@pytest.fixture(scope="session")
def hdb_cursor(hdb_conn): return hdb_conn.cursor()

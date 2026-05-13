"""test_ui.py - Selenium UI tests for LTM Chat UI"""
import pytest
import time
from selenium.webdriver.common.by import By

BASE_URL = "http://localhost:5000"

def test_page_loads(driver):
    driver.get(BASE_URL)
    assert driver.find_element(By.TAG_NAME, "body").is_displayed()

def test_chat_route_loads(driver):
    driver.get(BASE_URL + "/chat")
    assert driver.find_element(By.TAG_NAME, "body").is_displayed()

def test_ltm_save_btn_exists(driver):
    driver.get(BASE_URL)
    assert driver.find_element(By.ID, "ltmSaveBtn").is_displayed()

def test_ltm_recall_btn_exists(driver):
    driver.get(BASE_URL)
    assert driver.find_element(By.ID, "ltmRecallBtn").is_displayed()

def test_drag_db_fp_btn_exists(driver):
    driver.get(BASE_URL)
    assert driver.find_element(By.ID, "dragDbFpBtn").is_displayed()

def test_dbfp_div_exists(driver):
    driver.get(BASE_URL)
    el = driver.find_element(By.ID, "dbfp")
    assert el is not None

def test_send_message_appears_in_chat(driver):
    driver.get(BASE_URL)
    inp = driver.find_element(By.ID, "userInput")
    inp.clear(); inp.send_keys("hello world")
    driver.find_element(By.ID, "sendBtn").click()
    time.sleep(1)
    assert "hello" in driver.find_element(By.ID, "chatBox").text.lower()

def test_ltm_recall_panel_shows(driver):
    driver.get(BASE_URL)
    driver.find_element(By.ID, "ltmRecallBtn").click()
    time.sleep(1)
    panel = driver.find_element(By.ID, "ltmPanel")
    assert panel.is_displayed()

def test_dbfp_not_no_records_after_ltm_save(driver):
    driver.get(BASE_URL)
    driver.find_element(By.ID, "ltmSaveBtn").click()
    time.sleep(2)
    text = driver.find_element(By.ID, "dbfp").text.strip()
    assert text != "No records.", ("#dbfp shows No records. after ltmSaveBtn - telemetry chain BROKEN. "
        "Check: /api/ltm/send-telemetry, otel-collector:4318, DB write")

def test_dbfp_not_no_records_after_ltm_recall(driver):
    driver.get(BASE_URL)
    driver.find_element(By.ID, "ltmRecallBtn").click()
    time.sleep(2)
    text = driver.find_element(By.ID, "dbfp").text.strip()
    assert text != "No records.", "#dbfp No records after ltmRecallBtn - chain broken"

def test_drag_db_fp_btn_populates_dbfp(driver):
    driver.get(BASE_URL)
    driver.find_element(By.ID, "dragDbFpBtn").click()
    time.sleep(2)
    text = driver.find_element(By.ID, "dbfp").text.strip()
    assert text != "No records." and text != "Click Drag DB Footprint.", "dragDbFpBtn must populate #dbfp via API call, got: "+repr(text)

def test_status_bar_updates_on_action(driver):
    driver.get(BASE_URL)
    driver.find_element(By.ID, "ltmTelemetryBtn").click()
    time.sleep(1)
    status = driver.find_element(By.ID, "statusBar").text
    assert status != "Ready.", "statusBar must update after action"

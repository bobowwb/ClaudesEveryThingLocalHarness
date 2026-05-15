"""Selenium UI tests for Joule standalone webclient LTM scenarios.

Runs in a VISIBLE Chrome window by attaching to the already-running browser
via CDP remote debugging (the "browser opened by joule launch").

Prerequisites:
    Launch Chrome with remote debugging enabled:
        chrome.exe --remote-debugging-port=9222
    OR set CHROME_DEBUG_PORT env var to the port you used.

Run:
    pytest echo/tests/test_joule_launch.py -v -s
"""

import os
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

JOULE_URL = (
    "https://resources-joule-eu12-1rzwtmn9.eu12.sapdas.cloud.sap"
    "/webclient/standalone/epm_fpa_agent"
)
ALPHA_TRIGGER = "Run LTM Alpha forecast using pure oTel and appFnd telemetry"
BETA_TRIGGER  = "Run LTM Beta forecast using 4D memory enhanced agent"
RESPONSE_WAIT = 120  # seconds — A2A + SAP AI Core round-trip

# Attach to the Chrome that the user already launched (the "joule launch" browser).
CHROME_DEBUG_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))


@pytest.fixture(scope="module")
def joule_driver():
    """Attach to the already-running Chrome via CDP remote debugging.

    Start Chrome manually with:
        chrome.exe --remote-debugging-port=9222
    then run this test — it attaches to that window (SAP SSO session intact).
    Falls back to launching a fresh visible Chrome if no debugger is listening.
    """
    o = Options()
    try:
        o.debugger_address = f"localhost:{CHROME_DEBUG_PORT}"
        d = webdriver.Chrome(options=o)
        d.implicitly_wait(10)
    except Exception:
        # Fallback: fresh visible Chrome in a temp profile.
        o = Options()
        o.add_argument("--no-first-run")
        o.add_argument("--no-default-browser-check")
        # NOT headless — browser must be visible
        d = webdriver.Chrome(options=o)
        d.maximize_window()
        d.implicitly_wait(10)

    d.get(JOULE_URL)
    WebDriverWait(d, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(4)

    # Print current URL for diagnostics.
    current = d.current_url
    print(f"\n[joule_launch] Landed on: {current}")

    # Check for conversation starters — if none appear within 15 s the session
    # is not authenticated (SSO redirect or empty page).
    try:
        WebDriverWait(d, 15).until(EC.presence_of_element_located(
            (By.XPATH, "//button[contains(., 'LTM')] | //*[contains(text(), 'LTM Alpha')] | //*[contains(text(), 'LTM Beta')]")
        ))
    except Exception:
        try:
            d.quit()
        except Exception:
            pass
        pytest.skip(
            f"Joule conversation starters not visible on {current!r}. "
            "The browser is likely on the SSO login page. "
            "Start Chrome with --remote-debugging-port=9222 while already logged into Joule, "
            f"set CHROME_DEBUG_PORT={CHROME_DEBUG_PORT}, then re-run."
        )

    yield d
    try:
        d.quit()
    except Exception:
        pass


def _reset(driver) -> None:
    """Reload the Joule standalone page so conversation starters are visible."""
    driver.get(JOULE_URL)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)


def _click_starter(driver, trigger_text: str) -> None:
    """Click the conversation starter containing trigger_text."""
    wait = WebDriverWait(driver, 20)
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//button[contains(., '{trigger_text[:30]}')]")
        ))
    except Exception:
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, f"//*[contains(text(), '{trigger_text[:30]}')]")
        ))
    btn.click()


def _wait_response(driver) -> str:
    """Wait for loading to finish, return the last message element text."""
    time.sleep(2)
    try:
        WebDriverWait(driver, RESPONSE_WAIT).until_not(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class,'loading') or contains(@class,'spinner') or @aria-busy='true']")
            )
        )
    except Exception:
        pass
    time.sleep(2)
    msgs = driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'message') or contains(@class,'chat-item') or @role='article']"
    )
    if not msgs:
        return driver.find_element(By.TAG_NAME, "body").text
    return msgs[-1].text


# ── Tests ──────────────────────────────────────────────────────────────────────


def test_ltm_alpha_starter_returns_alpha_response(joule_driver):
    """LTM Alpha conversation starter must produce an Alpha scenario response."""
    _reset(joule_driver)
    _click_starter(joule_driver, "LTM Alpha")
    text = _wait_response(joule_driver)
    assert ("LTM Alpha" in text and "story" in text.lower()) or "scenario: LTM ALPHA" in text, (
        f"Expected Alpha scenario in response. Got:\n{text[:600]}"
    )


def test_ltm_beta_starter_returns_beta_response(joule_driver):
    """LTM Beta starter must route to the Beta scenario, not Alpha."""
    _reset(joule_driver)
    _click_starter(joule_driver, "LTM Beta")
    text = _wait_response(joule_driver)
    assert ("LTM Beta" in text and "story" in text.lower()) or "scenario: LTM BETA" in text, (
        f"Expected Beta scenario in response. Got:\n{text[:600]}"
    )
    assert "royalty cash flow" in text.lower() or "hedge" in text.lower(), (
        f"Expected Beta narrative in response. Got:\n{text[:600]}"
    )


def test_joule_da_found(joule_driver):
    """Webclient must NOT show 'Digital Assistant not found' after deploy."""
    _reset(joule_driver)
    time.sleep(3)
    body_text = joule_driver.find_element(By.TAG_NAME, "body").text
    assert "Digital Assistant not found" not in body_text, (
        "Joule webclient shows 'Digital Assistant not found'. "
        "The capability needs to be redeployed: bump version in "
        "capability.sapdas.yaml then run: joule deploy --compile da.sapdas.yaml"
    )


def test_ltm_alpha_response_has_text_and_card(joule_driver):
    """Joule returns at least two message items (prose text + card) for a business response."""
    _reset(joule_driver)
    _click_starter(joule_driver, "LTM Alpha")
    time.sleep(2)
    try:
        WebDriverWait(joule_driver, RESPONSE_WAIT).until_not(
            EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class,'loading') or contains(@class,'spinner')]")
            )
        )
    except Exception:
        pass
    time.sleep(2)
    bubbles = joule_driver.find_elements(
        By.XPATH,
        "//*[contains(@class,'message') or contains(@class,'chat-item') or contains(@class,'card') or @role='article']"
    )
    assert len(bubbles) >= 2, (
        f"Expected at least 2 message items (text + card) but found {len(bubbles)}."
    )

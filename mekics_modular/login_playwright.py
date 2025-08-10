# -*- coding: utf-8 -*-
import os
from typing import Dict
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "https://it.mek-ics.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"

def _to_requests_session(storage_state: dict) -> requests.Session:
    sess = requests.Session()
    for c in storage_state.get("cookies", []):
        if "it.mek-ics.com" in c.get("domain",""):
            sess.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path","/"))
    return sess

def login_and_get_session(user_id: str, user_pw: str, db_label: str = "MEK ICS") -> requests.Session:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="ko-KR", timezone_id="Asia/Seoul", user_agent=UA, viewport={"width": 1600, "height": 960})
        page = context.new_page()
        page.goto(BASE_URL + "/mekics", wait_until="domcontentloaded", timeout=60000)

        # fill id/pw (heuristics)
        for s in ['input[name="userId"]','input[name="loginId"]','input[name="username"]','input[id*="id"]','input[type="text"]']:
            if page.locator(s).count():
                page.locator(s).first.fill(user_id); break
        for s in ['input[type="password"]','input[name="password"]','input[name="loginPw"]']:
            if page.locator(s).count():
                page.locator(s).first.fill(user_pw); break

        # DB selection
        try:
            if page.locator("select").count():
                page.locator("select").first.select_option(label=db_label)
            else:
                try:
                    page.get_by_label(db_label).check()
                except Exception:
                    page.get_by_text(db_label, exact=True).click()
        except Exception:
            pass

        # login button
        clicked = False
        for name in ["로그인","Login","Sign in"]:
            try:
                page.get_by_role("button", name=name).click(timeout=2000); clicked=True; break
            except Exception:
                continue
        if not clicked and page.locator('input[type="submit"]').count():
            page.locator('input[type="submit"]').first.click()

        try:
            page.wait_for_load_state("networkidle", timeout=60000)
        except Exception:
            pass

        # preload sales page (optional)
        page.goto(BASE_URL + "/mekics/sales/ssa450skrv.do?authoUser=A", wait_until="domcontentloaded", timeout=60000)

        storage = context.storage_state()
        browser.close()
    return _to_requests_session(storage)

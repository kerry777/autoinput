# -*- coding: utf-8 -*-
"""
mekics_auto_all.py  (통합형)
- Playwright로 로그인(Headless) → requests로 그리드 JSON 수집/CSV → Excel 다운로드
- 계정/비밀번호는 인자 또는 환경변수(MEKICS_ID/MEKICS_PW) 사용
"""
import argparse, json, os, csv, time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

BASE_URL = "https://it.mek-ics.com"
SALES_PATH = "/mekics/sales/ssa450skrv.do?authoUser=A"
ROUTER = "/mekics/router.do"
EXCEL_DL = "/mekics/download/downloadExcel.do"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"

def to_requests_cookies(storage_state: dict) -> requests.Session:
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

        # 입력 추적(다단계 셀렉터)
        id_selectors = ['input[name="userId"]','input[name="loginId"]','input[name="username"]','input[id*="id"]','input[type="text"]']
        pw_selectors = ['input[type="password"]','input[name="password"]','input[name="loginPw"]']

        ok_id = False
        for s in id_selectors:
            if page.locator(s).count():
                page.locator(s).first.fill(user_id)
                ok_id = True
                break
        ok_pw = False
        for s in pw_selectors:
            if page.locator(s).count():
                page.locator(s).first.fill(user_pw)
                ok_pw = True
                break

        # DB 선택 시도
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

        # 로그인 버튼 클릭
        clicked = False
        for name in ["로그인","Login","Sign in"]:
            try:
                page.get_by_role("button", name=name).click(timeout=2000)
                clicked = True
                break
            except Exception:
                continue
        if not clicked and page.locator('input[type="submit"]').count():
            page.locator('input[type="submit"]').first.click()

        # 로드 대기
        try:
            page.wait_for_load_state("networkidle", timeout=60000)
        except PwTimeout:
            pass

        # sales 페이지 프리로드 (Referer 세팅 위해)
        page.goto(BASE_URL + SALES_PATH, wait_until="domcontentloaded", timeout=60000)

        # 스토리지에서 쿠키 추출
        storage = context.storage_state()
        browser.close()

    sess = to_requests_cookies(storage)
    return sess

def ensure_out(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

def grid_payload(date_fr: str, date_to: str, limit: int, page: int) -> dict:
    start = (page - 1) * limit
    data = {
        "DIV_CODE":"01","SALE_CUSTOM_CODE":"","SALE_CUSTOM_NAME":"","PROJECT_NO":"","PROJECT_NAME":"",
        "SALE_PRSN":"","ITEM_CODE":"","ITEM_NAME":"","undefined":["undefined","undefined"],
        "SALE_FR_DATE":date_fr,"SALE_TO_DATE":date_to,"TAX_TYPE":"","NATION_INOUT":"1","ITEM_ACCOUNT":"",
        "SALE_YN":"A","ENCLUDE_YN":"Y","TXT_CREATE_LOC":"","BILL_TYPE":"","AGENT_TYPE":"",
        "ITEM_GROUP_NAME":"","ITEM_GROUP_CODE":"","INOUT_TYPE_DETAIL":"","AREA_TYPE":"",
        "MANAGE_CUSTOM":"","MANAGE_CUSTOM_NAME":"","ORDER_TYPE":"","ITEM_LEVEL1":"","ITEM_LEVEL2":"",
        "ITEM_LEVEL3":"","BILL_FR_NO":"","BILL_TO_NO":"","PUB_FR_NUM":"","PUB_TO_NUM":"",
        "ORDER_FR_NUM":"","ORDER_TO_NUM":"","SALE_FR_Q":"","SALE_TO_Q":"","INOUT_FR_DATE":"",
        "INOUT_TO_DATE":"","REMARK":"","WH_CODE":"","WH_CELL_CODE":"","INCLUDE_LOT_YN":"Y",
        "SITE_CODE":"MICS","page":page,"start":start,"limit":limit
    }
    return {"action":"ssa450skrvService","method":"selectList1","data":[data],"type":"rpc","tid":1}

def fetch_grid(sess: requests.Session, out_dir: Path, date_fr: str, date_to: str, limit: int) -> Path:
    router_url = BASE_URL + ROUTER
    referer = BASE_URL + SALES_PATH
    headers = {
        "Accept":"*/*","Content-Type":"application/json","Origin":BASE_URL,"Referer":referer,
        "User-Agent":UA,"X-Requested-With":"XMLHttpRequest"
    }
    page = 1
    total_rows: List[dict] = []
    while True:
        payload = grid_payload(date_fr, date_to, limit, page)
        r = sess.post(router_url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        obj = r.json()
        # ExtDirect 단일 응답 or 리스트 대응
        result = None
        if isinstance(obj, dict) and "result" in obj:
            result = obj["result"]
        elif isinstance(obj, list) and obj and isinstance(obj[0], dict) and "result" in obj[0]:
            result = obj[0]["result"]
        rows = None
        if isinstance(result, dict):
            for k in ["list","data","rows","items","result"]:
                v = result.get(k)
                if isinstance(v, list):
                    rows = v; break
        if not rows:
            break
        total_rows.extend(rows)
        if len(rows) < limit:
            break
        page += 1
        if page > 200:  # safety
            break
    # save json
    raw_path = out_dir / "sales_grid_raw.json"
    raw_path.write_text(json.dumps(total_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    # save csv
    if total_rows:
        cols = set()
        for r in total_rows:
            cols.update(r.keys())
        cols = list(cols)
        csv_path = out_dir / "sales_grid.csv"
        import csv
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in total_rows:
                w.writerow({k: r.get(k, "") for k in cols})
        return csv_path
    return raw_path

def download_excel(sess: requests.Session, out_dir: Path, date_fr: str, date_to: str, template_xml_path: Path) -> Path:
    # Build form payload
    with open(template_xml_path, "r", encoding="utf-8") as f:
        xml_data = f.read()
    # 'data' JSON matches grid filters
    data_json = {
        "DIV_CODE":"01","SALE_CUSTOM_CODE":"","SALE_CUSTOM_NAME":"","PROJECT_NO":"","PROJECT_NAME":"",
        "SALE_PRSN":"","ITEM_CODE":"","ITEM_NAME":"","undefined":["undefined","undefined"],
        "SALE_FR_DATE":date_fr,"SALE_TO_DATE":date_to,"TAX_TYPE":"","NATION_INOUT":"1","ITEM_ACCOUNT":"",
        "SALE_YN":"A","ENCLUDE_YN":"Y","TXT_CREATE_LOC":"","BILL_TYPE":"","AGENT_TYPE":"",
        "ITEM_GROUP_NAME":"","ITEM_GROUP_CODE":"","INOUT_TYPE_DETAIL":"","AREA_TYPE":"",
        "MANAGE_CUSTOM":"","MANAGE_CUSTOM_NAME":"","ORDER_TYPE":"","ITEM_LEVEL1":"","ITEM_LEVEL2":"",
        "ITEM_LEVEL3":"","BILL_FR_NO":"","BILL_TO_NO":"","PUB_FR_NUM":"","PUB_TO_NUM":"",
        "ORDER_FR_NUM":"","ORDER_TO_NUM":"","SALE_FR_Q":"","SALE_TO_Q":"","INOUT_FR_DATE":"",
        "INOUT_TO_DATE":"","REMARK":"","WH_CODE":"","WH_CELL_CODE":"","INCLUDE_LOT_YN":"Y",
        "SITE_CODE":"MICS"
    }
    form = {
        "data": json.dumps(data_json, ensure_ascii=False),
        "xmlData": xml_data,
        "configId": "",
        "pgmId": "ssa450skrv",
        "extAction": "ssa450skrvService",
        "extMethod": "selectList1",
        "fileName": f"매출현황 조회-{datetime.now().strftime('%Y-%m-%d %H%M')}",
        "onlyData": "false",
        "isExportData": "false",
        "exportData": ""
    }
    headers = {
        "Content-Type":"application/x-www-form-urlencoded",
        "Origin": BASE_URL,
        "Referer": BASE_URL + SALES_PATH,
        "User-Agent": UA
    }
    url = BASE_URL + EXCEL_DL
    with sess.post(url, headers=headers, data=form, stream=True, timeout=120) as r:
        r.raise_for_status()
        # filename
        fname = "sales.xlsx"
        cd = r.headers.get("Content-Disposition","")
        if "filename" in cd:
            import re
            m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.I)
            if m:
                fname = m.group(1).strip().strip('"')
        out_path = out_dir / fname
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1024*256):
                if chunk:
                    f.write(chunk)
    return out_path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default=os.getenv("MEKICS_ID") or "", help="로그인 ID")
    ap.add_argument("--pw", default=os.getenv("MEKICS_PW") or "", help="로그인 PW")
    ap.add_argument("--db", default="MEK ICS", help="DB 라벨")
    ap.add_argument("--sale-fr", default=datetime.now().strftime("%Y%m01"), help="YYYYMMDD")
    ap.add_argument("--sale-to", default=datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    ap.add_argument("--limit", type=int, default=100, help="페이지당 행 수")
    ap.add_argument("--out", default="out_integrated", help="출력 디렉토리")
    args = ap.parse_args()

    if not args.id or not args.pw:
        raise SystemExit("ID/PW가 필요합니다. (--id/--pw 또는 MEKICS_ID/MEKICS_PW 환경변수)")

    out_dir = Path(args.out)
    ensure_out(out_dir)

    # 1) 로그인 → session
    sess = login_and_get_session(args.id, args.pw, args.db)

    # 2) 매출현황 페이지 GET (선행, referer 효과)
    sales_page = BASE_URL + SALES_PATH
    page_headers = {"User-Agent": UA, "Referer": BASE_URL + "/mekics/main_mics.do", "Accept":"text/html,application/xhtml+xml"}
    rp = sess.get(sales_page, headers=page_headers, timeout=60)
    (out_dir / "sales_page.html").write_bytes(rp.content)

    # 3) 그리드 수집 → CSV
    csv_path = fetch_grid(sess, out_dir, args.sale_fr, args.sale_to, args.limit)

    # 4) 엑셀 다운로드
    excel_path = download_excel(sess, out_dir, args.sale_fr, args.sale_to, Path(__file__).parent / "templates" / "ssa450skrv_excel_template.xml")

    print(f"[OK] CSV: {csv_path}")
    print(f"[OK] XLSX: {excel_path}")

if __name__ == "__main__":
    main()

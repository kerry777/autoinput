# -*- coding: utf-8 -*-
import json, csv
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests

BASE_URL = "https://it.mek-ics.com"
ROUTER = "/mekics/router.do"
SALES_PATH = "/mekics/sales/ssa450skrv.do?authoUser=A"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"

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

def fetch_sales_grid(session: requests.Session, out_dir: Path, date_fr: str, date_to: str, limit: int = 100) -> Path:
    router_url = BASE_URL + ROUTER
    referer = BASE_URL + SALES_PATH
    headers = {"Accept":"*/*","Content-Type":"application/json","Origin":BASE_URL,"Referer":referer,"User-Agent":UA,"X-Requested-With":"XMLHttpRequest"}

    page = 1
    total_rows: List[dict] = []
    while True:
        pld = grid_payload(date_fr, date_to, limit, page)
        r = session.post(router_url, headers=headers, json=pld, timeout=60)
        r.raise_for_status()
        obj = r.json()
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
        if page > 200: break

    raw_path = out_dir / "sales_grid_raw.json"
    raw_path.write_text(json.dumps(total_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    if total_rows:
        cols = set()
        for r in total_rows: cols.update(r.keys())
        cols = list(cols)
        csv_path = out_dir / "sales_grid.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in total_rows:
                w.writerow({k: r.get(k, "") for k in cols})
        return csv_path
    return raw_path

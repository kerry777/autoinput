# -*- coding: utf-8 -*-
import json
from pathlib import Path
import requests
from datetime import datetime

BASE_URL = "https://it.mek-ics.com"
EXCEL_DL = "/mekics/download/downloadExcel.do"
SALES_PATH = "/mekics/sales/ssa450skrv.do?authoUser=A"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"

def export_excel(session: requests.Session, out_dir: Path, date_fr: str, date_to: str, template_xml_path: Path) -> Path:
    with open(template_xml_path, "r", encoding="utf-8") as f:
        xml_data = f.read()
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
    headers = {"Content-Type":"application/x-www-form-urlencoded","Origin":BASE_URL,"Referer":BASE_URL+SALES_PATH,"User-Agent":UA}
    url = BASE_URL + EXCEL_DL
    with session.post(url, headers=headers, data=form, stream=True, timeout=120) as r:
        r.raise_for_status()
        fname = "sales.xlsx"
        cd = r.headers.get("Content-Disposition","")
        if "filename" in cd:
            import re
            m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.I)
            if m: fname = m.group(1).strip().strip('"')
        out_path = out_dir / fname
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(1024*256):
                if chunk: f.write(chunk)
    return out_path

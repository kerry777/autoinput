# -*- coding: utf-8 -*-
import argparse, os
from pathlib import Path
from datetime import datetime

from login_playwright import login_and_get_session
from sales_grid import fetch_sales_grid
from sales_excel_export import export_excel

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default=os.getenv("MEKICS_ID") or "", help="로그인 ID")
    ap.add_argument("--pw", default=os.getenv("MEKICS_PW") or "", help="로그인 PW")
    ap.add_argument("--db", default="MEK ICS", help="DB 라벨")
    ap.add_argument("--sale-fr", default=datetime.now().strftime("%Y%m01"), help="YYYYMMDD")
    ap.add_argument("--sale-to", default=datetime.now().strftime("%Y%m%d"), help="YYYYMMDD")
    ap.add_argument("--limit", type=int, default=100, help="페이지당 행 수")
    ap.add_argument("--out", default="out_modular", help="출력 디렉토리")
    args = ap.parse_args()

    if not args.id or not args.pw:
        raise SystemExit("ID/PW가 필요합니다. (--id/--pw 또는 MEKICS_ID/MEKICS_PW 환경변수)")

    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 로그인
    session = login_and_get_session(args.id, args.pw, args.db)

    # 2) 그리드 수집
    csv_path = fetch_sales_grid(session, out_dir, args.sale_fr, args.sale_to, args.limit)
    print("[OK] GRID CSV:", csv_path)

    # 3) 엑셀 다운로드
    xlsx_path = export_excel(session, out_dir, args.sale_fr, args.sale_to, Path(__file__).parent / "templates" / "ssa450skrv_excel_template.xml")
    print("[OK] XLSX:", xlsx_path)

if __name__ == "__main__":
    main()

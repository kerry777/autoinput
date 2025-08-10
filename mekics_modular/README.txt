Mek-ICS 자동화 (모듈형)
=======================
파일 구성:
- login_playwright.py         : 로그인(Headless) → requests.Session 반환
- sales_grid.py               : ssa450skrvService.selectList1 호출, CSV 저장
- sales_excel_export.py       : downloadExcel.do 호출, XLSX 저장
- auto1.py                    : 위 3개를 순서대로 실행(오케스트레이션)
- templates/ssa450skrv_excel_template.xml : 엑셀 템플릿

설치
  pip install -r requirements.txt
  playwright install

실행 예 (Windows)
  set MEKICS_ID=20210101
  set MEKICS_PW=1565718
  python auto1.py --sale-fr 20250804 --sale-to 20250811 --out out_modular

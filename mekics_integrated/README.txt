Mek-ICS 자동화 (통합형)
========================
기능: 자동 로그인(Headless) → 매출현황 Grid JSON 수집(CSV 저장) → 엑셀 파일 다운로드

1) 설치
   pip install -r requirements.txt
   playwright install

2) 실행 예시(Windows)
   set MEKICS_ID=20210101
   set MEKICS_PW=1565718
   python mekics_auto_all.py --sale-fr 20250804 --sale-to 20250811 --out out_integrated

3) 옵션
   --id/--pw 또는 MEKICS_ID/MEKICS_PW 환경변수
   --db "MEK ICS" (기본)
   --sale-fr/--sale-to  (YYYYMMDD)
   --limit 25
   --out   출력 디렉토리 (기본: out_integrated)

결과
- out_integrated/
  - sales_grid.csv            (그리드 JSON CSV 변환 결과)
  - sales_grid_raw.json       (그리드 원본 JSON)
  - sales_page.html           (매출현황 페이지 원본)
  - sales.xlsx                (엑셀 다운로드 결과)

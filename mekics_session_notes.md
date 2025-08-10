# Mek-ICS 자동화 세션 정리 (Ext JS / ExtDirect 기반)
**작성 시각:** 2025-08-11 04:49:50 UTC+09:00

본 문서는 대화 전반에서 주고받은 내용과 제공된 코드/엔드포인트/사용법을 **가능한 누락 없이** 정리한 것입니다.  
(보안 주의: 아래에는 테스트 중 공유된 계정/쿠키/요청 본문 등 민감정보가 포함될 수 있습니다. 외부 저장소 공유 금지!)

---


## 1) 목표
- 자동 로그인 (세션 쿠키 확보)
- 영업 → **매출현황** 진입/조회
- 데이터 수집(JSON → CSV) 및 **엑셀 다운로드**
- 하드코딩된 쿠키 제거(자동 로그인 사용), **유연한 실행 옵션** 제공

---

## 2) 최종 산출물 (다운로드)
- **통합 패키지** (로그인 → 그리드 수집 → 엑셀 다운로드까지 한 번에)
  - [mekics_automation_integrated.zip](sandbox:/mnt/data/mekics_automation_integrated.zip)
- **모듈 패키지** (login / grid / excel / orchestrator 분리)
  - [mekics_automation_modular.zip](sandbox:/mnt/data/mekics_automation_modular.zip)

### 세부 스크립트 (개별 파일)
- [mekics_router_extdirect.py](sandbox:/mnt/data/mekics_router_extdirect.py) — ExtDirect 배치 호출/CSV 변환 유틸
- [mekics_auto_sales_status.py](sandbox:/mnt/data/mekics_auto_sales_status.py) — 매출현황 초기 진입 및 기본 호출 자동화
- [mekics_sales_selectList1_batch.py](sandbox:/mnt/data/mekics_sales_selectList1_batch.py) — **ssa450skrvService.selectList1** 페이지네이션 수집 → CSV
- [mekics_excel_from_curl.py](sandbox:/mnt/data/mekics_excel_from_curl.py) — Copy as cURL 기반 엑셀/CSV 다운로드 재현기

> 위 네 개는 점진 구축 단계에서 제공되었으며, 통합/모듈 패키지에 최신 로직이 반영되어 있습니다.

---

## 3) 통합형 vs 모듈형 구조
### 통합형 (`mekics_auto_all.py`)
- Headless **Playwright**로 로그인 → 쿠키를 **requests.Session**에 이관
- **그리드 수집(JSON→CSV)**, 이어서 **엑셀 다운로드**
- 실행 예:
  ```bat
  pip install -r requirements.txt
  playwright install

  set MEKICS_ID=20210101
  set MEKICS_PW=1565718

  python mekics_auto_all.py --sale-fr 20250804 --sale-to 20250811 --out out_integrated
  ```

### 모듈형
- `login_playwright.py` — 로그인 후 `requests.Session` 반환
- `sales_grid.py` — `ssa450skrvService.selectList1` 호출, 전체 페이지 수집, CSV 저장
- `sales_excel_export.py` — `downloadExcel.do` 호출, XLSX 저장
- `auto1.py` — 위 3개를 순서대로 실행
- 실행 예:
  ```bat
  pip install -r requirements.txt
  playwright install

  set MEKICS_ID=20210101
  set MEKICS_PW=1565718

  python auto1.py --sale-fr 20250804 --sale-to 20250811 --out out_modular
  ```

**공통 사항**
- 하드코딩 쿠키 **없음**: 매 실행시 로그인으로 세션 재확보
- **Referer/Origin/User-Agent** 등 서버 기대값에 맞춰 헤더 설정
- CSV/HTML/XLSX 결과물은 `out_*` 디렉터리에 저장

---

## 4) 확인/분석한 핵심 엔드포인트
- ExtDirect 라우터: `POST /mekics/router.do`
  - `mainMenuService.getMenuList` (`moduleId=14` 등)
  - `extJsStateProviderService.selectStateInfo`
  - `extJsStateProviderService.updateStateDefault`
  - **`ssa450skrvService.selectList1`** ← 매출현황 본 데이터 API
- 콤보: `GET /mekics/com/getComboList.do`
- 엑셀 다운로드: `POST /mekics/download/downloadExcel.do`  
  - `application/x-www-form-urlencoded`  
  - 주요 파라미터: `data`(JSON, 그리드 필터), `xmlData`(엑셀 템플릿 XML), `pgmId`, `extAction`, `extMethod`, `fileName`, …

---

## 5) 대화에서 주고받은 주요 내용 (요약)
- Ext JS로 개발된 사이트 탐색 → 정부/공공 포털 위주 제안
- **기상청(KMA)** 예제 분석: API/로그 수집과 ExtJS 패턴 관찰
- **Mek-ICS 포털 분석** 요청 → 로그인 후 **영업/매출현황**으로 이동/수집
- 실제 **cURL 캡처**(router.do, combo, state provider, selectList1, downloadExcel) 공유
- 하드코딩 쿠키는 테스트용이고, **자동 로그인**으로 대체 필요함을 합의
- “**모듈형 vs 통합형**으로 제공” 요청 → 두 버전 **압축 제공**
- DevTools에서 **엑셀 요청 찾는 방법**과 **Copy as cURL** 절차 설명

---

## 6) 사용 방법 (공통 체크리스트)
1. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
2. **자격 증명 주입**
   - Windows:
     ```bat
     set MEKICS_ID=20210101
     set MEKICS_PW=1565718
     ```
   - macOS/Linux:
     ```bash
     export MEKICS_ID=20210101
     export MEKICS_PW=1565718
     ```
3. **실행**
   - 통합형: `python mekics_auto_all.py --sale-fr YYYYMMDD --sale-to YYYYMMDD`
   - 모듈형: `python auto1.py --sale-fr YYYYMMDD --sale-to YYYYMMDD`
4. **결과**
   - CSV: `sales_grid.csv`
   - JSON: `sales_grid_raw.json`
   - HTML 스냅샷: `sales_page.html`
   - 엑셀: `*.xlsx` (서버가 내려주는 파일명 유지)

> 날짜/필터/행수/출력경로는 CLI 옵션으로 조정 가능합니다.

---

## 7) 설계 포인트 & 유연성
- **Playwright 로그인 → requests로 전환**: 브라우저 자동화는 로그인까지, 이후는 경량 HTTP로 빠르게 수집
- **쿠키 자동 승계**: `storage_state()`에서 사이트 쿠키를 읽어 `requests.Session`에 주입
- **페이징 자동 처리**: `limit`/`page`/`start`로 모든 행 수집, `total` 또는 페이지 마지막 감지 시 종료
- **엑셀 템플릿 XML**: 화면에서 쓰던 `xmlData`를 템플릿으로 포함(필드/헤더는 필요 시 조정 가능)
- **에러/만료 대응**: 만료 쿠키는 다음 실행 시 새 로그인으로 해결

---

## 8) 다음 단계(옵션)
- 정렬/추가 필터(거래처/품목/담당자 등) CLI 옵션화
- 스케줄 실행(Windows 스케줄러/cron)
- 네트워크 불가 시 재시도/백오프
- 엑셀 다중 시트/다국어 파일명 처리

---

## 9) 사용자 제공 cURL (원문 보관)
> 아래 원문은 가능한 그대로 보관했습니다. 민감정보(쿠키 등) 취급 주의.

### (A) getMenuList (moduleId=14)
```bash
curl ^"https://it.mek-ics.com/mekics/router.do^" ^
  -H ^"Accept: */*^" ^
  -H ^"Accept-Language: en-US,en;q=0.9,ko;q=0.8^" ^
  -H ^"Connection: keep-alive^" ^
  -H ^"Content-Type: application/json^" ^
  -b ^"JSESSIONID=06BCB0FE36DCD8A40E9948C48EB04DBC; _fwb=50Kcq0XR7x7NO1Ef8oyIsE.1751477515647; _ga=GA1.1.1115446322.1751477518; _ga_MD30HW73ZS=GS2.1.s1751477517^$o1^$g1^$t1751477533^$j44^$l0^$h0; ext-main.panelNavigation=o^%^3Aweight^%^3Dn^%^253A-10^" ^
  -H ^"Origin: https://it.mek-ics.com^" ^
  -H ^"Referer: https://it.mek-ics.com/mekics/main_mics.do^" ^
  -H ^"Sec-Fetch-Dest: empty^" ^
  -H ^"Sec-Fetch-Mode: cors^" ^
  -H ^"Sec-Fetch-Site: same-origin^" ^
  -H ^"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36^" ^
  -H ^"X-Requested-With: XMLHttpRequest^" ^
  -H ^"sec-ch-ua: ^\^"Not;A=Brand^\^";v=^\^"99^\^", ^\^"Google Chrome^\^";v=^\^"139^\^", ^\^"Chromium^\^";v=^\^"139^\^"^" ^
  -H ^"sec-ch-ua-mobile: ?0^" ^
  -H ^"sec-ch-ua-platform: ^\^"Windows^\^"^" ^
  --data-raw ^"^{^\^"action^\^":^\^"mainMenuService^\^",^\^"method^\^":^\^"getMenuList^\^",^\^"data^\^":^[^{^\^"moduleId^\^":^\^"14^\^",^\^"node^\^":^\^"root^\^"^}],^\^"type^\^":^\^"rpc^\^",^\^"tid^\^":5^}^"
```

### (B) com/getComboList.do
```bash
curl ^"https://it.mek-ics.com/mekics/com/getComboList.do?comboType=BSA421^&comboCode=ssa450skrv__ssa450skrvGrid1^&includeMainCode=false^&_dc=1754852376444^&page=1^&start=0^&limit=25^" ^
  -H ^"Accept: */*^" ^
  -H ^"Accept-Language: en-US,en;q=0.9,ko;q=0.8^" ^
  -H ^"Connection: keep-alive^" ^
  -b ^"JSESSIONID=06BCB0FE36DCD8A40E9948C48EB04DBC; _fwb=50Kcq0XR7x7NO1Ef8oyIsE.1751477515647; _ga=GA1.1.1115446322.1751477518; _ga_MD30HW73ZS=GS2.1.s1751477517^$o1^$g1^$t1751477533^$j44^$l0^$h0; ext-main.panelNavigation=o^%^3Aweight^%^3Dn^%^253A-10^" ^
  -H ^"Referer: https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A^" ^
  -H ^"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36^" ^
  -H ^"X-Requested-With: XMLHttpRequest^"
```

### (C) extJsStateProviderService (selectStateInfo / updateStateDefault)
```bash
curl ^"https://it.mek-ics.com/mekics/router.do^" ^
  -H ^"Content-Type: application/json^" ^
  -H ^"Referer: https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A^" ^
  --data-raw ^"^{^\^"action^\^":^\^"extJsStateProviderService^\^",^\^"method^\^":^\^"selectStateInfo^\^",^\^"data^\^":^[^{^\^"PGM_ID^\^":^\^"ssa450skrv^\^",^\^"SHT_ID^\^":^\^"ssa450skrvGrid1^\^",^\^"SHT_SEQ^\^":^\^"1^\^"^}],^\^"type^\^":^\^"rpc^\^",^\^"tid^\^":1^}^"

curl ^"https://it.mek-ics.com/mekics/router.do^" ^
  -H ^"Content-Type: application/json^" ^
  -H ^"Referer: https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A^" ^
  --data-raw ^"^{^\^"action^\^":^\^"extJsStateProviderService^\^",^\^"method^\^":^\^"updateStateDefault^\^",^\^"data^\^":^[^{^\^"PGM_ID^\^":^\^"ssa450skrv^\^",^\^"SHT_ID^\^":^\^"ssa450skrvGrid1^\^",^\^"SHT_SEQ^\^":^\^"1^\^"^}],^\^"type^\^":^\^"rpc^\^",^\^"tid^\^":2^}^"
```

### (D) ssa450skrvService.selectList1 (데이터 본문)
```bash
curl ^"https://it.mek-ics.com/mekics/router.do^" ^
  -H ^"Content-Type: application/json^" ^
  -H ^"Referer: https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A^" ^
  --data-raw ^"^{^\^"action^\^":^\^"ssa450skrvService^\^",^\^"method^\^":^\^"selectList1^\^",^\^"data^\^":^[{^\^"DIV_CODE^\^":^\^"01^\^",^\^"SALE_CUSTOM_CODE^\^":^\^"^\^",^\^"SALE_CUSTOM_NAME^\^":^\^"^\^",^\^"PROJECT_NO^\^":^\^"^\^",^\^"PROJECT_NAME^\^":^\^"^\^",^\^"SALE_PRSN^\^":^\^"^\^",^\^"ITEM_CODE^\^":^\^"^\^",^\^"ITEM_NAME^\^":^\^"^\^",^\^"undefined^\^":[^\^"undefined^\^",^\^"undefined^\^"],^\^"SALE_FR_DATE^\^":^\^"20250804^\^",^\^"SALE_TO_DATE^\^":^\^"20250811^\^", ... ,^\^"SITE_CODE^\^":^\^"MICS^\^",^\^"page^\^":1,^\^"start^\^":0,^\^"limit^\^":25}],^\^"type^\^":^\^"rpc^\^",^\^"tid^\^":4^}^"
```

### (E) 엑셀 다운로드 downloadExcel.do (원문)
```bash
curl ^"https://it.mek-ics.com/mekics/download/downloadExcel.do^" ^
  -H ^"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7^" ^
  -H ^"Content-Type: application/x-www-form-urlencoded^" ^
  -H ^"Referer: https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A^" ^
  --data-raw ^"data=...&xmlData=...&pgmId=ssa450skrv&extAction=ssa450skrvService&extMethod=selectList1&fileName=매출현황 조회-2025-08-11 0414&onlyData=false&isExportData=false&exportData=^"
```

---

## 11) 메모
- 시간대: Asia/Seoul, 작성일 기준 2025-08-11
- 테스트 계정(예시): `20210101 / 1565718` (대화 중 공유됨 — 외부 유출 금지)

# 웹 스크래핑 트러블슈팅 가이드
작성일: 2025-08-09

## 사례: 장기요양보험 시설 데이터 다운로드 자동화

### 문제 상황
- **사이트**: https://longtermcare.or.kr
- **목표**: 전국 17개 시도별 요양기관 엑셀 데이터 자동 다운로드
- **초기 문제**: 팝업이 열리지 않음, 다운로드 버튼을 찾을 수 없음

### 문제 해결 과정

#### 1단계: 팝업이 열리지 않는 문제

**증상**:
```python
# doSearch() 함수 실행했지만 팝업이 안 열림
await page.evaluate('doSearch()')
```

**원인 분석**:
1. doSearch()는 사이트 전체 검색용 함수였음 (요양기관 검색이 아님)
2. 실제 검색 버튼은 `#btn_search_pop`
3. 위치 정보 권한 팝업이 추가로 떠서 메인 팝업 감지 실패

**해결 방법**:
```python
# 1. 위치 권한 거부 설정
context = await browser.new_context(
    permissions=[],  # 모든 권한 거부
    geolocation=None
)

# 2. 올바른 검색 버튼 클릭
search_btn = await page.query_selector('#btn_search_pop')
await search_btn.click()

# 3. context.pages로 팝업 감지 (wait_for_event 대신)
while waited < max_wait:
    await page.wait_for_timeout(1000)
    if len(context.pages) > pages_before:
        popup = context.pages[-1]
        break
```

#### 2단계: 타임아웃 문제

**증상**:
- 팝업이 열리는데 10초 이상 걸림
- "Timeout 10000ms exceeded" 에러

**원인**:
- 데이터가 많아서 팝업 로딩이 오래 걸림
- 기본 타임아웃 10초로는 부족

**해결 방법**:
```python
# 충분한 대기 시간 설정
max_wait = 20  # 20초까지 대기
while waited < max_wait:
    await page.wait_for_timeout(1000)
    waited += 1
    if len(context.pages) > pages_before:
        popup = context.pages[-1]
        print(f"Popup opened after {waited} seconds")
        break
```

#### 3단계: 다운로드 실패 문제

**증상**:
- 다운로드 버튼은 찾았지만 다운로드가 안 됨
- "Timeout exceeded while waiting for event download" 에러

**원인**:
- 잘못된 다운로드 이벤트 처리 방식

**해결 방법**:
```python
# async with expect_download 사용 (작동 확인!)
async with popup.expect_download(timeout=30000) as download_info:
    await download_btn.click()

download = await download_info.value
print(f"Download started: {download.suggested_filename}")

# 파일 저장
await download.save_as(filepath)
```

### 최종 작동 코드 핵심 부분

```python
class FinalRegionDownloader:
    async def download_region(self, page, context, region_code, region_name):
        # 1. 페이지 로드
        await page.goto(self.base_url, wait_until='networkidle')
        
        # 2. 지역 선택
        await page.select_option('select[name="siDoCd"]', value=region_code)
        
        # 3. 검색 버튼 클릭
        search_btn = await page.query_selector('#btn_search_pop')
        await search_btn.click()
        
        # 4. 팝업 대기 (최대 20초)
        pages_before = len(context.pages)
        waited = 0
        while waited < 20:
            await page.wait_for_timeout(1000)
            waited += 1
            if len(context.pages) > pages_before:
                popup = context.pages[-1]
                break
        
        # 5. 다운로드
        download_btn = await popup.query_selector('#btn_map_excel')
        async with popup.expect_download(timeout=30000) as download_info:
            await download_btn.click()
        
        download = await download_info.value
        await download.save_as(filepath)
```

### 두 가지 실행 모드

#### 1. 브라우저 화면 표시 모드 (Visual Mode)

**사용 시기**:
- 처음 테스트할 때
- 디버깅이 필요할 때
- 진행 과정을 확인하고 싶을 때
- 교육/시연 목적

**코드**:
```python
browser = await p.chromium.launch(
    headless=False,  # 브라우저 화면 표시
    slow_mo=1000     # 천천히 실행 (과정 확인 가능)
)
```

**실행 방법**:
```bash
python scripts/download_regions_with_browser.py
```

**장점**:
- 진행 상황 실시간 확인
- 문제 발생 지점 즉시 파악
- 교육/학습에 유용

**단점**:
- 실행 속도 느림
- 시스템 리소스 많이 사용

#### 2. Headless 모드 (Background Mode)

**사용 시기**:
- 실무에서 빠른 실행이 필요할 때
- 서버에서 자동화 실행
- 대량 데이터 수집
- 백그라운드 작업

**코드**:
```python
browser = await p.chromium.launch(
    headless=True,   # UI 렌더링 안 함
    slow_mo=200      # 빠른 실행
)
```

**실행 방법**:
```bash
python scripts/download_regions_headless.py
```

**장점**:
- 30-50% 빠른 실행 속도
- 서버 리소스 절약
- 백그라운드 실행 가능

**단점**:
- 진행 과정 확인 불가
- 디버깅 어려움

### 핵심 교훈

1. **정확한 요소 선택자 찾기**
   - 개발자 도구로 확인
   - 사용자 피드백 중요 ("name이 검색버튼이다")

2. **충분한 대기 시간**
   - 데이터가 많은 사이트는 로딩이 오래 걸림
   - 타임아웃을 충분히 설정 (30초 이상)

3. **팝업 처리 방법**
   - `wait_for_event('popup')` 보다 `context.pages` 모니터링이 더 안정적
   - 위치 권한 등 추가 팝업 처리 필요

4. **다운로드 처리**
   - `async with expect_download()` 패턴 사용
   - await 키워드 빠뜨리지 않기

### 재사용 가능한 패턴

```python
# 팝업 대기 패턴
async def wait_for_popup(context, max_wait=20):
    pages_before = len(context.pages)
    for i in range(max_wait):
        await asyncio.sleep(1)
        if len(context.pages) > pages_before:
            return context.pages[-1]
    return None

# 다운로드 패턴
async def download_file(page, button_selector, save_path):
    button = await page.query_selector(button_selector)
    async with page.expect_download() as download_info:
        await button.click()
    download = await download_info.value
    await download.save_as(save_path)
    return save_path
```

### 체크리스트

웹 스크래핑 프로젝트 시작 시 확인 사항:

- [ ] 팝업/새 창 열림 여부
- [ ] 위치 정보 등 권한 팝업 여부
- [ ] 로딩 시간 (타임아웃 설정)
- [ ] 정확한 버튼/요소 선택자
- [ ] 다운로드 메커니즘
- [ ] 서버 부하 고려 (대기 시간)
- [ ] Headless 모드 가능 여부

### 관련 파일

- 최종 작동 스크립트: `scripts/download_all_regions_final_working.py`
- 테스트 스크립트: `scripts/test_download_mechanism.py`
- 팝업 감지 테스트: `scripts/test_with_cdp.py`
# 웹 자동화 패턴 라이브러리

기존 경험을 바탕으로 한 재사용 가능한 자동화 패턴과 솔루션 모음

## 🎯 패턴 분류 체계

### A. 인증 우회 패턴
### B. 데이터 추출 패턴  
### C. 네비게이션 패턴
### D. 에러 처리 패턴
### E. 최적화 패턴

---

## 🔐 A. 인증 우회 패턴

### A1. 쿠키 재사용 패턴 (★★★★★)
**적용 사례**: Bizmeka 2FA 우회
```python
# 1단계: 수동 로그인 + 쿠키 저장
cookies = await browser.cookies()
with open('cookies.json', 'w') as f:
    json.dump(cookies, f)

# 2단계: 쿠키 재사용
await context.add_cookies(cookies)
await page.goto(target_url)  # 2FA 없이 접속!
```
**장점**: 99% 성공률, 가장 안정적
**단점**: 최초 수동 로그인 필요
**적용 대상**: 2FA 있는 모든 사이트

### A2. CDP 연결 패턴 (★★☆☆☆)
```python
browser = await playwright.chromium.connect_over_cdp("http://localhost:9222")
```
**장점**: 기존 브라우저 세션 활용
**단점**: 불안정, 제한적 효과
**적용 대상**: 특수한 경우에만

### A3. Stealth 우회 패턴 (★☆☆☆☆)
```python
await stealth_async(page)
```
**장점**: 일부 기본적인 탐지 우회
**단점**: 고급 시스템에는 무력, 오히려 의심받을 수 있음
**적용 대상**: 단순한 봇 탐지만 있는 사이트

---

## 📊 B. 데이터 추출 패턴

### B1. 테이블 기반 추출 패턴 (★★★★☆)
**적용 사례**: 전통적인 게시판
```python
rows = await page.query_selector_all('table tbody tr')
for row in rows:
    cells = await row.query_selector_all('td')
    data = {
        'title': await cells[1].inner_text(),
        'author': await cells[2].inner_text(),
        'date': await cells[3].inner_text()
    }
```

### B2. 리스트 아이템 추출 패턴 (★★★★★)
**적용 사례**: Bizmeka 메일 리스트
```python
items = await page.query_selector_all('li.m_data')
for item in items:
    data = {
        'sender': await item.get_attribute('data-fromname'),
        'subject': await item.query_selector('p.m_subject'),
        'date': await item.query_selector('span.m_date')
    }
```

### B3. 카드 레이아웃 추출 패턴 (★★★★☆)
**적용 사례**: 모던 웹사이트
```python
cards = await page.query_selector_all('.card, .item, .post')
for card in cards:
    title = await card.query_selector('h2, h3, .title')
    content = await card.query_selector('.content, .description')
```

### B4. JavaScript 렌더링 대응 패턴 (★★★☆☆)
```python
# 페이지 로드 대기
await page.wait_for_selector('.data-container', timeout=10000)
await page.wait_for_load_state('networkidle')

# JavaScript 실행 대기
await page.evaluate('() => new Promise(resolve => setTimeout(resolve, 2000))')
```

---

## 🧭 C. 네비게이션 패턴

### C1. 동적 ID/선택자 패턴 (★★★★★)
**적용 사례**: Bizmeka `mnu_Inbox_kilmoon`
```python
# 접두사 기반 선택자
element = await page.query_selector('[id^="mnu_Inbox_"]')

# 패턴 매칭
login_id = extract_login_id()  # 사용자별 추출
selector = f'#mnu_Inbox_{login_id}'
```

### C2. 팝업/모달 처리 패턴 (★★★★★)
**적용 사례**: Bizmeka 메일 용량 초과 팝업
```python
# 범용 팝업 닫기
async def close_all_popups(page):
    # ESC 키 (가장 효과적)
    for _ in range(3):
        await page.keyboard.press('Escape')
        await page.wait_for_timeout(500)
    
    # X 버튼 클릭
    close_selectors = [
        'button[aria-label="Close"]',
        '.ui-dialog-titlebar-close', 
        'button:has-text("확인")'
    ]
    for selector in close_selectors:
        try:
            btn = await page.query_selector(selector)
            if btn: await btn.click()
        except: pass
```

### C3. 페이지네이션 패턴 (★★★★☆)
```python
for page_num in range(1, max_pages + 1):
    # 데이터 추출
    extract_data(page)
    
    # 다음 페이지 이동
    next_selectors = [
        f'a:has-text("{page_num + 1}")',
        'a[title="다음"]',
        '.pagination .next'
    ]
    for selector in next_selectors:
        if await click_if_exists(page, selector):
            break
```

### C4. 프레임/iframe 처리 패턴 (★★★☆☆)
```python
# 모든 프레임 순회
for frame in page.frames:
    if 'target_keyword' in frame.url:
        data = await frame.query_selector_all('.data-item')
        # 프레임 내부에서 작업
```

---

## ⚠️ D. 에러 처리 패턴

### D1. 재시도 패턴 (★★★★★)
```python
async def retry_operation(operation, max_attempts=3, delay=1):
    for attempt in range(max_attempts):
        try:
            return await operation()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
            await asyncio.sleep(delay * (attempt + 1))
```

### D2. 폴백 선택자 패턴 (★★★★☆)
```python
async def find_element_fallback(page, selectors):
    for selector in selectors:
        try:
            element = await page.query_selector(selector)
            if element: return element
        except: continue
    return None

# 사용 예
selectors = ['#primary-btn', '.submit-button', 'input[type="submit"]']
button = await find_element_fallback(page, selectors)
```

### D3. 타임아웃 처리 패턴 (★★★★☆)
```python
try:
    element = await page.wait_for_selector('.target', timeout=5000)
except TimeoutError:
    # 대안 처리
    element = await page.query_selector('.alternative')
```

---

## ⚡ E. 최적화 패턴

### E1. 병렬 처리 패턴 (★★★★☆)
```python
async def process_multiple_pages(urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(process_single_page(url))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### E2. 캐싱 패턴 (★★★★☆)
```python
# 결과 캐싱
cache = {}
def cached_extraction(key, extraction_func):
    if key not in cache:
        cache[key] = extraction_func()
    return cache[key]
```

### E3. 리소스 최적화 패턴 (★★★☆☆)
```python
# 불필요한 리소스 차단
await context.route("**/*.{png,jpg,jpeg,gif,css}", lambda route: route.abort())

# 헤드리스 모드
browser = await p.chromium.launch(headless=True)
```

---

## 🛠️ 패턴 적용 가이드

### 새로운 사이트 분석 시 체크리스트

1. **인증 방식 확인**
   - [ ] 일반 로그인
   - [ ] 2FA 여부
   - [ ] 봇 탐지 시스템
   - [ ] 세션 유지 기간

2. **페이지 구조 분석**
   - [ ] 테이블 vs 리스트 vs 카드
   - [ ] 정적 vs 동적 렌더링
   - [ ] 프레임 구조
   - [ ] 페이지네이션 방식

3. **적용 패턴 선택**
   - [ ] 인증: A1 쿠키 재사용 우선
   - [ ] 추출: 구조에 맞는 B 패턴
   - [ ] 네비: 팝업 처리는 C2 필수
   - [ ] 에러: D1 재시도 항상 적용

4. **최적화 고려**
   - [ ] 병렬 처리 가능한지
   - [ ] 캐싱 적용점
   - [ ] 리소스 절약 방법

### 패턴 조합 예시

**일반적인 게시판 사이트**:
```
A1 (쿠키 재사용) + B1 (테이블 추출) + C2 (팝업 처리) + C3 (페이지네이션) + D1 (재시도)
```

**모던 웹앱**:
```
A1 (쿠키 재사용) + B3 (카드 추출) + B4 (JS 렌더링) + C2 (팝업 처리) + D2 (폴백 선택자)
```

**메일 시스템**:
```
A1 (쿠키 재사용) + B2 (리스트 추출) + C1 (동적 선택자) + C2 (팝업 처리) + C3 (페이지네이션)
```

---

## 📚 패턴 진화 기록

### v1.0 - 기본 패턴 (2025-08-10)
- Bizmeka 경험 기반 핵심 패턴 정립
- 쿠키 재사용 패턴 확립
- 팝업 처리 표준화

### v1.1 - 예상 (미래)
- 장기요양보험 사이트 패턴 추가
- 공공기관 사이트 특화 패턴
- HWP 파일 처리 패턴

### v1.2 - 예상 (미래)
- AI 기반 패턴 매칭
- 자동 패턴 선택 시스템
- 성능 최적화 패턴

---

**이 라이브러리의 핵심 가치**:
> "한 번 해결한 문제는 다시 해결하지 않는다"

매번 새로 시작하는 것이 아니라, 기존 패턴을 조합해서 빠르게 새로운 사이트를 공략할 수 있게 됩니다. 이것이 진정한 **기술 자산 축적**입니다! 🚀
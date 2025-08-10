# 로그인 자동화 노하우 문서 (Login Automation Know-How)

> 실제 사이트 테스트를 통해 축적된 로그인 자동화 경험과 해결 방법

## 📚 목차
1. [개요](#개요)
2. [웹 애플리케이션 유형별 접근법](#웹-애플리케이션-유형별-접근법)
3. [탐지 및 분석 방법론](#탐지-및-분석-방법론)
4. [실제 사례 분석](#실제-사례-분석)
5. [문제 해결 전략](#문제-해결-전략)
6. [자동화 코드 패턴](#자동화-코드-패턴)
7. [교훈 및 베스트 프랙티스](#교훈-및-베스트-프랙티스)

---

## 개요

### 핵심 인사이트
> "현실은 이렇거든...이렇게 로그인 방법이 간단치 않아" - 실제 프로젝트 경험

실제 웹사이트의 로그인 자동화는 교과서적인 예제와 매우 다릅니다. 각 사이트마다 고유한 구조, 보안 메커니즘, 프레임워크를 사용하며, 이를 모두 처리할 수 있는 유연한 접근법이 필요합니다.

### 주요 도전 과제
- **다양한 렌더링 방식**: HTML forms, SPA, Canvas 기반 앱
- **동적 콘텐츠**: AJAX 로딩, 지연 렌더링
- **보안 메커니즘**: CAPTCHA, 공인인증서, OTP
- **프레임워크 특성**: React, Vue, Angular, Flutter 등

---

## 웹 애플리케이션 유형별 접근법

### 1. 전통적 HTML Form
**특징**:
- `<form>` 태그와 `<input>` 필드 사용
- 서버 사이드 렌더링
- 표준 HTML 셀렉터로 접근 가능

**탐지 방법**:
```python
# HTML form 존재 확인
forms = await page.query_selector_all('form')
inputs = await page.query_selector_all('input')
print(f"Forms: {len(forms)}, Inputs: {len(inputs)}")
```

**자동화 전략**:
```python
# 표준 셀렉터 사용
await page.fill('input[name="username"]', username)
await page.fill('input[type="password"]', password)
await page.click('button[type="submit"]')
```

### 2. SPA (Single Page Application)
**특징**:
- React, Vue, Angular 등 사용
- 동적 DOM 조작
- Virtual DOM 사용 가능

**탐지 방법**:
```python
# React 앱 감지
react_root = await page.query_selector('#root, #app, [data-reactroot]')
vue_app = await page.query_selector('#app, [data-app]')

# Framework 특정 속성 확인
page_source = await page.content()
is_react = 'react' in page_source.lower() or '__react' in page_source
is_vue = '__vue__' in page_source or 'vue' in page_source.lower()
```

**자동화 전략**:
```python
# 동적 콘텐츠 대기
await page.wait_for_selector('input[type="text"]', state='visible')
await page.wait_for_load_state('networkidle')

# React/Vue 컴포넌트 대기
await page.wait_for_timeout(2000)  # 렌더링 시간 확보
```

### 3. Canvas 기반 애플리케이션 (Flutter Web)
**특징**:
- 전체 UI가 Canvas에 렌더링
- HTML 요소 없음
- 좌표 기반 상호작용 필요

**탐지 방법**:
```python
# Flutter 특정 요소 확인
flutter_elements = [
    'flt-glass-pane',
    'flt-scene-host', 
    'flt-scene',
    'flutter-view'
]

for selector in flutter_elements:
    element = await page.query_selector(selector)
    if element:
        print(f"Flutter app detected: {selector}")
        return "flutter"

# Canvas 전용 렌더링 확인
canvas = await page.query_selector('canvas')
inputs = await page.query_selector_all('input')
if canvas and len(inputs) == 0:
    print("Canvas-only rendering detected")
    return "canvas"
```

**자동화 전략**:
```python
# 좌표 기반 접근
viewport = page.viewport_size
center_x = viewport['width'] // 2
center_y = viewport['height'] // 2

# 예상 위치 클릭
username_y = center_y - 50
password_y = center_y + 20

await page.mouse.click(center_x, username_y)
await page.keyboard.type(username)
await page.keyboard.press('Tab')
await page.keyboard.type(password)
await page.keyboard.press('Enter')
```

### 4. iframe 내장 로그인
**특징**:
- 로그인 폼이 iframe 안에 존재
- Cross-origin 제약 가능

**탐지 방법**:
```python
frames = page.frames
for frame in frames:
    if frame != page.main_frame:
        inputs = await frame.query_selector_all('input')
        if len(inputs) > 0:
            print(f"Login form in iframe: {frame.url}")
```

**자동화 전략**:
```python
# iframe 내부 접근
login_frame = page.frame(url='**/login**')
if login_frame:
    await login_frame.fill('input[name="username"]', username)
    await login_frame.fill('input[type="password"]', password)
```

---

## 탐지 및 분석 방법론

### 단계별 분석 프로세스

#### 1단계: 초기 정찰
```python
async def reconnaissance(page):
    """사이트 구조 초기 분석"""
    
    results = {
        'type': 'unknown',
        'frameworks': [],
        'login_elements': {},
        'security_features': []
    }
    
    # 기본 HTML 구조 확인
    inputs = await page.query_selector_all('input')
    forms = await page.query_selector_all('form')
    buttons = await page.query_selector_all('button, input[type="submit"]')
    
    print(f"Basic elements - Inputs: {len(inputs)}, Forms: {len(forms)}, Buttons: {len(buttons)}")
    
    # 프레임워크 감지
    page_source = await page.content()
    if 'flutter' in page_source.lower():
        results['frameworks'].append('flutter')
    if 'react' in page_source.lower():
        results['frameworks'].append('react')
    if 'angular' in page_source.lower():
        results['frameworks'].append('angular')
    
    return results
```

#### 2단계: 심층 분석
```python
async def deep_analysis(page):
    """JavaScript 실행을 통한 심층 분석"""
    
    # Shadow DOM 포함 모든 input 찾기
    all_inputs = await page.evaluate('''() => {
        const inputs = [];
        const searchShadowDOM = (root) => {
            root.querySelectorAll('*').forEach(el => {
                if (el.shadowRoot) {
                    searchShadowDOM(el.shadowRoot);
                }
            });
            root.querySelectorAll('input').forEach(input => {
                inputs.push({
                    type: input.type,
                    name: input.name,
                    id: input.id,
                    visible: input.offsetParent !== null,
                    rect: input.getBoundingClientRect()
                });
            });
        };
        searchShadowDOM(document);
        return inputs;
    }''')
    
    return all_inputs
```

#### 3단계: 상호작용 테스트
```python
async def test_interaction(page):
    """실제 상호작용 가능성 테스트"""
    
    # 클릭 가능 영역 매핑
    clickable_areas = await page.evaluate('''() => {
        const elements = document.querySelectorAll('input, button, a');
        return Array.from(elements).map(el => ({
            tag: el.tagName,
            type: el.type,
            rect: el.getBoundingClientRect(),
            visible: el.offsetParent !== null
        }));
    }''')
    
    return clickable_areas
```

---

## 실제 사례 분석

### 사례 1: MSM 시스템 (http://it.mek-ics.com/msm)

**초기 가정**: Flutter Canvas 앱
**실제 발견**: 표준 HTML form (스크린샷 분석 후)

**교훈**:
1. 초기 분석이 잘못될 수 있음
2. 여러 방법으로 검증 필요
3. 스크린샷과 실제 DOM 구조 비교 중요

**해결 과정**:
```python
# 1차 시도: Canvas 기반 접근 (실패)
await page.mouse.click(center_x, center_y - 50)

# 2차 시도: 심층 DOM 분석
inputs = await page.query_selector_all('input')
# 발견: 실제로 2개의 input 필드 존재

# 3차 시도: 표준 셀렉터 (성공)
await page.fill('input#id', 'mdmtest')
await page.fill('input[type="password"]', '0001')
```

### 사례 2: 공인인증서 로그인

**특징**:
- ActiveX 또는 브라우저 확장 필요
- 로컬 인증서 파일 접근

**해결 전략**:
```python
# 인증서 선택 대화상자 처리
page.on('dialog', lambda dialog: handle_cert_dialog(dialog))

# 브라우저 확장 사전 설치
context = await browser.new_context(
    extensions=['path/to/cert_extension']
)
```

---

## 문제 해결 전략

### 일반적인 문제와 해결법

#### 1. "요소를 찾을 수 없음" 오류
**원인**:
- 동적 로딩
- iframe 내부
- Shadow DOM
- 잘못된 셀렉터

**해결**:
```python
# 다양한 대기 전략
await page.wait_for_selector('input', state='visible')
await page.wait_for_load_state('networkidle')
await page.wait_for_timeout(3000)

# 다중 셀렉터 시도
selectors = [
    'input[name="username"]',
    'input[type="text"]',
    'input#username',
    '.username-input'
]

for selector in selectors:
    try:
        elem = await page.query_selector(selector)
        if elem and await elem.is_visible():
            return selector
    except:
        continue
```

#### 2. CAPTCHA 처리
**전략**:
- 수동 입력 요청
- 2Captcha 같은 서비스 활용
- 세션 쿠키 재사용

```python
# 세션 유지 전략
if captcha_detected:
    print("[MANUAL] Please solve CAPTCHA...")
    await page.wait_for_timeout(30000)  # 30초 대기
    
    # 쿠키 저장
    cookies = await context.cookies()
    save_cookies(cookies)
```

#### 3. 동적 콘텐츠 대기
```python
# 다층적 대기 전략
async def wait_for_login_form(page):
    strategies = [
        lambda: page.wait_for_selector('form', timeout=5000),
        lambda: page.wait_for_load_state('domcontentloaded'),
        lambda: page.wait_for_function('document.readyState === "complete"'),
        lambda: page.wait_for_timeout(3000)
    ]
    
    for strategy in strategies:
        try:
            await strategy()
            return True
        except:
            continue
    
    return False
```

---

## 자동화 코드 패턴

### 범용 로그인 클래스
```python
class UniversalLoginAutomator:
    """다양한 사이트에 적응 가능한 로그인 자동화"""
    
    def __init__(self):
        self.strategies = {
            'html_form': self.handle_html_form,
            'spa': self.handle_spa,
            'canvas': self.handle_canvas,
            'iframe': self.handle_iframe
        }
    
    async def detect_type(self, page):
        """사이트 유형 자동 감지"""
        # 구현...
        pass
    
    async def login(self, page, username, password):
        """적응형 로그인 실행"""
        site_type = await self.detect_type(page)
        strategy = self.strategies.get(site_type, self.handle_unknown)
        return await strategy(page, username, password)
    
    async def handle_html_form(self, page, username, password):
        """표준 HTML form 처리"""
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        await page.press('input[type="password"]', 'Enter')
    
    async def handle_canvas(self, page, username, password):
        """Canvas 기반 앱 처리"""
        # 좌표 기반 로직
        pass
```

### 재시도 로직
```python
async def login_with_retry(page, username, password, max_attempts=3):
    """실패 시 재시도하는 로그인"""
    
    for attempt in range(max_attempts):
        try:
            print(f"[ATTEMPT {attempt + 1}] Trying login...")
            
            # 로그인 시도
            await perform_login(page, username, password)
            
            # 성공 확인
            if await check_login_success(page):
                print("[SUCCESS] Login successful")
                return True
            
            # 실패 시 페이지 새로고침
            await page.reload()
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"[ERROR] Attempt {attempt + 1} failed: {str(e)}")
            
            if attempt < max_attempts - 1:
                await page.reload()
                await page.wait_for_timeout(3000)
    
    return False
```

---

## 교훈 및 베스트 프랙티스

### 핵심 교훈

1. **가정하지 말고 검증하라**
   - 초기 분석이 틀릴 수 있음
   - 여러 방법으로 교차 검증
   - 스크린샷과 DOM 분석 병행

2. **점진적 접근**
   - Level 1: 수동 → Level 2: 반자동 → Level 3: 완전 자동
   - 각 단계에서 얻은 정보를 다음 단계에 활용

3. **유연한 전략**
   - 하나의 방법에 의존하지 않기
   - 여러 셀렉터와 접근법 준비
   - Fallback 메커니즘 구현

4. **문서화의 중요성**
   - 모든 시행착오 기록
   - 성공/실패 패턴 분석
   - 재사용 가능한 코드 패턴 구축

### 베스트 프랙티스

#### 개발 단계
1. **정찰 우선**: 자동화 전 철저한 분석
2. **증분 개발**: 작은 단위로 테스트하며 진행
3. **로깅 충실**: 모든 단계 상세 로깅
4. **스크린샷 활용**: 각 단계별 시각적 증거 수집

#### 운영 단계
1. **세션 관리**: 쿠키 저장 및 재사용
2. **에러 처리**: Graceful degradation
3. **모니터링**: 성공률 추적
4. **업데이트 대응**: 사이트 변경 감지 메커니즘

#### 보안 고려사항
1. **자격증명 보호**: 환경변수 또는 암호화 저장
2. **Rate limiting**: 과도한 요청 방지
3. **User-Agent 설정**: 실제 브라우저처럼 보이기
4. **프록시 활용**: IP 차단 대응

### 체크리스트

#### 새 사이트 자동화 시작 전
- [ ] 사이트 구조 분석 완료
- [ ] 프레임워크/기술 스택 파악
- [ ] 보안 메커니즘 확인
- [ ] 법적 제약사항 검토
- [ ] 테스트 계정 준비

#### 구현 중
- [ ] 다양한 셀렉터 전략 시도
- [ ] 동적 콘텐츠 대기 구현
- [ ] 에러 처리 및 재시도 로직
- [ ] 상세 로깅 구현
- [ ] 스크린샷 캡처

#### 구현 후
- [ ] 성공률 측정
- [ ] 성능 최적화
- [ ] 문서화 완료
- [ ] 유지보수 계획 수립
- [ ] 모니터링 설정

---

## 다음 단계

1. **자동 유형 감지 시스템 구축**
   - ML 기반 사이트 분류
   - 패턴 데이터베이스 구축

2. **Self-healing 셀렉터**
   - 변경 감지 및 자동 수정
   - 대체 셀렉터 자동 탐색

3. **통합 테스트 프레임워크**
   - 다양한 사이트 유형 테스트
   - 회귀 테스트 자동화

---

*이 문서는 실제 프로젝트 경험을 바탕으로 지속적으로 업데이트됩니다.*

**최종 업데이트**: 2025-08-09
**작성자**: AutoInput 개발팀
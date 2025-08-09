#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
고급 웹 스크래핑 기법 학습
실제 사이트에 적용 가능한 다양한 패턴
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
import re

class AdvancedScrapingTechniques:
    """고급 스크래핑 기법 모음"""
    
    def __init__(self):
        self.techniques_learned = []
        
    async def technique_1_iframe_navigation(self, page):
        """기법 1: iframe 내부 탐색"""
        print("\n[TECHNIQUE 1] iframe Navigation")
        print("-"*40)
        
        code_example = """
# iframe 처리 패턴
frames = page.frames
for frame in frames:
    if 'login' in frame.url:
        # iframe 내부에서 작업
        await frame.fill('input[name="username"]', 'user')
        await frame.fill('input[name="password"]', 'pass')
        await frame.click('button[type="submit"]')
        """
        
        print("Pattern:", code_example)
        
        # 실제 테스트
        await page.goto("https://web-scraping.dev")
        
        frames = page.frames
        print(f"Found {len(frames)} frames")
        
        for i, frame in enumerate(frames):
            print(f"  Frame {i}: {frame.url}")
            
            # iframe 내부 요소 접근
            if frame != page.main_frame:
                try:
                    inputs = await frame.query_selector_all('input')
                    print(f"    - {len(inputs)} inputs in frame")
                except:
                    print(f"    - Cannot access frame content")
        
        self.techniques_learned.append("iframe_navigation")
    
    async def technique_2_shadow_dom(self, page):
        """기법 2: Shadow DOM 처리"""
        print("\n[TECHNIQUE 2] Shadow DOM Handling")
        print("-"*40)
        
        code_example = """
# Shadow DOM 탐색
await page.evaluate('''() => {
    const searchShadowDOM = (root) => {
        const elements = [];
        root.querySelectorAll('*').forEach(el => {
            if (el.shadowRoot) {
                // Shadow root 발견
                searchShadowDOM(el.shadowRoot);
            }
        });
        return elements;
    };
    return searchShadowDOM(document);
}''')
        """
        
        print("Pattern:", code_example)
        
        # Shadow DOM 요소 찾기
        shadow_elements = await page.evaluate('''() => {
            const elements = [];
            const searchShadowDOM = (root) => {
                root.querySelectorAll('*').forEach(el => {
                    if (el.shadowRoot) {
                        elements.push({
                            tag: el.tagName,
                            hasShadow: true
                        });
                        searchShadowDOM(el.shadowRoot);
                    }
                });
            };
            searchShadowDOM(document);
            return elements;
        }''')
        
        if shadow_elements:
            print(f"Found {len(shadow_elements)} shadow DOM elements")
        else:
            print("No shadow DOM elements found")
        
        self.techniques_learned.append("shadow_dom")
    
    async def technique_3_infinite_scroll(self, page):
        """기법 3: 무한 스크롤 처리"""
        print("\n[TECHNIQUE 3] Infinite Scroll")
        print("-"*40)
        
        code_example = """
# 무한 스크롤 패턴
previous_height = 0
while True:
    # 현재 높이 측정
    current_height = await page.evaluate('document.body.scrollHeight')
    
    if current_height == previous_height:
        break  # 더 이상 로드되지 않음
    
    # 스크롤 다운
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await page.wait_for_timeout(2000)  # 로딩 대기
    
    previous_height = current_height
        """
        
        print("Pattern:", code_example)
        
        # 실제 구현
        await page.goto("https://web-scraping.dev/products")
        
        items_before = len(await page.query_selector_all('.product-item'))
        
        # 스크롤 시뮬레이션
        for i in range(3):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)
        
        items_after = len(await page.query_selector_all('.product-item'))
        
        print(f"Items before scroll: {items_before}")
        print(f"Items after scroll: {items_after}")
        
        self.techniques_learned.append("infinite_scroll")
    
    async def technique_4_wait_strategies(self, page):
        """기법 4: 다양한 대기 전략"""
        print("\n[TECHNIQUE 4] Wait Strategies")
        print("-"*40)
        
        strategies = {
            "wait_for_selector": """
# 특정 요소 대기
await page.wait_for_selector('.dynamic-content', state='visible')
            """,
            
            "wait_for_function": """
# JavaScript 조건 대기
await page.wait_for_function('document.querySelectorAll(".item").length > 10')
            """,
            
            "wait_for_load_state": """
# 네트워크 상태 대기
await page.wait_for_load_state('networkidle')  # 네트워크 요청 완료
await page.wait_for_load_state('domcontentloaded')  # DOM 로드
            """,
            
            "wait_for_response": """
# 특정 API 응답 대기
async with page.expect_response('**/api/data') as response_info:
    await page.click('#load-data')
response = await response_info.value
            """
        }
        
        for name, code in strategies.items():
            print(f"\n{name}:")
            print(code)
        
        # 실제 테스트
        await page.goto("https://web-scraping.dev")
        
        # 다양한 대기 방법 시연
        try:
            # 1. Selector 대기
            await page.wait_for_selector('body', timeout=1000)
            print("[OK] Selector wait completed")
            
            # 2. Function 대기
            await page.wait_for_function('document.readyState === "complete"', timeout=1000)
            print("[OK] Function wait completed")
            
            # 3. Load state 대기
            await page.wait_for_load_state('domcontentloaded')
            print("[OK] Load state wait completed")
            
        except Exception as e:
            print(f"[INFO] Wait example: {e}")
        
        self.techniques_learned.append("wait_strategies")
    
    async def technique_5_network_interception(self, page):
        """기법 5: 네트워크 요청 가로채기"""
        print("\n[TECHNIQUE 5] Network Interception")
        print("-"*40)
        
        code_example = """
# 네트워크 요청 가로채기
def handle_route(route):
    # 요청 수정
    headers = route.request.headers
    headers['Custom-Header'] = 'value'
    route.continue_(headers=headers)

# 또는 응답 수정
def modify_response(route):
    route.fulfill(
        status=200,
        body='{"modified": true}'
    )

page.route('**/api/**', handle_route)
        """
        
        print("Pattern:", code_example)
        
        # 네트워크 모니터링
        requests_intercepted = []
        
        def log_request(request):
            requests_intercepted.append({
                'url': request.url,
                'method': request.method
            })
        
        page.on('request', log_request)
        
        await page.goto("https://web-scraping.dev")
        
        print(f"Intercepted {len(requests_intercepted)} requests")
        
        # 주요 요청 출력
        for req in requests_intercepted[:5]:
            print(f"  {req['method']}: {req['url'][:50]}...")
        
        self.techniques_learned.append("network_interception")
    
    async def technique_6_cookie_management(self, page):
        """기법 6: 쿠키 관리"""
        print("\n[TECHNIQUE 6] Cookie Management")
        print("-"*40)
        
        code_example = """
# 쿠키 저장
cookies = await context.cookies()
with open('cookies.json', 'w') as f:
    json.dump(cookies, f)

# 쿠키 복원
with open('cookies.json', 'r') as f:
    cookies = json.load(f)
await context.add_cookies(cookies)
        """
        
        print("Pattern:", code_example)
        
        # 쿠키 작업
        await page.goto("https://web-scraping.dev")
        
        # 쿠키 추가
        await page.context.add_cookies([
            {
                'name': 'test_cookie',
                'value': 'test_value',
                'domain': '.web-scraping.dev',
                'path': '/'
            }
        ])
        
        # 쿠키 확인
        cookies = await page.context.cookies()
        print(f"Total cookies: {len(cookies)}")
        
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value'][:20]}...")
        
        self.techniques_learned.append("cookie_management")
    
    async def technique_7_javascript_execution(self, page):
        """기법 7: JavaScript 실행"""
        print("\n[TECHNIQUE 7] JavaScript Execution")
        print("-"*40)
        
        patterns = {
            "element_manipulation": """
# DOM 조작
await page.evaluate('''() => {
    document.querySelector('#hidden').style.display = 'block';
    document.querySelector('button').click();
}''')
            """,
            
            "data_extraction": """
# 데이터 추출
data = await page.evaluate('''() => {
    return Array.from(document.querySelectorAll('.item')).map(el => ({
        title: el.querySelector('.title')?.textContent,
        price: el.querySelector('.price')?.textContent
    }));
}''')
            """,
            
            "scroll_to_element": """
# 요소로 스크롤
await page.evaluate('''(selector) => {
    document.querySelector(selector).scrollIntoView();
}''', '#target-element')
            """
        }
        
        for name, code in patterns.items():
            print(f"\n{name}:")
            print(code)
        
        # 실제 실행
        await page.goto("https://web-scraping.dev")
        
        # JavaScript로 페이지 정보 추출
        page_info = await page.evaluate('''() => {
            return {
                title: document.title,
                url: window.location.href,
                links: document.querySelectorAll('a').length,
                images: document.querySelectorAll('img').length
            };
        }''')
        
        print("\nPage info extracted via JS:")
        for key, value in page_info.items():
            print(f"  {key}: {value}")
        
        self.techniques_learned.append("javascript_execution")
    
    async def technique_8_multi_tab_handling(self, page):
        """기법 8: 멀티 탭/윈도우 처리"""
        print("\n[TECHNIQUE 8] Multi-Tab Handling")
        print("-"*40)
        
        code_example = """
# 새 탭 감지 및 처리
async with context.expect_page() as new_page_info:
    await page.click('a[target="_blank"]')  # 새 탭 열기
new_page = await new_page_info.value

# 새 탭에서 작업
await new_page.wait_for_load_state()
await new_page.fill('input', 'data')

# 탭 전환
await page.bring_to_front()  # 원래 탭으로
        """
        
        print("Pattern:", code_example)
        
        # 멀티 탭 시뮬레이션
        context = page.context
        
        # 새 탭 열기
        new_page = await context.new_page()
        await new_page.goto("https://web-scraping.dev/products")
        
        print(f"Total pages: {len(context.pages)}")
        
        # 각 탭 정보
        for i, p in enumerate(context.pages):
            print(f"  Tab {i}: {p.url[:50]}...")
        
        await new_page.close()
        
        self.techniques_learned.append("multi_tab_handling")
    
    async def technique_9_error_recovery(self, page):
        """기법 9: 에러 복구 패턴"""
        print("\n[TECHNIQUE 9] Error Recovery")
        print("-"*40)
        
        code_example = """
# 재시도 패턴
async def retry_operation(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 지수 백오프

# 타임아웃 처리
try:
    await page.wait_for_selector('.may-not-exist', timeout=1000)
except:
    # 대체 방법 사용
    await page.wait_for_timeout(2000)
        """
        
        print("Pattern:", code_example)
        
        # 에러 처리 시연
        async def safe_click(selector):
            try:
                await page.click(selector, timeout=1000)
                return True
            except:
                print(f"  Could not click {selector}")
                return False
        
        # 여러 셀렉터 시도
        selectors = ['#non-existent', '.also-missing', 'body']
        for selector in selectors:
            if await safe_click(selector):
                print(f"  Successfully clicked: {selector}")
                break
        
        self.techniques_learned.append("error_recovery")
    
    async def technique_10_performance_optimization(self, page):
        """기법 10: 성능 최적화"""
        print("\n[TECHNIQUE 10] Performance Optimization")
        print("-"*40)
        
        optimizations = """
# 이미지 로딩 비활성화
await page.route('**/*.{png,jpg,jpeg,gif,svg}', lambda route: route.abort())

# CSS 비활성화
await page.route('**/*.css', lambda route: route.abort())

# 병렬 처리
import asyncio
tasks = [scrape_page(url) for url in urls]
results = await asyncio.gather(*tasks)

# 브라우저 컨텍스트 재사용
context = await browser.new_context()
pages = [await context.new_page() for _ in range(5)]
        """
        
        print("Optimizations:", optimizations)
        
        # 성능 측정
        start_time = datetime.now()
        
        # 리소스 차단하여 로딩 속도 개선
        await page.route('**/*.{png,jpg,jpeg,gif}', lambda route: route.abort())
        
        await page.goto("https://web-scraping.dev")
        
        load_time = (datetime.now() - start_time).total_seconds()
        print(f"\nPage loaded in {load_time:.2f} seconds (images blocked)")
        
        self.techniques_learned.append("performance_optimization")
    
    async def run_all_techniques(self):
        """모든 기법 실행"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=300
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            techniques = [
                self.technique_1_iframe_navigation,
                self.technique_2_shadow_dom,
                self.technique_3_infinite_scroll,
                self.technique_4_wait_strategies,
                self.technique_5_network_interception,
                self.technique_6_cookie_management,
                self.technique_7_javascript_execution,
                self.technique_8_multi_tab_handling,
                self.technique_9_error_recovery,
                self.technique_10_performance_optimization
            ]
            
            for technique in techniques:
                try:
                    await technique(page)
                except Exception as e:
                    print(f"[ERROR] Technique failed: {e}")
            
            # 학습 결과 저장
            print("\n" + "="*60)
            print("   TECHNIQUES LEARNED")
            print("="*60)
            
            for i, technique in enumerate(self.techniques_learned, 1):
                print(f"{i}. {technique}")
            
            # 결과 파일 저장
            result = {
                'timestamp': datetime.now().isoformat(),
                'techniques_learned': self.techniques_learned,
                'total': len(self.techniques_learned)
            }
            
            with open('logs/learning/techniques_learned.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"\n[COMPLETE] Learned {len(self.techniques_learned)} techniques")
            
            await browser.close()

async def main():
    learner = AdvancedScrapingTechniques()
    await learner.run_all_techniques()

if __name__ == "__main__":
    print("""
    ============================================
       Advanced Web Scraping Techniques
    ============================================
    Learning 10 essential scraping patterns...
    ============================================
    """)
    
    asyncio.run(main())
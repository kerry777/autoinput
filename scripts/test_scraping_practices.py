#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
웹 스크래핑 학습 사이트 테스트
다양한 스크래핑 기법 학습 및 실습
https://web-scraping.dev 활용
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

class ScrapingLearner:
    """웹 스크래핑 학습 도구"""
    
    def __init__(self):
        self.base_url = "https://web-scraping.dev"
        self.results = {}
        
    async def test_login_forms(self, page):
        """다양한 로그인 폼 테스트"""
        print("\n[TEST 1] Login Forms")
        print("="*50)
        
        # 기본 로그인 폼
        await page.goto(f"{self.base_url}/login")
        
        # 1. 표준 HTML form
        try:
            await page.fill('input[name="username"]', 'test_user')
            await page.fill('input[name="password"]', 'test_pass')
            
            # 로그인 버튼 찾기
            login_btn = await page.query_selector('button[type="submit"]')
            if login_btn:
                print("[OK] Standard HTML form found")
                self.results['html_form'] = True
        except:
            print("[FAIL] Standard HTML form not working")
            self.results['html_form'] = False
    
    async def test_dynamic_content(self, page):
        """동적 콘텐츠 처리"""
        print("\n[TEST 2] Dynamic Content")
        print("="*50)
        
        await page.goto(f"{self.base_url}/product/1")
        
        # AJAX 로딩 대기
        try:
            # 가격 정보가 동적으로 로드되는 경우
            await page.wait_for_selector('.product-price', timeout=5000)
            price = await page.text_content('.product-price')
            print(f"[OK] Dynamic price loaded: {price}")
            self.results['ajax_loading'] = True
            
            # Lazy loading 이미지
            images = await page.query_selector_all('img[loading="lazy"]')
            print(f"[INFO] Found {len(images)} lazy-loaded images")
            
            # 스크롤하여 이미지 로드
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1000)
            
        except:
            print("[FAIL] Dynamic content handling failed")
            self.results['ajax_loading'] = False
    
    async def test_javascript_rendering(self, page):
        """JavaScript 렌더링 콘텐츠"""
        print("\n[TEST 3] JavaScript Rendering")
        print("="*50)
        
        # SPA 페이지 테스트
        await page.goto(f"{self.base_url}/spa")
        
        try:
            # JS 렌더링 대기
            await page.wait_for_function('document.querySelector("#app").children.length > 0')
            
            # React/Vue 컴포넌트 확인
            app_content = await page.query_selector('#app')
            if app_content:
                print("[OK] SPA content rendered")
                self.results['spa_rendering'] = True
                
                # 라우팅 테스트
                await page.click('a[href="/spa/products"]')
                await page.wait_for_selector('.product-list')
                print("[OK] Client-side routing works")
                
        except:
            print("[FAIL] JavaScript rendering failed")
            self.results['spa_rendering'] = False
    
    async def test_pagination(self, page):
        """페이지네이션 처리"""
        print("\n[TEST 4] Pagination")
        print("="*50)
        
        await page.goto(f"{self.base_url}/products")
        
        all_products = []
        page_num = 1
        
        while True:
            print(f"[PAGE {page_num}] Scraping...")
            
            # 현재 페이지 상품 수집
            products = await page.query_selector_all('.product-item')
            for product in products:
                title = await product.query_selector('.product-title')
                if title:
                    title_text = await title.text_content()
                    all_products.append(title_text)
            
            # 다음 페이지 버튼 찾기
            next_btn = await page.query_selector('a.next-page:not(.disabled)')
            if next_btn:
                await next_btn.click()
                await page.wait_for_load_state('networkidle')
                page_num += 1
                
                if page_num > 3:  # 최대 3페이지만
                    break
            else:
                print("[INFO] No more pages")
                break
        
        print(f"[OK] Collected {len(all_products)} products from {page_num} pages")
        self.results['pagination'] = True
    
    async def test_form_interactions(self, page):
        """복잡한 폼 상호작용"""
        print("\n[TEST 5] Form Interactions")
        print("="*50)
        
        await page.goto(f"{self.base_url}/form")
        
        try:
            # 텍스트 입력
            await page.fill('input[name="name"]', '홍길동')
            
            # 드롭다운 선택
            await page.select_option('select[name="country"]', 'KR')
            
            # 체크박스
            await page.check('input[type="checkbox"][name="terms"]')
            
            # 라디오 버튼
            await page.click('input[type="radio"][value="premium"]')
            
            # 날짜 선택
            await page.fill('input[type="date"]', '2025-08-09')
            
            # 파일 업로드 (시뮬레이션)
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                # await file_input.set_input_files('path/to/file.pdf')
                print("[INFO] File upload field found")
            
            print("[OK] Form interactions completed")
            self.results['form_interaction'] = True
            
        except Exception as e:
            print(f"[FAIL] Form interaction failed: {e}")
            self.results['form_interaction'] = False
    
    async def test_captcha_detection(self, page):
        """CAPTCHA 감지"""
        print("\n[TEST 6] CAPTCHA Detection")
        print("="*50)
        
        await page.goto(f"{self.base_url}/login")
        
        # CAPTCHA 요소 찾기
        captcha_selectors = [
            '.g-recaptcha',
            '#recaptcha',
            'iframe[src*="recaptcha"]',
            '.h-captcha',
            'img[alt*="captcha"]'
        ]
        
        captcha_found = False
        for selector in captcha_selectors:
            element = await page.query_selector(selector)
            if element:
                print(f"[WARN] CAPTCHA detected: {selector}")
                captcha_found = True
                break
        
        if not captcha_found:
            print("[OK] No CAPTCHA found")
        
        self.results['captcha_detection'] = captcha_found
    
    async def test_session_management(self, page):
        """세션 및 쿠키 관리"""
        print("\n[TEST 7] Session Management")
        print("="*50)
        
        # 로그인 시뮬레이션
        await page.goto(f"{self.base_url}/login")
        
        # 쿠키 설정
        await page.context.add_cookies([
            {
                'name': 'session_id',
                'value': 'test_session_123',
                'domain': '.web-scraping.dev',
                'path': '/'
            }
        ])
        
        # 쿠키 확인
        cookies = await page.context.cookies()
        print(f"[INFO] Total cookies: {len(cookies)}")
        
        # 세션 유지 테스트
        await page.goto(f"{self.base_url}/account")
        
        # 로그인 상태 확인
        logged_in = await page.query_selector('.user-info')
        if logged_in:
            print("[OK] Session maintained")
            self.results['session_management'] = True
        else:
            print("[INFO] Session not maintained (expected)")
            self.results['session_management'] = False
    
    async def test_anti_scraping(self, page):
        """안티 스크래핑 대응"""
        print("\n[TEST 8] Anti-Scraping Measures")
        print("="*50)
        
        # User-Agent 설정
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Rate limiting 테스트
        for i in range(3):
            await page.goto(f"{self.base_url}/products")
            await page.wait_for_timeout(1000)  # 1초 대기
            
            # 차단 확인
            blocked = await page.query_selector('.rate-limit-message')
            if blocked:
                print(f"[WARN] Rate limited after {i+1} requests")
                break
        else:
            print("[OK] No rate limiting detected")
        
        self.results['anti_scraping_handled'] = True
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        
        print("\n" + "="*60)
        print("   WEB SCRAPING LEARNING TESTS")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # 모든 테스트 실행
            tests = [
                self.test_login_forms,
                self.test_dynamic_content,
                self.test_javascript_rendering,
                self.test_pagination,
                self.test_form_interactions,
                self.test_captcha_detection,
                self.test_session_management,
                self.test_anti_scraping
            ]
            
            for test_func in tests:
                try:
                    await test_func(page)
                except Exception as e:
                    print(f"[ERROR] Test failed: {e}")
            
            # 결과 요약
            print("\n" + "="*60)
            print("   TEST RESULTS SUMMARY")
            print("="*60)
            
            passed = sum(1 for v in self.results.values() if v)
            total = len(self.results)
            
            for test_name, result in self.results.items():
                status = "[PASS]" if result else "[FAIL]"
                print(f"{status} {test_name}")
            
            print(f"\nTotal: {passed}/{total} tests passed")
            
            # 결과 저장
            os.makedirs("logs/learning", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            with open(f'logs/learning/test_results_{timestamp}.json', 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n[SAVED] Results saved to logs/learning/test_results_{timestamp}.json")
            
            await browser.close()

async def main():
    """메인 실행 함수"""
    learner = ScrapingLearner()
    await learner.run_all_tests()

if __name__ == "__main__":
    print("""
    ============================================
         Web Scraping Learning Suite
    ============================================
    Testing various scraping techniques...
    ============================================
    """)
    
    asyncio.run(main())
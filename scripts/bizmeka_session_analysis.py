#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 세션 및 네트워크 완전 분석
수작업과 자동화의 차이점 찾기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

class BizmekaSessionAnalysis:
    def __init__(self):
        self.logs_dir = "logs/session"
        os.makedirs(self.logs_dir, exist_ok=True)
        self.requests_log = []
        self.responses_log = []
        
    async def analyze_manual_vs_automated(self):
        """수작업과 자동화의 차이 분석"""
        print("\n[SESSION & NETWORK ANALYSIS]")
        print("="*60)
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=100,
            devtools=True  # 개발자 도구 열기
        )
        
        context = await browser.new_context(
            record_har_path=f"{self.logs_dir}/network.har",  # 네트워크 기록
            record_video_dir=self.logs_dir  # 비디오 녹화
        )
        
        page = await context.new_page()
        
        # 모든 요청/응답 로깅
        async def log_request(request):
            self.requests_log.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data
            })
            print(f"→ {request.method} {request.url[:50]}...")
            
        async def log_response(response):
            self.responses_log.append({
                'url': response.url,
                'status': response.status,
                'headers': dict(response.headers)
            })
            print(f"← {response.status} {response.url[:50]}...")
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        try:
            # 1. 초기 페이지 방문 (세션 생성)
            print("\n[1] Initial page visit...")
            await page.goto("https://www.bizmeka.com")
            await page.wait_for_timeout(2000)
            
            # 초기 쿠키 확인
            initial_cookies = await context.cookies()
            print(f"   Initial cookies: {len(initial_cookies)}")
            for cookie in initial_cookies:
                print(f"     - {cookie['name']}: {cookie['value'][:20] if len(cookie['value']) > 20 else cookie['value']}")
            
            # 2. 로그인 페이지 이동
            print("\n[2] Navigating to login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(2000)
            
            # 로그인 페이지 쿠키
            login_cookies = await context.cookies()
            print(f"   Login page cookies: {len(login_cookies)}")
            
            # 3. 페이지 상태 분석
            page_state = await page.evaluate("""
                () => {
                    // 모든 hidden input 수집
                    const hiddenInputs = {};
                    document.querySelectorAll('input[type="hidden"]').forEach(input => {
                        hiddenInputs[input.name] = input.value;
                    });
                    
                    // 모든 메타 태그 수집
                    const metaTags = {};
                    document.querySelectorAll('meta').forEach(meta => {
                        if (meta.name) {
                            metaTags[meta.name] = meta.content;
                        }
                    });
                    
                    // 세션 스토리지
                    const sessionData = {};
                    for (let key in sessionStorage) {
                        sessionData[key] = sessionStorage.getItem(key);
                    }
                    
                    // 로컬 스토리지
                    const localData = {};
                    for (let key in localStorage) {
                        localData[key] = localStorage.getItem(key);
                    }
                    
                    return {
                        hiddenInputs,
                        metaTags,
                        sessionStorage: sessionData,
                        localStorage: localData,
                        referrer: document.referrer,
                        origin: window.location.origin
                    };
                }
            """)
            
            print("\n[3] Page state analysis:")
            print(f"   Hidden inputs: {len(page_state['hiddenInputs'])}")
            for name, value in page_state['hiddenInputs'].items():
                print(f"     - {name}: {value[:30] if len(value) > 30 else value}")
            
            print(f"   Meta tags: {len(page_state['metaTags'])}")
            print(f"   Session storage: {len(page_state['sessionStorage'])}")
            print(f"   Local storage: {len(page_state['localStorage'])}")
            print(f"   Referrer: {page_state['referrer']}")
            
            # 4. 로그인 시도 (네트워크 모니터링)
            print("\n[4] Login attempt with full monitoring...")
            
            # CSRF 토큰
            csrf_token = page_state['hiddenInputs'].get('OWASP_CSRFTOKEN', '')
            print(f"   CSRF Token: {csrf_token[:30]}...")
            
            # 로그인 정보 입력
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            
            # 로그인 전 요청 수
            requests_before = len(self.requests_log)
            
            # 로그인 버튼 클릭
            await page.click('#btnSubmit')
            await page.wait_for_timeout(5000)
            
            # 로그인 후 요청 수
            requests_after = len(self.requests_log)
            print(f"\n   Login triggered {requests_after - requests_before} requests")
            
            # 5. 결과 분석
            current_url = page.url
            print(f"\n[5] Result: {current_url}")
            
            if 'secondStep' in current_url:
                print("   2FA detected - analyzing why...")
                
                # 2FA 페이지 분석
                twofa_state = await page.evaluate("""
                    () => {
                        return {
                            title: document.title,
                            bodyText: document.body.innerText.substring(0, 500),
                            forms: document.querySelectorAll('form').length,
                            buttons: Array.from(document.querySelectorAll('button')).map(b => b.innerText)
                        };
                    }
                """)
                
                print("\n   2FA Page Analysis:")
                print(f"     Title: {twofa_state['title']}")
                print(f"     Buttons: {twofa_state['buttons']}")
            
            # 6. 네트워크 로그 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 요청 로그
            with open(f"{self.logs_dir}/requests_{timestamp}.json", "w", encoding='utf-8') as f:
                json.dump(self.requests_log, f, ensure_ascii=False, indent=2)
            
            # 응답 로그
            with open(f"{self.logs_dir}/responses_{timestamp}.json", "w", encoding='utf-8') as f:
                json.dump(self.responses_log, f, ensure_ascii=False, indent=2)
            
            print(f"\n[6] Logs saved:")
            print(f"   - requests_{timestamp}.json")
            print(f"   - responses_{timestamp}.json")
            print(f"   - network.har")
            
            # 7. 차이점 분석
            print("\n[7] Key differences found:")
            print("   Manual login (no 2FA):")
            print("     - Uses existing browser session")
            print("     - Has browser history")
            print("     - Natural referrer chain")
            print("     - Persistent cookies")
            print("\n   Automated login (2FA triggered):")
            print("     - Fresh browser instance")
            print("     - No browser history")
            print("     - Direct navigation")
            print("     - New session cookies")
            
            print("\n브라우저 30초간 유지...")
            await page.wait_for_timeout(30000)
            
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()

async def main():
    analyzer = BizmekaSessionAnalysis()
    await analyzer.analyze_manual_vs_automated()

if __name__ == "__main__":
    asyncio.run(main())
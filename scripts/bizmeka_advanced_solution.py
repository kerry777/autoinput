#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 고급 로그인 솔루션
- 자동화 탐지 우회
- 세션 관리
- 쿠키 활용
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import time

class BizmekaLogin:
    def __init__(self):
        self.session_data = {}
        self.cookies = []
        
    async def create_human_like_browser(self):
        """인간처럼 보이는 브라우저 생성"""
        playwright = await async_playwright().start()
        
        # 실제 Chrome 실행 파일 경로 사용 (있다면)
        browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=100,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=site-per-process',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins',
                '--disable-site-isolation-trials',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            permissions=['geolocation'],
            color_scheme='light',
            reduced_motion='no-preference',
            forced_colors='none'
        )
        
        # 자동화 탐지 우회 스크립트
        await context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Override plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
            
            // Chrome specific
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {}
            };
            
            // Override console.debug
            const originalDebug = console.debug;
            console.debug = function(...args) {
                if (args[0] && args[0].includes('devtools')) return;
                return originalDebug.apply(console, args);
            };
        """)
        
        page = await context.new_page()
        
        # 마우스 움직임 시뮬레이션
        await self.simulate_mouse_movement(page)
        
        return browser, context, page
    
    async def simulate_mouse_movement(self, page):
        """마우스 움직임 시뮬레이션"""
        for _ in range(3):
            x = 500 + (_ * 100)
            y = 300 + (_ * 50)
            await page.mouse.move(x, y)
            await page.wait_for_timeout(100)
    
    async def human_type(self, page, selector, text):
        """사람처럼 타이핑"""
        element = await page.query_selector(selector)
        if element:
            await element.click()
            await page.wait_for_timeout(500)
            
            # 기존 텍스트 삭제
            await page.keyboard.press('Control+A')
            await page.wait_for_timeout(100)
            await page.keyboard.press('Delete')
            await page.wait_for_timeout(200)
            
            # 한 글자씩 타이핑
            for char in text:
                await page.keyboard.type(char)
                delay = 50 + (30 * (ord(char) % 3))  # 랜덤한 딜레이
                await page.wait_for_timeout(delay)
            
            return True
        return False
    
    async def wait_for_navigation(self, page):
        """네비게이션 대기"""
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except:
            await page.wait_for_timeout(3000)
    
    async def login_method_1(self, page):
        """방법 1: 표준 로그인"""
        print("\n[방법 1] 표준 로그인 시도...")
        
        # 로그인 페이지로 이동
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await self.wait_for_navigation(page)
        
        # 로그인 정보 입력
        success = await self.human_type(page, '#username', 'kilmoon@mek-ics.com')
        if not success:
            print("   ID 입력 실패")
            return False
            
        await page.wait_for_timeout(500)
        
        success = await self.human_type(page, '#password', 'moon7410!@')
        if not success:
            print("   Password 입력 실패")
            return False
        
        await page.wait_for_timeout(500)
        
        # 로그인 버튼 클릭
        await page.click('#btnSubmit')
        await self.wait_for_navigation(page)
        
        # 로그인 성공 확인
        current_url = page.url
        if 'login' not in current_url.lower() or 'main' in current_url.lower():
            print("   [성공] 로그인 완료!")
            return True
        elif 'fail' in current_url.lower():
            print("   [실패] 로그인 실패 - 비밀번호 오류 또는 계정 잠김")
            return False
        else:
            print(f"   [불명] 현재 URL: {current_url}")
            return False
    
    async def login_method_2(self, page):
        """방법 2: JavaScript 실행"""
        print("\n[방법 2] JavaScript 로그인 시도...")
        
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await self.wait_for_navigation(page)
        
        # JavaScript로 직접 값 설정
        await page.evaluate("""
            () => {
                document.querySelector('#username').value = 'kilmoon@mek-ics.com';
                document.querySelector('#password').value = 'moon7410!@';
            }
        """)
        
        await page.wait_for_timeout(1000)
        
        # 폼 제출
        await page.evaluate("""
            () => {
                const form = document.querySelector('form');
                if (form) {
                    form.submit();
                } else {
                    document.querySelector('#btnSubmit').click();
                }
            }
        """)
        
        await self.wait_for_navigation(page)
        
        current_url = page.url
        if 'login' not in current_url.lower():
            print("   [성공] JavaScript 로그인 완료!")
            return True
        else:
            print("   [실패] JavaScript 로그인 실패")
            return False
    
    async def handle_password_reset(self, page):
        """비밀번호 재설정 처리"""
        print("\n[비밀번호 재설정]")
        
        # 비밀번호 찾기 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await self.wait_for_navigation(page)
        
        # 이메일 인증 선택
        radio_buttons = await page.query_selector_all('input[type="radio"]')
        if len(radio_buttons) >= 3:
            await radio_buttons[2].click()
            print("   이메일 인증 선택")
            await page.wait_for_timeout(1000)
            
            # 본인인증 버튼 클릭
            auth_button = await page.query_selector('.btn-danger')
            if auth_button:
                await auth_button.click()
                print("   본인인증 버튼 클릭")
                await page.wait_for_timeout(3000)
                
                # 정보 입력
                await self.human_type(page, 'input#idEM', '이길문')
                await self.human_type(page, 'input#preEmail', 'kilmoon')
                await self.human_type(page, 'input#nextEmail', 'mek-ics.com')
                
                print("   정보 입력 완료")
                
                # 캡차 처리
                print("\n   [캡차 발견]")
                print("   캡차를 수동으로 입력해주세요")
                
                # 스크린샷 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"logs/bizmeka/captcha_{timestamp}.png"
                os.makedirs("logs/bizmeka", exist_ok=True)
                await page.screenshot(path=screenshot_path)
                print(f"   스크린샷: {screenshot_path}")
    
    async def run(self):
        """메인 실행"""
        browser = None
        try:
            browser, context, page = await self.create_human_like_browser()
            
            print("""
            =====================================
            Bizmeka 고급 로그인 시스템
            =====================================
            """)
            
            # 방법 1 시도
            success = await self.login_method_1(page)
            
            if not success:
                # 방법 2 시도
                success = await self.login_method_2(page)
            
            if not success:
                # 비밀번호 재설정 시도
                await self.handle_password_reset(page)
            
            # 쿠키 저장
            if success:
                cookies = await context.cookies()
                with open("bizmeka_cookies.json", "w") as f:
                    json.dump(cookies, f)
                print("\n쿠키 저장 완료: bizmeka_cookies.json")
            
            print("\n브라우저는 30초 후 닫힙니다...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    login = BizmekaLogin()
    asyncio.run(login.run())
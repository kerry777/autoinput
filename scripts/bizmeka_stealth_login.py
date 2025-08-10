#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 스텔스 로그인 - 자동화 감지 완벽 우회
수작업과 동일하게 동작
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import random

class BizmekaStealthLogin:
    def __init__(self):
        self.logs_dir = "logs/stealth"
        os.makedirs(self.logs_dir, exist_ok=True)
        
    async def create_stealth_browser(self):
        """완벽한 스텔스 브라우저 생성"""
        playwright = await async_playwright().start()
        
        # 실제 Chrome 경로 사용 (있다면)
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            browser = await playwright.chromium.launch(
                executable_path=chrome_path,
                headless=False,
                slow_mo=100,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-automation',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--start-maximized',
                    '--disable-infobars',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-default-apps',
                    '--disable-sync',
                    '--disable-translate',
                    '--hide-scrollbars',
                    '--metrics-recording-only',
                    '--mute-audio',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                    '--password-store=basic',
                    '--use-mock-keychain'
                ]
            )
        else:
            browser = await playwright.chromium.launch(
                headless=False,
                slow_mo=100,
                args=['--disable-blink-features=AutomationControlled']
            )
        
        # 실제 브라우저처럼 컨텍스트 생성
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            screen={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            permissions=['geolocation', 'notifications'],
            color_scheme='light',
            reduced_motion='no-preference',
            forced_colors='none',
            accept_downloads=True,
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            offline=False,
            http_credentials=None,
            ignore_https_errors=False,
            java_script_enabled=True,
            bypass_csp=False,
            extra_http_headers={
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        # 완벽한 자동화 우회 스크립트
        await context.add_init_script("""
            // navigator.webdriver 제거
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Chrome 객체 정의
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 플러그인 정의
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf"},
                        1: {type: "application/pdf", suffixes: "pdf"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 2,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/x-nacl", suffixes: ""},
                        1: {type: "application/x-pnacl", suffixes: ""},
                        description: "Native Client",
                        filename: "internal-nacl-plugin",
                        length: 2,
                        name: "Native Client"
                    }
                ]
            });
            
            // 언어 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
            
            // 하드웨어 동시성
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            
            // 메모리
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // 권한 API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // WebGL Vendor
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
            
            // Canvas 노이즈 추가
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {
                    imageData.data[i] = imageData.data[i] + Math.random() * 0.1;
                }
                context.putImageData(imageData, 0, 0);
                return originalToDataURL.apply(this, arguments);
            };
            
            // Console 디버그 숨기기
            const originalLog = console.log;
            console.log = function(...args) {
                if (args[0] && args[0].includes('devtools')) return;
                return originalLog.apply(console, args);
            };
        """)
        
        page = await context.new_page()
        
        # 마우스 움직임 시뮬레이션
        await self.natural_mouse_movement(page)
        
        return browser, context, page
    
    async def natural_mouse_movement(self, page):
        """자연스러운 마우스 움직임"""
        for i in range(5):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await page.wait_for_timeout(random.randint(50, 150))
    
    async def human_type(self, page, text):
        """완벽한 사람 타이핑 시뮬레이션"""
        for char in text:
            await page.keyboard.type(char)
            # 랜덤 딜레이 (사람마다 타이핑 속도가 다름)
            delay = random.randint(50, 200)
            await page.wait_for_timeout(delay)
    
    async def login(self):
        """스텔스 로그인"""
        browser = None
        try:
            print("\n[STEALTH LOGIN]")
            print("="*60)
            
            browser, context, page = await self.create_stealth_browser()
            
            # 1. 메인 페이지 먼저 방문 (수작업처럼)
            print("\n[1] Visiting main page first (like manual browsing)...")
            await page.goto("https://www.bizmeka.com")
            await page.wait_for_timeout(random.randint(2000, 3000))
            
            # 랜덤 스크롤
            await page.evaluate("window.scrollTo(0, 300)")
            await page.wait_for_timeout(random.randint(500, 1000))
            
            # 2. 로그인 페이지로 이동
            print("\n[2] Navigating to login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(random.randint(2000, 3000))
            
            # 3. CSRF 토큰 확인
            csrf = await page.input_value('input[name="OWASP_CSRFTOKEN"]')
            if csrf:
                print(f"   CSRF Token: {csrf[:30]}...")
            
            # 4. 마우스로 필드 클릭 (수작업처럼)
            print("\n[3] Clicking and typing (human-like)...")
            
            # Username 필드 클릭
            username_box = await page.query_selector('#username')
            if username_box:
                box = await username_box.bounding_box()
                if box:
                    # 필드 중앙 클릭
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    await page.wait_for_timeout(random.randint(300, 500))
            
            # Username 입력
            await self.human_type(page, 'kilmoon@mek-ics.com')
            await page.wait_for_timeout(random.randint(500, 800))
            
            # Tab 키로 이동 (또는 마우스 클릭)
            if random.choice([True, False]):
                await page.keyboard.press('Tab')
            else:
                password_box = await page.query_selector('#password')
                if password_box:
                    box = await password_box.bounding_box()
                    if box:
                        await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            
            await page.wait_for_timeout(random.randint(300, 500))
            
            # Password 입력
            await self.human_type(page, 'moon7410!@')
            await page.wait_for_timeout(random.randint(500, 800))
            
            # 5. 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"{self.logs_dir}/before_stealth_{timestamp}.png")
            
            # 6. 로그인 버튼 클릭 (마우스로)
            print("\n[4] Clicking login button with mouse...")
            login_btn = await page.query_selector('#btnSubmit')
            if login_btn:
                box = await login_btn.bounding_box()
                if box:
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            
            # 7. 응답 대기
            await page.wait_for_timeout(5000)
            
            # 8. 결과 확인
            current_url = page.url
            print(f"\n[5] Result URL: {current_url}")
            
            await page.screenshot(path=f"{self.logs_dir}/after_stealth_{timestamp}.png")
            
            if 'secondStep' in current_url:
                print("   [INFO] 2차 인증 페이지 나타남")
            elif 'fail' in current_url:
                print("   [FAILED] 로그인 실패")
            else:
                print("   [SUCCESS] 로그인 성공 (2차 인증 없음)")
            
            print("\n브라우저 30초간 유지...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            if browser:
                await browser.close()

if __name__ == "__main__":
    stealth = BizmekaStealthLogin()
    asyncio.run(stealth.login())
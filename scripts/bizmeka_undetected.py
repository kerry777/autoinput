#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka Undetected - 최종 솔루션
Playwright-stealth 기법 적용
"""

import asyncio
from playwright.async_api import async_playwright
import random
import time
import os

class BizmekaUndetected:
    def __init__(self):
        self.logs_dir = "logs/undetected"
        os.makedirs(self.logs_dir, exist_ok=True)
    
    async def apply_stealth(self, page):
        """Stealth 기법 적용"""
        # 1. navigator.webdriver 제거
        await page.add_init_script("""
            // webdriver 완전 제거
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Chrome 객체 정의
            window.chrome = {
                runtime: {
                    connect: () => {},
                    sendMessage: () => {},
                    onMessage: { addListener: () => {} }
                },
                loadTimes: function() {
                    return {
                        requestTime: Date.now() / 1000,
                        startLoadTime: Date.now() / 1000,
                        commitLoadTime: Date.now() / 1000,
                        finishDocumentLoadTime: Date.now() / 1000,
                        finishLoadTime: Date.now() / 1000,
                        firstPaintTime: Date.now() / 1000,
                        firstPaintAfterLoadTime: 0,
                        navigationType: "Other",
                        wasFetchedViaSpdy: false,
                        wasNpnNegotiated: false,
                        npnNegotiatedProtocol: "",
                        wasAlternateProtocolAvailable: false,
                        connectionInfo: "http/1.1"
                    };
                },
                csi: function() { return { onloadT: Date.now(), startE: Date.now() - 1000 }; },
                app: {
                    isInstalled: false,
                    getDetails: () => null,
                    getIsInstalled: () => false,
                    runningState: () => 'running'
                }
            };
            
            // 플러그인 정의 (실제 Chrome과 동일)
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const pluginArray = [
                        {
                            0: { type: "application/x-google-chrome-pdf", suffixes: "pdf" },
                            1: { type: "application/pdf", suffixes: "pdf" },
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 2,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: { type: "application/x-nacl", suffixes: "" },
                            1: { type: "application/x-pnacl", suffixes: "" },
                            description: "Native Client",
                            filename: "internal-nacl-plugin",
                            length: 2,
                            name: "Native Client"
                        },
                        {
                            description: "Chrome PDF Viewer",
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        }
                    ];
                    pluginArray.length = 3;
                    return pluginArray;
                }
            });
            
            // 언어 설정
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en']
            });
            Object.defineProperty(navigator, 'language', {
                get: () => 'ko-KR'
            });
            
            // 하드웨어 정보
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });
            
            // Platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Vendor
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.'
            });
            
            // WebGL Vendor 스푸핑
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel(R) UHD Graphics';
                }
                return getParameter.apply(this, arguments);
            };
            
            // Canvas 노이즈 추가
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 100) {
                        imageData.data[i] = Math.min(255, imageData.data[i] + Math.random() * 0.5);
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // Console 디버그 숨기기
            const originalLog = console.log;
            console.log = function(...args) {
                if (args[0] && typeof args[0] === 'string' && args[0].includes('devtools')) return;
                return originalLog.apply(console, args);
            };
            
            // Permission API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // CDP 감지 우회
            delete window.__proto__.chrome;
            delete window.__proto__.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.__proto__.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.__proto__.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
    
    async def human_like_mouse(self, page, x, y):
        """인간같은 마우스 움직임"""
        current_x, current_y = 0, 0
        steps = random.randint(10, 20)
        
        for i in range(steps):
            progress = (i + 1) / steps
            # 베지어 곡선 시뮬레이션
            next_x = current_x + (x - current_x) * progress
            next_y = current_y + (y - current_y) * progress
            # 약간의 랜덤 오프셋
            next_x += random.uniform(-2, 2)
            next_y += random.uniform(-2, 2)
            
            await page.mouse.move(next_x, next_y)
            await page.wait_for_timeout(random.randint(10, 30))
        
        await page.mouse.move(x, y)
    
    async def human_like_type(self, page, text):
        """인간같은 타이핑"""
        for char in text:
            await page.keyboard.type(char)
            # 타이핑 속도 변화
            if char in '.@':
                await page.wait_for_timeout(random.randint(100, 200))
            else:
                await page.wait_for_timeout(random.randint(50, 150))
    
    async def login(self):
        """Undetected 로그인"""
        async with async_playwright() as p:
            # 브라우저 시작 (Chromium 대신 Chrome 경로 사용)
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=50,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-automation',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--allow-running-insecure-content',
                    '--disable-features=RendererCodeIntegrity',
                    '--disable-gpu-sandbox',
                    '--disable-logging',
                    '--disable-dev-tools',
                    '--disable-notifications',
                    '--disable-popup-blocking',
                    '--disable-save-password-bubble',
                    '--disable-translate',
                    '--metrics-recording-only',
                    '--no-first-run',
                    '--safebrowsing-disable-auto-update',
                    '--enable-automation=false',
                    '--hide-scrollbars',
                    '--mute-audio'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                screen={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                permissions=['geolocation'],
                is_mobile=False,
                has_touch=False,
                color_scheme='light'
            )
            
            page = await context.new_page()
            
            # Stealth 적용
            await self.apply_stealth(page)
            
            try:
                print("\n[UNDETECTED LOGIN]")
                print("="*60)
                
                # 1. 메인 페이지 먼저 방문 (정상적인 브라우징 패턴)
                print("\n[1] Visiting main page first...")
                await page.goto("https://www.bizmeka.com")
                await page.wait_for_timeout(random.randint(3000, 5000))
                
                # 랜덤 스크롤
                await page.evaluate(f"window.scrollTo(0, {random.randint(100, 500)})")
                await page.wait_for_timeout(random.randint(1000, 2000))
                
                # 2. 로그인 페이지로 자연스럽게 이동
                print("\n[2] Navigating to login page...")
                await page.goto("https://ezsso.bizmeka.com/loginForm.do")
                await page.wait_for_timeout(random.randint(2000, 3000))
                
                # 3. 마우스로 필드 클릭 (인간처럼)
                print("\n[3] Human-like interaction...")
                
                # Username 필드 클릭
                username_elem = await page.query_selector('#username')
                if username_elem:
                    box = await username_elem.bounding_box()
                    if box:
                        target_x = box['x'] + box['width']/2 + random.uniform(-20, 20)
                        target_y = box['y'] + box['height']/2 + random.uniform(-5, 5)
                        await self.human_like_mouse(page, target_x, target_y)
                        await page.mouse.click(target_x, target_y)
                        await page.wait_for_timeout(random.randint(500, 800))
                
                # Username 입력
                await self.human_like_type(page, 'kilmoon@mek-ics.com')
                await page.wait_for_timeout(random.randint(500, 1000))
                
                # Tab 또는 마우스로 Password 필드로
                if random.choice([True, False]):
                    await page.keyboard.press('Tab')
                else:
                    password_elem = await page.query_selector('#password')
                    if password_elem:
                        box = await password_elem.bounding_box()
                        if box:
                            target_x = box['x'] + box['width']/2 + random.uniform(-20, 20)
                            target_y = box['y'] + box['height']/2 + random.uniform(-5, 5)
                            await self.human_like_mouse(page, target_x, target_y)
                            await page.mouse.click(target_x, target_y)
                
                await page.wait_for_timeout(random.randint(500, 800))
                
                # Password 입력
                await self.human_like_type(page, 'moon7410!@')
                await page.wait_for_timeout(random.randint(800, 1200))
                
                # 4. 로그인 버튼 클릭
                print("\n[4] Clicking login button...")
                login_btn = await page.query_selector('#btnSubmit')
                if login_btn:
                    box = await login_btn.bounding_box()
                    if box:
                        target_x = box['x'] + box['width']/2 + random.uniform(-10, 10)
                        target_y = box['y'] + box['height']/2 + random.uniform(-3, 3)
                        await self.human_like_mouse(page, target_x, target_y)
                        await page.mouse.click(target_x, target_y)
                
                # 5. 결과 대기
                await page.wait_for_timeout(5000)
                
                # 6. 결과 확인
                current_url = page.url
                print(f"\n[5] Result URL: {current_url}")
                
                if 'secondStep' not in current_url:
                    print("\n>>> SUCCESS! No 2FA! <<<")
                    print("Successfully bypassed detection!")
                else:
                    print("\n2FA still triggered")
                    print("Site detection is very strong")
                
                # 스크린샷 저장
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"{self.logs_dir}/result_{timestamp}.png")
                
                print("\nBrowser will stay open for 30 seconds...")
                await page.wait_for_timeout(30000)
                
            except Exception as e:
                print(f"\nError: {e}")
                
            finally:
                await browser.close()

if __name__ == "__main__":
    undetected = BizmekaUndetected()
    asyncio.run(undetected.login())
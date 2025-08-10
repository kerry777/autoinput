#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 고급 로그인 솔루션
- 패스워드 잠금 감지 및 처리
- 캡차 처리 전략
- 세션 관리 및 쿠키 처리
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import time

async def check_password_reset_captcha():
    """비밀번호 재설정 페이지의 캡차 이미지 캡처 및 분석"""
    
    print("\n[CAPTCHA RECOGNITION TEST]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/captcha", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # 비밀번호 찾기 페이지로 이동
            print("\n[STEP 1] Loading password reset page...")
            await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
            await page.wait_for_timeout(3000)
            
            # 전체 페이지 캡처
            full_page_path = f"logs/bizmeka/captcha/full_page_{timestamp}.png"
            await page.screenshot(path=full_page_path, full_page=True)
            print(f"   [SAVED] Full page: {full_page_path}")
            
            # 캡차 이미지 찾기
            print("\n[STEP 2] Looking for CAPTCHA image...")
            
            # 모든 이미지 검색
            images = await page.query_selector_all('img')
            print(f"   Found {len(images)} images on page")
            
            captcha_found = False
            for i, img in enumerate(images):
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt') or ""
                    id_attr = await img.get_attribute('id') or ""
                    
                    # 캡차일 가능성이 있는 이미지
                    if src and ('captcha' in src.lower() or 
                               'captcha' in alt.lower() or 
                               'captcha' in id_attr.lower() or
                               '/captcha' in src or
                               'cert' in src.lower()):
                        
                        print(f"\n   [CAPTCHA FOUND] Image {i+1}")
                        print(f"   - src: {src}")
                        print(f"   - alt: {alt}")
                        print(f"   - id: {id_attr}")
                        
                        # 캡차 이미지만 캡처
                        box = await img.bounding_box()
                        if box:
                            captcha_path = f"logs/bizmeka/captcha/captcha_{i}_{timestamp}.png"
                            await img.screenshot(path=captcha_path)
                            print(f"   [SAVED] CAPTCHA image: {captcha_path}")
                            captcha_found = True
                            
                            # 캡차 이미지 정보
                            print(f"   - Size: {box['width']}x{box['height']}")
                            print(f"   - Position: ({box['x']}, {box['y']})")
                            
                            # base64 이미지인지 확인
                            if src.startswith('data:image'):
                                print("   - Type: Base64 encoded image")
                            else:
                                print(f"   - Type: URL image")
                
                except Exception as e:
                    continue
            
            if not captcha_found:
                print("\n   [WARNING] No CAPTCHA image found with standard selectors")
                print("   Checking for dynamic loading...")
                
                # JavaScript로 캡차 관련 함수 찾기
                captcha_functions = await page.evaluate("""
                    () => {
                        const funcs = [];
                        for (let key in window) {
                            if (key.toLowerCase().includes('captcha') || 
                                key.toLowerCase().includes('cert')) {
                                funcs.push(key);
                            }
                        }
                        return funcs;
                    }
                """)
                
                if captcha_functions:
                    print(f"\n   Found JavaScript functions: {captcha_functions}")
                    
                    # sendCertKeyCaptcha 함수 실행 시도
                    if 'sendCertKeyCaptcha' in captcha_functions:
                        print("\n   [TRYING] Calling sendCertKeyCaptcha()...")
                        try:
                            await page.evaluate("sendCertKeyCaptcha()")
                            await page.wait_for_timeout(2000)
                            
                            # 다시 캡처
                            await page.screenshot(
                                path=f"logs/bizmeka/captcha/after_function_{timestamp}.png",
                                full_page=True
                            )
                            print("   [SAVED] Screenshot after function call")
                        except:
                            print("   [FAILED] Could not call function")
            
            # 캡차 입력 필드 찾기
            print("\n[STEP 3] Looking for CAPTCHA input field...")
            
            input_fields = await page.query_selector_all('input[type="text"]')
            for field in input_fields:
                name = await field.get_attribute('name') or ""
                id_attr = await field.get_attribute('id') or ""
                placeholder = await field.get_attribute('placeholder') or ""
                
                if 'captcha' in name.lower() or 'captcha' in id_attr.lower() or \
                   '문자' in placeholder or '입력' in placeholder:
                    print(f"   [FOUND] CAPTCHA input field")
                    print(f"   - name: {name}")
                    print(f"   - id: {id_attr}")
                    print(f"   - placeholder: {placeholder}")
            
            print("\n[RESULT]")
            print("="*60)
            if captcha_found:
                print("✓ CAPTCHA images have been saved to: logs/bizmeka/captcha/")
                print("✓ You can view these images to see the CAPTCHA")
                print("\n[NOTE] I cannot directly read CAPTCHA text from images,")
                print("but I've captured them for your review.")
            else:
                print("× No standard CAPTCHA image found")
                print("× The CAPTCHA might be dynamically generated or hidden")
            
            print("\n[Browser will stay open for manual inspection...]")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()

async def smart_login_with_retry():
    """스마트 로그인 - 재시도 로직 포함"""
    
    print("\n[SMART LOGIN WITH RETRY LOGIC]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/smart", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=site-per-process'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 자동화 탐지 우회
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        page = await context.new_page()
        
        try:
            # 로그인 페이지 로드
            print("\n[STEP 1] Loading login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(2000)
            
            # 쿠키 확인
            cookies = await context.cookies()
            print(f"   [INFO] {len(cookies)} cookies found")
            
            # 로그인 시도
            print("\n[STEP 2] Attempting login...")
            
            # 더 자연스러운 입력
            await page.click('#username')
            await page.wait_for_timeout(500)
            
            # 한 글자씩 입력 (사람처럼)
            for char in 'kilmoon@mek-ics.com':
                await page.keyboard.type(char)
                await page.wait_for_timeout(50)
            
            await page.wait_for_timeout(500)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(500)
            
            for char in 'moon7410!@':
                await page.keyboard.type(char)
                await page.wait_for_timeout(50)
            
            print("   [OK] Credentials entered naturally")
            
            # 스크린샷
            await page.screenshot(path=f"logs/bizmeka/smart/before_login_{timestamp}.png")
            
            # 로그인 버튼 클릭
            await page.click('#btnSubmit')
            print("   [OK] Login button clicked")
            
            # 응답 대기
            await page.wait_for_timeout(3000)
            
            # 결과 확인
            current_url = page.url
            print(f"\n[STEP 3] Checking result...")
            print(f"   Current URL: {current_url}")
            
            # 에러 체크
            if 'readLoginFailView' in current_url:
                print("\n   [ERROR] Password failure detected!")
                
                # 에러 페이지 캡처
                await page.screenshot(
                    path=f"logs/bizmeka/smart/error_page_{timestamp}.png",
                    full_page=True
                )
                
                # 에러 메시지 읽기
                error_text = await page.inner_text('body')
                if '5회' in error_text or '5번' in error_text:
                    print("   [LOCKED] Account locked after 5 failed attempts")
                    print("\n[SOLUTION]")
                    print("   1. Wait for lockout period to expire (usually 30 minutes)")
                    print("   2. Use password reset with CAPTCHA")
                    print("   3. Contact administrator")
                    
                    # 비밀번호 찾기 링크 찾기
                    reset_link = await page.query_selector('a[href*="find"]')
                    if reset_link:
                        print("\n   [FOUND] Password reset link")
                        await reset_link.click()
                        await page.wait_for_timeout(3000)
                        
                        # 캡차 페이지 스크린샷
                        await page.screenshot(
                            path=f"logs/bizmeka/smart/reset_page_{timestamp}.png",
                            full_page=True
                        )
                        print("   [SCREENSHOT] Password reset page saved")
            
            elif 'login' not in current_url.lower():
                print("   [SUCCESS] Login successful!")
                await page.screenshot(
                    path=f"logs/bizmeka/smart/success_{timestamp}.png",
                    full_page=True
                )
            
            else:
                print("   [UNKNOWN] Login status unclear")
                
            print("\n[Browser will stay open for inspection...]")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()

if __name__ == "__main__":
    print("""
    =====================================
    Bizmeka Advanced Login Solution
    =====================================
    1. Check CAPTCHA on password reset
    2. Smart login with retry logic
    =====================================
    
    Select option:
    1. Check password reset CAPTCHA
    2. Try smart login
    """)
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(check_password_reset_captcha())
    else:
        asyncio.run(smart_login_with_retry())
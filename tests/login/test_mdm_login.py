#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MSM 사이트 로그인 테스트
URL: http://it.mek-ics.com/msm
ID: mdmtest
PW: 0001
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

async def test_msm_login():
    """MSM 사이트 로그인 테스트"""
    
    print("\n" + "="*50)
    print("[MSM LOGIN TEST] Starting...")
    print("="*50)
    print("\nTarget: http://it.mek-ics.com/msm")
    print("Test Account: mdmtest / 0001")
    
    # 스크린샷 디렉토리 생성
    os.makedirs("logs/screenshots/msm", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    async with async_playwright() as p:
        # 브라우저 실행 (GUI 모드로 천천히)
        print("\n[BROWSER] Launching Chromium...")
        browser = await p.chromium.launch(
            headless=False,  # 화면 표시
            slow_mo=1000      # 1초 딜레이로 천천히
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # 1. 사이트 접속
            print("\n[STEP 1] Navigating to MSM site...")
            await page.goto("http://it.mek-ics.com/msm", wait_until='networkidle')
            
            # 페이지 로드 대기
            await page.wait_for_timeout(2000)
            
            # 스크린샷 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"logs/screenshots/msm/msm_login_{timestamp}.png"
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"[SCREENSHOT] Initial page: {screenshot_path}")
            
            # 2. 페이지 분석
            print("\n[STEP 2] Analyzing page structure...")
            
            # 모든 input 필드 찾기
            inputs = await page.query_selector_all('input')
            print(f"[FOUND] {len(inputs)} input fields")
            
            # 각 input 필드 정보 수집
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type')
                input_name = await input_elem.get_attribute('name')
                input_id = await input_elem.get_attribute('id')
                input_placeholder = await input_elem.get_attribute('placeholder')
                is_visible = await input_elem.is_visible()
                
                print(f"  Input {i+1}:")
                print(f"    - Type: {input_type}")
                print(f"    - Name: {input_name}")
                print(f"    - ID: {input_id}")
                print(f"    - Placeholder: {input_placeholder}")
                print(f"    - Visible: {is_visible}")
            
            # 3. 로그인 필드 찾기 (다양한 방법 시도)
            print("\n[STEP 3] Looking for login fields...")
            
            username_field = None
            password_field = None
            
            # ID/Name 기반 선택자 시도
            username_selectors = [
                'input[name="userid"]',
                'input[name="username"]',
                'input[name="id"]',
                'input[name="user_id"]',
                'input[name="loginId"]',
                'input[id="userid"]',
                'input[id="username"]',
                'input[id="id"]',
                'input[placeholder*="ID"]',
                'input[placeholder*="아이디"]',
                'input[type="text"]:visible'
            ]
            
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[name="passwd"]',
                'input[name="pwd"]',
                'input[name="pass"]',
                'input[id="password"]',
                'input[id="passwd"]',
                'input[placeholder*="비밀번호"]',
                'input[placeholder*="Password"]'
            ]
            
            # Username 필드 찾기
            for selector in username_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        username_field = selector
                        print(f"[OK] Username field found: {selector}")
                        break
                except:
                    continue
            
            # Password 필드 찾기
            for selector in password_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        password_field = selector
                        print(f"[OK] Password field found: {selector}")
                        break
                except:
                    continue
            
            # 4. 로그인 정보 입력
            if username_field and password_field:
                print("\n[STEP 4] Entering login credentials...")
                
                # Username 입력
                await page.fill(username_field, "mdmtest")
                print("[INPUT] Username: mdmtest")
                await page.wait_for_timeout(500)
                
                # Password 입력
                await page.fill(password_field, "0001")
                print("[INPUT] Password: ****")
                await page.wait_for_timeout(500)
                
                # 입력 후 스크린샷
                await page.screenshot(path=f"logs/screenshots/msm/msm_filled_{timestamp}.png")
                print("[SCREENSHOT] Credentials entered")
                
                # 5. 로그인 버튼 찾기
                print("\n[STEP 5] Looking for login button...")
                
                button_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("로그인")',
                    'button:has-text("Login")',
                    'button:has-text("Sign in")',
                    'input[type="button"][value*="로그인"]',
                    'input[type="submit"][value*="로그인"]',
                    'a:has-text("로그인")',
                    '.login-button',
                    '#loginBtn',
                    'button.btn-login'
                ]
                
                login_button = None
                for selector in button_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem and await elem.is_visible():
                            login_button = selector
                            print(f"[OK] Login button found: {selector}")
                            break
                    except:
                        continue
                
                # Enter 키로도 시도 가능
                if login_button:
                    print("\n[ACTION] Ready to login...")
                    print("Press Enter in password field or click login button")
                    
                    # Enter 키 누르기 (자동 로그인)
                    print("[AUTO] Pressing Enter key...")
                    await page.press(password_field, 'Enter')
                else:
                    # 버튼을 못 찾으면 Enter 키로 시도
                    print("[AUTO] No button found, pressing Enter...")
                    await page.press(password_field, 'Enter')
                
                # 로그인 시도 후 대기
                print("\n[WAIT] Waiting for login response...")
                await page.wait_for_timeout(3000)
                
                # 로그인 후 URL 확인
                current_url = page.url
                print(f"[URL] Current: {current_url}")
                
                # 로그인 성공 여부 확인
                if current_url != "http://it.mek-ics.com/msm":
                    print("[SUCCESS] URL changed - Login might be successful!")
                else:
                    print("[CHECK] URL unchanged - Checking for error messages...")
                    
                    # 에러 메시지 확인
                    error_selectors = [
                        '.error-message',
                        '.alert-danger',
                        'span.error',
                        'div.error',
                        '*:has-text("실패")',
                        '*:has-text("오류")'
                    ]
                    
                    for selector in error_selectors:
                        try:
                            error = await page.query_selector(selector)
                            if error:
                                error_text = await error.text_content()
                                print(f"[ERROR] Found: {error_text}")
                                break
                        except:
                            continue
                
                # 최종 스크린샷
                await page.screenshot(path=f"logs/screenshots/msm/msm_result_{timestamp}.png")
                print("[SCREENSHOT] Final result saved")
                
                # 쿠키 저장 (성공 시)
                cookies = await context.cookies()
                if cookies:
                    with open('config/msm_cookies.json', 'w') as f:
                        json.dump(cookies, f, indent=2)
                    print(f"[COOKIES] Saved {len(cookies)} cookies")
                
            else:
                print("\n[ERROR] Could not find login fields!")
                print("Manual inspection needed")
            
            # 브라우저 열어두기
            print("\n[INFO] Browser will remain open for 15 seconds...")
            print("You can manually inspect the page...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"\n[ERROR] Exception occurred: {str(e)}")
            await page.screenshot(path=f"logs/screenshots/msm/error_{timestamp}.png")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")
    
    print("\n" + "="*50)
    print("MSM Login Test Complete")
    print("="*50)

if __name__ == "__main__":
    print("""
    ============================================
           MSM Site Login Test
    ============================================
    Site: http://it.mek-ics.com/msm
    Account: mdmtest / 0001
    ============================================
    """)
    
    asyncio.run(test_msm_login())
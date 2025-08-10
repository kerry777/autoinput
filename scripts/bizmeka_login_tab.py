#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 로그인 - Tab 키 사용 버전
1. ID 입력
2. Tab으로 Password 필드 이동
3. Password 입력
4. 로그인 버튼 클릭
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def bizmeka_login_with_tab():
    """Tab 키를 사용한 Bizmeka 로그인"""
    
    print("\n[BIZMEKA LOGIN - TAB METHOD]")
    print("="*50)
    
    os.makedirs("logs/bizmeka", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500  # 동작 확인용
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 로그인 페이지 로드
            print("\n[1] Loading login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_load_state('networkidle')
            print("   [OK] Page loaded")
            
            # CSRF 토큰 확인
            csrf_token = await page.input_value('input[name="OWASP_CSRFTOKEN"]')
            if csrf_token:
                print(f"   [INFO] CSRF Token found: {csrf_token[:20]}...")
            
            # 2. ID 필드 클릭 및 입력
            print("\n[2] Entering username...")
            id_field = await page.query_selector('#username')
            if id_field:
                await id_field.click()
                await page.wait_for_timeout(300)
                
                # 기존 값 삭제
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Delete')
                
                # ID 입력
                await page.keyboard.type('kilmoon@mek-ics.com')
                print("   [OK] Username typed: kilmoon@mek-ics.com")
            
            # 3. Tab으로 Password 필드로 이동
            print("\n[3] Tab to password field...")
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            print("   [OK] Moved to password field")
            
            # 4. Password 입력
            print("\n[4] Entering password...")
            await page.keyboard.type('moon7410!@')
            print("   [OK] Password typed: ****")
            
            # 스크린샷 (로그인 전)
            await page.screenshot(path=f"logs/bizmeka/tab_filled_{timestamp}.png")
            
            # 5. 로그인 버튼 클릭 (여러 방법 시도)
            print("\n[5] Clicking login button...")
            
            # 방법 1: ID로 직접 클릭
            login_button = await page.query_selector('#btnSubmit')
            if login_button and await login_button.is_visible():
                await login_button.click()
                print("   [OK] Clicked #btnSubmit")
            else:
                # 방법 2: Enter 키
                print("   [INFO] Button not found, trying Enter key...")
                await page.keyboard.press('Enter')
                print("   [OK] Pressed Enter")
            
            # 6. 로그인 응답 대기
            print("\n[6] Waiting for login response...")
            
            # 페이지 변화 대기
            try:
                # URL 변경 또는 에러 메시지 대기
                await page.wait_for_function(
                    """() => {
                        return window.location.href.indexOf('loginForm.do') === -1 || 
                               document.querySelector('.error') !== null ||
                               document.querySelector('[class*="alert"]') !== null;
                    }""",
                    timeout=5000
                )
                print("   [OK] Page changed")
            except:
                await page.wait_for_timeout(3000)
                print("   [INFO] Timeout - checking status...")
            
            # 7. 로그인 결과 확인
            print("\n[7] Checking login result...")
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            # 스크린샷 (로그인 후)
            await page.screenshot(path=f"logs/bizmeka/tab_result_{timestamp}.png")
            
            # 성공 여부 판단
            login_success = False
            
            # URL 변경 확인
            if "loginForm.do" not in current_url or "main" in current_url or "index" in current_url:
                print("   [SUCCESS] Login successful - URL changed!")
                login_success = True
            else:
                # 에러 메시지 확인
                page_text = await page.content()
                
                # 일반적인 에러 메시지
                if '잘못' in page_text or 'incorrect' in page_text.lower() or 'invalid' in page_text.lower():
                    print("   [FAILED] Login failed - incorrect credentials")
                elif '잠금' in page_text or 'locked' in page_text.lower():
                    print("   [FAILED] Account locked")
                elif 'captcha' in page_text.lower() or '인증' in page_text:
                    print("   [INFO] Additional verification required")
                else:
                    # username 필드 확인
                    username_value = await page.input_value('#username')
                    if not username_value or username_value != 'kilmoon@mek-ics.com':
                        print("   [SUCCESS] Username field cleared - might be logged in")
                        login_success = True
                    else:
                        print("   [WARNING] Login status unclear")
            
            # 8. 추가 확인 - 메인 페이지 접근 시도
            if not login_success:
                print("\n[8] Additional check - trying to access main page...")
                await page.goto("https://ezsso.bizmeka.com/main")
                await page.wait_for_timeout(2000)
                
                if "login" not in page.url.lower():
                    print("   [SUCCESS] Can access main page - logged in!")
                    login_success = True
            
            print("\n" + "="*50)
            if login_success:
                print("[FINAL] LOGIN SUCCESSFUL!")
            else:
                print("[FINAL] LOGIN FAILED or NEEDS VERIFICATION")
            print("="*50)
            
            print("\n[Browser will stay open for 15 seconds...]")
            await page.wait_for_timeout(15000)
            
            return login_success
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            await browser.close()
            print("\n[DONE] Browser closed")

if __name__ == "__main__":
    print("""
    =====================================
    Bizmeka Login - Tab Navigation
    =====================================
    1. Enter ID
    2. Press Tab
    3. Enter Password
    4. Click Login button
    =====================================
    """)
    
    asyncio.run(bizmeka_login_with_tab())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka SSO 로그인 자동화
https://ezsso.bizmeka.com/loginForm.do
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def bizmeka_login(username, password, headless=False):
    """
    Bizmeka SSO 로그인
    
    Args:
        username: 사용자 ID
        password: 비밀번호
        headless: 헤드리스 모드 여부
    
    Returns:
        bool: 로그인 성공 여부
    """
    
    print(f"\n[BIZMEKA LOGIN] Starting login process...")
    print(f"[INFO] Username: {username}")
    
    os.makedirs("logs/bizmeka", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=200 if not headless else 0
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드
            print("[1] Loading login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_load_state('networkidle')
            
            # 2. ID 입력
            print("[2] Entering username...")
            id_field = await page.query_selector('#username')
            if not id_field:
                id_field = await page.query_selector('input[name="username"]')
            
            if id_field:
                await id_field.click()
                await id_field.fill(username)
                print(f"   [OK] Username entered: {username}")
            else:
                print("   [ERROR] Username field not found")
                return False
            
            # 3. Password 입력
            print("[3] Entering password...")
            pw_field = await page.query_selector('#password')
            if not pw_field:
                pw_field = await page.query_selector('input[name="password"]')
            
            if pw_field:
                await pw_field.click()
                await pw_field.fill(password)
                print("   [OK] Password entered: ****")
            else:
                print("   [ERROR] Password field not found")
                return False
            
            # 스크린샷 (로그인 전)
            await page.screenshot(path=f"logs/bizmeka/before_login_{timestamp}.png")
            
            # 4. 로그인 버튼 클릭
            print("[4] Clicking login button...")
            
            # 여러 선택자 시도
            login_selectors = [
                'a:has-text("로그인")',
                'button:has-text("로그인")',
                'input[type="submit"]',
                'button[type="submit"]',
                '#loginBtn',
                '.login-btn'
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        await button.click()
                        print(f"   [OK] Login button clicked: {selector}")
                        login_clicked = True
                        break
                except:
                    continue
            
            # 버튼을 못 찾으면 JavaScript 함수 호출
            if not login_clicked:
                print("   [INFO] Trying JavaScript function...")
                try:
                    await page.evaluate("goLogin()")
                    print("   [OK] Called goLogin() function")
                    login_clicked = True
                except:
                    # Enter 키 시도
                    print("   [INFO] Trying Enter key...")
                    await pw_field.press('Enter')
                    login_clicked = True
            
            # 5. 로그인 결과 대기
            print("[5] Waiting for login response...")
            await page.wait_for_timeout(3000)
            
            # 6. 로그인 성공 확인
            print("[6] Checking login result...")
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            # 스크린샷 (로그인 후)
            await page.screenshot(path=f"logs/bizmeka/after_login_{timestamp}.png")
            
            # 로그인 성공 판별
            login_success = False
            
            # URL 변경 확인
            if "loginForm.do" not in current_url:
                print("   [SUCCESS] URL changed - Login successful!")
                login_success = True
            else:
                # 에러 메시지 확인
                try:
                    error_msg = await page.query_selector('.error-message, .alert-danger, .login-error')
                    if error_msg:
                        error_text = await error_msg.inner_text()
                        print(f"   [FAILED] Error message: {error_text}")
                    else:
                        # 페이지 내용 변경 확인
                        page_text = await page.content()
                        if username in page_text or "logout" in page_text.lower():
                            print("   [SUCCESS] User info found - Login successful!")
                            login_success = True
                        else:
                            print("   [WARNING] Login status unclear")
                except:
                    pass
            
            if not headless:
                print("\n[INFO] Browser will close in 5 seconds...")
                await page.wait_for_timeout(5000)
            
            return login_success
            
        except Exception as e:
            print(f"[ERROR] Login failed: {str(e)}")
            return False
            
        finally:
            await browser.close()
            print("[DONE] Browser closed")


async def test_bizmeka_login():
    """테스트 함수"""
    
    print("\n" + "="*50)
    print("BIZMEKA SSO LOGIN TEST")
    print("="*50)
    
    # 실제 사용자명과 비밀번호를 입력하세요
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    # 로그인 실행
    success = await bizmeka_login(
        username=username,
        password=password,
        headless=False
    )
    
    if success:
        print("\n[SUCCESS] LOGIN TEST PASSED")
    else:
        print("\n[FAILED] LOGIN TEST FAILED")
    
    return success


if __name__ == "__main__":
    # 테스트 실행
    # asyncio.run(test_bizmeka_login())
    
    # 또는 직접 실행
    asyncio.run(bizmeka_login("your_username", "your_password", headless=False))
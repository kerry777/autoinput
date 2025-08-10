#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka SSO 로그인 - 최종 완성 버전
확인된 HTML 요소:
- ID: <input type="text" id="username" name="username">
- PW: <input type="password" id="password" name="password">
- Button: <a href="#" id="btnSubmit" class="login-btn">Login</a>
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def bizmeka_login(username, password, headless=False):
    """
    Bizmeka SSO 로그인 - 확실한 버전
    
    Args:
        username: 사용자 ID 또는 회사 이메일
        password: 비밀번호
        headless: 헤드리스 모드 여부
    
    Returns:
        bool: 로그인 성공 여부
    """
    
    print(f"\n[BIZMEKA LOGIN] Starting...")
    print(f"[USER] {username}")
    
    os.makedirs("logs/bizmeka", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=300 if not headless else 0
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드
            print("\n[1] Loading page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_load_state('networkidle')
            print("   [OK] Page loaded")
            
            # 2. ID 입력 - id="username"
            print("\n[2] Filling username...")
            await page.fill('#username', username)
            print(f"   [OK] Username entered: {username}")
            
            # 3. Password 입력 - id="password"
            print("\n[3] Filling password...")
            await page.fill('#password', password)
            print("   [OK] Password entered: ****")
            
            # 스크린샷 (로그인 전)
            await page.screenshot(path=f"logs/bizmeka/ready_{timestamp}.png")
            
            # 4. 로그인 버튼 클릭 - id="btnSubmit"
            print("\n[4] Clicking login button...")
            
            # 방법 1: ID로 직접 클릭
            login_button = await page.query_selector('#btnSubmit')
            if login_button:
                await login_button.click()
                print("   [OK] Clicked #btnSubmit")
            else:
                # 방법 2: class로 클릭
                await page.click('.login-btn')
                print("   [OK] Clicked .login-btn")
            
            # 5. 로그인 처리 대기
            print("\n[5] Waiting for response...")
            
            # 페이지 이동 또는 에러 메시지 대기
            try:
                await page.wait_for_navigation(timeout=5000)
                print("   [OK] Page navigated")
            except:
                # 네비게이션이 없으면 AJAX 응답 대기
                await page.wait_for_timeout(3000)
                print("   [INFO] No navigation, checking response...")
            
            # 6. 로그인 결과 확인
            print("\n[6] Checking result...")
            current_url = page.url
            print(f"   URL: {current_url}")
            
            # 스크린샷 (로그인 후)
            await page.screenshot(path=f"logs/bizmeka/result_{timestamp}.png")
            
            # 성공 판별
            if "loginForm.do" not in current_url:
                print("\n[SUCCESS] Login successful - URL changed!")
                return True
            else:
                # 에러 메시지 확인
                error_selectors = [
                    '.error', '.alert', '.message', 
                    '[class*="error"]', '[class*="fail"]'
                ]
                
                for selector in error_selectors:
                    error = await page.query_selector(selector)
                    if error and await error.is_visible():
                        error_text = await error.inner_text()
                        print(f"\n[FAILED] Error: {error_text}")
                        return False
                
                # username 필드가 비어있으면 로그인 성공
                username_value = await page.input_value('#username')
                if not username_value:
                    print("\n[SUCCESS] Login form cleared - likely logged in!")
                    return True
                
                print("\n[WARNING] Login status unclear")
                return False
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            return False
            
        finally:
            if not headless:
                print("\n[INFO] Browser closing in 5 seconds...")
                await page.wait_for_timeout(5000)
            await browser.close()
            print("[DONE] Closed")


async def quick_login(username, password):
    """간단한 로그인 - 최소 코드"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 로그인 페이지
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_load_state('networkidle')
        
        # ID/PW 입력
        await page.fill('#username', username)
        await page.fill('#password', password)
        
        # 로그인 클릭
        await page.click('#btnSubmit')
        
        # 결과 대기
        await page.wait_for_timeout(3000)
        
        # 확인
        success = "loginForm.do" not in page.url
        print(f"Login {'SUCCESS' if success else 'FAILED'}")
        
        await page.wait_for_timeout(5000)
        await browser.close()
        
        return success


def run_login(username, password):
    """동기식 실행 함수"""
    return asyncio.run(bizmeka_login(username, password, headless=False))


if __name__ == "__main__":
    print("""
    =====================================
    Bizmeka SSO Login
    =====================================
    URL: https://ezsso.bizmeka.com
    =====================================
    """)
    
    # 방법 1: 대화형 입력
    # username = input("Username: ")
    # password = input("Password: ")
    # asyncio.run(bizmeka_login(username, password))
    
    # 방법 2: 직접 실행 (실제 계정 정보 입력)
    asyncio.run(bizmeka_login("kilmoon@mek-ics.com", "moon7410!@", headless=False))
    
    # 방법 3: 빠른 로그인
    # asyncio.run(quick_login("your_username", "your_password"))
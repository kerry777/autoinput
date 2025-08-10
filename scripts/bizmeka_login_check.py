#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 로그인 후 상태 확인
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def bizmeka_login_with_check():
    """로그인 후 상세 확인"""
    
    print("\n[BIZMEKA LOGIN CHECK]")
    print("="*50)
    
    os.makedirs("logs/bizmeka", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. 로그인 페이지
            print("\n[1] Loading login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_load_state('networkidle')
            
            # 2. 로그인 정보 입력
            print("[2] Entering credentials...")
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            print("   [OK] Credentials entered")
            
            # 3. 로그인 클릭
            print("[3] Clicking login...")
            await page.click('#btnSubmit')
            
            # 4. 응답 대기 (더 길게)
            print("[4] Waiting for response...")
            await page.wait_for_timeout(5000)
            
            # 5. 상태 확인
            print("\n[5] Checking status...")
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            # 페이지 제목 확인
            title = await page.title()
            print(f"   Page title: {title}")
            
            # 쿠키 확인
            cookies = await context.cookies()
            print(f"   Cookies: {len(cookies)} cookies set")
            for cookie in cookies:
                if 'session' in cookie['name'].lower() or 'token' in cookie['name'].lower():
                    print(f"     - {cookie['name']}: {cookie['value'][:20]}...")
            
            # 로그인 폼이 여전히 있는지 확인
            username_field = await page.query_selector('#username')
            if username_field:
                value = await username_field.input_value()
                if value:
                    print(f"   [INFO] Username field still has value: {value}")
                else:
                    print("   [INFO] Username field is empty")
            
            # 에러 메시지 확인
            page_content = await page.content()
            if 'error' in page_content.lower() or '실패' in page_content:
                print("   [WARNING] Error keyword found in page")
            
            # 로그아웃 링크 확인
            if 'logout' in page_content.lower() or '로그아웃' in page_content:
                print("   [SUCCESS] Logout link found - user is logged in!")
            
            # 다른 페이지로 이동 시도
            print("\n[6] Trying to navigate to main page...")
            await page.goto("https://ezsso.bizmeka.com/")
            await page.wait_for_timeout(3000)
            
            new_url = page.url
            print(f"   New URL: {new_url}")
            
            if 'login' not in new_url.lower():
                print("   [SUCCESS] Can access main page - logged in!")
            else:
                print("   [INFO] Redirected back to login")
            
            print("\n[7] Browser will stay open for manual inspection...")
            print("   Please check if you are logged in")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()
            print("\n[DONE] Complete")

if __name__ == "__main__":
    asyncio.run(bizmeka_login_with_check())
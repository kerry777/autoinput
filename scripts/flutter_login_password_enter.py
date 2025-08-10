#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - Password 필드에서 Enter
가장 간단한 방법
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def flutter_login_password_enter():
    """Password 필드에서 Enter로 로그인"""
    
    print("\n[FLUTTER LOGIN - PASSWORD ENTER METHOD]")
    print("="*50)
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500  # 동작 확인용
        )
        
        page = await browser.new_page()
        
        try:
            # 1. 페이지 로드
            print("\n[1] Loading page...")
            await page.goto("http://it.mek-ics.com/msm")
            await page.wait_for_timeout(5000)
            
            # 2. ID 입력
            print("\n[2] Entering credentials...")
            await page.click('body')
            await page.wait_for_timeout(500)
            
            # Tab으로 ID 필드로
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            
            print("  - ID: mdmtest")
            await page.keyboard.type('mdmtest')
            await page.wait_for_timeout(500)
            
            # 3. Password 입력
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            
            print("  - Password: ****")
            await page.keyboard.type('0001')
            await page.wait_for_timeout(500)
            
            # 4. Password 필드에서 Enter (여러 방법 시도)
            print("\n[3] Trying different Enter methods in password field...")
            
            # 방법 1: 단순 Enter
            print("  Method 1: Simple Enter")
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(3000)
            
            if page.url != "http://it.mek-ics.com/msm/":
                print("  [SUCCESS] Login with single Enter!")
                return True
            
            # 방법 2: Enter 두 번
            print("  Method 2: Double Enter")
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(1000)
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(3000)
            
            if page.url != "http://it.mek-ics.com/msm/":
                print("  [SUCCESS] Login with double Enter!")
                return True
            
            # 방법 3: Ctrl+Enter
            print("  Method 3: Ctrl+Enter")
            await page.keyboard.press('Control+Enter')
            await page.wait_for_timeout(3000)
            
            if page.url != "http://it.mek-ics.com/msm/":
                print("  [SUCCESS] Login with Ctrl+Enter!")
                return True
            
            # 5. 최종 확인
            print("\n[4] Final check...")
            print(f"  URL: {page.url}")
            
            # 페이지 내용 변화 확인
            try:
                # 로그인 폼이 사라졌는지 확인
                inputs = await page.query_selector_all('input')
                if len(inputs) == 0:
                    print("  [INFO] Input fields disappeared - might be logged in")
                    return True
            except:
                pass
            
            print("\n[INFO] Login might require clicking a button")
            print("  Browser will stay open for manual check")
            
            await page.wait_for_timeout(15000)
            return False
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            return False
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    =====================================
    Flutter Login - Password Enter
    =====================================
    Simple approach:
    1. Tab to ID field -> Enter mdmtest
    2. Tab to Password -> Enter 0001  
    3. Press Enter in password field
    =====================================
    """)
    
    asyncio.run(flutter_login_password_enter())
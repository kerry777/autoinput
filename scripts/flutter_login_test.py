#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 테스트 - 브라우저 표시 확인
"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_browser_display():
    """브라우저 표시 테스트"""
    
    print("\n[TEST] Starting browser display test...")
    print("Browser should open and stay visible for 30 seconds")
    
    async with async_playwright() as p:
        # 브라우저 실행 (헤드리스 모드 OFF)
        print("\n[1] Launching browser with headless=False...")
        browser = await p.chromium.launch(
            headless=False,  # 브라우저 창 표시
            slow_mo=1000,    # 1초씩 천천히
            args=['--start-maximized']  # 최대화
        )
        
        print("[2] Creating new page...")
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            no_viewport=True  # 전체 화면 사용
        )
        page = await context.new_page()
        
        print("[3] Navigating to MSM site...")
        await page.goto("http://it.mek-ics.com/msm")
        
        print("[4] Waiting for page to load...")
        await page.wait_for_timeout(5000)
        
        print("\n[5] Starting login process...")
        print("   - Clicking body to focus...")
        await page.click('body')
        
        print("   - Tab 1...")
        await page.keyboard.press('Tab')
        await page.wait_for_timeout(1000)
        
        print("   - Tab 2 (ID field)...")
        await page.keyboard.press('Tab')
        await page.wait_for_timeout(1000)
        
        print("   - Entering ID: mdmtest")
        await page.keyboard.type('mdmtest')
        await page.wait_for_timeout(1000)
        
        print("   - Tab 3 (Password field)...")
        await page.keyboard.press('Tab')
        await page.wait_for_timeout(1000)
        
        print("   - Entering Password: 0001")
        await page.keyboard.type('0001')
        await page.wait_for_timeout(1000)
        
        print("   - Pressing Enter to login...")
        await page.keyboard.press('Enter')
        
        print("\n[6] Waiting for login response...")
        await page.wait_for_timeout(5000)
        
        print(f"[7] Current URL: {page.url}")
        
        print("\n[8] Browser will stay open for 30 seconds...")
        print("    You should see the browser window now!")
        print("    Check if login was successful.")
        
        # 30초 대기
        for i in range(30, 0, -5):
            print(f"    Closing in {i} seconds...")
            await page.wait_for_timeout(5000)
        
        print("\n[9] Closing browser...")
        await browser.close()
        print("[DONE] Test completed")

if __name__ == "__main__":
    print("="*50)
    print("FLUTTER LOGIN - BROWSER DISPLAY TEST")
    print("="*50)
    print("\nThis test will:")
    print("1. Open a visible browser window")
    print("2. Navigate to MSM site")
    print("3. Attempt login with mdmtest/0001")
    print("4. Keep browser open for 30 seconds")
    print("="*50)
    
    # 실행
    asyncio.run(test_browser_display())
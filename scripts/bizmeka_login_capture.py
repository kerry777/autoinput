#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 로그인 후 메인 화면 캡처
로그인 성공 후 실제 메인 페이지를 캡처하여 확인
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def bizmeka_login_and_capture():
    """로그인 후 메인 화면 캡처"""
    
    print("\n[BIZMEKA LOGIN & CAPTURE MAIN]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/main", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 로그인 페이지
            print("\n[STEP 1] Loading login page...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_load_state('networkidle')
            print("   [OK] Login page loaded")
            
            # 로그인 전 스크린샷
            await page.screenshot(path=f"logs/bizmeka/main/01_login_page_{timestamp}.png")
            print("   [SCREENSHOT] Login page saved")
            
            # 2. 로그인 정보 입력
            print("\n[STEP 2] Entering credentials...")
            
            # ID 입력
            await page.click('#username')
            await page.keyboard.press('Control+A')
            await page.keyboard.type('kilmoon@mek-ics.com')
            print("   [OK] Username entered")
            
            # Tab으로 Password 이동
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            
            # Password 입력
            await page.keyboard.type('moon7410!@')
            print("   [OK] Password entered")
            
            # 입력 완료 스크린샷
            await page.screenshot(path=f"logs/bizmeka/main/02_credentials_entered_{timestamp}.png")
            print("   [SCREENSHOT] Credentials entered")
            
            # 3. 로그인 클릭
            print("\n[STEP 3] Clicking login button...")
            await page.click('#btnSubmit')
            print("   [OK] Login button clicked")
            
            # 4. 로그인 처리 대기
            print("\n[STEP 4] Waiting for login to complete...")
            await page.wait_for_timeout(5000)
            
            # 로그인 직후 스크린샷
            current_url = page.url
            print(f"   Current URL: {current_url}")
            await page.screenshot(path=f"logs/bizmeka/main/03_after_login_{timestamp}.png")
            print("   [SCREENSHOT] After login click")
            
            # 5. 메인 페이지들 시도
            print("\n[STEP 5] Navigating to main pages...")
            
            main_urls = [
                "https://ezsso.bizmeka.com/main",
                "https://ezsso.bizmeka.com/",
                "https://ezsso.bizmeka.com/index",
                "https://ezsso.bizmeka.com/home",
                "https://ezsso.bizmeka.com/dashboard"
            ]
            
            for i, url in enumerate(main_urls, 1):
                print(f"\n   Trying URL {i}: {url}")
                try:
                    await page.goto(url, wait_until='networkidle', timeout=10000)
                    await page.wait_for_timeout(2000)
                    
                    final_url = page.url
                    print(f"   Final URL: {final_url}")
                    
                    # 각 시도마다 스크린샷
                    screenshot_name = f"logs/bizmeka/main/04_main_attempt_{i}_{timestamp}.png"
                    await page.screenshot(path=screenshot_name, full_page=True)
                    print(f"   [SCREENSHOT] Saved: {screenshot_name}")
                    
                    # 로그인 성공 확인
                    if "login" not in final_url.lower():
                        print(f"   [SUCCESS] Main page accessed!")
                        
                        # 페이지 정보 수집
                        title = await page.title()
                        print(f"   Page Title: {title}")
                        
                        # 사용자 정보 찾기
                        page_text = await page.inner_text('body')
                        if 'kilmoon' in page_text.lower() or 'moon' in page_text:
                            print("   [FOUND] User information in page!")
                        
                        break
                except:
                    print(f"   [FAILED] Could not access {url}")
            
            # 6. 페이지 요소 확인
            print("\n[STEP 6] Checking page elements...")
            
            # 로그아웃 버튼 찾기
            logout_elements = [
                'a:has-text("로그아웃")',
                'a:has-text("Logout")',
                'button:has-text("로그아웃")',
                '[href*="logout"]'
            ]
            
            for selector in logout_elements:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        print(f"   [FOUND] Logout element: {selector}")
                        break
                except:
                    continue
            
            # 메뉴 확인
            menus = await page.query_selector_all('nav a, .menu a, [class*="menu"] a')
            if menus:
                print(f"   [FOUND] {len(menus)} menu items")
                for i, menu in enumerate(menus[:5]):  # 처음 5개만
                    text = await menu.inner_text()
                    if text.strip():
                        print(f"     - {text.strip()}")
            
            # 7. 최종 전체 페이지 스크린샷
            print("\n[STEP 7] Taking final full page screenshot...")
            
            # 전체 페이지 스크린샷
            final_screenshot = f"logs/bizmeka/main/05_FINAL_MAIN_PAGE_{timestamp}.png"
            await page.screenshot(path=final_screenshot, full_page=True)
            print(f"\n   [FINAL SCREENSHOT] {final_screenshot}")
            
            # Viewport 스크린샷 (보이는 부분만)
            visible_screenshot = f"logs/bizmeka/main/06_VISIBLE_MAIN_{timestamp}.png"
            await page.screenshot(path=visible_screenshot, full_page=False)
            print(f"   [VISIBLE SCREENSHOT] {visible_screenshot}")
            
            print("\n" + "="*60)
            print("[COMPLETE] All screenshots saved in: logs/bizmeka/main/")
            print("="*60)
            
            # 8. 브라우저 유지
            print("\n[Browser will stay open for 20 seconds for inspection...]")
            print("Check the screenshots in: logs/bizmeka/main/")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[DONE] Browser closed")

if __name__ == "__main__":
    print("""
    =====================================
    Bizmeka Login & Main Page Capture
    =====================================
    This will:
    1. Login to Bizmeka
    2. Navigate to main page
    3. Capture multiple screenshots
    4. Save to logs/bizmeka/main/
    =====================================
    """)
    
    asyncio.run(bizmeka_login_and_capture())
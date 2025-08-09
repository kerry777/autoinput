#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
빠른 로그인 테스트 - web-scraping.dev
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_web_scraping_dev():
    """web-scraping.dev 로그인 페이지 테스트"""
    
    print("\n" + "="*50)
    print("[LOGIN TEST] Starting: web-scraping.dev")
    print("="*50)
    
    # 스크린샷 디렉토리 생성
    os.makedirs("logs/screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        # 브라우저 실행 (GUI 모드)
        print("\n[INFO] Starting browser...")
        browser = await p.chromium.launch(
            headless=False,  # 화면 표시
            slow_mo=500       # 천천히 동작 (0.5초 딜레이)
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        # 로그인 페이지로 이동
        print("[INFO] Accessing login page...")
        await page.goto("https://web-scraping.dev/login")
        
        # 페이지 로드 대기
        await page.wait_for_load_state('networkidle')
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"logs/screenshots/login_page_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"[SCREENSHOT] Saved: {screenshot_path}")
        
        # 페이지 분석
        print("\n[ANALYZE] Analyzing page structure...")
        
        # Username 필드 찾기
        username_field = None
        username_selectors = [
            'input[name="username"]',
            'input[name="email"]',
            'input[type="text"]',
            '#username',
            '#email'
        ]
        
        for selector in username_selectors:
            if await page.is_visible(selector):
                username_field = selector
                print(f"[OK] Username field found: {selector}")
                break
        
        # Password 필드 찾기
        password_field = None
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            '#password'
        ]
        
        for selector in password_selectors:
            if await page.is_visible(selector):
                password_field = selector
                print(f"[OK] Password field found: {selector}")
                break
        
        # 로그인 버튼 찾기
        login_button = None
        button_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Sign in")',
            'button:has-text("Submit")'
        ]
        
        for selector in button_selectors:
            try:
                if await page.is_visible(selector):
                    login_button = selector
                    print(f"[OK] Login button found: {selector}")
                    break
            except:
                continue
        
        # 테스트 자동 입력
        if username_field and password_field:
            print("\n[AUTO] Testing auto-fill...")
            
            # 테스트 계정 정보 입력
            await page.fill(username_field, "testuser")
            print("[OK] Username entered: testuser")
            
            await page.fill(password_field, "testpass123")
            print("[OK] Password entered: ***")
            
            # 입력 후 스크린샷
            await page.screenshot(path=f"logs/screenshots/login_filled_{timestamp}.png")
            print("[SCREENSHOT] Auto-fill completed")
            
            # 로그인 버튼 클릭 (실제로는 하지 않음)
            if login_button:
                print(f"\n[READY] Login button ready: {login_button}")
                print("   (실제 클릭은 하지 않음 - 테스트 계정 없음)")
        
        # 페이지 구조 정보 수집
        print("\n[INFO] Page structure:")
        
        # 모든 input 필드 찾기
        inputs = await page.query_selector_all('input')
        print(f"   - Input 필드 개수: {len(inputs)}")
        
        # 모든 button 찾기  
        buttons = await page.query_selector_all('button')
        print(f"   - Button 개수: {len(buttons)}")
        
        # form 태그 확인
        forms = await page.query_selector_all('form')
        print(f"   - Form 개수: {len(forms)}")
        
        print("\n[WAIT] Browser will close in 10 seconds...")
        await asyncio.sleep(10)
        
        await browser.close()
    
    print("\n[COMPLETE] Test finished!")
    print("="*50)
    
    # 결과 요약
    print("\n[SUMMARY] Test results:")
    print(f"   - 로그인 페이지 접속: 성공")
    print(f"   - Username 필드: {'발견' if username_field else '미발견'}")
    print(f"   - Password 필드: {'발견' if password_field else '미발견'}")
    print(f"   - 로그인 버튼: {'발견' if login_button else '미발견'}")
    print(f"   - 자동 입력: {'성공' if username_field and password_field else '실패'}")
    
    return True

if __name__ == "__main__":
    print("""
    ============================================
         Web Scraping Login Test v1.0       
                                          
      Test Site: web-scraping.dev         
      Browser: Chromium (Playwright)         
    ============================================
    """)
    
    asyncio.run(test_web_scraping_dev())
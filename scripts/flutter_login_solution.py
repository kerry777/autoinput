#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter MSM 로그인 - 최종 해결책
Tab 키를 사용하여 숨겨진 input 필드에 접근
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_msm_login(username='mdmtest', password='0001', headless=False):
    """
    Flutter MSM 사이트 로그인
    
    Args:
        username: 로그인 ID
        password: 비밀번호
        headless: 헤드리스 모드 여부
    
    Returns:
        bool: 로그인 성공 여부
    """
    
    print(f"\n[LOGIN] Starting Flutter MSM login...")
    print(f"[INFO] Username: {username}")
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
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
            print("[LOAD] Opening http://it.mek-ics.com/msm...")
            await page.goto("http://it.mek-ics.com/msm")
            
            # Flutter 렌더링 대기
            print("[WAIT] Waiting for Flutter to render...")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 2. 페이지 클릭으로 포커스 활성화
            print("[INIT] Activating page focus...")
            await page.click('body')
            await page.wait_for_timeout(500)
            
            # 3. Tab 키로 ID 필드로 이동 (2번)
            print("[NAV] Navigating to ID field...")
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            
            # 4. ID 입력
            print(f"[INPUT] Entering ID: {username}")
            await page.keyboard.press('Control+A')  # 전체 선택
            await page.keyboard.press('Delete')     # 삭제
            await page.keyboard.type(username)
            
            # 5. Tab으로 Password 필드로 이동
            print("[NAV] Moving to Password field...")
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            
            # 6. Password 입력
            print("[INPUT] Entering Password...")
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Delete')
            await page.keyboard.type(password)
            
            # 스크린샷 저장
            await page.screenshot(path=f"logs/screenshots/flutter/login_{timestamp}.png")
            
            # 7. Password 필드에서 바로 Enter로 로그인
            print("[SUBMIT] Pressing Enter in password field...")
            await page.keyboard.press('Enter')
            
            # 8. 로그인 처리 대기
            print("[WAIT] Waiting for login response...")
            await page.wait_for_timeout(5000)
            
            # 9. 결과 확인
            current_url = page.url
            print(f"[CHECK] Current URL: {current_url}")
            
            # 로그인 성공 판별
            login_success = False
            
            # URL 변경 확인
            if current_url != "http://it.mek-ics.com/msm/":
                print("[SUCCESS] URL changed - Login successful!")
                login_success = True
            else:
                # 페이지 내용 변경 확인
                try:
                    # 로그인 후 나타나는 요소 대기
                    await page.wait_for_selector('text="Dashboard"', timeout=2000)
                    print("[SUCCESS] Dashboard found - Login successful!")
                    login_success = True
                except:
                    print("[WARNING] Login may have failed or needs verification")
            
            # 최종 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/result_{timestamp}.png")
            
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


async def test_login():
    """로그인 테스트"""
    
    print("\n" + "="*50)
    print("FLUTTER MSM LOGIN TEST")
    print("="*50)
    
    # 로그인 실행
    success = await flutter_msm_login(
        username='mdmtest',
        password='0001',
        headless=False
    )
    
    if success:
        print("\n[SUCCESS] LOGIN TEST PASSED")
    else:
        print("\n[FAILED] LOGIN TEST FAILED")
    
    return success


if __name__ == "__main__":
    # 테스트 실행
    result = asyncio.run(test_login())
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)
    print(f"Result: {'SUCCESS' if result else 'FAILED'}")
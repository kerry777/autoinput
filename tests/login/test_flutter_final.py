#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 최종 버전 - Tab 네비게이션 활용
Tab 키로 숨겨진 input 필드에 접근 가능
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_final():
    """Flutter 로그인 - Tab 키로 숨겨진 input 접근"""
    
    print("\n" + "="*50)
    print("[FLUTTER LOGIN - FINAL VERSION]")
    print("="*50)
    print("\n✅ Solution: Using Tab navigation to access hidden inputs")
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=300  # 동작 확인용
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드
            print("\n[STEP 1] Loading Flutter app...")
            await page.goto("http://it.mek-ics.com/msm")
            
            print("[WAIT] Waiting for Flutter to fully render...")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/flutter/final_initial_{timestamp}.png")
            
            # 2. Tab 키로 첫 번째 input 필드로 이동
            print("\n[STEP 2] Navigating to ID field with Tab...")
            
            # 페이지 클릭으로 포커스 활성화
            await page.click('body')
            await page.wait_for_timeout(500)
            
            # Tab을 2번 눌러서 첫 번째 input으로 이동
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            
            # 3. ID 입력
            print("[STEP 3] Entering ID...")
            
            # 기존 텍스트 선택 후 삭제
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Delete')
            
            # ID 입력
            await page.keyboard.type('mdmtest')
            print("[✓] ID entered: mdmtest")
            
            # 4. Tab으로 Password 필드로 이동
            print("\n[STEP 4] Moving to Password field...")
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            
            # 5. Password 입력
            print("[STEP 5] Entering Password...")
            
            # 기존 텍스트 선택 후 삭제
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Delete')
            
            # Password 입력
            await page.keyboard.type('0001')
            print("[✓] Password entered: ****")
            
            # 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/final_filled_{timestamp}.png")
            print("\n[SCREENSHOT] Login form filled")
            
            # 6. 로그인 시도
            print("\n[STEP 6] Attempting login...")
            
            # Enter 키로 로그인
            await page.keyboard.press('Enter')
            print("[✓] Pressed Enter to submit")
            
            # 로그인 처리 대기
            print("[WAIT] Waiting for login response...")
            await page.wait_for_timeout(5000)
            
            # 7. 결과 확인
            print("\n[STEP 7] Checking login result...")
            
            current_url = page.url
            print(f"[URL] Current: {current_url}")
            
            # URL 변경 확인
            if current_url != "http://it.mek-ics.com/msm/":
                print("[✅] SUCCESS - URL changed, login successful!")
            else:
                print("[⚠️] URL unchanged - checking for other indicators...")
                
                # 페이지 내용 변경 확인
                page_content = await page.content()
                if 'dashboard' in page_content.lower() or 'welcome' in page_content.lower():
                    print("[✅] SUCCESS - Dashboard content detected!")
                else:
                    print("[❌] Login might have failed or needs different credentials")
            
            # 최종 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/final_result_{timestamp}.png")
            print(f"\n[SAVED] Screenshots in logs/screenshots/flutter/")
            
            # 8. 추가 검증
            print("\n[STEP 8] Additional verification...")
            
            # 현재 포커스된 요소 확인
            focused_element = await page.evaluate("() => document.activeElement?.tagName")
            print(f"[FOCUS] Current focused element: {focused_element}")
            
            # 숨겨진 input 필드 정보 수집
            inputs_info = await page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input');
                    return Array.from(inputs).map(input => ({
                        type: input.type,
                        value: input.value ? '***' : 'empty',
                        visible: input.offsetParent !== null
                    }));
                }
            """)
            
            if inputs_info:
                print(f"[INFO] Found {len(inputs_info)} input fields:")
                for i, info in enumerate(inputs_info):
                    print(f"  Input {i+1}: type={info['type']}, visible={info['visible']}")
            
            print("\n[INFO] Keeping browser open for verification...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

async def flutter_login_with_verification():
    """로그인 후 성공 여부 자동 확인"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("http://it.mek-ics.com/msm")
        await page.wait_for_timeout(5000)
        
        # 빠른 로그인
        await page.click('body')
        await page.keyboard.press('Tab')
        await page.keyboard.press('Tab')
        await page.keyboard.type('mdmtest')
        await page.keyboard.press('Tab')
        await page.keyboard.type('0001')
        await page.keyboard.press('Enter')
        
        # 로그인 성공 대기
        try:
            # URL 변경 대기 (5초)
            await page.wait_for_url("**/dashboard", timeout=5000)
            print("[✅] Login successful - Dashboard loaded!")
            return True
        except:
            # 또는 특정 요소 대기
            try:
                await page.wait_for_selector('text="Welcome"', timeout=2000)
                print("[✅] Login successful - Welcome message found!")
                return True
            except:
                print("[❌] Login failed or taking too long")
                return False
        finally:
            await browser.close()

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║     Flutter Login - Final Solution     ║
    ╠════════════════════════════════════════╣
    ║  Site: http://it.mek-ics.com/msm      ║
    ║  Method: Tab Navigation                ║
    ║  Credentials: mdmtest / 0001          ║
    ╚════════════════════════════════════════╝
    """)
    
    # 메인 테스트 실행
    asyncio.run(flutter_login_final())
    
    # 또는 빠른 검증 버전
    # asyncio.run(flutter_login_with_verification())
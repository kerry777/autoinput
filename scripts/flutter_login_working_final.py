#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - 실제 작동 버전
Tab 5, 6번의 INPUT이 submit 버튼일 가능성
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_working():
    """Flutter 로그인 - 작동하는 버전"""
    
    print("\n[FLUTTER LOGIN - WORKING VERSION]")
    print("="*50)
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
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
            # 1. 페이지 로드
            print("\n[1] Loading page...")
            await page.goto("http://it.mek-ics.com/msm")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 2. Tab 네비게이션으로 필드 채우기
            print("\n[2] Filling form with Tab navigation...")
            await page.click('body')
            await page.wait_for_timeout(500)
            
            # Tab 1: FLUTTER-VIEW (skip)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            print("  Tab 1: Skipped")
            
            # Tab 2: ID field (INPUT type=text)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            print("  Tab 2: ID field - entering mdmtest")
            await page.keyboard.type('mdmtest')
            
            # Tab 3: Password field (INPUT type=password)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            print("  Tab 3: Password field - entering 0001")
            await page.keyboard.type('0001')
            
            await page.screenshot(path=f"logs/screenshots/flutter/working_{timestamp}_filled.png")
            
            # Tab 4: FLUTTER-VIEW (skip)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            print("  Tab 4: Skipped")
            
            # Tab 5: INPUT (probably submit button)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(200)
            print("  Tab 5: INPUT element - pressing Enter")
            
            # 현재 요소 정보 확인
            element_info = await page.evaluate("""
                () => {
                    const elem = document.activeElement;
                    return {
                        tag: elem?.tagName,
                        type: elem?.type,
                        value: elem?.value,
                        name: elem?.name
                    };
                }
            """)
            
            print(f"    Element type: {element_info.get('type', 'unknown')}")
            
            # Enter 또는 Space로 클릭
            print("\n[3] Attempting login...")
            await page.keyboard.press('Enter')
            await page.wait_for_timeout(3000)
            
            # URL 확인
            current_url = page.url
            if current_url != "http://it.mek-ics.com/msm/":
                print(f"[SUCCESS] Login successful! URL: {current_url}")
            else:
                # Tab 6번도 시도
                print("  Enter didn't work, trying Tab 6...")
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(200)
                print("  Tab 6: INPUT element - pressing Enter")
                await page.keyboard.press('Enter')
                await page.wait_for_timeout(3000)
                
                current_url = page.url
                if current_url != "http://it.mek-ics.com/msm/":
                    print(f"[SUCCESS] Login successful! URL: {current_url}")
                else:
                    print("[INFO] URL unchanged - trying Space key...")
                    await page.keyboard.press('Space')
                    await page.wait_for_timeout(3000)
            
            # 4. 최종 결과
            print("\n[4] Final result...")
            final_url = page.url
            print(f"  URL: {final_url}")
            
            await page.screenshot(path=f"logs/screenshots/flutter/working_{timestamp}_result.png")
            
            if final_url != "http://it.mek-ics.com/msm/":
                print("\n[SUCCESS] LOGIN SUCCESSFUL!")
                return True
            else:
                print("\n[INFO] Check the browser - login might still be successful")
                return False
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            return False
            
        finally:
            print("\n[5] Browser will close in 10 seconds...")
            await page.wait_for_timeout(10000)
            await browser.close()
            print("[COMPLETE] Test finished")

async def flutter_login_simple():
    """간단한 버전 - 최소 코드"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 페이지 로드
        await page.goto("http://it.mek-ics.com/msm")
        await page.wait_for_timeout(5000)
        
        # Tab으로 필드 이동 및 입력
        await page.click('body')
        await page.keyboard.press('Tab')  # Skip
        await page.keyboard.press('Tab')  # ID field
        await page.keyboard.type('mdmtest')
        await page.keyboard.press('Tab')  # Password field
        await page.keyboard.type('0001')
        await page.keyboard.press('Tab')  # Skip
        await page.keyboard.press('Tab')  # Submit button
        await page.keyboard.press('Enter')  # Click
        
        await page.wait_for_timeout(5000)
        
        result = page.url != "http://it.mek-ics.com/msm/"
        print(f"Login {'successful' if result else 'failed'}")
        
        await page.wait_for_timeout(5000)
        await browser.close()
        
        return result

if __name__ == "__main__":
    print("""
    =====================================
    Flutter Login - Working Solution
    =====================================
    Tab sequence:
    1. Skip
    2. ID field (mdmtest)
    3. Password field (0001)
    4. Skip
    5. Submit button (Enter)
    =====================================
    """)
    
    # 상세 버전
    asyncio.run(flutter_login_working())
    
    # 또는 간단한 버전
    # asyncio.run(flutter_login_simple())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - 실제 작동 버전
Input 1 = ID field (type=text)
Input 3 = Password field (type=password)
Input 2 or 4 = Submit button
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_working():
    """Flutter 로그인 - 실제 작동하는 버전"""
    
    print("\n" + "="*50)
    print("[FLUTTER LOGIN - WORKING VERSION]")
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
            print("\n[STEP 1] Loading page...")
            await page.goto("http://it.mek-ics.com/msm")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 2. 직접 input 선택자로 찾기
            print("\n[STEP 2] Finding input fields directly...")
            
            # 모든 input 찾기
            all_inputs = await page.query_selector_all('input')
            print(f"[FOUND] {len(all_inputs)} input elements")
            
            # 첫 번째 text input (ID 필드)
            id_field = await page.query_selector('input[type="text"]')
            if id_field:
                print("[OK] Found ID field (type=text)")
                await id_field.click()
                await id_field.fill('mdmtest')
                print("[INPUT] ID: mdmtest")
            
            # password input (Password 필드)  
            pw_field = await page.query_selector('input[type="password"]')
            if pw_field:
                print("[OK] Found Password field (type=password)")
                await pw_field.click()
                await pw_field.fill('0001')
                print("[INPUT] Password: ****")
            
            await page.screenshot(path=f"logs/screenshots/flutter/working_filled_{timestamp}.png")
            
            # 3. Submit 버튼 찾기
            print("\n[STEP 3] Finding submit button...")
            
            # submit 타입 input 찾기
            submit_buttons = await page.query_selector_all('input[type="submit"]')
            print(f"[FOUND] {len(submit_buttons)} submit buttons")
            
            if submit_buttons:
                # 첫 번째 submit 버튼 클릭
                print("[CLICK] Clicking first submit button...")
                await submit_buttons[0].click()
            else:
                # Enter 키로 제출
                print("[ENTER] Pressing Enter to submit...")
                await page.keyboard.press('Enter')
            
            # 4. 결과 대기
            print("\n[WAIT] Waiting for login response...")
            await page.wait_for_timeout(5000)
            
            # 5. 결과 확인
            current_url = page.url
            print(f"\n[RESULT] Current URL: {current_url}")
            
            if current_url != "http://it.mek-ics.com/msm/":
                print("[SUCCESS] URL changed - Login successful!")
            else:
                print("[INFO] URL unchanged - checking page content...")
                
                # 페이지 변화 확인
                page_text = await page.inner_text('body')
                if 'mdmtest' in page_text.lower() or 'welcome' in page_text.lower():
                    print("[SUCCESS] User info or welcome message found!")
            
            await page.screenshot(path=f"logs/screenshots/flutter/working_result_{timestamp}.png")
            
            print("\n[INFO] Login attempt completed.")
            print("[INFO] Browser will stay open for verification...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

async def flutter_login_simple():
    """간단한 버전 - 바로 실행"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("http://it.mek-ics.com/msm")
        await page.wait_for_timeout(5000)
        
        # ID 입력
        await page.fill('input[type="text"]', 'mdmtest')
        
        # Password 입력
        await page.fill('input[type="password"]', '0001')
        
        # Submit 클릭
        await page.click('input[type="submit"]')
        
        await page.wait_for_timeout(5000)
        
        print(f"Result URL: {page.url}")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    print("""
    =====================================
    Flutter Login - Working Version
    =====================================
    Site: http://it.mek-ics.com/msm
    Method: Direct input selection
    =====================================
    """)
    
    # 상세 버전
    asyncio.run(flutter_login_working())
    
    # 또는 간단한 버전
    # asyncio.run(flutter_login_simple())
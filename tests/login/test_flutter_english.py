#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - 영어 placeholder
placeholder: id, password
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_english():
    """Flutter 로그인 - 영어 placeholder로 접근"""
    
    print("\n" + "="*50)
    print("[FLUTTER LOGIN - ENGLISH PLACEHOLDERS]")
    print("="*50)
    print("\nLooking for: placeholder='id', placeholder='password'")
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
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
            
            # 2. placeholder로 input 찾기
            print("\n[STEP 2] Finding inputs by placeholder...")
            
            # ID 필드 찾기 (placeholder="id")
            print("[SEARCH] Looking for input[placeholder='id']...")
            id_field = await page.query_selector('input[placeholder="id"]')
            if not id_field:
                id_field = await page.query_selector('input[placeholder="ID"]')
            
            if id_field:
                print("[OK] Found ID field!")
                await id_field.click()
                await id_field.fill('mdmtest')
                print("[INPUT] Entered: mdmtest")
            else:
                print("[!] ID field not found by placeholder")
            
            # Password 필드 찾기 (placeholder="password")
            print("\n[SEARCH] Looking for input[placeholder='password']...")
            pw_field = await page.query_selector('input[placeholder="password"]')
            if not pw_field:
                pw_field = await page.query_selector('input[placeholder="Password"]')
            if not pw_field:
                pw_field = await page.query_selector('input[type="password"]')
            
            if pw_field:
                print("[OK] Found Password field!")
                await pw_field.click()
                await pw_field.fill('0001')
                print("[INPUT] Entered: ****")
            else:
                print("[!] Password field not found by placeholder")
            
            # 3. 필드를 못 찾았으면 Tab 네비게이션
            if not id_field or not pw_field:
                print("\n[STEP 3] Using Tab navigation as fallback...")
                
                await page.click('body')
                
                # Tab으로 필드 찾기
                for i in range(10):
                    await page.keyboard.press('Tab')
                    await page.wait_for_timeout(200)
                    
                    # 현재 포커스된 요소 정보
                    focused = await page.evaluate("""
                        () => {
                            const elem = document.activeElement;
                            return {
                                tag: elem?.tagName,
                                type: elem?.type,
                                placeholder: elem?.placeholder,
                                value: elem?.value
                            };
                        }
                    """)
                    
                    if focused.get('placeholder') == 'id':
                        print(f"[TAB {i+1}] Found ID field!")
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type('mdmtest')
                    elif focused.get('placeholder') == 'password':
                        print(f"[TAB {i+1}] Found Password field!")
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type('0001')
                        break
                    elif focused.get('type') == 'password':
                        print(f"[TAB {i+1}] Found password type field!")
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type('0001')
                        break
            
            await page.screenshot(path=f"logs/screenshots/flutter/english_filled_{timestamp}.png")
            
            # 4. 로그인 버튼 찾기
            print("\n[STEP 4] Finding login button...")
            
            # 다양한 로그인 버튼 패턴
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'button:has-text("Submit")',
                '[role="button"]:has-text("Login")',
                'button'  # 모든 버튼
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible():
                            text = await button.inner_text() if button else ""
                            print(f"[FOUND] Button: {selector} - Text: '{text}'")
                            login_button = button
                            break
                    if login_button:
                        break
                except:
                    continue
            
            if login_button:
                print("[CLICK] Clicking login button...")
                await login_button.click()
            else:
                print("[ENTER] No button found, pressing Enter...")
                await page.keyboard.press('Enter')
            
            # 5. 결과 대기
            print("\n[WAIT] Waiting for login response...")
            await page.wait_for_timeout(5000)
            
            # 6. 결과 확인
            current_url = page.url
            print(f"\n[RESULT] Current URL: {current_url}")
            
            if current_url != "http://it.mek-ics.com/msm/":
                print("[SUCCESS] URL changed - Login successful!")
            
            await page.screenshot(path=f"logs/screenshots/flutter/english_result_{timestamp}.png")
            
            # 7. 디버깅 정보
            print("\n[DEBUG] Checking all inputs on page...")
            all_inputs = await page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input');
                    return Array.from(inputs).map(input => ({
                        type: input.type,
                        placeholder: input.placeholder,
                        name: input.name,
                        id: input.id,
                        visible: input.offsetParent !== null,
                        value: input.value ? 'has value' : 'empty'
                    }));
                }
            """)
            
            if all_inputs:
                print(f"Found {len(all_inputs)} input elements:")
                for i, inp in enumerate(all_inputs):
                    print(f"  Input {i+1}: placeholder='{inp['placeholder']}', type={inp['type']}, visible={inp['visible']}")
            
            print("\n[INFO] Browser will stay open for inspection...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    =====================================
    Flutter Login - English Placeholders
    =====================================
    Target: http://it.mek-ics.com/msm
    Placeholders: id, password
    Credentials: mdmtest / 0001
    =====================================
    """)
    
    asyncio.run(flutter_login_english())
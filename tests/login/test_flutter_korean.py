#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - 한글 placeholder와 로그인 버튼 찾기
placeholder: 아이디, 비밀번호
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_korean():
    """Flutter 로그인 - 한글 placeholder로 접근"""
    
    print("\n" + "="*50)
    print("[FLUTTER LOGIN - KOREAN PLACEHOLDERS]")
    print("="*50)
    print("\n🔍 Looking for: 아이디, 비밀번호, 로그인 버튼")
    
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
            
            # 2. 한글 placeholder로 input 찾기
            print("\n[STEP 2] Finding inputs with Korean placeholders...")
            
            # 아이디 필드 찾기
            id_selectors = [
                'input[placeholder="아이디"]',
                'input[placeholder*="아이디"]',
                '[aria-label="아이디"]',
                '[aria-label*="아이디"]',
                'input[name*="id"]',
                'input[type="text"]:not([type="password"])'
            ]
            
            id_field = None
            for selector in id_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        is_visible = await elem.is_visible()
                        print(f"[FOUND] ID field with: {selector} (visible: {is_visible})")
                        if is_visible:
                            id_field = elem
                            break
                except:
                    continue
            
            # 비밀번호 필드 찾기
            pw_selectors = [
                'input[placeholder="비밀번호"]',
                'input[placeholder*="비밀번호"]',
                '[aria-label="비밀번호"]',
                '[aria-label*="비밀번호"]',
                'input[type="password"]'
            ]
            
            pw_field = None
            for selector in pw_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        is_visible = await elem.is_visible()
                        print(f"[FOUND] Password field with: {selector} (visible: {is_visible})")
                        if is_visible:
                            pw_field = elem
                            break
                except:
                    continue
            
            # 3. 필드가 보이지 않으면 Tab으로 접근
            if not id_field or not await id_field.is_visible():
                print("\n[STEP 3] Fields not visible, trying Tab navigation...")
                
                # 페이지 포커스
                await page.click('body')
                
                # Tab으로 이동하면서 placeholder 확인
                for i in range(10):
                    await page.keyboard.press('Tab')
                    await page.wait_for_timeout(200)
                    
                    # 현재 포커스된 요소의 placeholder 확인
                    focused_info = await page.evaluate("""
                        () => {
                            const elem = document.activeElement;
                            return {
                                tag: elem?.tagName,
                                type: elem?.type,
                                placeholder: elem?.placeholder,
                                ariaLabel: elem?.getAttribute('aria-label'),
                                name: elem?.name
                            };
                        }
                    """)
                    
                    print(f"Tab {i+1}: {focused_info}")
                    
                    # 아이디 필드 찾음
                    if focused_info.get('placeholder') == '아이디' or \
                       focused_info.get('ariaLabel') == '아이디':
                        print("[✓] Found 아이디 field!")
                        await page.keyboard.type('mdmtest')
                        print("[INPUT] Entered: mdmtest")
                        
                    # 비밀번호 필드 찾음  
                    elif focused_info.get('placeholder') == '비밀번호' or \
                         focused_info.get('ariaLabel') == '비밀번호' or \
                         focused_info.get('type') == 'password':
                        print("[✓] Found 비밀번호 field!")
                        await page.keyboard.type('0001')
                        print("[INPUT] Entered: ****")
                        break
            
            else:
                # 4. 보이는 필드에 직접 입력
                print("\n[STEP 4] Filling visible fields...")
                
                if id_field:
                    await id_field.click()
                    await id_field.fill('mdmtest')
                    print("[✓] ID entered: mdmtest")
                
                if pw_field:
                    await pw_field.click()
                    await pw_field.fill('0001')
                    print("[✓] Password entered: ****")
            
            await page.screenshot(path=f"logs/screenshots/flutter/korean_filled_{timestamp}.png")
            
            # 5. 로그인 버튼 찾기
            print("\n[STEP 5] Finding 로그인 button...")
            
            login_button_selectors = [
                'button:has-text("로그인")',
                'button:text("로그인")',
                '[role="button"]:has-text("로그인")',
                'input[type="submit"][value="로그인"]',
                'button[type="submit"]',
                'a:has-text("로그인")',
                'div:has-text("로그인"):not(:has(*))',  # 텍스트만 있는 div
                'span:has-text("로그인")'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        print(f"[✓] Login button found: {selector}")
                        login_button = elem
                        break
                except:
                    continue
            
            # 6. 버튼이 없으면 텍스트로 찾기
            if not login_button:
                print("\n[ALTERNATIVE] Searching for 로그인 text...")
                
                # JavaScript로 로그인 텍스트 찾기
                login_elements = await page.evaluate("""
                    () => {
                        const elements = Array.from(document.querySelectorAll('*'));
                        const results = [];
                        
                        elements.forEach(elem => {
                            if (elem.textContent?.trim() === '로그인' && 
                                elem.children.length === 0) {
                                const rect = elem.getBoundingClientRect();
                                results.push({
                                    tag: elem.tagName,
                                    x: rect.x + rect.width / 2,
                                    y: rect.y + rect.height / 2,
                                    width: rect.width,
                                    height: rect.height
                                });
                            }
                        });
                        
                        return results;
                    }
                """)
                
                if login_elements:
                    print(f"[FOUND] {len(login_elements)} elements with 로그인 text")
                    # 첫 번째 요소 클릭
                    elem = login_elements[0]
                    await page.mouse.click(elem['x'], elem['y'])
                    print(f"[CLICK] Clicked at ({elem['x']}, {elem['y']})")
            
            else:
                # 7. 로그인 버튼 클릭
                print("\n[STEP 6] Clicking login button...")
                await login_button.click()
                print("[✓] Login button clicked")
            
            # Enter 키도 시도
            if not login_button and not login_elements:
                print("\n[FALLBACK] Pressing Enter...")
                await page.keyboard.press('Enter')
            
            # 8. 결과 대기
            print("\n[WAIT] Waiting for login response...")
            await page.wait_for_timeout(5000)
            
            # 9. 결과 확인
            current_url = page.url
            print(f"\n[RESULT] Current URL: {current_url}")
            
            await page.screenshot(path=f"logs/screenshots/flutter/korean_result_{timestamp}.png")
            
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
    ╔════════════════════════════════════════╗
    ║   Flutter Login - Korean Interface     ║
    ╠════════════════════════════════════════╣
    ║  Placeholders: 아이디, 비밀번호        ║
    ║  Button: 로그인                        ║
    ║  Credentials: mdmtest / 0001          ║
    ╚════════════════════════════════════════╝
    """)
    
    asyncio.run(flutter_login_korean())
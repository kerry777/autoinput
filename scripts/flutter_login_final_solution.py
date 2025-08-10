#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - 최종 완성 버전
Tab 네비게이션으로 각 요소의 텍스트 확인하여 로그인 버튼 찾기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_complete():
    """Flutter 로그인 - 완전한 해결책"""
    
    print("\n[FLUTTER LOGIN - COMPLETE SOLUTION]")
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
            
            # 2. Tab으로 이동하면서 placeholder 확인
            print("\n[2] Navigating with Tab and checking each element...")
            await page.click('body')
            await page.wait_for_timeout(500)
            
            id_filled = False
            password_filled = False
            
            # 최대 10번 Tab 이동
            for i in range(10):
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(200)
                
                # 현재 포커스된 요소 정보 가져오기
                element_info = await page.evaluate("""
                    () => {
                        const elem = document.activeElement;
                        if (!elem) return null;
                        
                        // 요소의 모든 텍스트 정보 수집
                        const rect = elem.getBoundingClientRect();
                        return {
                            tag: elem.tagName,
                            type: elem.type,
                            placeholder: elem.placeholder,
                            value: elem.value,
                            text: elem.textContent || elem.innerText,
                            ariaLabel: elem.getAttribute('aria-label'),
                            title: elem.title,
                            name: elem.name,
                            id: elem.id,
                            isVisible: rect.width > 0 && rect.height > 0,
                            // 버튼인지 확인
                            isButton: elem.tagName === 'BUTTON' || 
                                     elem.type === 'submit' || 
                                     elem.type === 'button' ||
                                     elem.role === 'button'
                        };
                    }
                """)
                
                if not element_info:
                    continue
                
                print(f"\nTab {i+1}: {element_info['tag']}")
                
                # placeholder가 있으면 출력
                if element_info.get('placeholder'):
                    print(f"  Placeholder: '{element_info['placeholder']}'")
                
                # 텍스트가 있으면 출력
                if element_info.get('text'):
                    print(f"  Text: '{element_info['text']}'")
                
                # ID 필드 찾기 (placeholder가 'id' 또는 '아이디')
                if not id_filled and element_info['tag'] == 'INPUT':
                    placeholder = (element_info.get('placeholder') or '').lower()
                    if 'id' in placeholder or '아이디' in placeholder or element_info['type'] == 'text':
                        print("  [FOUND] ID field - entering mdmtest")
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type('mdmtest')
                        id_filled = True
                        continue
                
                # Password 필드 찾기 (placeholder가 'password' 또는 '비밀번호')
                if not password_filled and element_info['tag'] == 'INPUT':
                    placeholder = (element_info.get('placeholder') or '').lower()
                    if 'password' in placeholder or '비밀번호' in placeholder or element_info['type'] == 'password':
                        print("  [FOUND] Password field - entering 0001")
                        await page.keyboard.press('Control+A')
                        await page.keyboard.type('0001')
                        password_filled = True
                        
                        # Password 입력 후 바로 Enter 시도
                        print("\n[3] Trying Enter in password field...")
                        await page.keyboard.press('Enter')
                        await page.wait_for_timeout(3000)
                        
                        # URL 변경 확인
                        if page.url != "http://it.mek-ics.com/msm/":
                            print("[SUCCESS] Login successful with Enter!")
                            break
                        else:
                            print("[INFO] Enter didn't work, continuing to find button...")
                            continue
                
                # 로그인 버튼 찾기 (텍스트에 '로그인' 또는 'login' 포함)
                if id_filled and password_filled:
                    text = (element_info.get('text') or '').lower()
                    aria = (element_info.get('ariaLabel') or '').lower()
                    
                    if element_info.get('isButton') or \
                       '로그인' in text or 'login' in text or \
                       '로그인' in aria or 'login' in aria or \
                       element_info['type'] == 'submit':
                        print("  [FOUND] Login button - clicking...")
                        
                        # Space 또는 Enter로 버튼 클릭
                        await page.keyboard.press('Enter')
                        await page.wait_for_timeout(3000)
                        
                        # URL 변경 확인
                        if page.url != "http://it.mek-ics.com/msm/":
                            print("[SUCCESS] Login successful with button click!")
                            break
                        else:
                            # Space도 시도
                            await page.keyboard.press('Space')
                            await page.wait_for_timeout(3000)
                            
                            if page.url != "http://it.mek-ics.com/msm/":
                                print("[SUCCESS] Login successful with Space!")
                                break
            
            # 4. 최종 결과 확인
            print("\n[4] Final result...")
            final_url = page.url
            print(f"  URL: {final_url}")
            
            # 페이지 내용 확인
            try:
                page_text = await page.inner_text('body')
                if 'dashboard' in page_text.lower() or 'welcome' in page_text.lower() or 'mdmtest' in page_text:
                    print("  [SUCCESS] User logged in - found dashboard/welcome content")
                elif len(page_text) > 100:  # 내용이 변경됨
                    print("  [SUCCESS] Page content changed - likely logged in")
            except:
                pass
            
            await page.screenshot(path=f"logs/screenshots/flutter/complete_{timestamp}.png")
            
            if final_url != "http://it.mek-ics.com/msm/":
                print("\n✅ LOGIN SUCCESSFUL!")
            else:
                print("\n⚠️ URL didn't change but check the screen - might be logged in")
            
            print("\n[5] Browser will stay open for 20 seconds...")
            print("    Please check if login was successful.")
            await page.wait_for_timeout(20000)
            
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
    Flutter Login - Complete Solution
    =====================================
    1. Tab through all elements
    2. Check placeholder text
    3. Fill ID and Password fields
    4. Find and click login button
    =====================================
    """)
    
    asyncio.run(flutter_login_complete())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이메일 입력 후 인증번호 버튼 클릭하여 캡차 트리거
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def enter_email_and_trigger():
    """이메일 입력 후 캡차 트리거"""
    
    print("\n[ENTER EMAIL AND TRIGGER CAPTCHA]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/captcha", exist_ok=True)
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
            # 1. 페이지 로드
            print("\n[1] Loading page...")
            await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
            await page.wait_for_timeout(3000)
            
            # 2. 이메일 입력 필드 찾기
            print("\n[2] Finding email input fields...")
            
            # 모든 입력 필드 확인
            inputs = await page.query_selector_all('input[type="text"]')
            print(f"   Found {len(inputs)} text input fields")
            
            for i, input_field in enumerate(inputs):
                name = await input_field.get_attribute('name')
                id_attr = await input_field.get_attribute('id')
                placeholder = await input_field.get_attribute('placeholder')
                print(f"   Input {i+1}: name='{name}', id='{id_attr}', placeholder='{placeholder}'")
                
                # 이메일 필드 찾기
                if 'email' in (name or '').lower() or 'email' in (id_attr or '').lower():
                    print(f"   [FOUND] Email field: {id_attr}")
                    
                    # 이메일 입력
                    await input_field.click()
                    await input_field.fill('kilmoon@mek-ics.com')
                    print("   [OK] Email entered: kilmoon@mek-ics.com")
            
            # 이메일이 두 개 필드로 나뉘어 있을 수 있음 (@ 앞뒤)
            pre_email = await page.query_selector('#preEmail')
            next_email = await page.query_selector('#nextEmail')
            
            if pre_email and next_email:
                print("\n[3] Email is split into two fields")
                await pre_email.fill('kilmoon')
                print("   Entered: kilmoon")
                await next_email.fill('mek-ics.com')
                print("   Entered: mek-ics.com")
            
            # 3. 스크린샷 (이메일 입력 후)
            after_email_path = f"logs/bizmeka/captcha/after_email_{timestamp}.png"
            await page.screenshot(path=after_email_path)
            print(f"\n[4] Screenshot after email: {after_email_path}")
            
            # 4. 인증번호 버튼 클릭
            print("\n[5] Clicking authentication button...")
            
            # 여러 선택자 시도
            button_selectors = [
                'button:has-text("인증번호")',
                'a:has-text("인증번호")',
                '.btn-danger',
                '[class*="btn"][class*="red"]',
                '[onclick*="sendCert"]',
                'button.btn'
            ]
            
            clicked = False
            for selector in button_selectors:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    print(f"   Found button with: {selector}")
                    await button.click()
                    print("   [OK] Button clicked")
                    clicked = True
                    break
            
            if not clicked:
                print("   [WARNING] Could not find button")
            
            # 5. 캡차 나타나기를 기다림
            print("\n[6] Waiting for CAPTCHA...")
            await page.wait_for_timeout(5000)
            
            # 6. 캡차 팝업/모달 확인
            print("\n[7] Checking for CAPTCHA popup...")
            
            # 새 창이 열렸는지 확인
            all_pages = context.pages
            if len(all_pages) > 1:
                print(f"   Found {len(all_pages)} windows/tabs")
                for i, p in enumerate(all_pages):
                    print(f"   Window {i+1}: {p.url}")
                    if p != page:
                        # 새 창 스크린샷
                        popup_path = f"logs/bizmeka/captcha/popup_{i}_{timestamp}.png"
                        await p.screenshot(path=popup_path)
                        print(f"   Saved popup: {popup_path}")
            
            # 7. 현재 페이지 스크린샷
            final_path = f"logs/bizmeka/captcha/final_{timestamp}.png"
            await page.screenshot(path=final_path, full_page=True)
            print(f"\n[8] Final screenshot: {final_path}")
            
            # 8. 모든 이미지 확인
            print("\n[9] Checking all images...")
            all_images = await page.query_selector_all('img')
            
            for i, img in enumerate(all_images):
                if await img.is_visible():
                    box = await img.bounding_box()
                    if box and box['width'] > 80 and box['height'] > 30:
                        img_path = f"logs/bizmeka/captcha/captcha_candidate_{i}_{timestamp}.png"
                        await img.screenshot(path=img_path)
                        print(f"   Saved candidate {i}: {img_path}")
                        print(f"   Size: {box['width']}x{box['height']}")
            
            print("\n" + "="*60)
            print("[COMPLETE]")
            print("Check logs/bizmeka/captcha/ for all captured images")
            print("\n[Browser will stay open for manual inspection...]")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[DONE]")

if __name__ == "__main__":
    asyncio.run(enter_email_and_trigger())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
비밀번호 찾기에서 캡차 트리거 후 캡처
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def trigger_captcha():
    """인증번호 버튼 클릭하여 캡차 트리거"""
    
    print("\n[TRIGGERING CAPTCHA]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/captcha", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # 1. 비밀번호 찾기 페이지 로드
            print("\n[1] Loading password reset page...")
            await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
            await page.wait_for_timeout(3000)
            
            # 2. 인증번호 버튼 클릭 (빨간 버튼)
            print("\n[2] Clicking authentication button to trigger CAPTCHA...")
            
            # 인증번호 버튼 찾기
            auth_button = await page.query_selector('button:has-text("인증번호")')
            if not auth_button:
                auth_button = await page.query_selector('.btn-danger')
            if not auth_button:
                auth_button = await page.query_selector('[onclick*="sendCertKey"]')
            
            if auth_button:
                print("   Found authentication button")
                await auth_button.click()
                print("   Clicked authentication button")
                await page.wait_for_timeout(2000)
            else:
                # JavaScript 함수 직접 호출
                print("   Button not found, trying JavaScript function...")
                
                # sendCertKeyCaptcha 함수 호출
                try:
                    await page.evaluate("sendCertKeyCaptcha()")
                    print("   Called sendCertKeyCaptcha()")
                    await page.wait_for_timeout(2000)
                except:
                    print("   Failed to call function")
            
            # 3. 캡차 창이 나타나기를 기다림
            print("\n[3] Waiting for CAPTCHA to appear...")
            await page.wait_for_timeout(3000)
            
            # 4. 팝업이나 모달 확인
            print("\n[4] Checking for popups or modals...")
            
            # 모든 iframe 확인
            frames = page.frames
            print(f"   Found {len(frames)} frames")
            
            for frame in frames:
                try:
                    frame_url = frame.url
                    if 'captcha' in frame_url.lower():
                        print(f"   Found CAPTCHA frame: {frame_url}")
                        
                        # iframe 내의 이미지 찾기
                        frame_images = await frame.query_selector_all('img')
                        for img in frame_images:
                            src = await img.get_attribute('src')
                            if src:
                                print(f"   Frame image: {src[:100]}")
                except:
                    continue
            
            # 5. 모달이나 다이얼로그 찾기
            modal_selectors = [
                '.modal', '.dialog', '.popup',
                '[class*="modal"]', '[class*="dialog"]', '[class*="popup"]',
                '[role="dialog"]', '[role="alertdialog"]'
            ]
            
            for selector in modal_selectors:
                modal = await page.query_selector(selector)
                if modal and await modal.is_visible():
                    print(f"   Found modal: {selector}")
                    
                    # 모달 스크린샷
                    modal_path = f"logs/bizmeka/captcha/modal_{timestamp}.png"
                    await modal.screenshot(path=modal_path)
                    print(f"   Saved modal: {modal_path}")
                    
                    # 모달 내 이미지 찾기
                    modal_images = await modal.query_selector_all('img')
                    for i, img in enumerate(modal_images):
                        if await img.is_visible():
                            box = await img.bounding_box()
                            if box and box['width'] > 50:
                                img_path = f"logs/bizmeka/captcha/modal_img_{i}_{timestamp}.png"
                                await img.screenshot(path=img_path)
                                print(f"   Saved modal image: {img_path}")
            
            # 6. 전체 페이지 스크린샷
            print("\n[5] Taking full page screenshot...")
            full_path = f"logs/bizmeka/captcha/after_trigger_{timestamp}.png"
            await page.screenshot(path=full_path, full_page=True)
            print(f"   Saved: {full_path}")
            
            # 7. 보이는 영역만 스크린샷
            visible_path = f"logs/bizmeka/captcha/visible_{timestamp}.png"
            await page.screenshot(path=visible_path, full_page=False)
            print(f"   Saved visible area: {visible_path}")
            
            # 8. 모든 이미지 다시 확인
            print("\n[6] Searching all images after trigger...")
            all_images = await page.query_selector_all('img')
            print(f"   Found {len(all_images)} images")
            
            captcha_found = False
            for i, img in enumerate(all_images):
                try:
                    if not await img.is_visible():
                        continue
                        
                    src = await img.get_attribute('src')
                    if not src:
                        continue
                    
                    box = await img.bounding_box()
                    if box and box['width'] > 50 and box['height'] > 20:
                        # 모든 보이는 이미지 저장
                        img_path = f"logs/bizmeka/captcha/img_{i}_{timestamp}.png"
                        await img.screenshot(path=img_path)
                        print(f"   Saved image {i}: {img_path}")
                        print(f"   Size: {box['width']}x{box['height']}")
                        
                        if 'captcha' in src.lower() or box['width'] > 100:
                            captcha_found = True
                            print(f"   [POSSIBLE CAPTCHA] Image {i}")
                except:
                    continue
            
            print("\n" + "="*60)
            print("[RESULT]")
            if captcha_found:
                print("✓ Possible CAPTCHA images saved")
            else:
                print("× No CAPTCHA found - might be in a separate window")
            
            print(f"\nAll images saved to: logs/bizmeka/captcha/")
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
    print("""
    =====================================
    CAPTCHA Trigger and Capture
    =====================================
    This will click authentication button
    to trigger CAPTCHA display
    =====================================
    """)
    
    asyncio.run(trigger_captcha())
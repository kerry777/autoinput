#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
현재 비밀번호 찾기 페이지의 캡차 캡처 및 분석
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def capture_captcha_now():
    """휴대폰 인증 화면의 캡차 이미지 캡처"""
    
    print("\n[CAPTURING CURRENT CAPTCHA]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/captcha", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # 비밀번호 찾기 페이지로 이동
            print("\n[1] Loading password reset page...")
            await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
            await page.wait_for_timeout(3000)
            
            # 전체 페이지 스크린샷
            full_path = f"logs/bizmeka/captcha/full_{timestamp}.png"
            await page.screenshot(path=full_path, full_page=True)
            print(f"   Saved full page: {full_path}")
            
            # 모든 이미지 찾기
            print("\n[2] Searching for CAPTCHA images...")
            all_images = await page.query_selector_all('img')
            print(f"   Found {len(all_images)} images")
            
            captcha_candidates = []
            
            for i, img in enumerate(all_images):
                try:
                    src = await img.get_attribute('src')
                    if not src:
                        continue
                        
                    alt = await img.get_attribute('alt') or ""
                    id_attr = await img.get_attribute('id') or ""
                    is_visible = await img.is_visible()
                    
                    # 캡차 가능성이 있는 이미지
                    is_captcha = False
                    if 'captcha' in src.lower() or 'captcha' in alt.lower() or 'captcha' in id_attr.lower():
                        is_captcha = True
                    elif '/captcha' in src or '/Captcha' in src:
                        is_captcha = True
                    elif 'cert' in src.lower() and 'logo' not in src.lower():
                        is_captcha = True
                    elif src.startswith('data:image') and is_visible:
                        # Base64 이미지도 체크
                        box = await img.bounding_box()
                        if box and box['width'] > 50 and box['height'] > 20:
                            is_captcha = True
                    
                    if is_captcha and is_visible:
                        box = await img.bounding_box()
                        if box:
                            print(f"\n   [CAPTCHA {i+1}] Found potential CAPTCHA")
                            print(f"   - Source: {src[:100]}...")
                            print(f"   - Size: {box['width']}x{box['height']}")
                            print(f"   - Position: ({box['x']}, {box['y']})")
                            
                            # 캡차 이미지 저장
                            captcha_path = f"logs/bizmeka/captcha/captcha_{i}_{timestamp}.png"
                            await img.screenshot(path=captcha_path)
                            print(f"   - Saved: {captcha_path}")
                            
                            captcha_candidates.append({
                                'element': img,
                                'path': captcha_path,
                                'src': src,
                                'size': (box['width'], box['height'])
                            })
                
                except Exception as e:
                    continue
            
            # 가장 가능성 높은 캡차 찾기
            if captcha_candidates:
                # 일반적인 캡차 크기 (너비 100-300, 높이 30-100)
                best_captcha = None
                for candidate in captcha_candidates:
                    width, height = candidate['size']
                    if 80 <= width <= 400 and 20 <= height <= 150:
                        best_captcha = candidate
                        break
                
                if not best_captcha and captcha_candidates:
                    best_captcha = captcha_candidates[0]
                
                if best_captcha:
                    print(f"\n[3] PRIMARY CAPTCHA IDENTIFIED")
                    print(f"   Image: {best_captcha['path']}")
                    print(f"   Size: {best_captcha['size'][0]}x{best_captcha['size'][1]}")
            
            # JavaScript로 캡차 관련 정보 찾기
            print("\n[4] Checking JavaScript functions...")
            
            captcha_info = await page.evaluate("""
                () => {
                    // 캡차 관련 함수 찾기
                    const funcs = [];
                    for (let key in window) {
                        if (key.toLowerCase().includes('captcha') || 
                            key.toLowerCase().includes('cert')) {
                            funcs.push(key);
                        }
                    }
                    
                    // 캡차 입력 필드 찾기
                    const inputs = document.querySelectorAll('input[type="text"]');
                    const captchaInputs = [];
                    inputs.forEach(input => {
                        const name = input.name || '';
                        const id = input.id || '';
                        const placeholder = input.placeholder || '';
                        if (name.includes('captcha') || id.includes('captcha') || 
                            placeholder.includes('문자') || placeholder.includes('입력')) {
                            captchaInputs.push({
                                name: name,
                                id: id,
                                placeholder: placeholder
                            });
                        }
                    });
                    
                    return {
                        functions: funcs,
                        inputs: captchaInputs
                    };
                }
            """)
            
            if captcha_info['functions']:
                print(f"   Functions: {captcha_info['functions']}")
            
            if captcha_info['inputs']:
                print(f"   Input fields: {captcha_info['inputs']}")
            
            # 캡차 새로고침 버튼 찾기
            refresh_button = await page.query_selector('[onclick*="captcha"], [onclick*="Captcha"], [onclick*="cert"]')
            if refresh_button:
                print("\n[5] Found CAPTCHA refresh button")
                onclick = await refresh_button.get_attribute('onclick')
                print(f"   onclick: {onclick}")
            
            print("\n" + "="*60)
            print("[RESULT]")
            print("="*60)
            
            if captcha_candidates:
                print(f"✓ Found {len(captcha_candidates)} CAPTCHA image(s)")
                print(f"✓ Images saved to: logs/bizmeka/captcha/")
                print("\n[NOTE] I can capture CAPTCHA images but cannot read the text.")
                print("The images are saved for your manual review.")
                
                # 캡차 이미지 정보 표시
                print("\n[CAPTCHA FILES]")
                for i, candidate in enumerate(captcha_candidates, 1):
                    print(f"   {i}. {candidate['path']}")
                    print(f"      Size: {candidate['size'][0]}x{candidate['size'][1]} pixels")
            else:
                print("× No CAPTCHA images found")
                print("× The page might still be loading or CAPTCHA is dynamically generated")
            
            print("\n[Browser will remain open for 30 seconds...]")
            print("Please check the CAPTCHA manually in the browser")
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
    CAPTCHA Capture Tool
    =====================================
    This will capture CAPTCHA from:
    https://www.bizmeka.com/find/findPasswordCertTypeView.do
    =====================================
    """)
    
    asyncio.run(capture_captcha_now())
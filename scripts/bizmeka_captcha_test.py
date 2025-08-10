#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 캡차(CAPTCHA) 테스트
비밀번호 찾기 페이지의 캡차 분석 및 처리
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import base64

async def test_captcha():
    """캡차 분석 및 테스트"""
    
    print("\n[CAPTCHA TEST]")
    print("="*60)
    print("URL: https://www.bizmeka.com/find/findPasswordCertTypeView.do")
    print("="*60)
    
    os.makedirs("logs/captcha", exist_ok=True)
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
            print("\n[STEP 1] Loading page...")
            await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do", 
                          wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(3000)
            print("   [OK] Page loaded")
            
            # 전체 페이지 스크린샷
            await page.screenshot(path=f"logs/captcha/01_page_{timestamp}.png", full_page=True)
            print("   [SCREENSHOT] Full page saved")
            
            # 2. 캡차 이미지 찾기
            print("\n[STEP 2] Finding CAPTCHA image...")
            
            # 일반적인 캡차 이미지 선택자들
            captcha_selectors = [
                'img[id*="captcha"]',
                'img[class*="captcha"]',
                'img[src*="captcha"]',
                'img[alt*="captcha"]',
                '#captchaImage',
                '.captcha-image',
                'img[src*="Captcha"]',
                'img[src*="CAPTCHA"]',
                '[id*="captcha"] img',
                '[class*="captcha"] img'
            ]
            
            captcha_img = None
            captcha_selector_used = None
            
            for selector in captcha_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        captcha_img = elem
                        captcha_selector_used = selector
                        print(f"   [FOUND] CAPTCHA image: {selector}")
                        break
                except:
                    continue
            
            if not captcha_img:
                # 모든 이미지 찾기
                print("   [INFO] Searching all images...")
                all_images = await page.query_selector_all('img')
                print(f"   Found {len(all_images)} images total")
                
                for i, img in enumerate(all_images):
                    try:
                        src = await img.get_attribute('src')
                        alt = await img.get_attribute('alt')
                        id_attr = await img.get_attribute('id')
                        class_attr = await img.get_attribute('class')
                        
                        if await img.is_visible():
                            print(f"\n   Image {i+1}:")
                            print(f"     src: {src[:50] if src else 'None'}...")
                            print(f"     alt: {alt}")
                            print(f"     id: {id_attr}")
                            print(f"     class: {class_attr}")
                            
                            # 캡차일 가능성이 있는 이미지
                            if src and ('captcha' in src.lower() or 
                                       'verify' in src.lower() or
                                       'code' in src.lower() or
                                       'image' in src.lower() and 'logo' not in src.lower()):
                                captcha_img = img
                                print(f"     [POSSIBLE] This might be CAPTCHA")
                    except:
                        continue
            
            # 3. 캡차 이미지 캡처
            if captcha_img:
                print("\n[STEP 3] Capturing CAPTCHA image...")
                
                # 캡차 이미지의 위치와 크기
                box = await captcha_img.bounding_box()
                if box:
                    print(f"   Position: ({box['x']}, {box['y']})")
                    print(f"   Size: {box['width']}x{box['height']}")
                    
                    # 캡차 이미지만 스크린샷
                    await captcha_img.screenshot(path=f"logs/captcha/02_captcha_{timestamp}.png")
                    print(f"   [SAVED] CAPTCHA image: logs/captcha/02_captcha_{timestamp}.png")
                
                # src 속성 확인
                src = await captcha_img.get_attribute('src')
                if src:
                    print(f"   Image source: {src[:100]}...")
                    
                    # base64 이미지인 경우
                    if src.startswith('data:image'):
                        print("   [INFO] Base64 encoded image detected")
            
            # 4. 캡차 입력 필드 찾기
            print("\n[STEP 4] Finding CAPTCHA input field...")
            
            input_selectors = [
                'input[name*="captcha"]',
                'input[id*="captcha"]',
                'input[placeholder*="문자"]',
                'input[placeholder*="입력"]',
                'input[placeholder*="code"]',
                'input[type="text"][name*="code"]',
                '#captchaInput',
                '.captcha-input'
            ]
            
            captcha_input = None
            for selector in input_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        captcha_input = elem
                        print(f"   [FOUND] CAPTCHA input: {selector}")
                        
                        # 입력 필드 정보
                        attrs = await elem.evaluate("""
                            (el) => ({
                                name: el.name,
                                id: el.id,
                                placeholder: el.placeholder,
                                maxLength: el.maxLength
                            })
                        """)
                        print(f"   Attributes: {attrs}")
                        break
                except:
                    continue
            
            # 5. 새로고침 버튼 찾기
            print("\n[STEP 5] Finding refresh button...")
            
            refresh_selectors = [
                'button[onclick*="captcha"]',
                'a[onclick*="captcha"]',
                'img[onclick*="refresh"]',
                '[onclick*="reload"]',
                '[onclick*="새로"]',
                '[title*="새로"]',
                '[alt*="새로"]'
            ]
            
            for selector in refresh_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        print(f"   [FOUND] Refresh button: {selector}")
                        break
                except:
                    continue
            
            # 6. JavaScript 함수 찾기
            print("\n[STEP 6] Finding JavaScript functions...")
            
            js_functions = await page.evaluate("""
                () => {
                    const funcs = [];
                    for (let key in window) {
                        if (key.toLowerCase().includes('captcha') || 
                            key.toLowerCase().includes('refresh') ||
                            key.toLowerCase().includes('reload')) {
                            if (typeof window[key] === 'function') {
                                funcs.push(key);
                            }
                        }
                    }
                    return funcs;
                }
            """)
            
            if js_functions:
                print(f"   Found functions: {js_functions}")
            
            # 7. 캡차 처리 방법
            print("\n[STEP 7] CAPTCHA handling methods...")
            
            print("\n   Manual methods:")
            print("   1. Screenshot the CAPTCHA image")
            print("   2. Manually read the text")
            print("   3. Enter the text in input field")
            
            print("\n   Automated methods:")
            print("   1. OCR (Optical Character Recognition)")
            print("   2. 2Captcha/Anti-Captcha API services")
            print("   3. Machine Learning models")
            
            # 8. 테스트 입력
            if captcha_input:
                print("\n[STEP 8] Testing CAPTCHA input...")
                await captcha_input.click()
                await captcha_input.fill("TEST123")
                print("   [OK] Test text entered: TEST123")
                
                await page.screenshot(path=f"logs/captcha/03_with_input_{timestamp}.png")
                print("   [SCREENSHOT] With test input saved")
            
            # 9. 페이지 분석 결과
            print("\n" + "="*60)
            print("[ANALYSIS RESULT]")
            print("="*60)
            
            if captcha_img:
                print("   [OK] CAPTCHA image found and captured")
            else:
                print("   [!] CAPTCHA image not found - might be dynamically loaded")
            
            if captcha_input:
                print("   [OK] CAPTCHA input field found")
            else:
                print("   [!] CAPTCHA input field not found")
            
            print("\n[RECOMMENDATIONS]")
            print("   1. Check screenshots in logs/captcha/")
            print("   2. For automation, consider:")
            print("      - pytesseract for OCR")
            print("      - 2captcha API for solving")
            print("      - Manual intervention for critical operations")
            
            print("\n[Browser will stay open for 30 seconds...]")
            print("Please check the CAPTCHA manually in the browser")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[DONE] Test complete")

async def solve_captcha_with_ocr():
    """OCR을 사용한 캡차 해결 시도 (추가 라이브러리 필요)"""
    
    print("\n[OCR CAPTCHA SOLVER]")
    print("This would require:")
    print("1. pip install pytesseract pillow")
    print("2. Install Tesseract-OCR software")
    print("3. Process the CAPTCHA image with OCR")
    
    # 예시 코드 (실제 실행하려면 라이브러리 설치 필요)
    """
    from PIL import Image
    import pytesseract
    
    # 캡차 이미지 로드
    img = Image.open('logs/captcha/02_captcha_*.png')
    
    # 이미지 전처리 (흑백 변환, 노이즈 제거 등)
    img = img.convert('L')  # 그레이스케일
    
    # OCR 실행
    text = pytesseract.image_to_string(img, config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    print(f"Recognized text: {text}")
    """

if __name__ == "__main__":
    print("""
    =====================================
    CAPTCHA Test & Analysis
    =====================================
    This will analyze CAPTCHA on:
    https://www.bizmeka.com/find/findPasswordCertTypeView.do
    =====================================
    """)
    
    asyncio.run(test_captcha())
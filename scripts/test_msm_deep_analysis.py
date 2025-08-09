#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MSM 사이트 심층 분석 - iframe, shadow DOM 등 체크
URL: http://it.mek-ics.com/msm
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def deep_analyze_msm():
    """MSM 사이트 심층 구조 분석"""
    
    print("\n" + "="*50)
    print("[MSM DEEP ANALYSIS]")
    print("="*50)
    
    os.makedirs("logs/screenshots/msm", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # 콘솔 메시지 캡처
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))
        
        try:
            print("\n[STEP 1] Loading page...")
            await page.goto("http://it.mek-ics.com/msm", wait_until='domcontentloaded')
            await page.wait_for_timeout(3000)  # 충분한 로딩 시간
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. 페이지 타이틀 확인
            title = await page.title()
            print(f"\n[PAGE] Title: {title}")
            
            # 2. 현재 URL 확인
            current_url = page.url
            print(f"[PAGE] URL: {current_url}")
            
            # 3. iframe 확인
            print("\n[IFRAME] Checking for iframes...")
            iframes = page.frames
            print(f"[IFRAME] Found {len(iframes)} frames")
            
            for i, frame in enumerate(iframes):
                frame_url = frame.url
                frame_name = frame.name
                print(f"  Frame {i}: URL={frame_url}, Name={frame_name}")
                
                # 각 iframe 내부의 input 찾기
                if i > 0:  # 메인 프레임 제외
                    try:
                        inputs = await frame.query_selector_all('input')
                        print(f"    - Input fields in frame: {len(inputs)}")
                        
                        if inputs:
                            for j, inp in enumerate(inputs[:5]):  # 처음 5개만
                                inp_type = await inp.get_attribute('type')
                                inp_name = await inp.get_attribute('name')
                                inp_id = await inp.get_attribute('id')
                                print(f"      Input {j+1}: type={inp_type}, name={inp_name}, id={inp_id}")
                    except:
                        print(f"    - Could not access frame content")
            
            # 4. 모든 forms 찾기
            print("\n[FORMS] Looking for forms...")
            forms = await page.query_selector_all('form')
            print(f"[FORMS] Found {len(forms)} forms in main page")
            
            # 5. 버튼과 링크 찾기
            print("\n[BUTTONS] Looking for clickable elements...")
            buttons = await page.query_selector_all('button, input[type="button"], input[type="submit"], a')
            print(f"[BUTTONS] Found {len(buttons)} clickable elements")
            
            # 로그인 관련 텍스트가 있는 요소 찾기
            for btn in buttons[:10]:  # 처음 10개만
                text = await btn.text_content()
                if text and ('로그인' in text.lower() or 'login' in text.lower() or 'sign' in text.lower()):
                    btn_tag = await btn.evaluate('el => el.tagName')
                    print(f"  - Potential login element: <{btn_tag}> {text.strip()}")
            
            # 6. JavaScript로 직접 탐색
            print("\n[JS] Direct JavaScript exploration...")
            
            # 모든 input 요소 찾기 (shadow DOM 포함)
            all_inputs = await page.evaluate('''() => {
                const inputs = [];
                const searchShadowDOM = (root) => {
                    root.querySelectorAll('*').forEach(el => {
                        if (el.shadowRoot) {
                            searchShadowDOM(el.shadowRoot);
                        }
                    });
                    root.querySelectorAll('input').forEach(input => {
                        inputs.push({
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            placeholder: input.placeholder,
                            visible: input.offsetParent !== null
                        });
                    });
                };
                searchShadowDOM(document);
                return inputs;
            }''')
            
            print(f"[JS] Found {len(all_inputs)} input elements via JavaScript")
            for inp in all_inputs:
                print(f"  - Input: type={inp['type']}, name={inp['name']}, id={inp['id']}, visible={inp['visible']}")
            
            # 7. 특정 ID/Class 시도
            print("\n[SELECTORS] Trying common login selectors...")
            common_selectors = [
                '#userId', '#userPw', '#loginId', '#loginPw',
                '.login-id', '.login-pw', '.login-input',
                'input[name="userId"]', 'input[name="userPw"]',
                'input[name="id"]', 'input[name="pw"]'
            ]
            
            for selector in common_selectors:
                elem = await page.query_selector(selector)
                if elem:
                    is_visible = await elem.is_visible()
                    print(f"  [FOUND] {selector} - Visible: {is_visible}")
            
            # 8. 페이지 소스 일부 확인
            print("\n[HTML] Checking page source structure...")
            body_html = await page.content()
            
            # 로그인 관련 키워드 검색
            login_keywords = ['login', 'Login', '로그인', 'userId', 'password', 'form']
            for keyword in login_keywords:
                if keyword in body_html:
                    print(f"  - Found keyword: '{keyword}' in page source")
            
            # 스크린샷 저장
            await page.screenshot(path=f"logs/screenshots/msm/deep_analysis_{timestamp}.png", full_page=True)
            print(f"\n[SCREENSHOT] Saved: logs/screenshots/msm/deep_analysis_{timestamp}.png")
            
            print("\n[WAIT] Keeping browser open for manual inspection...")
            print("You can now manually check the page structure...")
            await page.wait_for_timeout(20000)  # 20초 대기
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Analysis finished")

if __name__ == "__main__":
    print("""
    ============================================
         MSM Site Deep Analysis
    ============================================
    Checking: iframes, forms, shadow DOM, etc.
    ============================================
    """)
    
    asyncio.run(deep_analyze_msm())
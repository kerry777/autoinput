#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka SSO 로그인 페이지 상세 분석
https://ezsso.bizmeka.com/loginForm.do
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json
import os

async def analyze_bizmeka_login():
    """Bizmeka 로그인 페이지 완전 분석"""
    
    print("\n" + "="*60)
    print("[BIZMEKA SSO LOGIN PAGE ANALYSIS]")
    print("="*60)
    print("URL: https://ezsso.bizmeka.com/loginForm.do")
    print("="*60)
    
    os.makedirs("logs/bizmeka", exist_ok=True)
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
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_load_state('networkidle')
            print("[OK] Page loaded")
            
            # 스크린샷 저장
            await page.screenshot(path=f"logs/bizmeka/page_{timestamp}.png")
            
            # 2. 모든 input 요소 분석
            print("\n[STEP 2] Analyzing all input elements...")
            inputs = await page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input');
                    return Array.from(inputs).map(input => ({
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        className: input.className,
                        value: input.value,
                        visible: input.offsetParent !== null,
                        required: input.required,
                        autocomplete: input.autocomplete
                    }));
                }
            """)
            
            print(f"Found {len(inputs)} input elements:")
            for i, inp in enumerate(inputs):
                if inp['visible']:
                    print(f"\n  Input {i+1}:")
                    print(f"    - Type: {inp['type']}")
                    print(f"    - Name: {inp['name']}")
                    print(f"    - ID: {inp['id']}")
                    print(f"    - Placeholder: {inp['placeholder']}")
                    print(f"    - Class: {inp['className']}")
            
            # 3. 로그인 관련 요소 찾기
            print("\n[STEP 3] Finding login-specific elements...")
            
            # ID 필드 찾기
            id_selectors = [
                'input[type="text"]',
                'input[name*="id"]',
                'input[name*="user"]',
                'input[name*="login"]',
                'input[id*="id"]',
                'input[id*="user"]',
                'input[placeholder*="아이디"]',
                'input[placeholder*="ID"]'
            ]
            
            id_field = None
            for selector in id_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem and await elem.is_visible():
                        id_field = elem
                        print(f"[OK] ID field found: {selector}")
                        
                        # 속성 가져오기
                        attrs = await elem.evaluate("""
                            (el) => ({
                                name: el.name,
                                id: el.id,
                                placeholder: el.placeholder
                            })
                        """)
                        print(f"    Attributes: {attrs}")
                        break
                except:
                    continue
            
            # Password 필드 찾기
            pw_field = await page.query_selector('input[type="password"]')
            if pw_field and await pw_field.is_visible():
                print("[OK] Password field found")
                attrs = await pw_field.evaluate("""
                    (el) => ({
                        name: el.name,
                        id: el.id,
                        placeholder: el.placeholder
                    })
                """)
                print(f"    Attributes: {attrs}")
            
            # 4. 버튼 분석
            print("\n[STEP 4] Analyzing buttons...")
            buttons = await page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"], a[onclick]');
                    return Array.from(buttons).map(btn => ({
                        tag: btn.tagName,
                        type: btn.type,
                        text: btn.textContent || btn.value,
                        onclick: btn.onclick ? btn.onclick.toString() : null,
                        className: btn.className,
                        id: btn.id,
                        visible: btn.offsetParent !== null
                    }));
                }
            """)
            
            print(f"Found {len(buttons)} buttons:")
            for i, btn in enumerate(buttons):
                if btn['visible'] and btn['text']:
                    print(f"\n  Button {i+1}:")
                    print(f"    - Tag: {btn['tag']}")
                    print(f"    - Text: {btn['text'].strip()}")
                    print(f"    - Class: {btn['className']}")
                    print(f"    - ID: {btn['id']}")
            
            # 5. Form 분석
            print("\n[STEP 5] Analyzing forms...")
            forms = await page.evaluate("""
                () => {
                    const forms = document.querySelectorAll('form');
                    return Array.from(forms).map(form => ({
                        action: form.action,
                        method: form.method,
                        name: form.name,
                        id: form.id,
                        onsubmit: form.onsubmit ? form.onsubmit.toString() : null
                    }));
                }
            """)
            
            if forms:
                print(f"Found {len(forms)} forms:")
                for i, form in enumerate(forms):
                    print(f"\n  Form {i+1}:")
                    print(f"    - Action: {form['action']}")
                    print(f"    - Method: {form['method']}")
                    print(f"    - Name: {form['name']}")
                    print(f"    - ID: {form['id']}")
            
            # 6. JavaScript 함수 찾기
            print("\n[STEP 6] Finding JavaScript login functions...")
            js_functions = await page.evaluate("""
                () => {
                    const scripts = Array.from(document.scripts);
                    const loginFunctions = [];
                    
                    // window 객체에서 login 관련 함수 찾기
                    for (let key in window) {
                        if (key.toLowerCase().includes('login') || 
                            key.toLowerCase().includes('submit') ||
                            key.toLowerCase().includes('signin')) {
                            if (typeof window[key] === 'function') {
                                loginFunctions.push(key);
                            }
                        }
                    }
                    
                    return loginFunctions;
                }
            """)
            
            if js_functions:
                print(f"Found JavaScript functions: {js_functions}")
            
            # 7. 실제 로그인 테스트
            print("\n[STEP 7] Testing login process...")
            
            if id_field and pw_field:
                print("\n[OK] Both ID and Password fields found!")
                print("Testing login with dummy credentials...")
                
                # ID 입력
                await id_field.click()
                await id_field.fill('testuser')
                print("  - Entered ID: testuser")
                
                # Password 입력
                await pw_field.click()
                await pw_field.fill('testpass')
                print("  - Entered Password: ****")
                
                # 스크린샷
                await page.screenshot(path=f"logs/bizmeka/filled_{timestamp}.png")
                
                # 로그인 버튼 찾기
                login_button = None
                button_selectors = [
                    'button:has-text("로그인")',
                    'input[type="submit"]',
                    'button[type="submit"]',
                    'a:has-text("로그인")',
                    '#loginBtn',
                    '.login-btn',
                    'button'
                ]
                
                for selector in button_selectors:
                    try:
                        btn = await page.query_selector(selector)
                        if btn and await btn.is_visible():
                            login_button = btn
                            print(f"\n[OK] Login button found: {selector}")
                            
                            # 버튼 정보
                            btn_text = await btn.inner_text() if btn else ""
                            print(f"  Button text: '{btn_text}'")
                            break
                    except:
                        continue
                
                if login_button:
                    print("\nLogin button is ready to click")
                    print("(Not clicking to avoid actual login attempt)")
                else:
                    print("\n[WARNING] Login button not found - might need Enter key")
            
            # 8. 최종 분석 결과
            print("\n" + "="*60)
            print("[ANALYSIS COMPLETE]")
            print("="*60)
            
            # 결과 저장
            analysis_result = {
                "url": "https://ezsso.bizmeka.com/loginForm.do",
                "timestamp": timestamp,
                "inputs": inputs,
                "buttons": [b for b in buttons if b['visible']],
                "forms": forms,
                "js_functions": js_functions,
                "login_method": {
                    "id_field_found": id_field is not None,
                    "password_field_found": pw_field is not None,
                    "login_button_found": login_button is not None if 'login_button' in locals() else False
                }
            }
            
            # JSON으로 저장
            with open(f"logs/bizmeka/analysis_{timestamp}.json", "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"\n[OK] Analysis saved to: logs/bizmeka/analysis_{timestamp}.json")
            print(f"[OK] Screenshots saved to: logs/bizmeka/")
            
            print("\n[Browser will stay open for 20 seconds for manual inspection...]")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Analysis finished")

if __name__ == "__main__":
    asyncio.run(analyze_bizmeka_login())
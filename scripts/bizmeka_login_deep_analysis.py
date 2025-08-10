#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 로그인 심층 분석 및 해결
모든 가능한 방법을 시도하여 로그인 성공
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

async def deep_analyze_bizmeka():
    """Bizmeka 로그인 완벽 분석"""
    
    print("\n[BIZMEKA DEEP ANALYSIS]")
    print("="*60)
    
    os.makedirs("logs/bizmeka/deep", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # JavaScript 실행 차단 우회
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드 및 네트워크 모니터링
            print("\n[STEP 1] Loading with network monitoring...")
            
            # 네트워크 요청 로깅
            requests_log = []
            
            async def log_request(request):
                requests_log.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': request.headers
                })
                if 'login' in request.url.lower():
                    print(f"   [REQUEST] {request.method} {request.url}")
            
            page.on('request', log_request)
            
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(3000)
            print("   [OK] Page loaded")
            
            # 2. JavaScript 환경 분석
            print("\n[STEP 2] Analyzing JavaScript environment...")
            
            js_info = await page.evaluate("""
                () => {
                    // 전역 함수들 찾기
                    const globalFuncs = [];
                    for (let key in window) {
                        if (typeof window[key] === 'function' && 
                            (key.includes('login') || key.includes('submit') || 
                             key.includes('Login') || key.includes('Submit'))) {
                            globalFuncs.push(key);
                        }
                    }
                    
                    // jQuery 존재 확인
                    const hasJQuery = typeof jQuery !== 'undefined';
                    
                    // Form 정보
                    const forms = Array.from(document.forms).map(form => ({
                        id: form.id,
                        action: form.action,
                        method: form.method,
                        onsubmit: form.onsubmit ? form.onsubmit.toString() : null
                    }));
                    
                    // 로그인 버튼 onclick
                    const loginBtn = document.querySelector('#btnSubmit');
                    const btnOnclick = loginBtn ? loginBtn.onclick ? loginBtn.onclick.toString() : loginBtn.getAttribute('onclick') : null;
                    
                    return {
                        globalFuncs,
                        hasJQuery,
                        forms,
                        btnOnclick,
                        cookies: document.cookie
                    };
                }
            """)
            
            print(f"   Global functions: {js_info['globalFuncs']}")
            print(f"   jQuery available: {js_info['hasJQuery']}")
            print(f"   Forms: {len(js_info['forms'])}")
            if js_info['btnOnclick']:
                print(f"   Button onclick: {js_info['btnOnclick'][:100]}...")
            
            # 3. Form 데이터 분석
            print("\n[STEP 3] Analyzing form structure...")
            
            form_data = await page.evaluate("""
                () => {
                    const form = document.querySelector('#loginForm') || document.querySelector('form');
                    if (!form) return null;
                    
                    const inputs = form.querySelectorAll('input');
                    const fields = {};
                    
                    inputs.forEach(input => {
                        fields[input.name || input.id] = {
                            type: input.type,
                            value: input.value,
                            required: input.required,
                            pattern: input.pattern
                        };
                    });
                    
                    return {
                        action: form.action,
                        method: form.method,
                        fields: fields
                    };
                }
            """)
            
            if form_data:
                print(f"   Form action: {form_data['action']}")
                print(f"   Form method: {form_data['method']}")
                print("   Form fields:")
                for name, info in form_data['fields'].items():
                    if name:
                        print(f"     - {name}: {info['type']} (required: {info['required']})")
            
            # 4. 로그인 시도 방법 1: 직접 입력
            print("\n[STEP 4] Method 1 - Direct input...")
            
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            print("   [OK] Credentials filled")
            
            # 5. 로그인 전 상태 확인
            print("\n[STEP 5] Checking pre-login state...")
            
            csrf_token = await page.input_value('input[name="OWASP_CSRFTOKEN"]')
            if csrf_token:
                print(f"   CSRF Token: {csrf_token[:20]}...")
            
            # 6. 다양한 로그인 시도
            print("\n[STEP 6] Trying different login methods...")
            
            # 방법 1: 버튼 클릭
            print("\n   Method A: Direct button click")
            try:
                await page.click('#btnSubmit', timeout=2000)
                print("     [OK] Button clicked")
                await page.wait_for_timeout(3000)
            except:
                print("     [FAILED] Could not click button")
            
            # URL 확인
            current_url = page.url
            if 'login' not in current_url.lower() or 'main' in current_url.lower():
                print(f"   [SUCCESS] Login successful! URL: {current_url}")
                await page.screenshot(path=f"logs/bizmeka/deep/success_{timestamp}.png")
                return True
            
            # 방법 2: JavaScript 함수 호출
            print("\n   Method B: JavaScript function call")
            
            # 다시 입력
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            
            try:
                # 가능한 함수들 시도
                for func in ['goLogin', 'doLogin', 'login', 'submitLogin', 'sendFormSubmit']:
                    try:
                        result = await page.evaluate(f"""
                            () => {{
                                if (typeof {func} === 'function') {{
                                    {func}();
                                    return true;
                                }}
                                return false;
                            }}
                        """)
                        if result:
                            print(f"     [OK] Called {func}()")
                            await page.wait_for_timeout(3000)
                            break
                    except:
                        continue
            except:
                print("     [FAILED] No JavaScript function worked")
            
            # URL 재확인
            current_url = page.url
            if 'login' not in current_url.lower() or 'main' in current_url.lower():
                print(f"   [SUCCESS] Login successful! URL: {current_url}")
                return True
            
            # 방법 3: Form submit
            print("\n   Method C: Form submit")
            
            # 다시 입력
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            
            try:
                await page.evaluate("""
                    () => {
                        const form = document.querySelector('#loginForm') || document.querySelector('form');
                        if (form) {
                            form.submit();
                            return true;
                        }
                        return false;
                    }
                """)
                print("     [OK] Form submitted")
                await page.wait_for_timeout(3000)
            except:
                print("     [FAILED] Could not submit form")
            
            # 방법 4: Enter 키
            print("\n   Method D: Enter key in password field")
            
            # 다시 입력
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            await page.press('#password', 'Enter')
            print("     [OK] Enter pressed")
            await page.wait_for_timeout(3000)
            
            # 7. 최종 결과 확인
            print("\n[STEP 7] Final verification...")
            
            final_url = page.url
            print(f"   Final URL: {final_url}")
            
            # 에러 메시지 확인
            error_messages = await page.evaluate("""
                () => {
                    const errors = [];
                    // 일반적인 에러 선택자들
                    const selectors = ['.error', '.alert', '.message', '[class*="fail"]', '[class*="error"]'];
                    
                    selectors.forEach(selector => {
                        const elem = document.querySelector(selector);
                        if (elem && elem.textContent) {
                            errors.push(elem.textContent.trim());
                        }
                    });
                    
                    return errors;
                }
            """)
            
            if error_messages:
                print("   Error messages found:")
                for msg in error_messages:
                    print(f"     - {msg}")
            
            # 로그인 성공 지표 확인
            success_indicators = await page.evaluate("""
                () => {
                    const indicators = {
                        hasLogout: !!document.querySelector('[href*="logout"]'),
                        hasUserInfo: document.body.textContent.includes('kilmoon'),
                        hasMainMenu: !!document.querySelector('.main-menu, nav'),
                        inputsCleared: !document.querySelector('#username')?.value
                    };
                    return indicators;
                }
            """)
            
            print("   Success indicators:")
            for key, value in success_indicators.items():
                print(f"     - {key}: {value}")
            
            # 스크린샷 저장
            await page.screenshot(path=f"logs/bizmeka/deep/final_{timestamp}.png", full_page=True)
            
            # 8. 네트워크 로그 저장
            with open(f"logs/bizmeka/deep/network_{timestamp}.json", "w") as f:
                json.dump(requests_log, f, indent=2)
            print(f"\n[SAVED] Network log: logs/bizmeka/deep/network_{timestamp}.json")
            
            print("\n[Browser will stay open for manual inspection...]")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[DONE] Analysis complete")

if __name__ == "__main__":
    print("""
    =====================================
    Bizmeka Login - Deep Analysis
    =====================================
    This will try EVERY possible method
    =====================================
    """)
    
    asyncio.run(deep_analyze_bizmeka())
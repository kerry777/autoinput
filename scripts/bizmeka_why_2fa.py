#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka가 자동화를 감지하는 정확한 이유 파악
"""

import asyncio
from playwright.async_api import async_playwright
import os
import json

async def analyze_detection_reasons():
    """자동화 감지 원인 분석"""
    
    print("\n[BIZMEKA 2FA 트리거 원인 분석]")
    print("="*60)
    
    os.makedirs("logs/detection", exist_ok=True)
    
    async with async_playwright() as p:
        # 1. 일반 브라우저 (최소 설정)
        print("\n[TEST 1] 최소 설정 브라우저")
        browser1 = await p.chromium.launch(headless=False)
        context1 = await browser1.new_context()
        page1 = await context1.new_page()
        
        # 브라우저 지문 수집
        fingerprint1 = await page1.evaluate("""
            () => {
                return {
                    webdriver: navigator.webdriver,
                    chrome: !!window.chrome,
                    chrome_runtime: !!(window.chrome && window.chrome.runtime),
                    plugins_length: navigator.plugins.length,
                    languages: navigator.languages,
                    platform: navigator.platform,
                    vendor: navigator.vendor,
                    userAgent: navigator.userAgent,
                    cookieEnabled: navigator.cookieEnabled,
                    permissions: typeof navigator.permissions !== 'undefined',
                    cdp_check: !!window.__playwright,
                    automation: !!window.document.__selenium_unwrapped,
                    headless: /HeadlessChrome/.test(navigator.userAgent),
                    // CDP 관련 속성들
                    cdc_props: Object.getOwnPropertyNames(window).filter(n => n.includes('cdc')),
                    proto_chrome: !!window.__proto__.chrome
                };
            }
        """)
        
        print("최소 설정 지문:")
        print(json.dumps(fingerprint1, indent=2, ensure_ascii=False))
        
        await browser1.close()
        
        # 2. Stealth 적용 브라우저
        print("\n[TEST 2] Stealth 적용 브라우저")
        browser2 = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context2 = await browser2.new_context()
        page2 = await context2.new_page()
        
        # Stealth 스크립트 적용
        await page2.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        fingerprint2 = await page2.evaluate("""
            () => {
                return {
                    webdriver: navigator.webdriver,
                    webdriver_check: 'webdriver' in navigator,
                    chrome: !!window.chrome,
                    modified: Object.getOwnPropertyDescriptor(navigator, 'webdriver') !== undefined
                };
            }
        """)
        
        print("Stealth 적용 지문:")
        print(json.dumps(fingerprint2, indent=2, ensure_ascii=False))
        
        await browser2.close()
        
        # 3. 실제 Bizmeka 접속 테스트
        print("\n[TEST 3] Bizmeka 실제 접속")
        browser3 = await p.chromium.launch(headless=False)
        context3 = await browser3.new_context()
        page3 = await context3.new_page()
        
        # 네트워크 요청 로깅
        requests_log = []
        
        async def log_request(request):
            if 'bot' in request.url.lower() or 'detect' in request.url.lower() or 'captcha' in request.url.lower():
                requests_log.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers)
                })
        
        page3.on('request', log_request)
        
        # Bizmeka 로그인 페이지 접속
        await page3.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page3.wait_for_timeout(3000)
        
        # 페이지에서 탐지 관련 스크립트 확인
        detection_info = await page3.evaluate("""
            () => {
                const scripts = Array.from(document.scripts).map(s => s.src).filter(src => src);
                const detection_scripts = scripts.filter(src => 
                    src.includes('bot') || 
                    src.includes('detect') || 
                    src.includes('captcha') ||
                    src.includes('BDC')
                );
                
                // BotDetect 관련 확인
                const botdetect = {
                    has_botdetect: typeof BotDetect !== 'undefined',
                    captcha_elements: document.querySelectorAll('[id*="botCaptcha"], [class*="botdetect"]').length,
                    captcha_scripts: detection_scripts
                };
                
                // 숨겨진 필드들
                const hidden_fields = {};
                document.querySelectorAll('input[type="hidden"]').forEach(input => {
                    if (input.name && (input.name.includes('BDC') || input.name.includes('CSRF'))) {
                        hidden_fields[input.name] = input.value;
                    }
                });
                
                return {
                    detection_scripts,
                    botdetect,
                    hidden_fields,
                    has_captcha: document.querySelector('img[src*="captcha"]') !== null
                };
            }
        """)
        
        print("\n탐지 시스템 분석:")
        print(json.dumps(detection_info, indent=2, ensure_ascii=False))
        
        # 로그인 시도
        await page3.fill('#username', 'kilmoon@mek-ics.com')
        await page3.fill('#password', 'moon7410!@')
        await page3.click('#btnSubmit')
        await page3.wait_for_timeout(5000)
        
        final_url = page3.url
        print(f"\n최종 URL: {final_url}")
        
        if 'secondStep' in final_url:
            print("\n[2FA 트리거됨]")
            
            # 2FA 페이지 분석
            twofa_info = await page3.evaluate("""
                () => {
                    return {
                        url: window.location.href,
                        cookies: document.cookie,
                        sessionStorage_keys: Object.keys(sessionStorage),
                        localStorage_keys: Object.keys(localStorage),
                        body_text: document.body.innerText.substring(0, 500)
                    };
                }
            """)
            
            print("\n2FA 페이지 정보:")
            print(f"- 쿠키: {twofa_info['cookies'][:100]}...")
            print(f"- SessionStorage: {twofa_info['sessionStorage_keys']}")
            print(f"- LocalStorage: {twofa_info['localStorage_keys']}")
        
        # 네트워크 로그 저장
        with open("logs/detection/network_log.json", "w", encoding='utf-8') as f:
            json.dump(requests_log, f, ensure_ascii=False, indent=2)
        
        print(f"\n[네트워크 로그 저장됨: logs/detection/network_log.json]")
        
        await page3.wait_for_timeout(10000)
        await browser3.close()
        
        # 4. 결론
        print("\n" + "="*60)
        print("[분석 결과]")
        print("="*60)
        print("""
1. BotDetect CAPTCHA 시스템 사용
   - botdetectcaptcha 스크립트 로드
   - BDC_VCID, BDC_BackWorkaround 필드 존재
   
2. 자동화 감지 포인트:
   - navigator.webdriver 속성
   - Chrome DevTools Protocol (CDP) 사용
   - 브라우저 런치 플래그
   - 신규 세션/쿠키
   
3. 2FA 트리거 조건:
   - 신규 디바이스/브라우저 (쿠키 없음)
   - 자동화 도구 감지
   - IP 기반 위험 점수
   - 로그인 패턴 이상
   
4. 핵심 원인:
   Playwright/Puppeteer 등 자동화 도구는 CDP를 사용하며,
   이는 근본적으로 감지 가능합니다. Stealth 기법을 적용해도
   BotDetect 같은 전문 솔루션은 이를 우회하기 어렵습니다.
        """)

if __name__ == "__main__":
    asyncio.run(analyze_detection_reasons())
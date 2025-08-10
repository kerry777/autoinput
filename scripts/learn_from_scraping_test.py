#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실제 스크래핑 테스트 사이트에서 학습하기
web-scraping.dev 사이트의 다양한 로그인 기법 실습
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

class ScrapingLearning:
    def __init__(self):
        self.logs_dir = "logs/learning"
        os.makedirs(self.logs_dir, exist_ok=True)
        self.session_cookies = {}
        
    async def learn_basic_login(self):
        """기본 폼 로그인 + 쿠키 학습"""
        print("\n[1] 기본 로그인 학습 (Form + Cookies)")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=200)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 로그인 페이지 접속
            await page.goto("https://web-scraping.dev/login")
            await page.wait_for_timeout(2000)
            
            # 페이지 구조 분석
            login_structure = await page.evaluate("""
                () => {
                    const form = document.querySelector('form');
                    const inputs = Array.from(document.querySelectorAll('input')).map(input => ({
                        type: input.type,
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        required: input.required
                    }));
                    const button = document.querySelector('button[type="submit"]');
                    
                    return {
                        form_action: form ? form.action : null,
                        form_method: form ? form.method : null,
                        inputs: inputs,
                        button_text: button ? button.innerText : null
                    };
                }
            """)
            
            print("  폼 구조:")
            print(f"    - Action: {login_structure['form_action']}")
            print(f"    - Method: {login_structure['form_method']}")
            print(f"    - 입력 필드: {len(login_structure['inputs'])}개")
            
            # 로그인 시도
            username_field = await page.query_selector('input[name="username"]')
            password_field = await page.query_selector('input[name="password"]')
            
            if username_field and password_field:
                await username_field.fill("admin")
                await password_field.fill("admin")
                print("  자격증명 입력 완료")
                
                # 로그인 버튼 클릭
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(2000)
                
                # 쿠키 확인
                cookies = await context.cookies()
                print(f"  쿠키 수집: {len(cookies)}개")
                for cookie in cookies:
                    print(f"    - {cookie['name']}: {cookie['value'][:20]}...")
                
                # 로그인 성공 확인
                current_url = page.url
                print(f"  로그인 후 URL: {current_url}")
                
                # 쿠키 저장
                self.session_cookies['basic'] = cookies
            
            await browser.close()
    
    async def learn_cookie_popup(self):
        """쿠키 팝업 처리 학습"""
        print("\n[2] 쿠키 팝업 처리 학습")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=200)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 쿠키 팝업이 있는 페이지
            await page.goto("https://web-scraping.dev/login?cookies")
            await page.wait_for_timeout(2000)
            
            # 팝업 감지
            popup_detected = await page.evaluate("""
                () => {
                    // 모달이나 오버레이 찾기
                    const modals = document.querySelectorAll('.modal, [class*="popup"], [class*="cookie"]');
                    const overlays = document.querySelectorAll('.overlay, [class*="backdrop"]');
                    
                    return {
                        has_modal: modals.length > 0,
                        has_overlay: overlays.length > 0,
                        modal_text: modals[0] ? modals[0].innerText.substring(0, 100) : null
                    };
                }
            """)
            
            print(f"  팝업 감지: {popup_detected['has_modal']}")
            print(f"  오버레이: {popup_detected['has_overlay']}")
            
            if popup_detected['has_modal']:
                # 팝업 닫기 버튼 찾기
                close_buttons = await page.query_selector_all('button:has-text("Accept"), button:has-text("Close"), button:has-text("OK")')
                if close_buttons:
                    await close_buttons[0].click()
                    print("  팝업 닫기 완료")
            
            await browser.close()
    
    async def learn_referer_control(self):
        """Referer 헤더 제어 학습"""
        print("\n[3] Referer 헤더 제어 학습")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=200)
            context = await browser.new_context()
            
            # Referer 헤더 설정
            await context.set_extra_http_headers({
                'Referer': 'https://web-scraping.dev/login'
            })
            
            page = await context.new_page()
            
            # 보호된 페이지 접속
            await page.goto("https://web-scraping.dev/credentials")
            await page.wait_for_timeout(2000)
            
            # 접속 성공 확인
            current_url = page.url
            if 'blocked' in current_url:
                print("  접속 차단됨 - Referer 없음")
            else:
                print("  접속 성공 - Referer 헤더 작동")
                content = await page.inner_text('body')
                print(f"  페이지 내용: {content[:100]}...")
            
            await browser.close()
    
    async def learn_csrf_token(self):
        """CSRF 토큰 처리 학습"""
        print("\n[4] CSRF 토큰 처리 학습")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=200)
            context = await browser.new_context()
            page = await context.new_page()
            
            # 제품 페이지 접속
            await page.goto("https://web-scraping.dev/product/1")
            await page.wait_for_timeout(2000)
            
            # CSRF 토큰 찾기
            csrf_token = await page.evaluate("""
                () => {
                    // 메타 태그에서
                    const metaCSRF = document.querySelector('meta[name="csrf-token"]');
                    if (metaCSRF) return metaCSRF.content;
                    
                    // 숨겨진 입력에서
                    const inputCSRF = document.querySelector('input[name*="csrf"]');
                    if (inputCSRF) return inputCSRF.value;
                    
                    // 쿠키에서
                    const cookies = document.cookie.split(';');
                    for (let cookie of cookies) {
                        if (cookie.includes('csrf')) {
                            return cookie.split('=')[1];
                        }
                    }
                    
                    return null;
                }
            """)
            
            if csrf_token:
                print(f"  CSRF 토큰 발견: {csrf_token[:20]}...")
                
                # CSRF 토큰을 포함한 요청 시뮬레이션
                await page.evaluate("""
                    (token) => {
                        fetch('/api/reviews', {
                            headers: {
                                'X-CSRF-Token': token
                            }
                        });
                    }
                """, csrf_token)
                
                print("  CSRF 토큰 포함 요청 전송 완료")
            else:
                print("  CSRF 토큰 없음")
            
            await browser.close()
    
    async def apply_to_bizmeka(self):
        """학습한 내용을 Bizmeka에 적용"""
        print("\n[5] Bizmeka에 학습 내용 적용")
        print("-" * 50)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False, 
                slow_mo=200,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context()
            
            # 자동화 탐지 우회
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            # Bizmeka 로그인 페이지
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(2000)
            
            # 1. CSRF 토큰 추출
            csrf_token = await page.input_value('input[name="OWASP_CSRFTOKEN"]')
            if csrf_token:
                print(f"  CSRF 토큰: {csrf_token[:20]}...")
            
            # 2. 폼 구조 확인
            form_data = await page.evaluate("""
                () => {
                    const form = document.querySelector('#loginForm');
                    return {
                        action: form ? form.action : null,
                        method: form ? form.method : null,
                        has_username: !!document.querySelector('#username'),
                        has_password: !!document.querySelector('#password'),
                        button_selector: '#btnSubmit'
                    };
                }
            """)
            
            print("  폼 구조 확인:")
            print(f"    - Action: {form_data['action']}")
            print(f"    - Username 필드: {form_data['has_username']}")
            print(f"    - Password 필드: {form_data['has_password']}")
            
            # 3. 로그인 시도 (학습한 기법 적용)
            if form_data['has_username'] and form_data['has_password']:
                # 사람처럼 입력
                await page.click('#username')
                await page.wait_for_timeout(500)
                for char in 'kilmoon@mek-ics.com':
                    await page.keyboard.type(char)
                    await page.wait_for_timeout(30)
                
                await page.click('#password')
                await page.wait_for_timeout(500)
                for char in 'moon7410!@':
                    await page.keyboard.type(char)
                    await page.wait_for_timeout(30)
                
                print("  자격증명 입력 완료 (human-like)")
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"{self.logs_dir}/bizmeka_ready_{timestamp}.png")
                
                print("\n  [결과] 학습한 기법 적용 완료:")
                print("    1. CSRF 토큰 추출 ✓")
                print("    2. 자동화 탐지 우회 ✓")
                print("    3. Human-like 입력 ✓")
                print("    4. 폼 구조 분석 ✓")
            
            await page.wait_for_timeout(5000)
            await browser.close()

async def main():
    learner = ScrapingLearning()
    
    print("""
    =====================================
    웹 스크래핑 기법 실제 학습
    =====================================
    web-scraping.dev 사이트에서 실습
    =====================================
    """)
    
    # 단계별 학습
    await learner.learn_basic_login()
    await learner.learn_cookie_popup()
    await learner.learn_referer_control()
    await learner.learn_csrf_token()
    
    # Bizmeka에 적용
    await learner.apply_to_bizmeka()
    
    print("\n학습 완료! 실제 기법들을 습득했습니다.")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 최종 솔루션 - 학습한 내용 적용
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

class BizmekaFinalSolution:
    def __init__(self):
        self.logs_dir = "logs/final"
        os.makedirs(self.logs_dir, exist_ok=True)
        
    async def login(self):
        """학습한 모든 기법을 적용한 로그인"""
        print("\n[BIZMEKA LOGIN - FINAL SOLUTION]")
        print("="*60)
        
        async with async_playwright() as p:
            # 1. 브라우저 설정 (자동화 탐지 우회)
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=150,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 2. 자동화 탐지 우회 스크립트
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            page = await context.new_page()
            
            try:
                # 3. 로그인 페이지 접속
                print("\n[1] Navigating to login page...")
                await page.goto("https://ezsso.bizmeka.com/loginForm.do")
                await page.wait_for_load_state('networkidle')
                print("   Page loaded")
                
                # 4. CSRF 토큰 추출
                print("\n[2] Extracting CSRF token...")
                csrf_token = await page.input_value('input[name="OWASP_CSRFTOKEN"]')
                if csrf_token:
                    print(f"   CSRF Token: {csrf_token[:30]}...")
                
                # 5. 폼 구조 확인
                print("\n[3] Analyzing form structure...")
                form_info = await page.evaluate("""
                    () => {
                        const form = document.querySelector('#loginForm');
                        const username = document.querySelector('#username');
                        const password = document.querySelector('#password');
                        const button = document.querySelector('#btnSubmit');
                        
                        return {
                            has_form: !!form,
                            has_username: !!username,
                            has_password: !!password,
                            has_button: !!button,
                            form_action: form ? form.action : null
                        };
                    }
                """)
                
                print(f"   Form found: {form_info['has_form']}")
                print(f"   Username field: {form_info['has_username']}")
                print(f"   Password field: {form_info['has_password']}")
                print(f"   Submit button: {form_info['has_button']}")
                
                # 6. 로그인 정보 입력 (Human-like)
                print("\n[4] Entering credentials (human-like)...")
                
                # Username 입력
                await page.click('#username')
                await page.wait_for_timeout(500)
                
                # 기존 값 삭제
                await page.keyboard.press('Control+A')
                await page.keyboard.press('Delete')
                await page.wait_for_timeout(200)
                
                # 한 글자씩 입력
                username = 'kilmoon@mek-ics.com'
                for char in username:
                    await page.keyboard.type(char)
                    await page.wait_for_timeout(50)
                print(f"   Username entered: {username}")
                
                # Tab으로 Password 필드로 이동
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(300)
                
                # Password 입력
                password = 'moon7410!@'
                for char in password:
                    await page.keyboard.type(char)
                    await page.wait_for_timeout(50)
                print("   Password entered: ****")
                
                # 7. 스크린샷 (로그인 전)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                before_path = f"{self.logs_dir}/before_login_{timestamp}.png"
                await page.screenshot(path=before_path)
                print(f"\n[5] Screenshot saved: {before_path}")
                
                # 8. 로그인 버튼 클릭
                print("\n[6] Clicking login button...")
                await page.click('#btnSubmit')
                
                # 9. 응답 대기
                print("\n[7] Waiting for response...")
                await page.wait_for_timeout(5000)
                
                # 10. 결과 확인
                current_url = page.url
                print(f"\n[8] Current URL: {current_url}")
                
                # 11. 결과 스크린샷
                after_path = f"{self.logs_dir}/after_login_{timestamp}.png"
                await page.screenshot(path=after_path, full_page=True)
                print(f"   Screenshot saved: {after_path}")
                
                # 12. 로그인 성공 여부 판단
                print("\n[9] Checking login status...")
                
                if 'fail' in current_url.lower():
                    print("   [FAILED] Login failed - Password error or account locked")
                    
                    # 에러 메시지 확인
                    error_text = await page.inner_text('body')
                    if '5' in error_text:
                        print("   [INFO] Account locked after 5 failed attempts")
                        print("   [SOLUTION] Need password reset or wait 30 minutes")
                    
                elif 'login' not in current_url.lower() or 'main' in current_url.lower():
                    print("   [SUCCESS] Login successful!")
                    
                    # 쿠키 저장
                    cookies = await context.cookies()
                    print(f"   Cookies saved: {len(cookies)} cookies")
                    
                else:
                    print("   [UNKNOWN] Login status unclear")
                    
                    # 페이지 내용 확인
                    page_text = await page.inner_text('body')
                    if 'kilmoon' in page_text.lower():
                        print("   [SUCCESS] User info found - likely logged in")
                    else:
                        print("   [INFO] May need additional verification")
                
                print("\n[10] Browser will remain open for 30 seconds...")
                await page.wait_for_timeout(30000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
                print("\n[DONE] Process complete")

async def main():
    solution = BizmekaFinalSolution()
    await solution.login()

if __name__ == "__main__":
    print("""
    =====================================
    BIZMEKA LOGIN - LEARNED SOLUTION
    =====================================
    Applying all learned techniques:
    - CSRF token extraction
    - Automation detection bypass
    - Human-like input simulation
    - Form structure analysis
    =====================================
    """)
    
    asyncio.run(main())
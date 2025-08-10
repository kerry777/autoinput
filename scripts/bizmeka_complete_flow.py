#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 완전한 로그인 플로우
1차 로그인 -> 2차 인증 -> 메인 페이지
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

class BizmekaCompleteFlow:
    def __init__(self):
        self.logs_dir = "logs/complete"
        os.makedirs(self.logs_dir, exist_ok=True)
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup_browser(self):
        """브라우저 설정"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=150,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        self.page = await self.context.new_page()
    
    async def first_login(self):
        """1차 로그인"""
        print("\n[STEP 1] 1차 로그인")
        print("-"*50)
        
        # 로그인 페이지
        await self.page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await self.page.wait_for_load_state('networkidle')
        
        # CSRF 토큰
        csrf = await self.page.input_value('input[name="OWASP_CSRFTOKEN"]')
        print(f"  CSRF Token: {csrf[:30]}...")
        
        # 로그인 정보 입력
        await self.page.click('#username')
        await self.page.keyboard.press('Control+A')
        await self.page.keyboard.type('kilmoon@mek-ics.com')
        
        await self.page.keyboard.press('Tab')
        await self.page.keyboard.type('moon7410!@')
        
        print("  Credentials entered")
        
        # 로그인 버튼 클릭
        await self.page.click('#btnSubmit')
        await self.page.wait_for_timeout(3000)
        
        current_url = self.page.url
        print(f"  After login URL: {current_url}")
        
        if 'secondStep' in current_url:
            print("  [SUCCESS] 1차 로그인 성공 - 2차 인증 필요")
            return True
        elif 'fail' in current_url:
            print("  [FAILED] 로그인 실패")
            return False
        else:
            print("  [SUCCESS] 완전 로그인 성공")
            return True
    
    async def second_verification(self):
        """2차 인증"""
        print("\n[STEP 2] 2차 인증")
        print("-"*50)
        
        # 현재 페이지 분석
        page_content = await self.page.evaluate("""
            () => {
                const buttons = Array.from(document.querySelectorAll('button, a.btn')).map(btn => ({
                    text: btn.innerText,
                    onclick: btn.onclick ? btn.onclick.toString() : null,
                    href: btn.href
                }));
                
                return {
                    title: document.title,
                    buttons: buttons,
                    has_email_option: document.body.innerText.includes('이메일')
                };
            }
        """)
        
        print(f"  Page title: {page_content['title']}")
        print(f"  Buttons found: {len(page_content['buttons'])}")
        
        # 이메일 인증 버튼 찾기
        for button_info in page_content['buttons']:
            print(f"    - {button_info['text']}")
        
        # 이메일로 인증번호 받기 클릭
        email_button = await self.page.query_selector('button:has-text("이메일로 인증번호 받기")')
        if not email_button:
            email_button = await self.page.query_selector('a:has-text("이메일로 인증번호 받기")')
        if not email_button:
            # 모든 버튼 중에서 이메일 관련 찾기
            all_buttons = await self.page.query_selector_all('button, a.btn')
            for btn in all_buttons:
                text = await btn.inner_text()
                if '이메일' in text:
                    email_button = btn
                    break
        
        if email_button:
            print("  이메일 인증 버튼 발견!")
            await email_button.click()
            await self.page.wait_for_timeout(3000)
            
            # 인증번호 입력 필드 확인
            verification_input = await self.page.query_selector('input[type="text"]')
            if verification_input:
                print("  인증번호 입력 필드 발견")
                print("  [대기] 이메일로 인증번호를 받아 입력해주세요")
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"{self.logs_dir}/verification_page_{timestamp}.png"
                await self.page.screenshot(path=screenshot_path)
                print(f"  Screenshot: {screenshot_path}")
        else:
            print("  [WARNING] 이메일 인증 버튼을 찾을 수 없음")
            
            # 현재 페이지 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"{self.logs_dir}/current_page_{timestamp}.png"
            await self.page.screenshot(path=screenshot_path)
            print(f"  Current page saved: {screenshot_path}")
    
    async def run(self):
        """전체 플로우 실행"""
        try:
            await self.setup_browser()
            
            print("""
            =====================================
            BIZMEKA COMPLETE LOGIN FLOW
            =====================================
            1차 로그인 -> 2차 인증 -> 메인 페이지
            =====================================
            """)
            
            # 1차 로그인
            login_success = await self.first_login()
            
            if login_success:
                # 2차 인증
                await self.second_verification()
            
            print("\n브라우저는 60초 후 닫힙니다...")
            print("수동으로 인증번호를 입력하실 수 있습니다.")
            await self.page.wait_for_timeout(60000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.browser:
                await self.browser.close()

if __name__ == "__main__":
    flow = BizmekaCompleteFlow()
    asyncio.run(flow.run())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
스마트 자동화 - 페이지 상태를 정확히 파악하고 적절히 대응
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

class SmartAutomation:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs("logs/smart", exist_ok=True)
        
    async def setup(self):
        """브라우저 설정"""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        
    async def analyze_page(self):
        """현재 페이지 상태 분석"""
        print("\n[페이지 분석]")
        
        # URL 확인
        url = self.page.url
        print(f"URL: {url}")
        
        # 페이지 타입 판별
        page_info = await self.page.evaluate("""
            () => {
                // 로그인 페이지인지
                const isLoginPage = document.querySelector('#username') !== null;
                
                // 비밀번호 재설정 페이지인지
                const isPasswordReset = window.location.href.includes('find');
                
                // 라디오 버튼 있는지 (인증 방법 선택)
                const hasRadioButtons = document.querySelectorAll('input[type="radio"]').length > 0;
                
                // 입력 필드들
                const textInputs = Array.from(document.querySelectorAll('input[type="text"]:visible')).map(input => ({
                    id: input.id,
                    name: input.name,
                    placeholder: input.placeholder,
                    value: input.value,
                    visible: input.offsetParent !== null
                }));
                
                // 버튼들
                const buttons = Array.from(document.querySelectorAll('button, a.btn')).map(btn => ({
                    text: btn.innerText,
                    class: btn.className,
                    visible: btn.offsetParent !== null
                }));
                
                // 캡차 이미지
                const images = Array.from(document.querySelectorAll('img')).filter(img => 
                    img.offsetParent !== null && img.width > 50
                ).map(img => ({
                    src: img.src.substring(0, 50),
                    width: img.width,
                    height: img.height
                }));
                
                return {
                    isLoginPage,
                    isPasswordReset,
                    hasRadioButtons,
                    textInputs,
                    buttons,
                    images,
                    pageText: document.body.innerText.substring(0, 200)
                };
            }
        """)
        
        print(f"로그인 페이지: {page_info['isLoginPage']}")
        print(f"비밀번호 재설정: {page_info['isPasswordReset']}")
        print(f"라디오 버튼: {page_info['hasRadioButtons']}")
        print(f"텍스트 입력 필드: {len(page_info['textInputs'])}개")
        print(f"버튼: {len(page_info['buttons'])}개")
        
        return page_info
        
    async def handle_password_reset(self):
        """비밀번호 재설정 처리"""
        print("\n[비밀번호 재설정 페이지 처리]")
        
        # 1. 라디오 버튼이 있으면 이메일 인증 선택
        radio_buttons = await self.page.query_selector_all('input[type="radio"]')
        if len(radio_buttons) >= 3:
            print("이메일 인증 옵션 선택...")
            await radio_buttons[2].click()  # 세번째 = 이메일 인증
            await self.page.wait_for_timeout(1000)
            
            # 본인인증 버튼 클릭
            auth_btn = await self.page.query_selector('a:has-text("본인인증")')
            if not auth_btn:
                auth_btn = await self.page.query_selector('.btn-danger')
            
            if auth_btn:
                print("본인인증 버튼 클릭...")
                await auth_btn.click()
                await self.page.wait_for_timeout(3000)
                
                # 페이지 변화 확인
                await self.analyze_page()
                
                # 이름 입력 필드 찾기
                name_field = await self.page.query_selector('input#idEM')
                if not name_field:
                    name_field = await self.page.query_selector('input[placeholder*="아이디"]')
                
                if name_field and await name_field.is_visible():
                    print("이름/아이디 필드에 입력...")
                    await name_field.click()
                    await name_field.fill("이길문")
                    
                    # 이메일 필드
                    email_fields = await self.page.query_selector_all('input#preEmail, input#nextEmail')
                    if len(email_fields) == 2:
                        print("이메일 입력...")
                        await email_fields[0].fill("kilmoon")
                        await email_fields[1].fill("mek-ics.com")
                    
                    # 캡차 확인
                    await self.handle_captcha()
                    
    async def handle_captcha(self):
        """캡차 처리"""
        print("\n[캡차 확인]")
        
        # 모든 이미지 확인
        images = await self.page.query_selector_all('img')
        for i, img in enumerate(images):
            if await img.is_visible():
                box = await img.bounding_box()
                if box and box['width'] > 80 and box['height'] > 30:
                    # 캡차 가능성 있는 이미지
                    captcha_path = f"logs/smart/captcha_{i}_{self.timestamp}.png"
                    await img.screenshot(path=captcha_path)
                    print(f"캡차 후보 저장: {captcha_path}")
                    print(f"크기: {box['width']}x{box['height']}")
        
        print("\n캡차 이미지가 저장되었습니다.")
        print("수동으로 캡차 텍스트를 확인하고 입력해주세요.")
        
    async def handle_login(self):
        """로그인 페이지 처리"""
        print("\n[로그인 페이지 처리]")
        
        # ID/Password 입력
        await self.page.fill('#username', 'kilmoon@mek-ics.com')
        await self.page.fill('#password', 'moon7410!@')
        
        # 로그인 버튼 클릭
        await self.page.click('#btnSubmit')
        await self.page.wait_for_timeout(3000)
        
        # 결과 확인
        if 'fail' in self.page.url.lower():
            print("로그인 실패 - 비밀번호 재설정 필요")
            await self.page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
            await self.handle_password_reset()
            
    async def run(self, url):
        """메인 실행"""
        await self.setup()
        
        try:
            # 페이지 로드
            await self.page.goto(url)
            await self.page.wait_for_timeout(2000)
            
            # 현재 페이지 분석
            page_info = await self.analyze_page()
            
            # 페이지 타입에 따라 처리
            if page_info['isLoginPage']:
                await self.handle_login()
            elif page_info['isPasswordReset']:
                await self.handle_password_reset()
            else:
                print("알 수 없는 페이지 타입")
                
            # 최종 스크린샷
            final_path = f"logs/smart/final_{self.timestamp}.png"
            await self.page.screenshot(path=final_path)
            print(f"\n최종 스크린샷: {final_path}")
            
            print("\n브라우저는 30초 후 닫힙니다...")
            await self.page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"오류: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    automation = SmartAutomation()
    
    # Bizmeka 로그인 시도
    await automation.run("https://ezsso.bizmeka.com/loginForm.do")

if __name__ == "__main__":
    print("""
    =====================================
    Smart Automation System
    =====================================
    페이지 상태를 분석하고 적절히 대응
    =====================================
    """)
    
    asyncio.run(main())
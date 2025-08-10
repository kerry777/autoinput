#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka Advanced Solution - CAPTCHA & CSRF 처리
"""

import asyncio
import os
import json
import random
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class BizmekaAdvancedLogin:
    def __init__(self):
        self.profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_advanced"
        self.logs_dir = "logs/advanced"
        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
    async def human_delay(self, min_ms=50, max_ms=200):
        """인간같은 딜레이"""
        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)
    
    async def human_type(self, page, selector, text):
        """인간같은 타이핑"""
        element = await page.query_selector(selector)
        if element:
            # 클릭 전 딜레이
            await self.human_delay(100, 300)
            
            # 요소로 포커스 이동
            await element.click()
            await self.human_delay(50, 150)
            
            # 한 글자씩 타이핑
            for char in text:
                await page.keyboard.type(char)
                # 특수문자나 @ 뒤에는 더 긴 딜레이
                if char in '@.!':
                    await self.human_delay(150, 300)
                else:
                    await self.human_delay(50, 150)
    
    async def extract_hidden_fields(self, page):
        """모든 숨겨진 필드 추출"""
        fields = await page.evaluate("""
            () => {
                const result = {};
                document.querySelectorAll('input[type="hidden"]').forEach(input => {
                    if (input.name) {
                        result[input.name] = input.value;
                    }
                });
                return result;
            }
        """)
        return fields
    
    async def extract_captcha_info(self, page):
        """CAPTCHA 관련 정보 추출"""
        captcha = await page.evaluate("""
            () => {
                const result = {
                    hasImage: false,
                    imageUrl: null,
                    vcid: null,
                    backWorkaround: null
                };
                
                // CAPTCHA 이미지 확인
                const captchaImg = document.querySelector('img[src*="botdetectcaptcha"]');
                if (captchaImg) {
                    result.hasImage = true;
                    result.imageUrl = captchaImg.src;
                }
                
                // BDC_VCID 값 추출
                const vcidInput = document.querySelector('input[name*="BDC_VCID"]');
                if (vcidInput) {
                    result.vcid = vcidInput.value;
                }
                
                // BDC_BackWorkaround 값 추출
                const backInput = document.querySelector('input[name*="BDC_BackWorkaround"]');
                if (backInput) {
                    result.backWorkaround = backInput.value;
                }
                
                return result;
            }
        """)
        return captcha
    
    async def manual_login_with_session_save(self):
        """수동 로그인으로 세션 저장"""
        print("\n[수동 로그인 모드]")
        print("="*60)
        print("1. 브라우저에서 수동으로 로그인하세요")
        print("2. CAPTCHA가 있으면 직접 입력하세요")
        print("3. 2차 인증까지 완료하세요")
        print("4. 완료 후 Enter를 누르세요")
        print("="*60)
        
        async with async_playwright() as p:
            # 영구 프로필로 브라우저 실행
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                viewport=None,
                no_viewport=True
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 로그인 페이지
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            
            print("\n브라우저에서 로그인을 완료하세요...")
            input("완료 후 Enter: ")
            
            # 세션 정보 저장
            cookies = await browser.cookies()
            session_data = {
                "cookies": cookies,
                "url": page.url,
                "timestamp": datetime.now().isoformat()
            }
            
            session_file = Path(self.logs_dir) / "session.json"
            session_file.write_text(
                json.dumps(session_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            print(f"세션 저장 완료: {session_file}")
            await browser.close()
    
    async def automated_login_with_csrf(self):
        """CSRF 토큰을 올바르게 처리하는 자동 로그인"""
        print("\n[자동 로그인 - CSRF & CAPTCHA 처리]")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                viewport=None,
                no_viewport=True
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 로그인 페이지 접속
            print("[1] 로그인 페이지 접속")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await self.human_delay(2000, 3000)
            
            # 숨겨진 필드들 추출
            print("[2] 보안 토큰 추출")
            hidden_fields = await self.extract_hidden_fields(page)
            print(f"추출된 필드: {list(hidden_fields.keys())}")
            
            # CSRF 토큰 확인
            csrf_token = hidden_fields.get('OWASP_CSRFTOKEN', '')
            if csrf_token:
                print(f"CSRF 토큰: {csrf_token[:20]}...")
            
            # CAPTCHA 정보 확인
            print("[3] CAPTCHA 확인")
            captcha_info = await self.extract_captcha_info(page)
            
            if captcha_info['hasImage']:
                print("⚠️ CAPTCHA 이미지 감지됨")
                print(f"VCID: {captcha_info['vcid']}")
                
                # CAPTCHA가 있으면 수동 입력 필요
                print("\n브라우저에서 CAPTCHA를 입력하세요...")
                captcha_value = input("CAPTCHA 값 입력: ")
                
                # CAPTCHA 입력
                captcha_input = await page.query_selector('input[name*="BDC_UserSpecifiedCaptchaInput"]')
                if captcha_input:
                    await captcha_input.fill(captcha_value)
            
            # 로그인 정보 입력 (인간같은 패턴)
            print("[4] 로그인 정보 입력")
            await self.human_type(page, '#username', 'kilmoon@mek-ics.com')
            await self.human_delay(500, 1000)
            await self.human_type(page, '#password', 'moon7410!@')
            await self.human_delay(800, 1200)
            
            # 폼 제출 전 최종 필드 확인
            print("[5] 폼 제출 준비")
            final_fields = await self.extract_hidden_fields(page)
            
            # 제출 버튼 클릭
            print("[6] 로그인 제출")
            submit_btn = await page.query_selector('#btnSubmit')
            if submit_btn:
                await self.human_delay(500, 800)
                await submit_btn.click()
            
            # 결과 대기
            await page.wait_for_timeout(5000)
            
            # 결과 확인
            current_url = page.url
            print(f"\n[결과] URL: {current_url}")
            
            if 'secondStep' in current_url:
                print("2차 인증 페이지로 이동됨")
                
                # 2차 인증 페이지의 CAPTCHA 확인
                captcha_2fa = await self.extract_captcha_info(page)
                if captcha_2fa['hasImage']:
                    print("2차 인증 페이지에도 CAPTCHA 있음")
            elif 'main.do' in current_url:
                print("✅ 로그인 성공!")
            
            # 로그 저장
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "csrf_token": csrf_token,
                "captcha_detected": captcha_info['hasImage'],
                "final_url": current_url,
                "hidden_fields": list(hidden_fields.keys())
            }
            
            log_file = Path(self.logs_dir) / f"login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            log_file.write_text(
                json.dumps(log_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            print("\n브라우저는 30초 후 종료됩니다...")
            await page.wait_for_timeout(30000)
            await browser.close()
    
    async def test_session_reuse(self):
        """저장된 세션으로 재접속 테스트"""
        print("\n[세션 재사용 테스트]")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                locale="ko-KR",
                timezone_id="Asia/Seoul",
                viewport=None,
                no_viewport=True
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 바로 메인 페이지로
            print("메인 페이지 직접 접속 시도...")
            await page.goto("https://www.bizmeka.com/app/main.do")
            await page.wait_for_timeout(3000)
            
            current_url = page.url
            print(f"현재 URL: {current_url}")
            
            if 'loginForm' not in current_url:
                print("✅ 세션 유지됨! 로그인 상태")
            else:
                print("❌ 세션 만료, 재로그인 필요")
            
            await page.wait_for_timeout(10000)
            await browser.close()

async def main():
    login = BizmekaAdvancedLogin()
    
    print("\n옵션 선택:")
    print("1. 수동 로그인 (세션 저장)")
    print("2. 자동 로그인 (CSRF 처리)")
    print("3. 세션 재사용 테스트")
    
    choice = input("\n선택 (1/2/3): ")
    
    if choice == "1":
        await login.manual_login_with_session_save()
    elif choice == "2":
        await login.automated_login_with_csrf()
    elif choice == "3":
        await login.test_session_reuse()

if __name__ == "__main__":
    asyncio.run(main())
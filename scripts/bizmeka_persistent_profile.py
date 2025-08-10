#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka Login - Persistent Profile Solution
Based on GPT5's analysis: Remove all stealth, use persistent profile
"""

import asyncio
from playwright.async_api import async_playwright
import os
import time
import json

class BizmekaPersistentLogin:
    def __init__(self):
        # 영구 프로필 디렉토리
        self.profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka"
        self.logs_dir = "logs/persistent"
        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    async def first_time_manual_setup(self):
        """첫 번째 수동 로그인을 위한 브라우저 실행"""
        print("\n[첫 번째 설정 - 수동 로그인 필요]")
        print("="*60)
        print("1. 브라우저가 열리면 수동으로 로그인하세요")
        print("2. 2차 인증까지 완료하세요")
        print("3. '로그인 상태 유지' 체크하세요")
        print("4. 완료 후 Enter를 누르세요")
        print("="*60)
        
        async with async_playwright() as p:
            # 최소한의 설정으로 브라우저 실행
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                # 아무런 stealth 플래그 없음
                args=[
                    '--start-maximized'
                ],
                viewport=None,
                no_viewport=True
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 로그인 페이지로 이동
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            
            print("\n브라우저에서 수동으로 로그인을 완료하세요...")
            print("완료되면 여기서 Enter를 누르세요...")
            input()
            
            # 쿠키 저장
            cookies = await browser.cookies()
            with open(f"{self.logs_dir}/cookies.json", "w", encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print("쿠키가 저장되었습니다.")
            await browser.close()
    
    async def automated_login_with_profile(self):
        """저장된 프로필로 자동 로그인"""
        print("\n[자동 로그인 - 저장된 프로필 사용]")
        print("="*60)
        
        async with async_playwright() as p:
            # 저장된 프로필로 브라우저 실행
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                # 최소한의 설정만
                args=[
                    '--start-maximized'
                ],
                viewport=None,
                no_viewport=True
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 직접 서비스 페이지로 이동 (로그인 상태 확인)
            print("서비스 페이지로 이동 중...")
            await page.goto("https://www.bizmeka.com/app/main.do")
            await page.wait_for_timeout(3000)
            
            # 로그인 상태 확인
            current_url = page.url
            print(f"현재 URL: {current_url}")
            
            if "loginForm" not in current_url:
                print("\n✅ SUCCESS! 자동 로그인 성공!")
                print("저장된 세션으로 로그인되었습니다.")
                
                # 페이지 내용 확인
                try:
                    user_info = await page.text_content('.user-info')
                    print(f"사용자 정보: {user_info}")
                except:
                    pass
            else:
                print("\n세션이 만료되었습니다. 재로그인 시도...")
                
                # 로그인 필요
                await page.fill('#username', 'kilmoon@mek-ics.com')
                await page.fill('#password', 'moon7410!@')
                await page.click('#btnSubmit')
                
                await page.wait_for_timeout(5000)
                
                final_url = page.url
                if 'secondStep' in final_url:
                    print("2차 인증이 필요합니다.")
                else:
                    print("로그인 성공!")
            
            # 스크린샷 저장
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"{self.logs_dir}/session_{timestamp}.png")
            
            print("\n브라우저는 30초 후 종료됩니다...")
            await page.wait_for_timeout(30000)
            
            await browser.close()
    
    async def test_minimal_automation(self):
        """최소한의 자동화로 테스트"""
        print("\n[최소 자동화 테스트]")
        print("="*60)
        
        async with async_playwright() as p:
            # 완전히 깨끗한 설정
            browser = await p.chromium.launch(
                headless=False,
                # 플래그 없음
                args=[]
            )
            
            context = await browser.new_context(
                # 기본 설정만
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # 탐지 확인
            detection_check = await page.evaluate("""
                () => {
                    return {
                        webdriver: navigator.webdriver,
                        automation: window.navigator.automation,
                        chrome: !!window.chrome,
                        plugins: navigator.plugins.length
                    };
                }
            """)
            
            print("브라우저 속성:")
            print(json.dumps(detection_check, indent=2))
            
            # 로그인 페이지
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(2000)
            
            # 단순 입력
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            
            print("\n로그인 시도 중...")
            await page.click('#btnSubmit')
            
            await page.wait_for_timeout(5000)
            
            url = page.url
            print(f"결과 URL: {url}")
            
            if 'secondStep' in url:
                print("❌ 2차 인증 트리거됨")
            else:
                print("✅ 2차 인증 없이 통과!")
            
            await page.wait_for_timeout(10000)
            await browser.close()

async def main():
    login = BizmekaPersistentLogin()
    
    print("\n무엇을 실행하시겠습니까?")
    print("1. 첫 번째 수동 설정 (프로필 생성)")
    print("2. 저장된 프로필로 자동 로그인")
    print("3. 최소 자동화 테스트")
    
    choice = input("\n선택 (1/2/3): ")
    
    if choice == "1":
        await login.first_time_manual_setup()
    elif choice == "2":
        await login.automated_login_with_profile()
    elif choice == "3":
        await login.test_minimal_automation()
    else:
        print("잘못된 선택")

if __name__ == "__main__":
    asyncio.run(main())
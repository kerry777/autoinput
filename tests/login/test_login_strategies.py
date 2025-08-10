#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
로그인 자동화 전략 테스트
반자동 → 완전자동 단계별 구현
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os
from datetime import datetime
from typing import Dict, Optional
import keyring  # 보안 저장소
import getpass

class LoginAutomation:
    """로그인 자동화 단계별 구현"""
    
    def __init__(self):
        self.credentials_file = "config/credentials.json"
        self.screenshot_dir = "logs/screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def level1_manual_login(self, url: str):
        """
        Level 1: 완전 수동 로그인
        - 브라우저만 자동으로 열어줌
        - 사용자가 직접 입력
        """
        print("\n=== Level 1: 완전 수동 로그인 ===")
        print("브라우저를 열어드립니다. 직접 로그인해주세요.")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # GUI 표시
                slow_mo=100      # 천천히 동작
            )
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.goto(url)
            print(f"URL 열림: {url}")
            print("수동으로 로그인 후 Enter를 눌러주세요...")
            input()
            
            # 로그인 후 쿠키 저장
            cookies = await context.cookies()
            self.save_cookies(cookies)
            print(f"쿠키 {len(cookies)}개 저장됨")
            
            await browser.close()
    
    async def level2_semi_auto_login(self, url: str):
        """
        Level 2: 반자동 로그인
        - ID/PW는 자동 입력
        - 보안 문자(CAPTCHA)는 수동
        - 공인인증서는 수동
        """
        print("\n=== Level 2: 반자동 로그인 ===")
        
        # 저장된 자격증명 불러오기 (없으면 입력받기)
        credentials = self.get_credentials()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.goto(url)
            
            # ID/PW 자동 입력
            try:
                # 일반적인 셀렉터들
                username_selectors = [
                    'input[name="username"]',
                    'input[name="userid"]', 
                    'input[name="id"]',
                    'input[type="text"]',
                    '#username',
                    '#userid'
                ]
                
                password_selectors = [
                    'input[name="password"]',
                    'input[name="pw"]',
                    'input[type="password"]',
                    '#password'
                ]
                
                # Username 입력
                for selector in username_selectors:
                    if await page.is_visible(selector):
                        await page.fill(selector, credentials['username'])
                        print(f"✓ ID 자동 입력: {credentials['username']}")
                        break
                
                # Password 입력
                for selector in password_selectors:
                    if await page.is_visible(selector):
                        await page.fill(selector, credentials['password'])
                        print("✓ Password 자동 입력: ***")
                        break
                
                # 스크린샷 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(
                    path=f"{self.screenshot_dir}/login_{timestamp}.png"
                )
                
                print("\n⚠️  다음 작업은 수동으로 진행하세요:")
                print("1. CAPTCHA가 있다면 입력")
                print("2. 공인인증서가 필요하면 선택")
                print("3. 로그인 버튼 클릭")
                print("\n완료 후 Enter를 눌러주세요...")
                input()
                
                # 로그인 성공 확인
                await page.wait_for_load_state('networkidle')
                cookies = await context.cookies()
                self.save_cookies(cookies)
                print(f"✓ 로그인 완료, 쿠키 {len(cookies)}개 저장")
                
            except Exception as e:
                print(f"❌ 자동 입력 실패: {e}")
                print("수동으로 진행해주세요...")
                input()
            
            await browser.close()
    
    async def level3_full_auto_login(self, url: str):
        """
        Level 3: 완전 자동 로그인
        - 저장된 쿠키로 세션 복원
        - 로그인 상태 자동 확인
        - 실패 시 Level 2로 폴백
        """
        print("\n=== Level 3: 완전 자동 로그인 ===")
        
        cookies = self.load_cookies()
        if not cookies:
            print("저장된 쿠키 없음. 반자동 모드로 전환...")
            return await self.level2_semi_auto_login(url)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # 백그라운드
            context = await browser.new_context()
            
            # 쿠키 복원
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            
            # 로그인 상태 확인
            login_indicators = [
                'text=로그아웃',
                'text=Logout', 
                'text=마이페이지',
                'text=My Page',
                '.user-info',
                '#user-menu'
            ]
            
            is_logged_in = False
            for indicator in login_indicators:
                if await page.is_visible(indicator):
                    is_logged_in = True
                    break
            
            if is_logged_in:
                print("✓ 자동 로그인 성공!")
                
                # 작업 수행
                await self.perform_automated_task(page)
                
            else:
                print("❌ 쿠키 만료. 재로그인 필요...")
                await browser.close()
                return await self.level2_semi_auto_login(url)
            
            await browser.close()
    
    async def perform_automated_task(self, page):
        """로그인 후 자동 작업 수행"""
        print("\n📋 자동 작업 수행 중...")
        
        # 예: 데이터 수집
        try:
            # 특정 페이지로 이동
            # await page.goto('/data')
            
            # 데이터 추출
            # data = await page.text_content('.data-content')
            
            print("✓ 작업 완료")
            
        except Exception as e:
            print(f"❌ 작업 실패: {e}")
    
    def get_credentials(self) -> Dict[str, str]:
        """자격증명 관리 (보안 저장)"""
        
        # 1. 환경변수에서 읽기
        username = os.getenv('AUTO_USERNAME')
        password = os.getenv('AUTO_PASSWORD')
        
        if username and password:
            return {'username': username, 'password': password}
        
        # 2. keyring에서 읽기 (Windows 자격증명 관리자)
        try:
            username = keyring.get_password('autoinput', 'username')
            password = keyring.get_password('autoinput', 'password')
            
            if username and password:
                return {'username': username, 'password': password}
        except:
            pass
        
        # 3. 사용자 입력
        print("\n자격증명 입력 (한 번만 입력하면 저장됩니다)")
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        
        # keyring에 저장
        try:
            keyring.set_password('autoinput', 'username', username)
            keyring.set_password('autoinput', 'password', password)
            print("✓ 자격증명이 안전하게 저장되었습니다")
        except:
            print("⚠️  자격증명 저장 실패 (다음에 다시 입력 필요)")
        
        return {'username': username, 'password': password}
    
    def save_cookies(self, cookies):
        """쿠키 저장"""
        os.makedirs('config', exist_ok=True)
        with open('config/cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
    
    def load_cookies(self) -> Optional[list]:
        """쿠키 불러오기"""
        if os.path.exists('config/cookies.json'):
            with open('config/cookies.json', 'r') as f:
                return json.load(f)
        return None


async def test_sites():
    """다양한 사이트 테스트"""
    
    automation = LoginAutomation()
    
    # 테스트 사이트 목록
    test_sites = {
        '1': {
            'name': 'web-scraping.dev (테스트용)',
            'url': 'https://web-scraping.dev/login',
            'note': '가장 안전한 테스트 환경'
        },
        '2': {
            'name': 'GitHub (실제 서비스)',
            'url': 'https://github.com/login',
            'note': '2FA 있음, 실제 계정 필요'
        },
        '3': {
            'name': 'Demo Site',
            'url': 'https://demo.opencart.com/admin',
            'note': 'Username: demo, Password: demo'
        },
        '4': {
            'name': '장기요양 포털 (실전)',
            'url': 'https://www.longtermcare.or.kr',
            'note': '공인인증서 필수, 실제 계정 필요'
        }
    }
    
    print("\n=== 로그인 테스트 사이트 선택 ===")
    for key, site in test_sites.items():
        print(f"{key}. {site['name']}")
        print(f"   URL: {site['url']}")
        print(f"   참고: {site['note']}\n")
    
    choice = input("테스트할 사이트 선택 (1-4): ")
    
    if choice in test_sites:
        site = test_sites[choice]
        
        print(f"\n선택: {site['name']}")
        print("\n로그인 레벨 선택:")
        print("1. Level 1 - 완전 수동")
        print("2. Level 2 - 반자동 (ID/PW 자동)")
        print("3. Level 3 - 완전 자동 (쿠키 사용)")
        
        level = input("\n레벨 선택 (1-3): ")
        
        if level == '1':
            await automation.level1_manual_login(site['url'])
        elif level == '2':
            await automation.level2_semi_auto_login(site['url'])
        elif level == '3':
            await automation.level3_full_auto_login(site['url'])
        else:
            print("잘못된 선택")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║     로그인 자동화 단계별 테스트          ║
    ║                                          ║
    ║  Level 1: 완전 수동 (브라우저만 열기)    ║
    ║  Level 2: 반자동 (ID/PW 자동 입력)      ║
    ║  Level 3: 완전 자동 (쿠키 세션 복원)    ║
    ╚══════════════════════════════════════════╝
    """)
    
    asyncio.run(test_sites())
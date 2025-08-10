#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
스마트 로그인 매니저 - 사이트별 특성을 자동 처리
"""

import json
from pathlib import Path
from playwright.async_api import Page, BrowserContext


class SmartLoginManager:
    """각 사이트 특성에 맞게 자동으로 로그인 처리"""
    
    def __init__(self):
        self.sites_dir = Path("sites")
        self.data_dir = Path("data")
        
    async def login(self, site_id: str, page: Page) -> bool:
        """
        사이트별 최적 로그인 전략 자동 선택
        
        1. 쿠키 있으면 → 쿠키 로그인 (Bizmeka)
        2. 쿠키 없으면 → 직접 로그인 (MEK-ICS)
        3. 2FA 필요하면 → 수동 로그인 후 쿠키 저장
        """
        
        site_id = site_id.lower()
        
        # 1단계: 쿠키 확인
        cookie_paths = [
            self.sites_dir / site_id / "data" / "cookies.json",
            self.data_dir / f"{site_id}_cookies.json",
            self.data_dir / "bizmeka_cookies.json"  # 레거시 호환
        ]
        
        for cookie_path in cookie_paths:
            if cookie_path.exists():
                print(f"[Smart Login] Found cookies for {site_id}")
                success = await self._login_with_cookies(site_id, page, cookie_path)
                if success:
                    return True
                print(f"[Smart Login] Cookie expired, trying direct login...")
        
        # 2단계: 직접 로그인
        settings_path = self.sites_dir / site_id / "config" / "settings.json"
        if settings_path.exists():
            print(f"[Smart Login] Trying direct login for {site_id}")
            return await self._direct_login(site_id, page, settings_path)
        
        # 3단계: 수동 로그인 안내
        print(f"\n[Smart Login] {site_id} requires manual login")
        print("Run manual login first to save cookies:")
        print(f"  python scripts/{site_id}_manual_login.py")
        return False
    
    async def _login_with_cookies(self, site_id: str, page: Page, cookie_path: Path) -> bool:
        """쿠키로 로그인"""
        try:
            # 쿠키 로드
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # 쿠키 주입
            await page.context.add_cookies(cookies)
            print(f"  Loaded {len(cookies)} cookies")
            
            # 사이트별 메인 페이지
            main_urls = {
                'bizmeka': 'https://www.bizmeka.com/app/main.do',
                'mekics': 'https://it.mek-ics.com/mekics/main/main.do'
            }
            
            # 메인 페이지 접속
            main_url = main_urls.get(site_id, '/')
            await page.goto(main_url)
            await page.wait_for_timeout(3000)
            
            # 로그인 확인
            current_url = page.url
            if 'login' not in current_url.lower():
                print(f"  ✓ Logged in with cookies!")
                return True
            else:
                print(f"  ✗ Cookies expired")
                return False
                
        except Exception as e:
            print(f"  Cookie login failed: {e}")
            return False
    
    async def _direct_login(self, site_id: str, page: Page, settings_path: Path) -> bool:
        """ID/PW로 직접 로그인"""
        try:
            # 설정 로드
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            credentials = settings.get('credentials', {})
            username = credentials.get('username', '')
            password = credentials.get('password', '')
            
            # 로그인 URL
            login_urls = {
                'mekics': 'https://it.mek-ics.com/mekics/login/login.do',
                'bizmeka': 'https://ezsso.bizmeka.com/loginForm.do'
            }
            
            login_url = login_urls.get(site_id)
            if not login_url:
                return False
            
            # 로그인 페이지 이동
            await page.goto(login_url)
            await page.wait_for_timeout(3000)
            
            # 사이트별 셀렉터
            selectors = {
                'mekics': {
                    'username': 'input[name="userid"]',
                    'password': 'input[type="password"]'
                },
                'bizmeka': {
                    'username': 'input[name="userId"]',
                    'password': 'input[name="userPw"]'
                }
            }
            
            site_selectors = selectors.get(site_id, {})
            
            # 로그인 입력
            await page.fill(site_selectors['username'], username)
            await page.fill(site_selectors['password'], password)
            await page.keyboard.press('Enter')
            
            # 결과 대기
            await page.wait_for_timeout(5000)
            
            # 성공 확인
            if 'login' not in page.url.lower():
                print(f"  ✓ Direct login successful!")
                
                # 쿠키 저장
                await self._save_cookies(site_id, page)
                return True
            else:
                print(f"  ✗ Direct login failed (2FA required?)")
                return False
                
        except Exception as e:
            print(f"  Direct login failed: {e}")
            return False
    
    async def _save_cookies(self, site_id: str, page: Page):
        """로그인 성공 후 쿠키 저장"""
        cookies = await page.context.cookies()
        
        # 저장 경로
        cookie_path = self.sites_dir / site_id / "data" / "cookies.json"
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print(f"  Saved {len(cookies)} cookies for future use")


# 사용 예시
async def example():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        smart = SmartLoginManager()
        
        # 알아서 처리 (쿠키 있으면 쿠키, 없으면 직접 로그인)
        await smart.login("bizmeka", page)  # 쿠키 사용
        # await smart.login("mekics", page)   # 직접 로그인
        
        await page.wait_for_timeout(60000)
        await browser.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example())
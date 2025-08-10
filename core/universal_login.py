#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
범용 로그인 매니저 - 사이트 ID만으로 자동 로그인
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import Page, BrowserContext


class UniversalLoginManager:
    """모든 사이트 로그인을 처리하는 범용 매니저"""
    
    def __init__(self):
        self.docs_dir = Path("docs")
        self.sites_dir = Path("sites")
        self.site_configs = {}
        self._load_all_site_configs()
    
    def _load_all_site_configs(self):
        """모든 SITE_DB 문서 자동 로드"""
        for doc_file in self.docs_dir.glob("SITE_DB_*.md"):
            site_name = doc_file.stem.replace("SITE_DB_", "").lower()
            self.site_configs[site_name] = self._parse_site_doc(doc_file)
    
    def _parse_site_doc(self, doc_path: Path) -> Dict[str, Any]:
        """SITE_DB 문서 파싱"""
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        config = {}
        
        # YAML 블록 추출
        yaml_pattern = r'```yaml\n(.*?)\n```'
        yaml_matches = re.findall(yaml_pattern, content, re.DOTALL)
        
        for yaml_content in yaml_matches:
            try:
                data = yaml.safe_load(yaml_content)
                if isinstance(data, dict):
                    # Authentication 섹션 처리
                    if 'Authentication' in data:
                        auth = data['Authentication']
                        config['login_url'] = auth.get('URL', '')
                        config['selectors'] = auth.get('Selectors', {})
                    else:
                        config.update(data)
            except:
                continue
        
        # 로그인 URL 백업 추출
        if not config.get('login_url'):
            url_match = re.search(r'\*\*로그인 URL\*\*.*?\|\s*(https?://[^\s]+)', content)
            if url_match:
                config['login_url'] = url_match.group(1)
        
        # 사이트별 설정 파일 확인
        site_name = doc_path.stem.replace("SITE_DB_", "").lower()
        settings_path = self.sites_dir / site_name / "config" / "settings.json"
        
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                config['credentials'] = settings.get('credentials', {})
        
        return config
    
    async def login(self, site_id: str, page: Page) -> bool:
        """사이트 ID만으로 자동 로그인"""
        
        site_id = site_id.lower()
        
        # 설정 확인
        if site_id not in self.site_configs:
            print(f"Error: No configuration found for site '{site_id}'")
            print(f"Available sites: {list(self.site_configs.keys())}")
            return False
        
        config = self.site_configs[site_id]
        
        # 필수 정보 확인
        if 'login_url' not in config:
            print(f"Error: No login URL found for {site_id}")
            return False
        
        if 'credentials' not in config:
            print(f"Error: No credentials found for {site_id}")
            return False
        
        print(f"\n{'='*50}")
        print(f"Universal Login: {site_id.upper()}")
        print(f"{'='*50}")
        
        # 로그인 페이지 이동
        print(f"1. Navigating to: {config['login_url']}")
        await page.goto(config['login_url'])
        await page.wait_for_timeout(3000)
        
        # 사용자명 입력
        username = config['credentials'].get('username', '')
        password = config['credentials'].get('password', '')
        
        print(f"2. Entering username: {username}")
        
        # 여러 셀렉터 시도
        username_selectors = [
            config.get('selectors', {}).get('username'),
            'input[name="userId"]',
            'input[name="userid"]', 
            'input[name="username"]',
            'input[name="id"]',
            '#userId',
            '#username',
            'input[type="text"]:first-of-type'
        ]
        
        for selector in username_selectors:
            if selector:
                try:
                    await page.fill(selector, username)
                    print(f"   Success with: {selector}")
                    break
                except:
                    continue
        
        # 비밀번호 입력
        print("3. Entering password")
        password_selectors = [
            config.get('selectors', {}).get('password'),
            'input[type="password"]',
            'input[name="password"]',
            'input[name="passwd"]',
            '#password'
        ]
        
        for selector in password_selectors:
            if selector:
                try:
                    await page.fill(selector, password)
                    break
                except:
                    continue
        
        # 로그인 시도
        print("4. Attempting login")
        
        # 제출 버튼 또는 Enter
        submit_selector = config.get('selectors', {}).get('submit')
        if submit_selector:
            try:
                await page.click(submit_selector)
            except:
                await page.keyboard.press('Enter')
        else:
            await page.keyboard.press('Enter')
        
        # 결과 대기
        print("5. Waiting for result...")
        await page.wait_for_timeout(5000)
        
        # 성공 여부 확인
        current_url = page.url
        if 'login' not in current_url.lower():
            print(f"\nSUCCESS! Logged in to {site_id}")
            print(f"Current URL: {current_url}")
            
            # 쿠키 저장
            await self._save_cookies(site_id, page.context)
            return True
        else:
            print(f"\nLogin might have failed or requires 2FA")
            print(f"Current URL: {current_url}")
            return False
    
    async def _save_cookies(self, site_id: str, context: BrowserContext):
        """쿠키 저장"""
        cookies = await context.cookies()
        cookie_path = self.sites_dir / site_id / "data" / "cookies.json"
        cookie_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print(f"Cookies saved: {len(cookies)} cookies")
    
    async def load_cookies(self, site_id: str, context: BrowserContext) -> bool:
        """저장된 쿠키 로드"""
        cookie_path = self.sites_dir / site_id / "data" / "cookies.json"
        
        if cookie_path.exists():
            with open(cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print(f"Loaded {len(cookies)} cookies for {site_id}")
            return True
        return False
    
    def get_site_config(self, site_id: str) -> Dict[str, Any]:
        """사이트 설정 반환"""
        return self.site_configs.get(site_id.lower(), {})


# 사용 예시
async def example_usage():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 범용 로그인 매니저
        login_manager = UniversalLoginManager()
        
        # 사이트 ID만으로 로그인!
        await login_manager.login("mekics", page)  # MEK-ICS 자동 로그인
        # await login_manager.login("bizmeka", page)  # Bizmeka 자동 로그인
        
        await page.wait_for_timeout(60000)
        await browser.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
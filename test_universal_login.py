#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
범용 로그인 테스트 - 사이트 ID만으로 로그인
"""

import asyncio
from pathlib import Path
import sys

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.universal_login import UniversalLoginManager
from playwright.async_api import async_playwright


async def test_login():
    """범용 로그인 테스트"""
    
    print("\n" + "="*60)
    print("UNIVERSAL LOGIN TEST")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # 범용 로그인 매니저 생성
        login_manager = UniversalLoginManager()
        
        # 사이트 목록 확인
        print("\nAvailable sites:")
        for site_id in login_manager.site_configs.keys():
            config = login_manager.site_configs[site_id]
            print(f"  - {site_id}: {config.get('login_url', 'No URL')}")
        
        # MEK-ICS 로그인 테스트
        print("\nTesting MEK-ICS login...")
        success = await login_manager.login("mekics", page)
        
        if success:
            print("\n✅ LOGIN SUCCESS!")
            print("You can now use the page for any operation")
            
            # 3분 대기
            print("\nBrowser will stay open for 3 minutes...")
            await page.wait_for_timeout(180000)
        else:
            print("\n❌ LOGIN FAILED")
            print("Please check the configuration")
            
            # 1분 대기
            await page.wait_for_timeout(60000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_login())
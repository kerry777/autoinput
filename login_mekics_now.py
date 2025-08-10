#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 로그인 - 범용 모듈 사용
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from core.universal_login import UniversalLoginManager
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # 범용 로그인 매니저로 로그인
        login_manager = UniversalLoginManager()
        await login_manager.login("mekics", page)
        
        print("\nMEK-ICS logged in. Browser open for 3 minutes.")
        await page.wait_for_timeout(180000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
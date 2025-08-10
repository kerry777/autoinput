#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
범용 실행기 - 사이트 ID만 받아서 실행
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.universal_login import UniversalLoginManager
from playwright.async_api import async_playwright


async def run(site_id):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        login_manager = UniversalLoginManager()
        success = await login_manager.login(site_id, page)
        
        if success:
            print(f"\n{site_id.upper()} login success! Browser open for 3 minutes.")
            await page.wait_for_timeout(180000)
        else:
            print(f"\n{site_id.upper()} login failed!")
            await page.wait_for_timeout(30000)
            
        await browser.close()


if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else "mekics"
    asyncio.run(run(site))
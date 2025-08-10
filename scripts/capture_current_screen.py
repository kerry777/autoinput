#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
현재 화면 즉시 캡처
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def capture_now():
    """현재 화면 즉시 캡처"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/realtime", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Bizmeka 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        # 현재 화면 캡처
        screenshot_path = f"logs/realtime/screen_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
        
        # URL과 제목
        print(f"URL: {page.url}")
        print(f"Title: {await page.title()}")
        
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_now())
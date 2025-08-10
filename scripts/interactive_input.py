#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
대화형 입력 - 사용자 지시에 따라 입력
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def capture_and_wait():
    """현재 화면 캡처하고 대기"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/interactive", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        # 현재 화면 캡처
        screenshot_path = f"logs/interactive/current_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"현재 화면 캡처: {screenshot_path}")
        
        print("브라우저 열려있음. 지시를 기다립니다...")
        await page.wait_for_timeout(60000)  # 60초 대기
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_and_wait())
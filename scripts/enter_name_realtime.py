#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이름 입력 - 이길문
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def enter_name():
    """이름 필드에 이길문 입력"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/realtime", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 현재 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        # 이름 입력 필드 찾기
        name_selectors = [
            'input[name*="name"]',
            'input[id*="name"]',
            'input[placeholder*="이름"]',
            'input[type="text"]:visible'
        ]
        
        for selector in name_selectors:
            try:
                input_field = await page.query_selector(selector)
                if input_field and await input_field.is_visible():
                    await input_field.click()
                    await input_field.fill("이길문")
                    print(f"이름 입력 완료: 이길문")
                    
                    # 스크린샷
                    screenshot_path = f"logs/realtime/after_name_{timestamp}.png"
                    await page.screenshot(path=screenshot_path)
                    print(f"Screenshot: {screenshot_path}")
                    break
            except:
                continue
        
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(enter_name())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이길문 입력하고 엔터
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def type_name():
    """이길문 입력하고 엔터"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/interactive", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        # 현재 포커스된 곳에 바로 입력
        print("이길문 입력 중...")
        await page.keyboard.type("이길문")
        print("입력 완료: 이길문")
        
        await page.wait_for_timeout(500)
        
        print("엔터 키 입력...")
        await page.keyboard.press("Enter")
        print("엔터 완료")
        
        await page.wait_for_timeout(3000)
        
        # 결과 화면 캡처
        screenshot_path = f"logs/interactive/after_name_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"결과 화면: {screenshot_path}")
        
        print("브라우저 30초간 열려있음...")
        await page.wait_for_timeout(30000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(type_name())
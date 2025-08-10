#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이름 입력하고 엔터
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def enter_name_and_submit():
    """이름 입력하고 엔터"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/realtime", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 현재 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        print("이름 입력 중...")
        
        # 첫번째 보이는 텍스트 입력 필드에 입력
        first_input = await page.query_selector('input[type="text"]:visible')
        if not first_input:
            first_input = await page.query_selector('input[type="text"]')
        
        if first_input:
            await first_input.click()
            await first_input.fill("이길문")
            print("이름 입력: 이길문")
            
            # 엔터 키 입력
            await page.keyboard.press("Enter")
            print("엔터 키 입력 완료")
            
            await page.wait_for_timeout(3000)
            
            # 결과 스크린샷
            screenshot_path = f"logs/realtime/after_enter_{timestamp}.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot: {screenshot_path}")
        
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(enter_name_and_submit())
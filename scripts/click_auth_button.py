#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
본인인증 버튼 클릭
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def click_auth_button():
    """본인인증 버튼 클릭"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/realtime", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        print("본인인증 버튼 클릭 중...")
        
        # 본인인증 버튼 클릭 (빨간색 버튼)
        button_clicked = False
        
        # 여러 선택자 시도
        button_selectors = [
            'button:has-text("본인인증")',
            'a:has-text("본인인증")',
            '.btn-danger',
            'button.btn.btn-danger',
            '[class*="btn-danger"]',
            'button[style*="red"]'
        ]
        
        for selector in button_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    print(f"본인인증 버튼 클릭 완료! (selector: {selector})")
                    button_clicked = True
                    break
            except:
                continue
        
        if not button_clicked:
            # 두 번째 버튼 시도 (보통 첫번째는 취소, 두번째가 본인인증)
            all_buttons = await page.query_selector_all('button')
            if len(all_buttons) >= 2:
                await all_buttons[1].click()
                print("두 번째 버튼 클릭 (본인인증)")
                button_clicked = True
        
        await page.wait_for_timeout(3000)
        
        # 결과 스크린샷
        screenshot_path = f"logs/realtime/after_auth_click_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
        
        # URL 변경 확인
        new_url = page.url
        print(f"Current URL: {new_url}")
        
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(click_auth_button())
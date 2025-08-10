#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이메일 인증번호 받기 클릭
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def click_email_verification():
    """이메일로 인증번호 받기 클릭"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/verification", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 현재 페이지로 이동 (2차 인증 페이지)
        await page.goto("https://ezsso.bizmeka.com/rule/secondStepVerifView.do")
        await page.wait_for_timeout(2000)
        
        print("이메일로 인증번호 받기 버튼 찾는 중...")
        
        # 이메일 인증 버튼 찾기
        button_selectors = [
            'button:has-text("이메일로 인증번호 받기")',
            'a:has-text("이메일로 인증번호 받기")',
            'button:has-text("이메일")',
            '[onclick*="email"]',
            'button.btn'
        ]
        
        for selector in button_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    print(f"버튼 클릭 완료: {selector}")
                    break
            except:
                continue
        
        await page.wait_for_timeout(3000)
        
        # 결과 스크린샷
        screenshot_path = f"logs/verification/after_email_click_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot: {screenshot_path}")
        
        print("브라우저 30초간 열려있음...")
        await page.wait_for_timeout(30000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(click_email_verification())
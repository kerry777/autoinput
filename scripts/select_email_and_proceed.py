#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이메일 인증 선택 후 본인인증 버튼 클릭
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def select_email_auth():
    """이메일 인증 선택 후 진행"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs/realtime", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 페이지로 이동
        await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
        await page.wait_for_timeout(2000)
        
        print("Step 1: 이메일 인증 옵션 선택...")
        
        # 세 번째 라디오 버튼 클릭 (이메일 인증)
        radio_buttons = await page.query_selector_all('input[type="radio"]')
        if len(radio_buttons) >= 3:
            await radio_buttons[2].click()  # 0-indexed, 세번째는 index 2
            print("이메일 인증 선택 완료")
            await page.wait_for_timeout(1000)
        
        print("Step 2: 본인인증 버튼 클릭...")
        
        # 본인인증 버튼 클릭
        auth_button = await page.query_selector('a:has-text("본인인증")')
        if not auth_button:
            auth_button = await page.query_selector('.btn-danger')
        
        if auth_button:
            await auth_button.click()
            print("본인인증 버튼 클릭 완료")
        
        await page.wait_for_timeout(3000)
        
        print("Step 3: 다음 화면 확인...")
        
        # 이름 입력 필드가 나타났는지 확인
        name_input = await page.query_selector('input[placeholder*="이름"]')
        if not name_input:
            name_input = await page.query_selector('input[name*="name"]')
        if not name_input:
            name_input = await page.query_selector('input#idEM')
        
        if name_input and await name_input.is_visible():
            print("Step 4: 이름 입력 필드 발견! 이길문 입력...")
            await name_input.click()
            await name_input.fill("이길문")
            print("이름 입력 완료: 이길문")
            
            print("Step 5: 엔터 키 입력...")
            await page.keyboard.press("Enter")
            print("엔터 키 입력 완료")
            
            await page.wait_for_timeout(3000)
        
        # 결과 스크린샷
        screenshot_path = f"logs/realtime/email_auth_result_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"Screenshot: {screenshot_path}")
        
        print("브라우저는 10초 후 닫힙니다...")
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(select_email_auth())
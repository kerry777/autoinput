#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 로그인 - 지금 당장
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def login_now():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        print("\nMEK-ICS LOGIN")
        print("="*50)
        
        # 로그인 페이지 직접 접속
        print("1. Going to login page...")
        await page.goto("https://it.mek-ics.com/mekics/login/login.do")
        await page.wait_for_timeout(3000)
        
        # 로그인 필드 확인
        print("2. Checking login fields...")
        
        # ID 입력
        print(f"3. Entering username: {config['credentials']['username']}")
        try:
            await page.fill('input[name="userId"]', config['credentials']['username'])
        except:
            try:
                await page.fill('input[name="userid"]', config['credentials']['username'])
            except:
                await page.fill('input[type="text"]', config['credentials']['username'])
        
        await page.wait_for_timeout(500)
        
        # 비밀번호 입력
        print("4. Entering password...")
        await page.fill('input[type="password"]', config['credentials']['password'])
        await page.wait_for_timeout(500)
        
        # 스크린샷
        await page.screenshot(path=str(data_dir / f"login_ready_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
        
        # 로그인 버튼 클릭
        print("5. Clicking login button...")
        try:
            await page.click('button[type="submit"]')
        except:
            try:
                await page.click('input[type="submit"]')
            except:
                await page.click('#loginBtn')
        
        print("\n6. Waiting for login result...")
        await page.wait_for_timeout(5000)
        
        # 현재 URL 확인
        current_url = page.url
        print(f"\nCurrent URL: {current_url}")
        
        if "main" in current_url:
            print("SUCCESS! Logged in successfully!")
            
            # 쿠키 저장
            cookies = await context.cookies()
            with open(data_dir / "cookies_new.json", 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"Cookies saved: {len(cookies)} cookies")
            
            # 스크린샷
            screenshot = data_dir / f"main_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot))
            print(f"Screenshot: {screenshot}")
            
        elif "2fa" in current_url.lower() or "otp" in current_url.lower():
            print("\n2FA REQUIRED!")
            print("Please complete 2FA manually in the browser")
            print("Waiting 60 seconds for 2FA completion...")
            
            await page.wait_for_timeout(60000)
            
            # 2FA 후 URL 확인
            current_url = page.url
            if "main" in current_url:
                print("2FA completed! Now on main page")
                
                # 쿠키 저장
                cookies = await context.cookies()
                with open(data_dir / "cookies_new.json", 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print(f"Cookies saved after 2FA: {len(cookies)} cookies")
        else:
            print(f"Unknown state. Current URL: {current_url}")
            print("Please check the browser window")
        
        print("\n" + "="*50)
        print("Browser will remain open for 3 minutes")
        print("="*50)
        
        # 3분 대기
        await page.wait_for_timeout(180000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(login_now())
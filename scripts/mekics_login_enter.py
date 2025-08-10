#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 로그인 - Enter 키 사용
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def login_with_enter():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        print("\nMEK-ICS LOGIN WITH ENTER KEY")
        print("="*50)
        
        # 로그인 페이지
        print("1. Opening login page...")
        await page.goto("https://it.mek-ics.com/mekics/login/login.do")
        await page.wait_for_timeout(3000)
        
        # ID 입력 - 여러 선택자 시도
        print(f"2. Entering ID: {config['credentials']['username']}")
        id_entered = False
        
        for selector in ['input[name="userId"]', 'input[name="userid"]', '#userId', '#userid', 'input[type="text"]:first-of-type']:
            try:
                await page.fill(selector, config['credentials']['username'])
                id_entered = True
                print(f"   ID entered with selector: {selector}")
                break
            except:
                continue
        
        if not id_entered:
            print("   Warning: Could not enter ID")
        
        await page.wait_for_timeout(500)
        
        # 비밀번호 입력
        print("3. Entering password...")
        await page.fill('input[type="password"]', config['credentials']['password'])
        await page.wait_for_timeout(500)
        
        # Enter 키로 로그인
        print("4. Pressing Enter to login...")
        await page.keyboard.press('Enter')
        
        print("5. Waiting for response...")
        await page.wait_for_timeout(7000)
        
        # URL 확인
        current_url = page.url
        print(f"\nResult URL: {current_url}")
        
        if "main" in current_url or "Main" in current_url:
            print("\n✓ LOGIN SUCCESS!")
            
            # 쿠키 저장
            cookies = await context.cookies()
            cookie_file = data_dir / "cookies.json"
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print(f"Cookies saved: {len(cookies)} cookies to {cookie_file}")
            
            # 스크린샷
            screenshot = data_dir / f"logged_in_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot))
            print(f"Screenshot: {screenshot}")
            
            print("\n" + "="*50)
            print("LOGGED IN SUCCESSFULLY!")
            print("Browser will stay open for 3 minutes")
            print("="*50)
            
        else:
            print("\nLogin might have failed or requires 2FA")
            print("Please check the browser window")
            
            # 2FA 대기
            if "2fa" in current_url.lower() or "otp" in current_url.lower() or "auth" in current_url.lower():
                print("\n2FA DETECTED!")
                print("Please complete 2FA in the browser")
                print("Waiting 60 seconds...")
                
                await page.wait_for_timeout(60000)
                
                # 재확인
                if "main" in page.url:
                    print("2FA completed successfully!")
                    cookies = await context.cookies()
                    with open(data_dir / "cookies.json", 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    print("Cookies saved after 2FA")
        
        # 브라우저 유지
        await page.wait_for_timeout(180000)  # 3분
        await browser.close()


if __name__ == "__main__":
    asyncio.run(login_with_enter())
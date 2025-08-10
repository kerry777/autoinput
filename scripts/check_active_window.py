#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
현재 활성 브라우저 창 확인 및 캡처
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def check_active_window():
    """현재 활성 창 확인"""
    
    print("\n[CHECKING ACTIVE WINDOW]")
    print("="*60)
    
    os.makedirs("logs/realtime", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async with async_playwright() as p:
        # 기존 브라우저에 연결 시도
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100
        )
        
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 현재 열려있는 모든 페이지 확인
            all_contexts = browser.contexts
            print(f"\n[CONTEXTS] Found {len(all_contexts)} contexts")
            
            for i, ctx in enumerate(all_contexts):
                pages = ctx.pages
                print(f"\nContext {i+1}: {len(pages)} pages")
                
                for j, pg in enumerate(pages):
                    url = pg.url
                    title = await pg.title()
                    print(f"  Page {j+1}:")
                    print(f"    URL: {url}")
                    print(f"    Title: {title}")
                    
                    # 각 페이지 스크린샷
                    screenshot_path = f"logs/realtime/window_{i}_{j}_{timestamp}.png"
                    await pg.screenshot(path=screenshot_path)
                    print(f"    Screenshot: {screenshot_path}")
            
            # 새 탭으로 현재 상태 확인
            await page.goto("https://www.bizmeka.com/find/findPasswordCertTypeView.do")
            await page.wait_for_timeout(2000)
            
            current_url = page.url
            current_title = await page.title()
            
            print(f"\n[CURRENT PAGE]")
            print(f"  URL: {current_url}")
            print(f"  Title: {current_title}")
            
            # 현재 페이지 스크린샷
            current_screenshot = f"logs/realtime/current_{timestamp}.png"
            await page.screenshot(path=current_screenshot, full_page=False)
            print(f"  Screenshot: {current_screenshot}")
            
            print("\n[Browser stays open for inspection]")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_active_window())
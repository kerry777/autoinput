#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
기존 Chrome 브라우저 사용하여 로그인
"""

import asyncio
from playwright.async_api import async_playwright
import subprocess
import os
import time

async def use_existing_chrome():
    # 1. Chrome을 디버그 모드로 실행
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    # 디버그 포트로 Chrome 실행
    subprocess.Popen([
        chrome_path,
        '--remote-debugging-port=9222',
        '--user-data-dir=C:\\temp\\chrome_profile'
    ])
    
    time.sleep(3)  # Chrome 시작 대기
    
    async with async_playwright() as p:
        # 2. 실행 중인 Chrome에 연결
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        
        # 기존 컨텍스트 사용
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
        else:
            context = await browser.new_context()
            page = await context.new_page()
        
        # 3. 로그인 수행
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(2000)
        
        await page.fill('#username', 'kilmoon@mek-ics.com')
        await page.fill('#password', 'moon7410!@')
        await page.click('#btnSubmit')
        
        await page.wait_for_timeout(5000)
        
        print(f"결과 URL: {page.url}")
        
        if 'secondStep' not in page.url:
            print("SUCCESS - 2FA 없이 로그인!")
        
        await page.wait_for_timeout(30000)

if __name__ == "__main__":
    asyncio.run(use_existing_chrome())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chrome 디버그 모드 실행 및 연결
"""

import asyncio
from playwright.async_api import async_playwright
import subprocess
import time
import os

async def direct_connect():
    # Chrome 디버그 모드로 실행
    chrome_cmd = r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=C:\temp\chrome_test'
    
    print("Chrome 실행 중...")
    subprocess.Popen(chrome_cmd, shell=True)
    time.sleep(5)  # Chrome 시작 대기
    
    async with async_playwright() as p:
        print("Chrome 연결 중...")
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 로그인 수행
        print("로그인 페이지 이동...")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(3000)
        
        print("로그인 정보 입력...")
        await page.fill('#username', 'kilmoon@mek-ics.com')
        await page.fill('#password', 'moon7410!@')
        
        print("로그인 클릭...")
        await page.click('#btnSubmit')
        
        await page.wait_for_timeout(5000)
        
        url = page.url
        print(f"\n최종 URL: {url}")
        
        if 'secondStep' not in url:
            print(">>> SUCCESS! 2차 인증 없음 <<<")
        else:
            print("2차 인증 나타남")
        
        time.sleep(30)

if __name__ == "__main__":
    asyncio.run(direct_connect())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
수동으로 Chrome 실행 후 연결
"""

import asyncio
from playwright.async_api import async_playwright
import time

print("""
=====================================
수동 Chrome 연결 방법
=====================================

1. CMD 창을 열고 다음 명령 실행:
   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222

2. Chrome이 열리면 Enter를 누르세요...
""")

input("Chrome을 실행하고 Enter: ")

async def connect_and_login():
    async with async_playwright() as p:
        try:
            # 이미 실행 중인 Chrome에 연결
            print("\nChrome에 연결 중...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("연결 성공!")
            
            # 현재 열린 페이지 가져오기
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            # 로그인 페이지로 이동
            print("\n로그인 페이지 이동...")
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(3000)
            
            # 로그인
            print("로그인 정보 입력...")
            await page.fill('#username', 'kilmoon@mek-ics.com')
            await page.fill('#password', 'moon7410!@')
            
            print("로그인 버튼 클릭...")
            await page.click('#btnSubmit')
            
            await page.wait_for_timeout(5000)
            
            # 결과
            url = page.url
            print(f"\n결과 URL: {url}")
            
            if 'secondStep' not in url:
                print("[SUCCESS] 2차 인증 없이 로그인 성공!")
            else:
                print("[INFO] 2차 인증 페이지")
            
            print("\n브라우저를 닫지 마세요. 30초 후 종료됩니다...")
            await page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"오류: {e}")

if __name__ == "__main__":
    asyncio.run(connect_and_login())
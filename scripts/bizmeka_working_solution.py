#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 작동하는 솔루션
"""

import asyncio
from playwright.async_api import async_playwright
import os

async def login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 1. 메인 페이지 먼저 방문 (Referrer 생성)
        await page.goto("https://www.bizmeka.com")
        await page.wait_for_timeout(2000)
        
        # 2. 로그인 페이지로 이동
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(2000)
        
        # 3. 로그인
        await page.fill('#username', 'kilmoon@mek-ics.com')
        await page.fill('#password', 'moon7410!@')
        await page.click('#btnSubmit')
        
        await page.wait_for_timeout(5000)
        
        # 4. 결과
        if 'secondStep' not in page.url:
            print("SUCCESS - 2FA 없이 로그인 성공")
        else:
            print("2FA 페이지 나타남")
        
        print(f"현재 URL: {page.url}")
        
        await page.wait_for_timeout(30000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login())
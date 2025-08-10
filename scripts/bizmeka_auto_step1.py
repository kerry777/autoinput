#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1 자동 실행 버전 - 브라우저만 열어줌
"""

import asyncio
import json
import time
from playwright.async_api import async_playwright

async def open_browser_for_login():
    print("\n" + "="*60)
    print("Bizmeka 로그인 브라우저 실행")
    print("="*60)
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_production"
    cookies_file = "C:\\projects\\autoinput\\data\\bizmeka_cookies.json"
    
    async with async_playwright() as p:
        # 브라우저 실행
        print("\n[1] Chrome 브라우저 실행 중...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        # 로그인 페이지로 이동
        print("[2] 로그인 페이지로 이동...")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        
        print("\n" + "="*60)
        print("브라우저에서 수동으로 로그인하세요!")
        print("="*60)
        print("아이디: kilmoon@mek-ics.com")
        print("비밀번호: moon7410!@")
        print("\n2차 인증까지 완료하세요.")
        print("로그인 완료 후 60초 기다립니다...")
        
        # 60초 대기
        for i in range(60, 0, -10):
            print(f"대기 중... {i}초")
            await page.wait_for_timeout(10000)
            
            # 중간에 URL 확인
            if i == 30:
                current_url = page.url
                if 'main.do' in current_url:
                    print("\n로그인 감지됨! 쿠키 수집 시작...")
                    break
        
        # 메인 페이지로 이동 시도
        print("\n[3] 메인 페이지 확인...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        
        if 'loginForm' not in current_url and 'secondStep' not in current_url:
            # 쿠키 수집
            print("\n[4] 쿠키 수집 중...")
            cookies = await browser.cookies()
            
            # 쿠키 저장
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"\n[성공] 쿠키 {len(cookies)}개 저장됨!")
            print(f"저장 위치: {cookies_file}")
            
            # JSESSIONID 확인
            for cookie in cookies:
                if cookie['name'] == 'JSESSIONID':
                    print(f"세션 ID: {cookie['value'][:30]}...")
                    break
            
            print("\n이제 Step 2를 실행하면 자동 로그인이 가능합니다!")
        else:
            print("\n[경고] 로그인이 완료되지 않았습니다.")
            print("브라우저에서 로그인을 완료한 후 다시 실행하세요.")
        
        print("\n브라우저를 10초 후 닫습니다...")
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(open_browser_for_login())
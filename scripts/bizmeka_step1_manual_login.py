#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: 수동 로그인으로 쿠키 저장
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def manual_login():
    print("\n" + "="*60)
    print("Bizmeka 수동 로그인 - 쿠키 저장")
    print("="*60)
    print("\n[안내]")
    print("1. Chrome 브라우저가 열립니다")
    print("2. 로그인 페이지가 자동으로 나타납니다")
    print("3. 아이디: kilmoon@mek-ics.com")
    print("4. 비밀번호: moon7410!@")
    print("5. 로그인 버튼 클릭")
    print("6. 2차 인증이 나오면 완료하세요")
    print("7. 메인 페이지가 보이면 이 창으로 돌아와서 Enter를 누르세요")
    print("\n준비되면 Enter를 누르세요...")
    input()
    
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
        print("브라우저에서 로그인을 완료하세요!")
        print("로그인과 2차 인증을 완료한 후...")
        print("이 창으로 돌아와서 Enter를 누르세요")
        print("="*60)
        input("\n로그인 완료 후 Enter: ")
        
        # 메인 페이지로 이동
        print("\n[3] 메인 페이지로 이동 중...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(2000)
        
        # 현재 URL 확인
        current_url = page.url
        
        if 'loginForm' in current_url or 'secondStep' in current_url:
            print("\n[ERROR] 아직 로그인이 완료되지 않았습니다!")
            print("브라우저에서 로그인을 완료하세요.")
            input("완료 후 다시 Enter: ")
            await page.goto("https://www.bizmeka.com/app/main.do")
            await page.wait_for_timeout(2000)
        
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
        print("브라우저를 닫아도 됩니다.")
        
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(manual_login())
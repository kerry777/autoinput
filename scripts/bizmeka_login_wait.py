#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
브라우저 열고 충분히 기다리는 버전
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def login_with_wait():
    print("\n" + "="*60)
    print("Bizmeka 로그인 - 충분한 대기 시간")
    print("="*60)
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_production"
    cookies_file = "C:\\projects\\autoinput\\data\\bizmeka_cookies.json"
    
    async with async_playwright() as p:
        print("\n[1] Chrome 브라우저 실행...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        print("[2] 로그인 페이지로 이동...")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        
        print("\n" + "="*60)
        print("수동 로그인 안내")
        print("="*60)
        print("1. 아이디: kilmoon@mek-ics.com")
        print("2. 비밀번호: moon7410!@")
        print("3. 로그인 버튼 클릭")
        print("4. 2차 인증 (이메일 인증) 완료")
        print("5. 메인 페이지가 나타날 때까지 기다림")
        print("\n*** 5분(300초) 동안 기다립니다 ***")
        print("2차 인증을 충분히 완료하세요!")
        print("="*60)
        
        # 5분 대기 (30초마다 상태 체크)
        for i in range(10):
            remaining = 300 - (i * 30)
            print(f"\n대기 중... 남은 시간: {remaining}초")
            await page.wait_for_timeout(30000)  # 30초 대기
            
            # URL 체크
            current_url = page.url
            if 'main.do' in current_url or 'MainAction.do' in current_url:
                print("\n[성공] 로그인 완료 감지!")
                break
            elif 'secondStep' in current_url:
                print("2차 인증 페이지 확인... 계속 기다립니다.")
        
        # 메인 페이지로 이동 시도
        print("\n[3] 메인 페이지 확인...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        
        if 'loginForm' not in current_url and 'secondStep' not in current_url:
            # 로그인 성공 - 쿠키 수집
            print("\n[4] 로그인 성공! 쿠키 수집 중...")
            cookies = await browser.cookies()
            
            # 쿠키 저장
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"\n" + "="*60)
            print(f"[성공] 쿠키 {len(cookies)}개 저장 완료!")
            print(f"저장 위치: {cookies_file}")
            
            # JSESSIONID 확인
            for cookie in cookies:
                if cookie['name'] == 'JSESSIONID':
                    print(f"세션 ID: {cookie['value'][:30]}...")
                    break
            
            print("\n다음 단계:")
            print("python scripts/bizmeka_step2_auto_access.py")
            print("위 명령으로 자동 로그인이 가능합니다!")
            print("="*60)
        else:
            print("\n[실패] 로그인이 완료되지 않았습니다.")
            print("현재 URL:", current_url)
            print("다시 시도해주세요.")
        
        print("\n브라우저를 30초 후 닫습니다...")
        print("(수동으로 닫아도 됩니다)")
        await page.wait_for_timeout(30000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_with_wait())
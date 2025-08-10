#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 세션 최대한 연장하기
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright

async def extend_session():
    print("\n" + "="*60)
    print("Bizmeka 세션 연장 - 로그인 유지 체크")
    print("="*60)
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_extended"
    cookies_file = "C:\\projects\\autoinput\\data\\bizmeka_extended_cookies.json"
    
    async with async_playwright() as p:
        print("\n[1] 영구 프로필로 브라우저 실행...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        print("[2] 로그인 페이지로 이동...")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(2000)
        
        print("\n" + "="*60)
        print("중요! 로그인시 다음을 확인하세요:")
        print("="*60)
        print("1. ✅ '로그인 상태 유지' 체크박스 확인!")
        print("2. ✅ '자동 로그인' 옵션이 있다면 체크!")
        print("3. ✅ '30일간 로그인 유지' 등의 옵션 체크!")
        print("\n아이디: kilmoon@mek-ics.com")
        print("비밀번호: moon7410!@")
        print("\n로그인과 2차 인증을 완료하세요.")
        print("="*60)
        
        # 5분 대기
        for i in range(10):
            remaining = 300 - (i * 30)
            print(f"\n대기 중... {remaining}초")
            await page.wait_for_timeout(30000)
            
            # URL 체크
            current_url = page.url
            if 'main' in current_url.lower() and 'login' not in current_url.lower():
                print("\n[성공] 로그인 완료!")
                break
        
        # 메인 페이지로 이동
        print("\n[3] 메인 페이지 확인...")
        await page.goto("https://www.bizmeka.com/")
        await page.wait_for_timeout(3000)
        
        # 쿠키 수집 - 영구 프로필에서
        print("\n[4] 확장된 세션 쿠키 수집...")
        cookies = await browser.cookies()
        
        # 쿠키 수정 - 만료 시간 연장
        extended_cookies = []
        for cookie in cookies:
            new_cookie = cookie.copy()
            
            # JSESSIONID 만료 시간 설정
            if cookie['name'] == 'JSESSIONID':
                # 30일 후로 설정
                future_time = datetime.now() + timedelta(days=30)
                new_cookie['expires'] = future_time.timestamp()
                print(f"JSESSIONID 만료 시간 설정: 30일 후")
            
            # 다른 세션 관련 쿠키도 연장
            elif 'session' in cookie['name'].lower() or 'remember' in cookie['name'].lower():
                if cookie.get('expires', -1) == -1:
                    future_time = datetime.now() + timedelta(days=30)
                    new_cookie['expires'] = future_time.timestamp()
                    print(f"{cookie['name']} 만료 시간 설정: 30일 후")
            
            extended_cookies.append(new_cookie)
        
        # 확장된 쿠키 저장
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(extended_cookies, f, ensure_ascii=False, indent=2)
        
        print(f"\n[5] 확장된 쿠키 {len(extended_cookies)}개 저장!")
        print(f"저장 위치: {cookies_file}")
        
        # 쿠키 정보 출력
        print("\n" + "="*60)
        print("쿠키 만료 정보:")
        print("="*60)
        for cookie in extended_cookies:
            if cookie['name'] in ['JSESSIONID', 'rememberMe', 'autoLogin']:
                name = cookie['name']
                expires = cookie.get('expires', -1)
                if expires == -1:
                    print(f"{name}: 세션 쿠키")
                else:
                    expire_date = datetime.fromtimestamp(expires)
                    remaining = expire_date - datetime.now()
                    print(f"{name}: {remaining.days}일 유효")
        
        print("\n" + "="*60)
        print("팁: 세션 유지를 위해")
        print("="*60)
        print("1. 매일 한 번씩 자동 접속 스크립트 실행")
        print("2. 주말에도 한 번씩 실행")
        print("3. 쿠키 만료 7일 전 재로그인")
        print("="*60)
        
        print("\n브라우저를 30초 후 닫습니다...")
        await page.wait_for_timeout(30000)
        await browser.close()

async def daily_keep_alive():
    """매일 실행하여 세션 유지"""
    print("\n[세션 유지 스크립트]")
    
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_extended_cookies.json")
    
    if not cookies_file.exists():
        print("쿠키 파일이 없습니다. 먼저 extend_session을 실행하세요.")
        return
    
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # 백그라운드 실행
        context = await browser.new_context()
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 메인 페이지 접속으로 세션 갱신
        await page.goto("https://www.bizmeka.com/")
        await page.wait_for_timeout(3000)
        
        # 새로운 쿠키 저장
        new_cookies = await context.cookies()
        
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(new_cookies, f, ensure_ascii=False, indent=2)
        
        print(f"[{datetime.now()}] 세션 갱신 완료")
        
        await browser.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'keep':
        asyncio.run(daily_keep_alive())
    else:
        asyncio.run(extend_session())
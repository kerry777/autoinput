#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 2: 저장된 쿠키로 자동 접근
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def auto_access():
    print("\n" + "="*60)
    print("Bizmeka 자동 접근 - 쿠키 사용")
    print("="*60)
    
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
    
    # 쿠키 파일 확인
    if not cookies_file.exists():
        print("\n[ERROR] 쿠키 파일이 없습니다!")
        print("먼저 bizmeka_step1_manual_login.py를 실행하세요.")
        return
    
    # 쿠키 로드
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"\n[1] 쿠키 {len(cookies)}개 로드됨")
    
    async with async_playwright() as p:
        # 새 브라우저 (프로필 없이)
        print("[2] 새 브라우저 실행...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        # 쿠키 주입
        print("[3] 쿠키 주입...")
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 메인 페이지 직접 접근
        print("[4] 메인 서비스 접근...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        print(f"\n현재 URL: {current_url}")
        
        # 결과 확인
        if 'loginForm' in current_url:
            print("\n[FAIL] 세션이 만료되었습니다!")
            print("Step 1을 다시 실행하세요.")
        elif 'secondStep' in current_url:
            print("\n[WARN] 2차 인증이 필요합니다.")
            print("Step 1을 다시 실행하세요.")
        else:
            print("\n" + "="*60)
            print("[SUCCESS] 자동 로그인 성공!")
            print("="*60)
            print("2차 인증 없이 로그인되었습니다!")
            
            # 페이지 정보
            title = await page.title()
            print(f"페이지 제목: {title}")
            
            print("\n이제 필요한 작업을 자동으로 수행할 수 있습니다.")
            print("예: 데이터 수집, 폼 제출, 보고서 다운로드 등")
            
            # 여기에 실제 자동화 작업 코드 추가 가능
            # 예시:
            # await page.click('selector')
            # await page.fill('input', 'value')
            # etc...
            
            print("\n브라우저는 30초 후 종료됩니다...")
            print("(필요한 작업을 확인하세요)")
            await page.wait_for_timeout(30000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(auto_access())
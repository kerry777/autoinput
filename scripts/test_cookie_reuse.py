#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
쿠키 재사용 테스트
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def test_cookie_reuse():
    """저장된 쿠키로 세션 재사용 테스트"""
    
    print("\n[쿠키 재사용 테스트]")
    print("="*60)
    
    # 쿠키 파일 읽기
    cookies_file = Path("C:/projects/autoinput/data/bizmeka_login_analyzer_min/analyze_out/run_20250810_130512/cookies_after.json")
    
    if not cookies_file.exists():
        print("쿠키 파일이 없습니다!")
        return
    
    cookies = json.loads(cookies_file.read_text(encoding="utf-8"))
    print(f"쿠키 {len(cookies)}개 로드됨")
    
    # 주요 쿠키 확인
    for cookie in cookies:
        if cookie['name'] == 'JSESSIONID':
            print(f"JSESSIONID: {cookie['value'][:20]}...")
    
    async with async_playwright() as p:
        # 일반 브라우저 실행
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        # 쿠키 주입
        print("\n[1] 쿠키 주입")
        try:
            await context.add_cookies(cookies)
            print("[OK] 쿠키 주입 성공")
        except Exception as e:
            print(f"[ERROR] 쿠키 주입 실패: {e}")
        
        page = await context.new_page()
        
        # 메인 페이지 직접 접속
        print("\n[2] 메인 페이지 접속 시도")
        await page.goto("https://www.bizmeka.com/app/main.do", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        print(f"현재 URL: {current_url}")
        
        # 결과 판단
        if 'loginForm' in current_url:
            print("\n[FAIL] 로그인 페이지로 리다이렉트됨")
            print("쿠키가 유효하지 않거나 만료됨")
        elif 'secondStep' in current_url:
            print("\n[WARN] 2차 인증 페이지")
            print("쿠키는 유효하지만 2차 인증 필요")
        else:
            print("\n[SUCCESS] 로그인 성공!")
            print("쿠키로 세션 재사용 성공")
            
            # 페이지 제목 확인
            title = await page.title()
            print(f"페이지 제목: {title}")
        
        # 다른 경로 시도
        print("\n[3] SSO 페이지 접속 시도")
        await page.goto("https://ezsso.bizmeka.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        sso_url = page.url
        print(f"SSO URL: {sso_url}")
        
        if 'loginForm' not in sso_url and 'secondStep' not in sso_url:
            print("-> SSO 세션 유지됨")
        else:
            print("-> SSO 세션 만료")
        
        print("\n브라우저는 20초 후 종료됩니다...")
        await page.wait_for_timeout(20000)
        
        await context.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_cookie_reuse())
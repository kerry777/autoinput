#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 재로그인 - 쿠키 갱신
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def relogin():
    print("\n" + "="*60)
    print("Bizmeka 재로그인 - 쿠키 갱신")
    print("="*60)
    print("\n세션이 만료된 것 같습니다. 다시 로그인합니다.")
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_production"
    cookies_file = "C:\\projects\\autoinput\\data\\bizmeka_cookies.json"
    
    async with async_playwright() as p:
        print("\n[1] 브라우저 실행...")
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
        print("수동 로그인 필요")
        print("="*60)
        print("1. 아이디: kilmoon@mek-ics.com")
        print("2. 비밀번호: moon7410!@")
        print("3. 2차 인증 완료")
        print("\n3분 동안 기다립니다...")
        
        # 3분 대기
        for i in range(6):
            remaining = 180 - (i * 30)
            print(f"대기 중... {remaining}초 남음")
            await page.wait_for_timeout(30000)
            
            # URL 체크
            current_url = page.url
            if 'app/main.do' in current_url or 'MainAction.do' in current_url:
                print("\n[성공] 로그인 완료!")
                break
        
        # 메인 페이지 확인
        print("\n[3] 로그인 상태 확인...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        # 페이지 내용 확인
        page_content = await page.content()
        
        if "이용에 불편을 드려" in page_content:
            print("\n[경고] 접근 권한 문제 발생!")
            print("다른 페이지를 시도합니다...")
            
            # 다른 URL 시도
            await page.goto("https://www.bizmeka.com/")
            await page.wait_for_timeout(2000)
            
            # 또는 SSO 메인으로
            await page.goto("https://ezsso.bizmeka.com/main.do")
            await page.wait_for_timeout(2000)
        
        current_url = page.url
        
        if 'loginForm' not in current_url:
            # 쿠키 저장
            print("\n[4] 새 쿠키 저장...")
            cookies = await browser.cookies()
            
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"쿠키 {len(cookies)}개 저장됨")
            print(f"시간: {datetime.now()}")
            
            # 현재 페이지 정보
            title = await page.title()
            print(f"\n현재 페이지: {title}")
            print(f"URL: {current_url}")
            
            # 사용 가능한 링크 확인
            print("\n[5] 사용 가능한 페이지 확인...")
            links = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const text = (a.innerText || a.textContent || '').trim();
                        const href = a.href;
                        if (text && href && !href.includes('javascript') && !href.includes('logout')) {
                            links.push({text: text.substring(0, 30), href: href});
                        }
                    });
                    return links.slice(0, 15);
                }
            """)
            
            if links:
                print("\n접근 가능한 링크:")
                for link in links:
                    print(f"  - {link['text']}")
        else:
            print("\n[실패] 로그인이 완료되지 않았습니다.")
        
        print("\n브라우저를 20초 후 닫습니다...")
        await page.wait_for_timeout(20000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(relogin())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 자동 로그인 후 작업 수행
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def auto_login_and_work():
    print("\n" + "="*60)
    print("Bizmeka 자동 로그인 및 작업")
    print("="*60)
    
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
    
    if not cookies_file.exists():
        print("[ERROR] 쿠키 파일이 없습니다!")
        return
    
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"[1] 쿠키 {len(cookies)}개 로드")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        # 쿠키 주입
        await context.add_cookies(cookies)
        print("[2] 쿠키 주입 완료")
        
        page = await context.new_page()
        
        # 메인 페이지 접속
        print("[3] 메인 페이지 접속...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        
        if 'loginForm' not in current_url and 'secondStep' not in current_url:
            print("\n" + "="*60)
            print("[SUCCESS] 자동 로그인 성공!")
            print("="*60)
            
            # 페이지 분석
            print("\n[4] 페이지 분석 중...")
            
            # 메뉴 항목 찾기
            menu_items = await page.evaluate("""
                () => {
                    const menus = [];
                    document.querySelectorAll('a[href*="menu"], .menu-item, .nav-item, [class*="menu"]').forEach(item => {
                        const text = item.innerText || item.textContent;
                        const href = item.href;
                        if (text && text.trim()) {
                            menus.push({text: text.trim(), href: href});
                        }
                    });
                    return menus;
                }
            """)
            
            print("\n발견된 메뉴 항목:")
            for item in menu_items[:10]:  # 처음 10개만
                print(f"  - {item['text']}")
            
            # 주요 링크 찾기
            links = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const text = a.innerText || a.textContent;
                        const href = a.href;
                        if (text && text.trim() && href && !href.includes('javascript')) {
                            links.push({text: text.trim(), href: href});
                        }
                    });
                    return links.slice(0, 20);  // 처음 20개만
                }
            """)
            
            print("\n주요 링크:")
            for link in links[:10]:
                print(f"  - {link['text']}: {link['href'][:50]}...")
            
            # 폼 요소 찾기
            forms = await page.evaluate("""
                () => {
                    return {
                        forms: document.querySelectorAll('form').length,
                        inputs: document.querySelectorAll('input').length,
                        buttons: document.querySelectorAll('button, input[type="submit"]').length,
                        selects: document.querySelectorAll('select').length
                    };
                }
            """)
            
            print(f"\n페이지 요소:")
            print(f"  - 폼: {forms['forms']}개")
            print(f"  - 입력 필드: {forms['inputs']}개")
            print(f"  - 버튼: {forms['buttons']}개")
            print(f"  - 선택 박스: {forms['selects']}개")
            
            print("\n" + "="*60)
            print("이제 무엇을 할까요?")
            print("="*60)
            print("가능한 작업:")
            print("1. 특정 메뉴/페이지로 이동")
            print("2. 데이터 조회/다운로드")
            print("3. 폼 작성 및 제출")
            print("4. 보고서 생성")
            print("5. 기타 자동화 작업")
            print("\n어떤 작업을 자동화하고 싶으신가요?")
            
            # 브라우저 유지
            print("\n브라우저를 확인하고 원하는 작업을 알려주세요.")
            print("60초 동안 대기합니다...")
            await page.wait_for_timeout(60000)
            
        else:
            print("[FAIL] 로그인 실패 - 쿠키가 만료되었을 수 있습니다.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(auto_login_and_work())
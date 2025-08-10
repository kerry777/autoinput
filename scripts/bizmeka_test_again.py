#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 자동 로그인 재시도
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

async def test_auto_login():
    print("\n" + "="*60)
    print("Bizmeka 자동 로그인 테스트")
    print("="*60)
    
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
    
    if not cookies_file.exists():
        print("[ERROR] 쿠키 파일이 없습니다!")
        print("먼저 수동 로그인이 필요합니다.")
        return
    
    # 쿠키 파일 정보
    file_time = datetime.fromtimestamp(cookies_file.stat().st_mtime)
    print(f"쿠키 파일 생성: {file_time}")
    
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"쿠키 개수: {len(cookies)}개")
    
    # JSESSIONID 확인
    for cookie in cookies:
        if cookie['name'] == 'JSESSIONID':
            print(f"세션 ID: {cookie['value'][:30]}...")
            break
    
    async with async_playwright() as p:
        print("\n[1] 브라우저 실행...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        print("[2] 쿠키 주입...")
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        print("[3] Bizmeka 메인 페이지 접속 시도...")
        
        # 먼저 기본 도메인으로
        await page.goto("https://www.bizmeka.com/")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        title = await page.title()
        
        print(f"\n현재 URL: {current_url}")
        print(f"페이지 제목: {title}")
        
        # 로그인 상태 확인
        page_content = await page.content()
        
        if 'loginForm' in current_url:
            print("\n[상태] 로그인 페이지로 리다이렉트됨")
            print("→ 쿠키가 만료되었습니다. 재로그인 필요!")
            
        elif '이용에 불편을' in page_content:
            print("\n[상태] 접근 권한 오류")
            print("→ 다른 페이지를 시도합니다...")
            
            # SSO 메인 시도
            await page.goto("https://ezsso.bizmeka.com/")
            await page.wait_for_timeout(2000)
            
            current_url = page.url
            if 'loginForm' not in current_url:
                print(f"SSO 페이지 접속 성공: {current_url}")
            
        else:
            print("\n[성공] 로그인 상태 유지됨!")
            
            # 페이지 분석
            print("\n[4] 페이지 내용 분석...")
            
            # 사용자 정보 찾기
            user_info = await page.evaluate("""
                () => {
                    // 사용자 정보가 있을 만한 요소들 찾기
                    const selectors = [
                        '.user-name', '.user-info', '.login-info',
                        '[class*="user"]', '[class*="member"]',
                        '#userId', '#userName'
                    ];
                    
                    for (let selector of selectors) {
                        const elem = document.querySelector(selector);
                        if (elem && elem.textContent) {
                            return elem.textContent.trim();
                        }
                    }
                    return null;
                }
            """)
            
            if user_info:
                print(f"사용자 정보: {user_info}")
            
            # 주요 링크 수집
            links = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const text = (a.innerText || a.textContent || '').trim();
                        const href = a.href;
                        if (text && href && 
                            !href.includes('javascript') && 
                            !href.includes('logout') &&
                            !href.includes('#') &&
                            text.length > 2) {
                            links.push({
                                text: text.substring(0, 30),
                                href: href
                            });
                        }
                    });
                    // 중복 제거
                    const unique = [];
                    const seen = new Set();
                    links.forEach(link => {
                        if (!seen.has(link.text)) {
                            seen.add(link.text);
                            unique.push(link);
                        }
                    });
                    return unique.slice(0, 20);
                }
            """)
            
            if links:
                print(f"\n발견된 주요 링크 ({len(links)}개):")
                for i, link in enumerate(links, 1):
                    print(f"{i:2}. {link['text']}")
            
            # 폼 요소 확인
            forms_info = await page.evaluate("""
                () => {
                    const forms = document.querySelectorAll('form');
                    const result = [];
                    forms.forEach((form, idx) => {
                        result.push({
                            action: form.action,
                            method: form.method,
                            inputs: form.querySelectorAll('input').length,
                            buttons: form.querySelectorAll('button, input[type="submit"]').length
                        });
                    });
                    return result;
                }
            """)
            
            if forms_info:
                print(f"\n폼 발견 ({len(forms_info)}개):")
                for i, form in enumerate(forms_info, 1):
                    print(f"  폼 {i}: {form['inputs']}개 입력, {form['buttons']}개 버튼")
        
        print("\n" + "="*60)
        print("브라우저를 확인하세요.")
        print("30초 후 자동 종료됩니다...")
        print("="*60)
        
        await page.wait_for_timeout(30000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_auto_login())
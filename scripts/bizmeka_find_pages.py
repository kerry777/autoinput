#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 접근 가능한 페이지 찾기
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def find_accessible_pages():
    print("\n" + "="*60)
    print("Bizmeka 접근 가능한 페이지 찾기")
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
        
        await context.add_cookies(cookies)
        print("[2] 쿠키 주입 완료")
        
        page = await context.new_page()
        
        # 다양한 URL 시도
        test_urls = [
            "https://www.bizmeka.com/",
            "https://www.bizmeka.com/index.do",
            "https://www.bizmeka.com/main.do",
            "https://ezsso.bizmeka.com/",
            "https://ezsso.bizmeka.com/main.do",
            "https://ezsso.bizmeka.com/MainAction.do",
            "https://www.bizmeka.com/mypage/main.do",
            "https://www.bizmeka.com/service/main.do"
        ]
        
        print("\n[3] 접근 가능한 페이지 찾기...")
        
        for url in test_urls:
            print(f"\n시도: {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(2000)
                
                # 페이지 내용 확인
                page_content = await page.content()
                current_url = page.url
                title = await page.title()
                
                if "이용에 불편을" in page_content:
                    print("  → 접근 거부됨")
                elif "loginForm" in current_url:
                    print("  → 로그인 페이지로 리다이렉트")
                elif "404" in title or "Not Found" in title:
                    print("  → 페이지 없음")
                else:
                    print(f"  → 성공! 제목: {title}")
                    
                    # 이 페이지에서 링크 수집
                    links = await page.evaluate("""
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                const text = (a.innerText || a.textContent || '').trim();
                                const href = a.href;
                                if (text && href && 
                                    !href.includes('javascript') && 
                                    !href.includes('logout') &&
                                    !href.includes('#')) {
                                    links.push({
                                        text: text.substring(0, 50),
                                        href: href
                                    });
                                }
                            });
                            return links;
                        }
                    """)
                    
                    if links:
                        print(f"\n  발견된 링크 ({len(links)}개):")
                        for link in links[:20]:  # 처음 20개만
                            print(f"    - {link['text']}")
                            if 'service' in link['href'] or 'board' in link['href'] or 'notice' in link['href']:
                                print(f"      URL: {link['href']}")
                    
                    # 메뉴 찾기
                    menus = await page.evaluate("""
                        () => {
                            const menus = [];
                            // 다양한 메뉴 선택자 시도
                            const selectors = [
                                '.gnb a', '.lnb a', '.menu a',
                                '[class*="menu"] a', '[class*="nav"] a',
                                '#menu a', '#nav a'
                            ];
                            
                            selectors.forEach(selector => {
                                document.querySelectorAll(selector).forEach(a => {
                                    const text = (a.innerText || a.textContent || '').trim();
                                    const href = a.href;
                                    if (text && href) {
                                        menus.push({text: text, href: href});
                                    }
                                });
                            });
                            return menus;
                        }
                    """)
                    
                    if menus:
                        print(f"\n  메뉴 항목 ({len(menus)}개):")
                        for menu in menus[:10]:
                            print(f"    - {menu['text']}")
                    
                    break  # 성공한 페이지 찾으면 중단
                    
            except Exception as e:
                print(f"  → 오류: {str(e)[:50]}")
        
        print("\n" + "="*60)
        print("어떤 페이지/기능을 사용하고 싶으신가요?")
        print("브라우저에서 원하는 페이지로 이동해보세요.")
        print("="*60)
        
        print("\n60초 동안 대기합니다...")
        await page.wait_for_timeout(60000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_accessible_pages())
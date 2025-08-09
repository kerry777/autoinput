#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
게시판 구조 분석 테스트
"""

import asyncio
from playwright.async_api import async_playwright
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def analyze_board():
    """게시판 구조 분석"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # 서식 자료실 페이지로 이동
        url = "https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000002207"
        print(f"[이동] {url}\n")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 스크린샷 저장
        await page.screenshot(path='logs/screenshots/board_page.png')
        print("[스크린샷] logs/screenshots/board_page.png 저장\n")
        
        # 여러 가능한 셀렉터 테스트
        selectors = [
            'table.board-list tbody tr',
            'table.list tbody tr',
            '.board-list-table tbody tr',
            '.bbs-list tbody tr',
            '.tbl_list tbody tr',
            'table tbody tr',
            '.list-body tr',
            '.board_list tr',
            'div.board-item',
            'li.board-item',
            '.list-item'
        ]
        
        print("[게시판 구조 분석]\n")
        
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"✓ '{selector}': {len(elements)}개 발견")
                
                # 첫 번째 요소의 내용 확인
                if elements:
                    first_text = await elements[0].text_content()
                    print(f"  첫 번째 항목: {first_text[:100] if first_text else 'Empty'}...")
                break
        else:
            print("✗ 표준 게시판 구조를 찾을 수 없음")
            
            # 페이지 전체 HTML 구조 일부 출력
            print("\n[페이지 HTML 구조 샘플]")
            html = await page.content()
            
            # table 태그 찾기
            tables = await page.query_selector_all('table')
            print(f"\n테이블 개수: {len(tables)}개")
            
            for idx, table in enumerate(tables[:3], 1):
                print(f"\n테이블 {idx}:")
                table_html = await table.inner_html()
                print(table_html[:500] + "..." if len(table_html) > 500 else table_html)
        
        # 게시물 링크 찾기
        print("\n[게시물 링크 분석]")
        links = await page.query_selector_all('a[onclick*="fn"], a[href*="view"], a[href*="detail"]')
        print(f"발견된 링크: {len(links)}개")
        
        for idx, link in enumerate(links[:5], 1):
            text = await link.text_content()
            onclick = await link.get_attribute('onclick')
            href = await link.get_attribute('href')
            print(f"  {idx}. 텍스트: {text[:50] if text else 'None'}")
            if onclick:
                print(f"     onclick: {onclick[:100]}")
            if href:
                print(f"     href: {href[:100]}")
        
        # 첨부파일 아이콘 찾기
        print("\n[첨부파일 아이콘 분석]")
        file_indicators = [
            'img[alt*="첨부"]',
            'img[src*="file"]',
            'img[src*="attach"]',
            'span.file-icon',
            'i.fa-paperclip',
            '.ico-file',
            '.attach-icon'
        ]
        
        for selector in file_indicators:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"✓ '{selector}': {len(elements)}개 발견")
        
        print("\n[분석 완료] 10초 후 브라우저가 닫힙니다...")
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    print("\n게시판 구조 분석을 시작합니다...\n")
    asyncio.run(analyze_board())
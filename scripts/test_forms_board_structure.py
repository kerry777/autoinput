#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서식자료실 페이지 구조 테스트
"""

import asyncio
from playwright.async_api import async_playwright
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_structure():
    """페이지 구조 테스트"""
    
    url = "https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()
        
        print(f"[이동] {url}\n")
        await page.goto(url, wait_until='networkidle')
        
        # 충분한 대기
        print("[대기] 페이지 로딩 중...")
        await page.wait_for_timeout(5000)
        
        # HTML 구조 분석
        print("\n[HTML 구조 분석]")
        
        # 1. 모든 테이블 찾기
        tables = await page.query_selector_all('table')
        print(f"테이블 개수: {len(tables)}개")
        
        for idx, table in enumerate(tables, 1):
            print(f"\n테이블 {idx}:")
            # 테이블 클래스와 ID 확인
            table_class = await table.get_attribute('class')
            table_id = await table.get_attribute('id')
            print(f"  class: {table_class}")
            print(f"  id: {table_id}")
            
            # tbody 확인
            tbody = await table.query_selector('tbody')
            if tbody:
                trs = await tbody.query_selector_all('tr')
                print(f"  tbody tr 개수: {len(trs)}개")
                
                # 첫 번째 행 내용 확인
                if trs:
                    first_tr = trs[0]
                    tds = await first_tr.query_selector_all('td')
                    print(f"  첫 번째 행 td 개수: {len(tds)}개")
                    
                    if tds:
                        # 각 td 내용 확인
                        for j, td in enumerate(tds[:5], 1):
                            text = await td.text_content()
                            print(f"    td {j}: {text[:30] if text else 'Empty'}...")
        
        # 2. 게시물 링크 찾기
        print("\n[게시물 링크 찾기]")
        
        # 다양한 링크 패턴
        link_patterns = [
            'a[onclick*="fnViewDetail"]',
            'a[onclick*="fnDetail"]',
            'a[onclick*="view"]',
            'td a[href*="#"]',
            'td:nth-child(2) a',
            'td.title a',
            'td.subject a'
        ]
        
        for pattern in link_patterns:
            links = await page.query_selector_all(pattern)
            if links:
                print(f"✓ 패턴 '{pattern}': {len(links)}개 링크 발견")
                
                # 첫 번째 링크 정보
                if links:
                    first_link = links[0]
                    text = await first_link.text_content()
                    onclick = await first_link.get_attribute('onclick')
                    print(f"  첫 번째 링크:")
                    print(f"    텍스트: {text[:50] if text else 'None'}")
                    print(f"    onclick: {onclick[:100] if onclick else 'None'}")
                break
        
        # 3. 첨부파일 아이콘 찾기
        print("\n[첨부파일 표시 찾기]")
        
        file_indicators = [
            'img[alt*="첨부"]',
            'img[src*="file"]',
            'img[src*="attach"]',
            'img[src*="icon"]',
            'span.file',
            'i.ico-file',
            '[class*="file"]',
            '[class*="attach"]'
        ]
        
        for indicator in file_indicators:
            elements = await page.query_selector_all(indicator)
            if elements:
                print(f"✓ '{indicator}': {len(elements)}개 발견")
        
        # 4. JavaScript 변수 확인
        print("\n[JavaScript 변수 확인]")
        
        js_result = await page.evaluate('''() => {
            const result = {};
            
            // jQuery 확인
            if (typeof $ !== 'undefined') {
                result.jquery = true;
                result.jqueryVersion = $.fn.jquery;
            }
            
            // 게시판 관련 함수 확인
            if (typeof fnViewDetail !== 'undefined') result.fnViewDetail = true;
            if (typeof fnDetail !== 'undefined') result.fnDetail = true;
            if (typeof fnFileDown !== 'undefined') result.fnFileDown = true;
            
            // 게시판 데이터 변수 확인
            if (typeof boardList !== 'undefined') result.boardList = true;
            if (typeof dataList !== 'undefined') result.dataList = true;
            
            return result;
        }''')
        
        print(f"JavaScript 환경: {js_result}")
        
        print("\n[테스트 완료] 10초 후 종료...")
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    print("\n서식자료실 구조 테스트\n")
    asyncio.run(test_structure())
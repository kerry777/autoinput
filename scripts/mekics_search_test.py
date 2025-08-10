#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 검색 기능 테스트 - "대리점 채권" 검색
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def test_search():
    """검색 기능 테스트"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 메인 페이지 접속
        print("\n[1] MEK-ICS accessing...")
        await page.goto("https://it.mek-ics.com/mekics/main/main.do")
        await page.wait_for_timeout(5000)
        
        print("\n[2] Looking for search functionality...")
        
        # 다양한 방법으로 검색 기능 찾기
        
        # 1. 검색 아이콘 클릭 시도
        search_clicked = False
        search_icon_selectors = [
            'button[title*="search" i]',
            'button[title*="검색" i]',
            'a[title*="search" i]',
            'a[title*="검색" i]',
            '[class*="search-icon"]',
            '[class*="search-btn"]',
            '[class*="btn-search"]',
            'button:has(i[class*="search"])',
            'button:has(span[class*="search"])',
            '.toolbar button:has(span)',
            '#searchBtn',
            '[onclick*="search" i]'
        ]
        
        for selector in search_icon_selectors:
            try:
                if await page.locator(selector).first.is_visible():
                    print(f"   Found search element: {selector}")
                    await page.click(selector, timeout=2000)
                    search_clicked = True
                    await page.wait_for_timeout(2000)
                    break
            except:
                continue
        
        if search_clicked:
            print("   Search icon clicked!")
        else:
            print("   Search icon not found, looking for search input field directly...")
        
        # 2. 검색 입력 필드 찾기
        search_input_selectors = [
            'input[type="search"]',
            'input[placeholder*="검색" i]',
            'input[placeholder*="search" i]',
            'input[name*="search" i]',
            'input[id*="search" i]',
            '.search-input',
            '.search-box input',
            'input.x-form-text:visible'
        ]
        
        search_input = None
        for selector in search_input_selectors:
            try:
                elements = await page.locator(selector).all()
                for elem in elements:
                    if await elem.is_visible():
                        search_input = elem
                        print(f"   Found search input: {selector}")
                        break
                if search_input:
                    break
            except:
                continue
        
        if search_input:
            print("\n[3] Entering search term: '대리점 채권'")
            await search_input.fill("대리점 채권")
            await page.wait_for_timeout(1000)
            
            # Enter 키 또는 검색 버튼 클릭
            print("   Pressing Enter to search...")
            await search_input.press("Enter")
            await page.wait_for_timeout(3000)
            
            # 검색 결과 확인
            print("\n[4] Checking search results...")
            
            # 스크린샷 저장
            screenshot = data_dir / f"search_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot))
            print(f"   Screenshot saved: {screenshot}")
            
            # 검색 결과 분석
            results = await page.evaluate("""
                () => {
                    // 검색 결과 패널 찾기
                    const resultPanels = document.querySelectorAll('.search-result, .result-panel, [class*="result"]');
                    
                    // 그리드에 결과가 표시되었는지 확인
                    const grids = document.querySelectorAll('.x-grid, [class*="grid"]');
                    
                    // 리스트 형태의 결과
                    const lists = document.querySelectorAll('ul.search-results, .result-list');
                    
                    return {
                        resultPanels: resultPanels.length,
                        grids: grids.length,
                        lists: lists.length,
                        pageChanged: window.location.href
                    };
                }
            """)
            
            print(f"\n[5] Search results analysis:")
            print(f"   - Result panels found: {results['resultPanels']}")
            print(f"   - Grids found: {results['grids']}")
            print(f"   - Lists found: {results['lists']}")
            print(f"   - Current URL: {results['pageChanged']}")
            
            # 검색 결과 내용 추출
            if results['grids'] > 0:
                print("\n   Extracting grid content...")
                grid_data = await page.evaluate("""
                    () => {
                        const firstGrid = document.querySelector('.x-grid, [class*="grid"]');
                        if (firstGrid) {
                            const rows = firstGrid.querySelectorAll('tr, .x-grid-row');
                            const data = [];
                            for (let i = 0; i < Math.min(5, rows.length); i++) {
                                data.push(rows[i].textContent.trim().substring(0, 100));
                            }
                            return data;
                        }
                        return [];
                    }
                """)
                
                if grid_data:
                    print("   Top results:")
                    for i, row in enumerate(grid_data, 1):
                        print(f"   {i}. {row}")
            
            # 검색 결과 문서화
            doc_path = data_dir / "SEARCH_FUNCTION_TEST.md"
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write("# MEK-ICS 검색 기능 테스트\n\n")
                f.write(f"테스트 시간: {datetime.now()}\n\n")
                f.write("## 검색 테스트\n")
                f.write("- **검색어**: 대리점 채권\n")
                f.write(f"- **검색 입력 필드**: {search_input if search_input else 'Not found'}\n")
                f.write(f"- **검색 결과**:\n")
                f.write(f"  - Result panels: {results['resultPanels']}\n")
                f.write(f"  - Grids: {results['grids']}\n")
                f.write(f"  - Lists: {results['lists']}\n")
                f.write(f"- **스크린샷**: {screenshot}\n")
            
            print(f"\n   Documentation saved: {doc_path}")
            
        else:
            print("\n   Could not find search input field")
            print("   The search might be in a different location or require different interaction")
            
            # 화면 전체 구조 확인
            print("\n[Alternative] Checking page structure...")
            structure = await page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input[type="text"]:visible');
                    const buttons = document.querySelectorAll('button:visible');
                    return {
                        visibleInputs: inputs.length,
                        visibleButtons: buttons.length,
                        firstInputPlaceholder: inputs[0]?.placeholder || 'none',
                        firstButtonText: buttons[0]?.textContent || 'none'
                    };
                }
            """)
            
            print(f"   Visible inputs: {structure['visibleInputs']}")
            print(f"   Visible buttons: {structure['visibleButtons']}")
            print(f"   First input placeholder: {structure['firstInputPlaceholder']}")
            print(f"   First button text: {structure['firstButtonText']}")
        
        print("\n[6] Keeping browser open for 2 minutes...")
        print("   You can manually interact with the search feature")
        await page.wait_for_timeout(120000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_search())
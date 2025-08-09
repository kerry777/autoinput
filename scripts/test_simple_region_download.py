#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단한 테스트 - 서울특별시만 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_seoul_download():
    """서울특별시만 테스트"""
    
    print("\n" + "="*60)
    print("   서울특별시 장기요양기관 다운로드 테스트")
    print("="*60)
    
    # 디렉토리 생성
    os.makedirs("downloads/test", exist_ok=True)
    os.makedirs("logs/screenshots/test", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 화면 보이게
            slow_mo=1000     # 천천히 실행
        )
        
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # 1. 페이지 이동
            print("\n[STEP 1] Loading page...")
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/test/initial_{timestamp}.png")
            print("[SCREENSHOT] Initial page saved")
            
            # 2. 페이지 분석
            print("\n[STEP 2] Analyzing page structure...")
            
            # 모든 select 요소 찾기
            all_selects = await page.query_selector_all('select')
            print(f"Found {len(all_selects)} select elements")
            
            for i, sel in enumerate(all_selects):
                name = await sel.get_attribute('name')
                id_attr = await sel.get_attribute('id')
                options_count = len(await sel.query_selector_all('option'))
                print(f"  Select {i+1}: name='{name}', id='{id_attr}', options={options_count}")
            
            # 3. 시도 선택
            print("\n[STEP 3] Trying to select Seoul...")
            
            # 첫 번째 select가 시도 선택 박스일 가능성이 높음
            if all_selects:
                sido_select = all_selects[0]
                
                # 옵션들 확인
                options = await sido_select.query_selector_all('option')
                print(f"First select has {len(options)} options:")
                
                for opt in options[:5]:  # 처음 5개만
                    value = await opt.get_attribute('value')
                    text = await opt.text_content()
                    print(f"  - value='{value}': {text}")
                
                # 서울 선택 (value="11")
                # CSS 선택자 문자열을 사용해야 함
                await page.select_option('select[name="siDoCd"]', value="11")
                print("Selected Seoul (value='11')")
                await page.wait_for_timeout(2000)
                
                # 선택 후 스크린샷
                await page.screenshot(path=f"logs/screenshots/test/seoul_selected_{timestamp}.png")
                print("[SCREENSHOT] After Seoul selection")
            
            # 4. 검색 버튼 찾기
            print("\n[STEP 4] Looking for search button...")
            
            # 모든 버튼과 링크 찾기
            buttons = await page.query_selector_all('button, a.btn, a[onclick]')
            print(f"Found {len(buttons)} clickable elements")
            
            for i, btn in enumerate(buttons[:10]):  # 처음 10개만
                text = await btn.text_content()
                tag = await btn.evaluate('el => el.tagName')
                if text and '검색' in text:
                    print(f"  {tag} {i+1}: {text.strip()} <-- SEARCH BUTTON")
                elif text:
                    print(f"  {tag} {i+1}: {text.strip()}")
            
            # 검색 버튼 찾기 - name="검색버튼" 속성으로
            print("\nLooking for search button...")
            
            # name 속성으로 찾기
            search_button = await page.query_selector('[name="검색버튼"]')
            if not search_button:
                search_button = await page.query_selector('button[name="검색버튼"]')
            if not search_button:
                search_button = await page.query_selector('a[name="검색버튼"]')
            
            # name이 없으면 title이나 onclick으로
            if not search_button:
                search_button = await page.query_selector('[title*="검색"]')
            if not search_button:
                search_button = await page.query_selector('[onclick*="search"]')
            if search_button:
                print("Found search button!")
                
                # 버튼이 보이는지 확인
                is_visible = await search_button.is_visible()
                if not is_visible:
                    print("Button not visible, scrolling into view...")
                    await search_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                
                # 실제로 보이는 검색 버튼 찾기 (여러 개 중에서)
                all_search_buttons = await page.query_selector_all('[title*="검색"], [onclick*="search"], [name="검색버튼"]')
                print(f"Total search-related elements: {len(all_search_buttons)}")
                
                # 보이는 버튼 찾기
                visible_button = None
                for btn in all_search_buttons:
                    if await btn.is_visible():
                        visible_button = btn
                        print("Found visible search button!")
                        break
                
                if visible_button:
                    search_button = visible_button
                
                # 팝업 대기 준비
                popup_promise = page.wait_for_event('popup')
                
                # 검색 버튼 클릭
                await search_button.click()
                print("Clicked search button")
                
                # 팝업 대기
                try:
                    print("\n[STEP 5] Waiting for popup...")
                    popup = await asyncio.wait_for(popup_promise, timeout=10)
                    print("Popup opened!")
                    
                    await popup.wait_for_load_state('networkidle')
                    await popup.wait_for_timeout(2000)
                    
                    # 팝업 스크린샷
                    await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                    print("[SCREENSHOT] Popup window saved")
                    
                    # 팝업에서 다운로드 버튼 찾기
                    print("\n[STEP 6] Looking for download button in popup...")
                    
                    download_btn = await popup.query_selector('button:has-text("다운로드")')
                    if not download_btn:
                        download_btn = await popup.query_selector('a:has-text("다운로드")')
                    if not download_btn:
                        download_btn = await popup.query_selector('button:has-text("엑셀")')
                    
                    if download_btn:
                        print("Found download button in popup!")
                        
                        # 다운로드 시도
                        try:
                            download_promise = popup.wait_for_event('download', timeout=10000)
                            await download_btn.click()
                            print("Clicked download button")
                            
                            download = await download_promise
                            
                            # 파일 저장
                            filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                            await download.save_as(filepath)
                            print(f"[SUCCESS] File saved: {filepath}")
                            
                        except asyncio.TimeoutError:
                            print("[WARNING] Download timeout")
                    else:
                        print("[WARNING] Download button not found in popup")
                        
                        # 팝업의 모든 버튼 확인
                        popup_buttons = await popup.query_selector_all('button, a')
                        print(f"Popup has {len(popup_buttons)} clickable elements")
                        for i, btn in enumerate(popup_buttons[:10]):
                            text = await btn.text_content()
                            if text:
                                print(f"  - {text.strip()}")
                    
                    await popup.close()
                    
                except asyncio.TimeoutError:
                    print("[WARNING] No popup appeared")
            else:
                print("[ERROR] Search button not found")
            
            print("\n[INFO] Browser will remain open for 15 seconds...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
            # 에러 스크린샷
            await page.screenshot(path=f"logs/screenshots/test/error_{timestamp}.png")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    ============================================
       서울특별시 다운로드 테스트
    ============================================
    목적: 지역 선택 박스 찾기 및 다운로드 테스트
    ============================================
    """)
    
    asyncio.run(test_seoul_download())
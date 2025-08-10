#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
검색 버튼을 제대로 클릭하여 팝업 띄우기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_search_button():
    """검색 버튼 클릭 테스트"""
    
    print("\n" + "="*60)
    print("   검색 버튼 클릭 테스트")
    print("="*60)
    
    os.makedirs("downloads/test", exist_ok=True)
    os.makedirs("logs/screenshots/test", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
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
            
            # 2. 서울 선택
            print("\n[STEP 2] Selecting Seoul...")
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(1000)
            print("Selected Seoul")
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/test/before_search_{timestamp}.png")
            
            # 3. 검색 버튼 찾기 - 다양한 방법 시도
            print("\n[STEP 3] Finding search button...")
            
            # 방법 1: 클래스와 텍스트로 찾기 (Bootstrap 스타일)
            search_button = await page.query_selector('button.btn.btn-danger')
            
            if not search_button:
                # 방법 2: 텍스트로 찾기
                buttons_with_text = await page.query_selector_all('button')
                for btn in buttons_with_text:
                    text = await btn.text_content()
                    if text and '검색' in text:
                        search_button = btn
                        print(f"Found button with text: {text.strip()}")
                        break
            
            if not search_button:
                # 방법 3: 이미지 alt 텍스트로 찾기
                search_button = await page.query_selector('img[alt*="검색"]')
                if search_button:
                    # 이미지의 부모 요소(링크나 버튼) 찾기
                    parent = await search_button.evaluate_handle('(el) => el.parentElement')
                    if parent:
                        search_button = parent
            
            if search_button:
                print("Found search button!")
                
                # 팝업 이벤트 리스너 등록
                popup_promise = None
                popup_page = None
                
                async def handle_popup(popup):
                    nonlocal popup_page
                    popup_page = popup
                    print("[EVENT] Popup opened!")
                
                page.on('popup', handle_popup)
                
                # 4. 검색 버튼 클릭
                print("\n[STEP 4] Clicking search button...")
                
                # 버튼이 보이는지 확인
                is_visible = await search_button.is_visible()
                print(f"Button visible: {is_visible}")
                
                if not is_visible:
                    # 스크롤하여 보이게 하기
                    await search_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                
                # 클릭 시도
                await search_button.click()
                print("Clicked search button")
                
                # 팝업 대기
                print("\n[STEP 5] Waiting for popup...")
                await page.wait_for_timeout(3000)
                
                # 팝업 확인
                all_pages = context.pages
                print(f"Total pages open: {len(all_pages)}")
                
                if len(all_pages) > 1:
                    popup_page = all_pages[-1]  # 마지막 페이지가 팝업
                    print(f"Popup URL: {popup_page.url}")
                    
                    # 팝업 로드 대기
                    await popup_page.wait_for_load_state('networkidle')
                    
                    # 팝업 스크린샷
                    await popup_page.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                    print("[SCREENSHOT] Popup saved")
                    
                    # 팝업 내용 확인
                    print("\n[STEP 6] Analyzing popup content...")
                    
                    # 테이블 있는지 확인 (검색 결과)
                    tables = await popup_page.query_selector_all('table')
                    print(f"Tables in popup: {len(tables)}")
                    
                    # 행 수 확인
                    if tables:
                        rows = await tables[0].query_selector_all('tr')
                        print(f"Rows in first table: {len(rows)}")
                    
                    # 엑셀 다운로드 버튼 찾기 - 정확한 ID로
                    excel_button = await popup_page.query_selector('#btn_map_excel')
                    if not excel_button:
                        excel_button = await popup_page.query_selector('button#btn_map_excel')
                    if not excel_button:
                        excel_button = await popup_page.query_selector('button.btnLayer#btn_map_excel')
                    if not excel_button:
                        excel_button = await popup_page.query_selector('button:has-text("다운로드")')
                    
                    if excel_button:
                        print("Found Excel download button in popup!")
                        
                        # 엑셀 다운로드 시도
                        try:
                            download_promise = popup_page.wait_for_event('download', timeout=10000)
                            await excel_button.click()
                            print("Clicked Excel button")
                            
                            download = await download_promise
                            filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                            await download.save_as(filepath)
                            print(f"[SUCCESS] Downloaded: {filepath}")
                        except:
                            print("[WARNING] Download failed")
                    else:
                        print("Excel button not found in popup")
                        
                        # 팝업의 모든 이미지 확인
                        all_images = await popup_page.query_selector_all('img[alt]')
                        print(f"\nAll images in popup ({len(all_images)}):")
                        for img in all_images[:10]:
                            alt = await img.get_attribute('alt')
                            src = await img.get_attribute('src')
                            print(f"  - alt='{alt}', src='{src}'")
                else:
                    print("[WARNING] No popup opened")
                    
                    # JavaScript로 다시 시도
                    print("\n[STEP 5B] Trying JavaScript method...")
                    result = await page.evaluate('''() => {
                        // doSearch 함수 호출
                        if (typeof doSearch === 'function') {
                            doSearch();
                            return 'doSearch called';
                        }
                        // 폼 제출
                        const form = document.querySelector('form');
                        if (form) {
                            form.submit();
                            return 'form submitted';
                        }
                        return 'no action taken';
                    }''')
                    print(f"JavaScript result: {result}")
                    
                    await page.wait_for_timeout(3000)
                    
                    # 다시 확인
                    all_pages = context.pages
                    if len(all_pages) > 1:
                        print("Popup opened after JavaScript call!")
            else:
                print("[ERROR] Search button not found")
                
                # 페이지의 모든 버튼 리스트
                all_buttons = await page.query_selector_all('button, a.btn')
                print(f"\nAll buttons on page ({len(all_buttons)}):")
                for i, btn in enumerate(all_buttons[:20]):
                    text = await btn.text_content()
                    tag = await btn.evaluate('el => el.tagName')
                    classes = await btn.get_attribute('class')
                    if text:
                        print(f"  {i+1}. <{tag}> class='{classes}': {text.strip()}")
            
            print("\n[INFO] Browser will remain open for 15 seconds...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    ============================================
       검색 버튼 클릭 테스트
    ============================================
    목표: 검색 버튼을 제대로 클릭하여 
          결과가 있는 팝업 띄우기
    ============================================
    """)
    
    asyncio.run(test_search_button())
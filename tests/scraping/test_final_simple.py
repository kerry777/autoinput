#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단한 최종 테스트 - 사용자가 알려준 정보 활용
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_final_simple():
    """최종 간단 테스트"""
    
    print("\n" + "="*60)
    print("   최종 간단 테스트")
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
            print("\n[1] Loading page...")
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 2. 서울 선택
            print("\n[2] Selecting Seoul...")
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(1000)
            
            # 3. 사용자가 알려준 버튼 찾기
            # <a href="#" id="btn_search_pop" class="btn_search" title="새창으로 이동">
            #   <img src="/npbs/images/np/btn/btn_search.png" alt="검색버튼">
            # </a>
            
            print("\n[3] Looking for #btn_search_pop...")
            
            # ID로 직접 찾기
            search_btn = await page.query_selector('#btn_search_pop')
            
            if search_btn:
                print("Found #btn_search_pop!")
                
                # 클릭 가능한지 확인
                is_visible = await search_btn.is_visible()
                print(f"  Visible: {is_visible}")
                
                # title 속성 확인
                title = await search_btn.get_attribute('title')
                print(f"  Title: {title}")
                
                # 팝업 감지 설정
                popup_opened = False
                popup_page = None
                
                async def handle_popup(popup):
                    nonlocal popup_opened, popup_page
                    popup_opened = True
                    popup_page = popup
                    print("[POPUP] Detected!")
                
                page.on('popup', handle_popup)
                
                # 클릭
                print("\n[4] Clicking #btn_search_pop...")
                await search_btn.click()
                
                # 팝업 대기
                print("[5] Waiting for popup...")
                await page.wait_for_timeout(5000)
                
                # 팝업 확인
                if popup_opened and popup_page:
                    print("[SUCCESS] Popup opened!")
                    
                    await popup_page.wait_for_load_state('networkidle')
                    
                    # 스크린샷
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await popup_page.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                    
                    # 다운로드 버튼 찾기
                    # <button class="btnLayer" id="btn_map_excel">다운로드</button>
                    print("\n[6] Looking for #btn_map_excel...")
                    
                    download_btn = await popup_page.query_selector('#btn_map_excel')
                    
                    if download_btn:
                        print("Found #btn_map_excel!")
                        
                        # 다운로드 시도
                        try:
                            download_promise = popup_page.wait_for_event('download', timeout=10000)
                            await download_btn.click()
                            print("Clicked download button")
                            
                            download = await download_promise
                            filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                            await download.save_as(filepath)
                            print(f"[SUCCESS] Downloaded: {filepath}")
                            
                        except asyncio.TimeoutError:
                            print("[WARNING] Download timeout")
                    else:
                        print("[ERROR] #btn_map_excel not found")
                        
                        # 모든 버튼 확인
                        all_buttons = await popup_page.query_selector_all('button')
                        print(f"\nAll buttons in popup: {len(all_buttons)}")
                        for i, btn in enumerate(all_buttons[:10]):
                            btn_id = await btn.get_attribute('id')
                            btn_text = await btn.text_content()
                            print(f"  {i}: id='{btn_id}', text='{btn_text}'")
                    
                elif len(context.pages) > 1:
                    # page.on('popup') 이벤트를 못 잡았지만 새 페이지는 열림
                    print("[INFO] New page detected in context.pages")
                    popup_page = context.pages[-1]
                    
                    await popup_page.wait_for_load_state('networkidle')
                    
                    # 다운로드 버튼 찾기
                    download_btn = await popup_page.query_selector('#btn_map_excel')
                    if download_btn:
                        print("Found download button!")
                        await download_btn.click()
                        print("Clicked download button")
                else:
                    print("[ERROR] No popup opened")
                    
                    # 현재 페이지 URL 확인
                    current_url = page.url
                    print(f"  Current URL: {current_url}")
            else:
                print("[ERROR] #btn_search_pop not found")
                
                # 디버깅 - 모든 a 태그 확인
                all_links = await page.query_selector_all('a')
                print(f"\nTotal links: {len(all_links)}")
                
                for link in all_links[:50]:
                    link_id = await link.get_attribute('id')
                    if link_id and 'search' in link_id.lower():
                        link_class = await link.get_attribute('class')
                        link_title = await link.get_attribute('title')
                        print(f"  Found: id='{link_id}', class='{link_class}', title='{link_title}'")
            
            print("\n[INFO] Browser will remain open for 10 seconds...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    ============================================
       최종 간단 테스트
    ============================================
    사용자 제공 정보:
    - 검색 버튼: #btn_search_pop
    - 다운로드 버튼: #btn_map_excel
    ============================================
    """)
    
    asyncio.run(test_final_simple())
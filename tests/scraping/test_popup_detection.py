#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
팝업 감지 테스트 - 정확한 팝업 감지 방법 찾기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_popup_detection():
    """팝업 감지 테스트"""
    
    print("\n" + "="*60)
    print("   팝업 감지 테스트")
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
        
        # 모든 새 페이지 감지
        new_pages = []
        
        def handle_page(page):
            print(f"[NEW PAGE] {page.url}")
            new_pages.append(page)
        
        context.on('page', handle_page)
        
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
            
            # 3. 검색 실행 전 페이지 수
            print(f"\n[3] Pages before search: {len(context.pages)}")
            for i, p in enumerate(context.pages):
                print(f"  Page {i}: {p.url[:50]}...")
            
            # 4. JavaScript로 검색 실행
            print("\n[4] Executing doSearch()...")
            await page.evaluate('doSearch()')
            
            # 5. 잠시 대기
            print("\n[5] Waiting 5 seconds...")
            await page.wait_for_timeout(5000)
            
            # 6. 현재 열린 페이지들 확인
            print(f"\n[6] Pages after search: {len(context.pages)}")
            for i, p in enumerate(context.pages):
                print(f"  Page {i}: {p.url[:50]}...")
            
            # 7. 새로 열린 페이지 확인
            if len(context.pages) > 1:
                popup = context.pages[-1]
                print(f"\n[7] POPUP FOUND!")
                print(f"  URL: {popup.url}")
                
                # 팝업 로드 대기
                await popup.wait_for_load_state('networkidle', timeout=10000)
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                
                # 다운로드 버튼 찾기 - 정확한 ID 사용
                print("\n[8] Looking for download button...")
                
                # ID로 직접 찾기
                download_btn = await popup.query_selector('#btn_map_excel')
                if download_btn:
                    print("  Found button by ID: #btn_map_excel")
                else:
                    # 다른 방법들
                    download_btn = await popup.query_selector('button#btn_map_excel')
                    if download_btn:
                        print("  Found: button#btn_map_excel")
                    else:
                        download_btn = await popup.query_selector('[id="btn_map_excel"]')
                        if download_btn:
                            print("  Found: [id='btn_map_excel']")
                
                if download_btn:
                    print("\n[9] Clicking download button...")
                    
                    # 다운로드 대기 준비
                    try:
                        download_promise = popup.wait_for_event('download', timeout=10000)
                        await download_btn.click()
                        
                        download = await download_promise
                        filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                        await download.save_as(filepath)
                        print(f"[SUCCESS] Downloaded: {filepath}")
                    except asyncio.TimeoutError:
                        print("[WARNING] Download timeout - trying JavaScript")
                        
                        # JavaScript로 다운로드 시도
                        await popup.evaluate('''() => {
                            const btn = document.querySelector('#btn_map_excel');
                            if (btn) btn.click();
                            else console.log('Button not found');
                        }''')
                else:
                    print("[WARNING] Download button not found")
                    
                    # 모든 버튼 확인
                    all_buttons = await popup.query_selector_all('button')
                    print(f"\n  All buttons in popup: {len(all_buttons)}")
                    for i, btn in enumerate(all_buttons[:10]):
                        btn_id = await btn.get_attribute('id')
                        btn_class = await btn.get_attribute('class')
                        btn_text = await btn.text_content()
                        print(f"    {i}: id='{btn_id}', class='{btn_class}', text='{btn_text}'")
            else:
                print("\n[7] NO POPUP DETECTED")
                
                # 현재 페이지가 변경되었는지 확인
                current_url = page.url
                print(f"  Current URL: {current_url}")
                if current_url != url:
                    print("  URL changed - might be a redirect instead of popup")
            
            # 8. 새로 열린 페이지들 확인
            if new_pages:
                print(f"\n[8] New pages detected: {len(new_pages)}")
                for p in new_pages:
                    print(f"  - {p.url[:50]}...")
            
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
       팝업 감지 정밀 테스트
    ============================================
    목표: doSearch() 실행 후 팝업 정확히 감지
    ============================================
    """)
    
    asyncio.run(test_popup_detection())
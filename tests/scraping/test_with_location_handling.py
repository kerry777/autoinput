#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
위치 정보 팝업 처리 포함 테스트
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_with_location_handling():
    """위치 정보 팝업 처리 테스트"""
    
    print("\n" + "="*60)
    print("   위치 정보 팝업 처리 테스트")
    print("="*60)
    
    os.makedirs("downloads/test", exist_ok=True)
    os.makedirs("logs/screenshots/test", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        
        # 위치 정보 권한 거부 설정
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            permissions=[],  # 모든 권한 거부
            geolocation=None  # 위치 정보 제공 안 함
        )
        
        page = await context.new_page()
        
        # 다이얼로그 자동 처리
        async def handle_dialog(dialog):
            print(f"[DIALOG] {dialog.type}: {dialog.message}")
            await dialog.dismiss()  # 거부/취소
        
        page.on('dialog', handle_dialog)
        
        try:
            # 1. 페이지 이동
            print("\n[1] Loading page...")
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 2. 서울 선택
            print("\n[2] Selecting Seoul...")
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(2000)
            
            # 3. 검색 버튼 찾기
            print("\n[3] Finding search button...")
            search_btn = await page.query_selector('#btn_search_pop')
            
            if not search_btn:
                print("[ERROR] Search button not found")
                return
            
            # 4. 검색 버튼 클릭
            print("\n[4] Clicking search button...")
            await search_btn.click()
            
            # 5. 잠시 대기 후 페이지 확인
            print("\n[5] Waiting for windows to open...")
            await page.wait_for_timeout(5000)
            
            # 6. 열린 모든 페이지 확인
            all_pages = context.pages
            print(f"\n[6] Total pages open: {len(all_pages)}")
            
            for i, p in enumerate(all_pages):
                print(f"  Page {i}: {p.url[:80]}...")
            
            # 7. 팝업 찾기 (마지막 열린 페이지)
            if len(all_pages) > 1:
                popup = all_pages[-1]
                print(f"\n[7] Working with popup: {popup.url[:80]}...")
                
                # 팝업 로드 대기
                await popup.wait_for_load_state('networkidle', timeout=30000)
                await popup.wait_for_timeout(3000)
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                
                # 8. 다운로드 버튼 찾기
                print("\n[8] Looking for download button...")
                download_btn = await popup.query_selector('#btn_map_excel')
                
                if download_btn:
                    print("Found download button!")
                    
                    # 9. 다운로드 시도
                    print("\n[9] Clicking download button...")
                    download_promise = popup.wait_for_event('download', timeout=30000)
                    
                    await download_btn.click()
                    
                    try:
                        download = await download_promise
                        filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                        await download.save_as(filepath)
                        print(f"\n[SUCCESS] Downloaded: {filepath}")
                        
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            print(f"File size: {file_size:,} bytes")
                    except asyncio.TimeoutError:
                        print("[WARNING] Download timeout")
                        
                        # JavaScript로 다운로드 시도
                        print("Trying JavaScript download...")
                        await popup.evaluate('''() => {
                            const btn = document.querySelector('#btn_map_excel');
                            if (btn) {
                                btn.click();
                                return 'clicked';
                            }
                            return 'not found';
                        }''')
                else:
                    print("[ERROR] Download button not found")
                    
                    # 페이지 내용 확인
                    title = await popup.title()
                    print(f"Popup title: {title}")
                    
                    # 모든 버튼 확인
                    all_buttons = await popup.query_selector_all('button')
                    print(f"\nButtons found: {len(all_buttons)}")
                    for i, btn in enumerate(all_buttons[:5]):
                        btn_id = await btn.get_attribute('id')
                        btn_class = await btn.get_attribute('class')
                        btn_text = await btn.text_content()
                        print(f"  Button {i}: id='{btn_id}', class='{btn_class}', text='{btn_text}'")
            else:
                print("\n[WARNING] No popup opened")
                
                # JavaScript로 새 창 열기 시도
                print("Trying to open window with JavaScript...")
                await page.evaluate('''() => {
                    const btn = document.querySelector('#btn_search_pop');
                    if (btn) {
                        // onclick 이벤트 직접 실행
                        if (btn.onclick) {
                            btn.onclick();
                        }
                        // href로 새 창 열기
                        else if (btn.href && btn.href !== '#') {
                            window.open(btn.href, '_blank');
                        }
                    }
                }''')
                
                await page.wait_for_timeout(5000)
                
                # 다시 확인
                if len(context.pages) > 1:
                    print("Window opened after JavaScript!")
            
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
       위치 정보 팝업 처리 테스트
    ============================================
    - 위치 정보 권한 자동 거부
    - 다이얼로그 자동 처리
    - context.pages로 팝업 감지
    ============================================
    """)
    
    asyncio.run(test_with_location_handling())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서울특별시만 테스트 - 타임아웃 증가 버전
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_seoul_only():
    """서울만 테스트"""
    
    print("\n" + "="*60)
    print("   서울특별시 다운로드 테스트")
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
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000)
            
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
            
            print("Found search button!")
            
            # 4. 팝업 대기 준비
            print("\n[4] Setting up popup listener...")
            popup_promise = page.wait_for_event('popup', timeout=60000)  # 60초 대기
            
            # 5. 검색 버튼 클릭
            print("\n[5] Clicking search button...")
            await search_btn.click()
            
            # 6. 팝업 대기
            print("\n[6] Waiting for popup (up to 60 seconds)...")
            print("   데이터가 많아서 시간이 걸릴 수 있습니다...")
            
            try:
                popup = await popup_promise
                print("\n[SUCCESS] Popup opened!")
                
                # 7. 팝업 로드 대기
                print("\n[7] Waiting for popup to load completely...")
                await popup.wait_for_load_state('networkidle', timeout=60000)
                await popup.wait_for_timeout(5000)
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                print("Screenshot saved")
                
                # 8. 다운로드 버튼 찾기
                print("\n[8] Looking for download button...")
                download_btn = await popup.query_selector('#btn_map_excel')
                
                if download_btn:
                    print("Found download button!")
                    
                    # 9. 다운로드 시도
                    print("\n[9] Attempting download...")
                    download_promise = popup.wait_for_event('download', timeout=60000)
                    
                    await download_btn.click()
                    print("Clicked download button")
                    
                    try:
                        download = await download_promise
                        filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                        await download.save_as(filepath)
                        print(f"\n[SUCCESS] File downloaded: {filepath}")
                        
                        # 파일 크기 확인
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            print(f"File size: {file_size:,} bytes")
                    except asyncio.TimeoutError:
                        print("[WARNING] Download timeout")
                else:
                    print("[ERROR] Download button not found")
                    
                    # 모든 버튼 확인
                    all_buttons = await popup.query_selector_all('button')
                    print(f"\nAll buttons in popup: {len(all_buttons)}")
                    for i, btn in enumerate(all_buttons[:10]):
                        btn_id = await btn.get_attribute('id')
                        btn_text = await btn.text_content()
                        print(f"  {i}: id='{btn_id}', text='{btn_text}'")
                
            except asyncio.TimeoutError:
                print("\n[ERROR] Popup timeout - 팝업이 열리지 않았습니다")
                
                # 현재 페이지 수 확인
                print(f"Total pages: {len(context.pages)}")
            
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
       서울특별시 다운로드 테스트
    ============================================
    타임아웃: 60초
    데이터가 많아서 시간이 걸립니다
    ============================================
    """)
    
    asyncio.run(test_seoul_only())
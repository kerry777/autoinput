#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
안정적인 다운로드 버전 - 서울만 테스트
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def download_seoul():
    """서울 데이터 다운로드"""
    
    print("\n" + "="*60)
    print("   서울특별시 다운로드 (안정화 버전)")
    print("="*60)
    
    os.makedirs("downloads/stable", exist_ok=True)
    os.makedirs("logs/screenshots/stable", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1500  # 더 천천히
        )
        
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            permissions=[],  # 위치 권한 거부
            geolocation=None
        )
        
        page = await context.new_page()
        
        try:
            # 1. 페이지 이동
            print("\n[1] Loading page...")
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(5000)
            
            # 2. 서울 선택
            print("[2] Selecting Seoul...")
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(2000)
            
            # 3. 검색 버튼 클릭
            print("[3] Clicking search button...")
            search_btn = await page.query_selector('#btn_search_pop')
            if search_btn:
                await search_btn.click()
            else:
                print("[ERROR] Search button not found")
                return
            
            # 4. 팝업 대기 (충분한 시간)
            print("[4] Waiting for popup to open and stabilize...")
            await page.wait_for_timeout(8000)  # 8초 대기
            
            # 5. 모든 페이지 확인
            all_pages = context.pages
            print(f"[5] Total pages: {len(all_pages)}")
            
            popup = None
            for p in all_pages:
                if p != page:  # 메인 페이지가 아닌 것
                    popup = p
                    print(f"    Found popup: {popup.url[:60]}...")
                    break
            
            if not popup:
                print("[ERROR] No popup found")
                return
            
            # 6. 팝업이 완전히 로드될 때까지 대기
            print("[6] Waiting for popup to fully load...")
            try:
                await popup.wait_for_load_state('domcontentloaded', timeout=30000)
                await popup.wait_for_timeout(3000)
            except:
                print("[WARNING] Popup load timeout, continuing anyway...")
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                await popup.screenshot(path=f"logs/screenshots/stable/popup_{timestamp}.png")
                print("    Screenshot saved")
            except:
                print("    [WARNING] Could not take screenshot")
            
            # 7. 다운로드 버튼 찾기 (여러 방법 시도)
            print("[7] Looking for download button...")
            download_btn = None
            
            # 방법 1: ID로 찾기
            try:
                download_btn = await popup.query_selector('#btn_map_excel')
                if download_btn:
                    print("    Found by ID: #btn_map_excel")
            except:
                pass
            
            # 방법 2: 클래스와 ID로 찾기
            if not download_btn:
                try:
                    download_btn = await popup.query_selector('button.btnLayer#btn_map_excel')
                    if download_btn:
                        print("    Found by class+ID")
                except:
                    pass
            
            # 방법 3: 텍스트로 찾기
            if not download_btn:
                try:
                    all_buttons = await popup.query_selector_all('button')
                    for btn in all_buttons:
                        text = await btn.text_content()
                        if text and '다운로드' in text:
                            download_btn = btn
                            print(f"    Found by text: {text}")
                            break
                except:
                    pass
            
            if download_btn:
                print("[8] Clicking download button...")
                
                # 다운로드 대기 준비
                download_promise = popup.wait_for_event('download', timeout=30000)
                
                # 버튼 클릭
                await download_btn.click()
                
                try:
                    download = await download_promise
                    filepath = f"downloads/stable/seoul_{timestamp}.xlsx"
                    await download.save_as(filepath)
                    print(f"[SUCCESS] Downloaded: {filepath}")
                    
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"    File size: {file_size:,} bytes")
                except asyncio.TimeoutError:
                    print("[WARNING] Download timeout")
                    
                    # JavaScript로 재시도
                    print("    Trying JavaScript click...")
                    try:
                        result = await popup.evaluate('''() => {
                            const btn = document.querySelector('#btn_map_excel');
                            if (btn) {
                                btn.click();
                                return 'clicked';
                            }
                            return 'not found';
                        }''')
                        print(f"    JavaScript result: {result}")
                    except:
                        print("    JavaScript failed")
            else:
                print("[ERROR] Download button not found")
                
                # 디버깅 정보
                try:
                    all_buttons = await popup.query_selector_all('button')
                    print(f"    Total buttons: {len(all_buttons)}")
                    for i, btn in enumerate(all_buttons[:5]):
                        btn_id = await btn.get_attribute('id')
                        btn_text = await btn.text_content()
                        print(f"      Button {i}: id='{btn_id}', text='{btn_text}'")
                except:
                    print("    Could not list buttons")
            
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
       안정적인 다운로드 테스트
    ============================================
    - 충분한 대기 시간
    - 에러 처리 강화
    - 여러 방법으로 요소 찾기
    ============================================
    """)
    
    asyncio.run(download_seoul())
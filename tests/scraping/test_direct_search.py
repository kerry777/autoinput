#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
직접 JavaScript 함수 호출로 검색 실행
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_direct_search():
    """JavaScript 함수 직접 호출"""
    
    print("\n" + "="*60)
    print("   JavaScript 직접 호출 테스트")
    print("="*60)
    
    # 디렉토리 생성
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
        
        # 팝업 감지 설정
        popup_page = None
        
        def handle_popup(popup):
            nonlocal popup_page
            popup_page = popup
            print("[POPUP] New popup detected!")
        
        context.on('page', handle_popup)
        
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
            await page.screenshot(path=f"logs/screenshots/test/seoul_{timestamp}.png")
            
            # 3. JavaScript 함수 확인
            print("\n[STEP 3] Checking JavaScript functions...")
            
            # 페이지의 JavaScript 함수들 확인
            js_functions = await page.evaluate('''() => {
                const funcs = [];
                for (const key in window) {
                    if (typeof window[key] === 'function' && 
                        (key.toLowerCase().includes('search') || 
                         key.toLowerCase().includes('submit') ||
                         key.toLowerCase().includes('do') ||
                         key.toLowerCase().includes('fn'))) {
                        funcs.push(key);
                    }
                }
                return funcs;
            }''')
            
            print(f"Found JavaScript functions: {js_functions}")
            
            # 4. 검색 함수 직접 호출
            print("\n[STEP 4] Calling search function directly...")
            
            # 일반적인 검색 함수명들 시도
            search_functions = [
                'doSearch()',
                'fnSearch()',
                'fn_search()',
                'search()',
                'submit()',
                'doSubmit()',
                'fnSubmit()',
                'goSearch()',
                'searchLtco()',
                'selectLtcoSrch()'
            ]
            
            for func in search_functions:
                try:
                    print(f"Trying: {func}")
                    
                    # 팝업이 열릴 것을 대비
                    await page.evaluate(f'''() => {{
                        if (typeof {func.replace('()', '')} === 'function') {{
                            {func}
                            return true;
                        }}
                        return false;
                    }}''')
                    
                    # 잠시 대기
                    await page.wait_for_timeout(2000)
                    
                    # 팝업이 열렸는지 확인
                    if popup_page:
                        print(f"[SUCCESS] Popup opened with {func}!")
                        break
                    
                    # URL이 변경되었는지 확인
                    if page.url != url:
                        print(f"[SUCCESS] Page changed with {func}!")
                        break
                        
                except Exception as e:
                    print(f"  Failed: {e}")
                    continue
            
            # 5. 팝업 처리
            if popup_page:
                print("\n[STEP 5] Processing popup...")
                await popup_page.wait_for_load_state('networkidle')
                await popup_page.wait_for_timeout(2000)
                
                # 팝업 스크린샷
                await popup_page.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                print("[SCREENSHOT] Popup saved")
                
                # 팝업에서 엑셀 다운로드 버튼 찾기
                print("Looking for Excel download button in popup...")
                
                # 엑셀 관련 이미지나 버튼 찾기
                download_btn = await popup_page.query_selector('img[alt*="엑셀"]')
                if not download_btn:
                    download_btn = await popup_page.query_selector('img[src*="excel"]')
                if not download_btn:
                    download_btn = await popup_page.query_selector('a[title*="엑셀"]')
                if not download_btn:
                    download_btn = await popup_page.query_selector('button:has-text("엑셀")')
                if not download_btn:
                    download_btn = await popup_page.query_selector('a:has-text("엑셀")')
                if not download_btn:
                    download_btn = await popup_page.query_selector('[onclick*="excel"]')
                if not download_btn:
                    download_btn = await popup_page.query_selector('[onclick*="Excel"]')
                
                # 모든 이미지 버튼 확인
                if not download_btn:
                    print("Checking all image buttons...")
                    img_buttons = await popup_page.query_selector_all('img[alt]')
                    print(f"Found {len(img_buttons)} image buttons")
                    for img in img_buttons[:10]:
                        alt_text = await img.get_attribute('alt')
                        src = await img.get_attribute('src')
                        print(f"  - alt='{alt_text}', src='{src}'")
                        if alt_text and ('엑셀' in alt_text or 'excel' in alt_text.lower() or '다운' in alt_text):
                            download_btn = img
                            print(f"    -> Selected this as download button")
                            break
                
                if download_btn:
                    print("Found download button!")
                    
                    try:
                        # 다운로드 시도
                        download_promise = popup_page.wait_for_event('download', timeout=10000)
                        await download_btn.click()
                        print("Clicked download button")
                        
                        download = await download_promise
                        
                        # 파일 저장
                        filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                        await download.save_as(filepath)
                        print(f"[SUCCESS] File saved: {filepath}")
                        
                    except asyncio.TimeoutError:
                        print("[WARNING] Download timeout")
                        
                        # JavaScript로 다운로드 함수 호출
                        await popup_page.evaluate('''() => {
                            if (typeof doExcelDown === 'function') doExcelDown();
                            else if (typeof excelDownload === 'function') excelDownload();
                            else if (typeof fnExcelDown === 'function') fnExcelDown();
                        }''')
                else:
                    print("Download button not found in popup")
                    
                    # 팝업의 모든 버튼 확인
                    all_buttons = await popup_page.query_selector_all('button, a.btn')
                    print(f"Popup has {len(all_buttons)} buttons")
                    for i, btn in enumerate(all_buttons[:5]):
                        text = await btn.text_content()
                        if text:
                            print(f"  - {text.strip()}")
            else:
                print("\n[WARNING] No popup opened")
                
                # 폼 제출 시도
                print("Trying form submit...")
                await page.evaluate('''() => {
                    const forms = document.querySelectorAll('form');
                    if (forms.length > 0) {
                        forms[0].submit();
                        return true;
                    }
                    return false;
                }''')
            
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
       JavaScript 직접 호출 테스트
    ============================================
    버튼 클릭 대신 JavaScript 함수 직접 호출
    ============================================
    """)
    
    asyncio.run(test_direct_search())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JavaScript 함수 탐색 및 검색 버튼 직접 찾기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_javascript_functions():
    """JavaScript 함수 및 검색 버튼 탐색"""
    
    print("\n" + "="*60)
    print("   JavaScript 함수 탐색")
    print("="*60)
    
    os.makedirs("logs/screenshots/test", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        
        context = await browser.new_context(
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
            
            # 3. JavaScript 함수들 탐색
            print("\n[3] Exploring JavaScript functions...")
            
            js_functions = await page.evaluate('''() => {
                const funcs = [];
                for (const key in window) {
                    if (typeof window[key] === 'function') {
                        const keyLower = key.toLowerCase();
                        if (keyLower.includes('search') || 
                            keyLower.includes('submit') ||
                            keyLower.includes('popup') ||
                            keyLower.includes('open') ||
                            keyLower.includes('do') ||
                            keyLower.includes('fn')) {
                            funcs.push(key);
                        }
                    }
                }
                return funcs;
            }''')
            
            print(f"Found functions: {js_functions}")
            
            # 4. 검색 관련 요소들 찾기
            print("\n[4] Finding search-related elements...")
            
            # ID가 btn_search_pop인 요소 찾기
            search_pop_btn = await page.query_selector('#btn_search_pop')
            if search_pop_btn:
                print("Found #btn_search_pop")
                
                # onclick 속성 확인
                onclick = await search_pop_btn.get_attribute('onclick')
                print(f"  onclick: {onclick}")
                
                # 클릭해보기
                print("\n[5] Clicking #btn_search_pop...")
                
                # 팝업 대기 준비
                popup_promise = page.wait_for_event('popup', timeout=5000)
                
                await search_pop_btn.click()
                
                try:
                    popup = await popup_promise
                    print("[SUCCESS] Popup opened!")
                    
                    await popup.wait_for_load_state('networkidle')
                    
                    # 스크린샷
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                    
                    # 다운로드 버튼 찾기
                    download_btn = await popup.query_selector('#btn_map_excel')
                    if download_btn:
                        print("Found download button #btn_map_excel!")
                        
                        # 다운로드 시도
                        try:
                            download_promise = popup.wait_for_event('download', timeout=10000)
                            await download_btn.click()
                            
                            download = await download_promise
                            filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                            os.makedirs("downloads/test", exist_ok=True)
                            await download.save_as(filepath)
                            print(f"[SUCCESS] Downloaded: {filepath}")
                        except:
                            print("[WARNING] Download failed")
                    
                except asyncio.TimeoutError:
                    print("[WARNING] No popup after clicking #btn_search_pop")
            
            # 다른 검색 버튼들 찾기
            print("\n[6] Finding all search buttons...")
            
            # 이미지 alt 텍스트로 찾기
            search_images = await page.query_selector_all('img[alt*="검색"]')
            print(f"Found {len(search_images)} search images")
            
            for i, img in enumerate(search_images):
                alt = await img.get_attribute('alt')
                src = await img.get_attribute('src')
                print(f"  Image {i}: alt='{alt}', src='{src}'")
                
                # 부모 요소 확인
                parent = await img.evaluate_handle('(el) => el.parentElement')
                if parent:
                    parent_tag = await parent.evaluate('el => el.tagName')
                    parent_id = await parent.evaluate('el => el.id')
                    parent_onclick = await parent.evaluate('el => el.onclick ? el.onclick.toString() : null')
                    print(f"    Parent: <{parent_tag}> id='{parent_id}'")
                    if parent_onclick:
                        print(f"    onclick: {parent_onclick[:100]}...")
            
            # 모든 onclick 속성 가진 요소들
            print("\n[7] Elements with onclick...")
            onclick_elements = await page.query_selector_all('[onclick]')
            print(f"Found {len(onclick_elements)} elements with onclick")
            
            for i, elem in enumerate(onclick_elements[:10]):
                onclick = await elem.get_attribute('onclick')
                tag = await elem.evaluate('el => el.tagName')
                text = await elem.text_content()
                if 'search' in onclick.lower() or 'popup' in onclick.lower():
                    print(f"  {tag}: onclick='{onclick[:50]}...', text='{text}'")
            
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
       JavaScript 함수 및 검색 버튼 탐색
    ============================================
    목표: 실제 검색 버튼과 팝업 열기 방법 찾기
    ============================================
    """)
    
    asyncio.run(test_javascript_functions())
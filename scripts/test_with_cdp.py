#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CDP를 사용한 새 탭 감지 테스트
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_with_cdp():
    """CDP를 사용한 테스트"""
    
    print("\n" + "="*60)
    print("   CDP 새 탭 감지 테스트")
    print("="*60)
    
    os.makedirs("downloads/test", exist_ok=True)
    os.makedirs("logs/screenshots/test", exist_ok=True)
    
    async with async_playwright() as p:
        # Chrome 브라우저 사용 (CDP 지원)
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1500,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            permissions=[]
        )
        
        # 모든 새 페이지 이벤트 감지
        all_pages = []
        
        def on_page(page):
            print(f"[NEW PAGE] {page.url}")
            all_pages.append(page)
        
        context.on('page', on_page)
        
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
            
            # 3. 검색 버튼 클릭 - 여러 방법 시도
            print("[3] Finding and clicking search button...")
            
            # 방법 1: 일반 클릭
            search_btn = await page.query_selector('#btn_search_pop')
            if search_btn:
                print("    Found #btn_search_pop")
                
                # Ctrl+클릭으로 새 탭에서 열기
                await search_btn.click(modifiers=['Control'])
                print("    Clicked with Ctrl")
                
                await page.wait_for_timeout(5000)
                
                # 새 페이지 확인
                if len(context.pages) > 1:
                    print("    [SUCCESS] New tab opened with Ctrl+Click")
                else:
                    # 일반 클릭
                    await search_btn.click()
                    print("    Clicked normally")
                    await page.wait_for_timeout(5000)
            
            # 4. JavaScript로 강제 새 창 열기
            if len(context.pages) == 1:
                print("\n[4] Trying JavaScript window.open...")
                
                # href 가져오기
                href = await page.evaluate('''() => {
                    const btn = document.querySelector('#btn_search_pop');
                    if (btn) {
                        // onclick 함수 실행
                        if (btn.onclick) {
                            btn.onclick();
                        }
                        return btn.href || 'clicked';
                    }
                    return 'not found';
                }''')
                print(f"    Result: {href}")
                
                await page.wait_for_timeout(5000)
            
            # 5. 결과 확인
            print(f"\n[5] Final check:")
            print(f"    Total pages in context: {len(context.pages)}")
            print(f"    New pages detected: {len(all_pages)}")
            
            # 팝업/새 탭 처리
            popup = None
            for p in context.pages:
                if p != page:
                    popup = p
                    print(f"    Working with: {popup.url[:80]}...")
                    break
            
            if popup:
                # 로드 대기
                try:
                    await popup.wait_for_load_state('domcontentloaded', timeout=20000)
                except:
                    pass
                
                await popup.wait_for_timeout(3000)
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                try:
                    await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                    print("    Screenshot saved")
                except:
                    pass
                
                # 다운로드 버튼 찾기
                print("\n[6] Looking for download button...")
                try:
                    # JavaScript로 직접 찾기
                    btn_exists = await popup.evaluate('''() => {
                        const btn = document.querySelector('#btn_map_excel');
                        if (btn) {
                            return {
                                exists: true,
                                text: btn.textContent,
                                visible: btn.offsetParent !== null
                            };
                        }
                        return { exists: false };
                    }''')
                    
                    print(f"    Button check: {btn_exists}")
                    
                    if btn_exists['exists']:
                        # JavaScript로 클릭
                        await popup.evaluate('''() => {
                            const btn = document.querySelector('#btn_map_excel');
                            if (btn) btn.click();
                        }''')
                        print("    Clicked download button via JavaScript")
                        
                        await popup.wait_for_timeout(5000)
                except:
                    print("    Error checking button")
            
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
       CDP 새 탭 감지 테스트
    ============================================
    - Ctrl+Click으로 새 탭 열기
    - context.on('page') 이벤트 사용
    - JavaScript 직접 실행
    ============================================
    """)
    
    asyncio.run(test_with_cdp())
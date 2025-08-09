#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
요양기관 검색 - 올바른 폼과 버튼 찾기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_facility_search():
    """요양기관 검색 테스트"""
    
    print("\n" + "="*60)
    print("   요양기관 검색 테스트")
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
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/test/initial_{timestamp}.png")
            
            # 2. 페이지 분석
            print("\n[2] Analyzing page structure...")
            
            # ltco_info 폼 찾기 (요양기관 정보 폼)
            ltco_form = await page.query_selector('form#ltco_info')
            if ltco_form:
                print("Found ltco_info form")
                
                # 폼 내부의 select 요소들
                selects = await ltco_form.query_selector_all('select')
                print(f"  Selects in form: {len(selects)}")
                
                for i, sel in enumerate(selects):
                    name = await sel.get_attribute('name')
                    print(f"    Select {i}: name='{name}'")
            
            # 3. 서울 선택
            print("\n[3] Selecting Seoul...")
            
            # siDoCd select 찾기
            sido_select = await page.query_selector('select[name="siDoCd"]')
            if sido_select:
                # 폼 내부에 있는지 확인
                parent_form = await sido_select.evaluate('(el) => el.closest("form") ? el.closest("form").id : null')
                print(f"  Select is in form: {parent_form}")
                
                await page.select_option('select[name="siDoCd"]', value="11")
                await page.wait_for_timeout(1000)
                print("  Seoul selected")
            
            # 4. 검색 버튼들 찾기
            print("\n[4] Finding search buttons...")
            
            # 모든 이미지 찾기
            all_images = await page.query_selector_all('img')
            print(f"Total images: {len(all_images)}")
            
            search_buttons = []
            for img in all_images:
                alt = await img.get_attribute('alt')
                src = await img.get_attribute('src')
                
                if alt and '검색' in alt:
                    # 부모 요소 확인
                    parent = await img.evaluate('''(el) => {
                        const parent = el.parentElement;
                        return {
                            tag: parent.tagName,
                            id: parent.id,
                            class: parent.className,
                            onclick: parent.onclick ? parent.onclick.toString() : null,
                            href: parent.href
                        };
                    }''')
                    
                    search_buttons.append({
                        'alt': alt,
                        'src': src,
                        'parent': parent,
                        'element': img
                    })
                    
                    print(f"  Found search button: alt='{alt}'")
                    print(f"    Parent: {parent['tag']} id='{parent['id']}' class='{parent['class']}'")
            
            # 5. 올바른 검색 버튼 찾기
            print("\n[5] Testing search buttons...")
            
            # ltco_info 폼과 관련된 검색 버튼 찾기
            for btn_info in search_buttons:
                img = btn_info['element']
                
                # 이 버튼이 ltco_info 폼과 관련있는지 확인
                is_ltco_related = await img.evaluate('''(el) => {
                    const form = document.getElementById('ltco_info');
                    if (!form) return false;
                    
                    // 버튼이 폼 근처에 있는지 확인
                    const rect1 = el.getBoundingClientRect();
                    const rect2 = form.getBoundingClientRect();
                    
                    // Y 좌표가 폼 영역 내에 있는지
                    return rect1.top >= rect2.top && rect1.bottom <= rect2.bottom;
                }''')
                
                if is_ltco_related:
                    print(f"\n  This button seems related to ltco_info form")
                    
                    # 부모 클릭
                    parent_elem = await img.evaluate_handle('(el) => el.parentElement')
                    
                    # 팝업 대기 준비
                    print("  Clicking search button...")
                    
                    # 클릭 전 페이지 수
                    pages_before = len(context.pages)
                    
                    await parent_elem.click()
                    
                    # 잠시 대기
                    await page.wait_for_timeout(3000)
                    
                    # 새 페이지 확인
                    pages_after = len(context.pages)
                    
                    if pages_after > pages_before:
                        print("[SUCCESS] New page opened!")
                        popup = context.pages[-1]
                        
                        await popup.wait_for_load_state('networkidle')
                        
                        # 스크린샷
                        await popup.screenshot(path=f"logs/screenshots/test/popup_{timestamp}.png")
                        
                        # URL 확인
                        print(f"  Popup URL: {popup.url[:100]}...")
                        
                        # 다운로드 버튼 찾기
                        download_btn = await popup.query_selector('#btn_map_excel')
                        if download_btn:
                            print("  Found download button!")
                            
                            try:
                                download_promise = popup.wait_for_event('download', timeout=10000)
                                await download_btn.click()
                                
                                download = await download_promise
                                filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                                await download.save_as(filepath)
                                print(f"[SUCCESS] Downloaded: {filepath}")
                            except:
                                print("[WARNING] Download failed")
                        
                        break
                    else:
                        print("  No popup opened, trying next button...")
            
            # 6. JavaScript 함수들 확인
            print("\n[6] Checking JavaScript functions in ltco_info context...")
            
            js_funcs = await page.evaluate('''() => {
                const results = [];
                
                // onclick 속성들 확인
                const elements = document.querySelectorAll('[onclick]');
                for (const el of elements) {
                    const onclick = el.onclick.toString();
                    if (onclick.includes('ltco') || onclick.includes('Ltco')) {
                        results.push({
                            tag: el.tagName,
                            id: el.id,
                            onclick: onclick.substring(0, 100)
                        });
                    }
                }
                
                return results;
            }''')
            
            if js_funcs:
                print("Found ltco-related functions:")
                for func in js_funcs:
                    print(f"  {func['tag']} id='{func['id']}': {func['onclick']}...")
            
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
       요양기관 검색 정확한 방법 찾기
    ============================================
    목표: ltco_info 폼의 검색 버튼 찾기
    ============================================
    """)
    
    asyncio.run(test_facility_search())
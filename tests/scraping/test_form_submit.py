#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
폼 제출 방식으로 검색 실행
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_form_submit():
    """폼 제출 방식 테스트"""
    
    print("\n" + "="*60)
    print("   폼 제출 검색 테스트")
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
            
            # 3. 폼 찾기
            print("\n[3] Finding forms...")
            forms_info = await page.evaluate('''() => {
                const forms = document.querySelectorAll('form');
                const info = [];
                for (let i = 0; i < forms.length; i++) {
                    const form = forms[i];
                    info.push({
                        index: i,
                        id: form.id,
                        name: form.name,
                        action: form.action,
                        method: form.method,
                        target: form.target
                    });
                }
                return info;
            }''')
            
            print(f"Found {len(forms_info)} forms:")
            for form in forms_info:
                print(f"  Form {form['index']}: id='{form['id']}', name='{form['name']}', target='{form['target']}'")
            
            # 4. doSearch 함수의 내용 확인
            print("\n[4] Checking doSearch function...")
            doSearch_code = await page.evaluate('''() => {
                if (typeof doSearch === 'function') {
                    return doSearch.toString();
                }
                return 'Not found';
            }''')
            
            if doSearch_code != 'Not found':
                print("doSearch function found:")
                print(doSearch_code[:500] + "..." if len(doSearch_code) > 500 else doSearch_code)
            
            # 5. 팝업 창으로 폼 제출 시도
            print("\n[5] Trying different search methods...")
            
            # 방법 1: target="_blank"로 폼 수정 후 제출
            print("\n  Method 1: Modify form target...")
            result = await page.evaluate('''() => {
                const forms = document.querySelectorAll('form');
                if (forms.length > 0) {
                    const form = forms[0];
                    form.target = '_blank';  // 새 창에서 열기
                    form.submit();
                    return 'Form submitted with target=_blank';
                }
                return 'No form found';
            }''')
            print(f"  Result: {result}")
            
            # 잠시 대기
            await page.wait_for_timeout(3000)
            
            # 새 페이지 확인
            if len(context.pages) > 1:
                print("\n[SUCCESS] New page opened!")
                popup = context.pages[-1]
                print(f"  URL: {popup.url[:100]}...")
                
                await popup.wait_for_load_state('networkidle')
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await popup.screenshot(path=f"logs/screenshots/test/result_{timestamp}.png")
                
                # 다운로드 버튼 찾기
                print("\n[6] Looking for download button...")
                
                # 여러 선택자 시도
                selectors = [
                    '#btn_map_excel',
                    'button#btn_map_excel',
                    'button.btnLayer#btn_map_excel',
                    'button:has-text("다운로드")',
                    'a:has-text("엑셀")',
                    'img[alt*="엑셀"]'
                ]
                
                download_btn = None
                for selector in selectors:
                    btn = await popup.query_selector(selector)
                    if btn:
                        print(f"  Found with: {selector}")
                        download_btn = btn
                        break
                
                if download_btn:
                    print("\n[7] Attempting download...")
                    try:
                        download_promise = popup.wait_for_event('download', timeout=10000)
                        await download_btn.click()
                        
                        download = await download_promise
                        filepath = f"downloads/test/seoul_{timestamp}.xlsx"
                        await download.save_as(filepath)
                        print(f"[SUCCESS] Downloaded: {filepath}")
                    except asyncio.TimeoutError:
                        print("[WARNING] Download timeout")
                else:
                    print("[WARNING] Download button not found")
                    
                    # 페이지 내용 확인
                    tables = await popup.query_selector_all('table')
                    print(f"\n  Tables found: {len(tables)}")
                    
                    buttons = await popup.query_selector_all('button')
                    print(f"  Buttons found: {len(buttons)}")
                    for i, btn in enumerate(buttons[:5]):
                        text = await btn.text_content()
                        btn_id = await btn.get_attribute('id')
                        print(f"    Button {i}: id='{btn_id}', text='{text}'")
            else:
                print("\n[WARNING] No new page opened")
                
                # 현재 페이지가 변경되었는지 확인
                current_url = page.url
                print(f"  Current URL: {current_url}")
                
                # 방법 2: window.open으로 시도
                print("\n  Method 2: Using window.open...")
                await page.evaluate('''() => {
                    const form = document.querySelector('form');
                    if (form) {
                        const formData = new FormData(form);
                        const params = new URLSearchParams(formData);
                        const url = form.action + '?' + params.toString();
                        window.open(url, '_blank');
                    }
                }''')
                
                await page.wait_for_timeout(3000)
                
                if len(context.pages) > 1:
                    print("[SUCCESS] Popup opened with window.open!")
            
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
       폼 제출 방식 검색 테스트
    ============================================
    목표: 폼을 직접 제출하여 검색 결과 얻기
    ============================================
    """)
    
    asyncio.run(test_form_submit())
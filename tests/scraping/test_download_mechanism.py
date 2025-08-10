#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
다운로드 메커니즘 테스트 - 서울만
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import tempfile

async def test_download():
    """다운로드 테스트"""
    
    print("\n" + "="*60)
    print("   다운로드 메커니즘 테스트")
    print("="*60)
    
    # 임시 다운로드 폴더 생성
    temp_dir = tempfile.mkdtemp(prefix="ltc_download_")
    print(f"Download directory: {temp_dir}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        
        # 다운로드 경로 지정
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            permissions=[]
        )
        
        page = await context.new_page()
        
        try:
            # 1. 페이지 이동
            print("\n[1] Loading page...")
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 2. 서울 선택
            print("[2] Selecting Seoul...")
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(2000)
            
            # 3. 검색 버튼 클릭
            print("[3] Clicking search button...")
            search_btn = await page.query_selector('#btn_search_pop')
            await search_btn.click()
            
            # 4. 팝업 대기
            print("[4] Waiting for popup...")
            max_wait = 15
            waited = 0
            popup = None
            
            while waited < max_wait:
                await page.wait_for_timeout(1000)
                waited += 1
                
                if len(context.pages) > 1:
                    popup = context.pages[-1]
                    print(f"    Popup opened after {waited} seconds")
                    break
            
            if not popup:
                print("[ERROR] No popup")
                return
            
            # 5. 팝업 로드 대기
            print("[5] Waiting for popup to load...")
            await popup.wait_for_timeout(5000)
            
            # 6. 다운로드 버튼 상태 확인
            print("[6] Checking download button...")
            
            # JavaScript로 버튼 상태 확인
            btn_info = await popup.evaluate('''() => {
                const btn = document.querySelector('#btn_map_excel');
                if (btn) {
                    return {
                        exists: true,
                        text: btn.textContent,
                        visible: btn.offsetParent !== null,
                        disabled: btn.disabled,
                        onclick: btn.onclick ? btn.onclick.toString() : null,
                        href: btn.href || null,
                        tagName: btn.tagName
                    };
                }
                return { exists: false };
            }''')
            
            print(f"    Button info: {btn_info}")
            
            if btn_info['exists']:
                # 7. 다운로드 시도 - 여러 방법
                print("\n[7] Trying download methods...")
                
                # 방법 1: 일반 클릭 + 다운로드 이벤트
                print("    Method 1: Normal click with download event")
                
                try:
                    async with popup.expect_download() as download_info:
                        btn = await popup.query_selector('#btn_map_excel')
                        await btn.click()
                    
                    download = await download_info.value
                    print(f"    Download started: {download.suggested_filename}")
                    
                    # 파일 저장
                    save_path = os.path.join(temp_dir, f"seoul_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
                    await download.save_as(save_path)
                    print(f"    [SUCCESS] Saved to: {save_path}")
                    
                    # 파일 크기 확인
                    if os.path.exists(save_path):
                        size = os.path.getsize(save_path)
                        print(f"    File size: {size:,} bytes")
                        
                except Exception as e:
                    print(f"    Error: {str(e)}")
                    
                    # 방법 2: JavaScript 클릭
                    print("\n    Method 2: JavaScript click")
                    
                    # onclick 함수 직접 실행
                    result = await popup.evaluate('''() => {
                        const btn = document.querySelector('#btn_map_excel');
                        if (btn) {
                            // onclick 이벤트 확인
                            if (btn.onclick) {
                                btn.onclick();
                                return 'onclick executed';
                            }
                            // 일반 클릭
                            btn.click();
                            return 'clicked';
                        }
                        return 'not found';
                    }''')
                    
                    print(f"    JavaScript result: {result}")
                    
                    # 방법 3: 다운로드 함수 직접 호출
                    print("\n    Method 3: Direct function call")
                    
                    funcs = await popup.evaluate('''() => {
                        const funcs = [];
                        for (const key in window) {
                            if (key.toLowerCase().includes('excel') || 
                                key.toLowerCase().includes('download')) {
                                funcs.push(key);
                            }
                        }
                        return funcs;
                    }''')
                    
                    print(f"    Found functions: {funcs}")
                    
                    if funcs:
                        for func in funcs[:3]:
                            try:
                                await popup.evaluate(f'{func}()')
                                print(f"    Called: {func}")
                            except:
                                pass
            
            # 8. 다운로드 폴더 확인
            print(f"\n[8] Checking download folder: {temp_dir}")
            files = os.listdir(temp_dir)
            print(f"    Files: {files}")
            
            print("\n[INFO] Browser will remain open for 15 seconds...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")
            print(f"Download folder: {temp_dir}")

if __name__ == "__main__":
    print("""
    ============================================
       다운로드 메커니즘 테스트
    ============================================
    - expect_download 사용
    - JavaScript 직접 실행
    - 다운로드 폴더 확인
    ============================================
    """)
    
    asyncio.run(test_download())
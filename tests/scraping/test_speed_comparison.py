#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Headless vs Browser 모드 속도 비교 테스트
서울특별시 데이터만 다운로드하여 시간 측정
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import time
import os

async def download_seoul_with_mode(headless=True):
    """서울 데이터 다운로드 - 모드별 시간 측정"""
    
    mode_name = "Headless" if headless else "Browser"
    print(f"\n{'='*60}")
    print(f"  {mode_name} 모드 테스트")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    async with async_playwright() as p:
        # 브라우저 시작 시간
        browser_start = time.time()
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=200 if headless else 1000
        )
        browser_time = time.time() - browser_start
        print(f"브라우저 시작: {browser_time:.2f}초")
        
        context = await browser.new_context(
            accept_downloads=True,
            viewport={'width': 1920, 'height': 1080},
            permissions=[]
        )
        
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드 시간
            page_start = time.time()
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            page_time = time.time() - page_start
            print(f"페이지 로드: {page_time:.2f}초")
            
            # 2. 지역 선택
            select_start = time.time()
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(2000)
            select_time = time.time() - select_start
            print(f"지역 선택: {select_time:.2f}초")
            
            # 3. 검색 버튼 클릭 및 팝업 대기
            popup_start = time.time()
            search_btn = await page.query_selector('#btn_search_pop')
            await search_btn.click()
            
            # 팝업 대기
            pages_before = len(context.pages)
            waited = 0
            popup = None
            
            while waited < 20:
                await page.wait_for_timeout(1000)
                waited += 1
                if len(context.pages) > pages_before:
                    popup = context.pages[-1]
                    break
            
            popup_time = time.time() - popup_start
            print(f"팝업 열기: {popup_time:.2f}초 (대기 {waited}초)")
            
            if popup:
                # 4. 팝업 로드
                load_start = time.time()
                await popup.wait_for_timeout(5000)
                load_time = time.time() - load_start
                print(f"팝업 로드: {load_time:.2f}초")
                
                # 5. 다운로드
                download_start = time.time()
                download_btn = await popup.query_selector('#btn_map_excel')
                
                if download_btn:
                    try:
                        async with popup.expect_download(timeout=30000) as download_info:
                            await download_btn.click()
                        
                        download = await download_info.value
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filepath = f"downloads/test/seoul_{mode_name}_{timestamp}.xlsx"
                        os.makedirs("downloads/test", exist_ok=True)
                        await download.save_as(filepath)
                        
                        download_time = time.time() - download_start
                        print(f"다운로드: {download_time:.2f}초")
                        
                        if os.path.exists(filepath):
                            file_size = os.path.getsize(filepath)
                            print(f"파일 크기: {file_size:,} bytes")
                    except:
                        print("다운로드 실패")
                else:
                    print("다운로드 버튼 없음")
                
                await popup.close()
            else:
                print("팝업 열기 실패")
            
        except Exception as e:
            print(f"에러: {str(e)}")
            
        finally:
            await browser.close()
    
    total_time = time.time() - start_time
    return total_time

async def main():
    """속도 비교 테스트"""
    print("""
    ============================================
       Headless vs Browser 속도 비교 테스트
    ============================================
    서울특별시 데이터를 두 가지 모드로 다운로드하여
    실행 시간을 비교합니다.
    ============================================
    """)
    
    print("\n[1/2] Browser 모드 테스트 시작...")
    browser_time = await download_seoul_with_mode(headless=False)
    
    print("\n잠시 대기...")
    await asyncio.sleep(5)
    
    print("\n[2/2] Headless 모드 테스트 시작...")
    headless_time = await download_seoul_with_mode(headless=True)
    
    # 결과 비교
    print("\n" + "="*60)
    print("   테스트 결과")
    print("="*60)
    print(f"Browser 모드:  {browser_time:.2f}초")
    print(f"Headless 모드: {headless_time:.2f}초")
    print(f"\n시간 차이: {browser_time - headless_time:.2f}초")
    print(f"속도 향상: {((browser_time - headless_time) / browser_time * 100):.1f}%")
    
    if headless_time < browser_time:
        speedup = browser_time / headless_time
        print(f"Headless가 {speedup:.1f}배 빠름")
    
    print("\n" + "="*60)
    print("분석:")
    print("- Headless는 UI 렌더링을 하지 않아 CPU/메모리 절약")
    print("- slow_mo 값도 더 작게 설정 (200ms vs 1000ms)")
    print("- 네트워크 대기 시간은 동일 (서버 응답 속도)")

if __name__ == "__main__":
    asyncio.run(main())
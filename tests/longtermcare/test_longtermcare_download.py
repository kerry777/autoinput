#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양보험 공단 사이트 다운로드 자동화 테스트
https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650
장기요양기관 검색 및 엑셀 다운로드 기능
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import time

class LongTermCareDownloader:
    """장기요양보험 사이트 다운로드 자동화"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.search_url = "/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
        self.download_dir = "downloads/longtermcare"
        
    async def analyze_page_structure(self, page):
        """페이지 구조 분석"""
        print("\n[STEP 1] Analyzing page structure...")
        print("="*50)
        
        # 페이지 로드
        url = self.base_url + self.search_url
        print(f"Navigating to: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 페이지 타이틀
        title = await page.title()
        print(f"Page title: {title}")
        
        # 검색 조건 필드 찾기
        print("\n[검색 조건 분석]")
        
        # 시도 선택 박스
        sido_select = await page.query_selector('select#siDoCd')
        if sido_select:
            print("[OK] 시도 선택 박스 발견")
            
            # 시도 옵션들 가져오기
            sido_options = await page.evaluate('''() => {
                const select = document.querySelector('select#siDoCd');
                if (!select) return [];
                return Array.from(select.options).map(opt => ({
                    value: opt.value,
                    text: opt.text
                }));
            }''')
            
            print(f"  - 시도 옵션 수: {len(sido_options)}")
            for opt in sido_options[:5]:  # 처음 5개만 출력
                print(f"    {opt['value']}: {opt['text']}")
        
        # 시군구 선택 박스
        sigungu_select = await page.query_selector('select#siGunGuCd')
        if sigungu_select:
            print("[OK] 시군구 선택 박스 발견")
        
        # 급여종류 체크박스
        service_types = await page.query_selector_all('input[type="checkbox"][name="pttnSvcCd"]')
        print(f"[OK] 급여종류 체크박스: {len(service_types)}개")
        
        # 검색 버튼
        search_button = await page.query_selector('button.btn_search, a.btn_search, #searchBtn')
        if search_button:
            print("[OK] 검색 버튼 발견")
        
        # 다운로드 버튼 찾기
        download_buttons = await page.query_selector_all('a[href*="excel"], button:has-text("엑셀"), button:has-text("다운로드")')
        print(f"[OK] 다운로드 관련 버튼: {len(download_buttons)}개")
        
        return True
    
    async def search_facilities(self, page, sido="41", sigungu="480"):
        """시설 검색 수행"""
        print("\n[STEP 2] Performing search...")
        print("="*50)
        
        # 시도 선택 (41 = 경기도)
        print(f"Selecting 시도: {sido}")
        await page.select_option('select#siDoCd', sido)
        await page.wait_for_timeout(1000)
        
        # 시군구 로딩 대기
        print("Waiting for 시군구 to load...")
        await page.wait_for_function('''() => {
            const select = document.querySelector('select#siGunGuCd');
            return select && select.options.length > 1;
        }''', timeout=5000)
        
        # 시군구 선택 (480 = 하남시)
        print(f"Selecting 시군구: {sigungu}")
        await page.select_option('select#siGunGuCd', sigungu)
        await page.wait_for_timeout(500)
        
        # 급여종류 전체 선택
        print("Selecting all service types...")
        checkboxes = await page.query_selector_all('input[type="checkbox"][name="pttnSvcCd"]')
        for checkbox in checkboxes:
            is_checked = await checkbox.is_checked()
            if not is_checked:
                await checkbox.check()
        
        # 검색 버튼 클릭
        print("Clicking search button...")
        
        # 여러 방법으로 검색 버튼 찾기
        search_selectors = [
            'a.btn_search',
            'button.btn_search',
            '#searchBtn',
            'a[onclick*="search"]',
            'button[onclick*="search"]',
            '.btn_area a.btn_blue',
            '.btn_area button'
        ]
        
        search_clicked = False
        for selector in search_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    await button.click()
                    search_clicked = True
                    print(f"  Clicked: {selector}")
                    break
            except:
                continue
        
        if not search_clicked:
            print("[WARNING] Could not click search button")
            # JavaScript로 직접 검색 함수 호출 시도
            await page.evaluate('if(typeof doSearch === "function") doSearch();')
        
        # 검색 결과 대기
        print("Waiting for search results...")
        await page.wait_for_timeout(3000)
        
        # 결과 확인
        result_count = await page.evaluate('''() => {
            // 결과 테이블이나 목록 찾기
            const table = document.querySelector('table.tbl_list, table.list_table, #resultTable');
            if (table) {
                const rows = table.querySelectorAll('tbody tr');
                return rows.length;
            }
            
            // 또는 결과 건수 텍스트
            const countText = document.querySelector('.result_count, .total_count');
            if (countText) {
                const match = countText.textContent.match(/\d+/);
                return match ? parseInt(match[0]) : 0;
            }
            
            return 0;
        }''')
        
        print(f"Search results: {result_count} items found")
        
        return result_count > 0
    
    async def download_excel(self, page):
        """엑셀 파일 다운로드"""
        print("\n[STEP 3] Downloading Excel file...")
        print("="*50)
        
        # 다운로드 이벤트 준비
        download_promise = page.wait_for_event('download')
        
        # 다운로드 버튼 찾기
        download_selectors = [
            'a[onclick*="excel"]',
            'a[onclick*="Excel"]',
            'button[onclick*="excel"]',
            'a.btn_excel',
            'button.btn_excel',
            'a:has-text("엑셀")',
            'button:has-text("엑셀")',
            'a:has-text("다운로드")',
            'button:has-text("다운로드")',
            '.btn_area a[href*="excel"]',
            'img[alt*="엑셀"]',
            'img[alt*="Excel"]'
        ]
        
        download_clicked = False
        for selector in download_selectors:
            try:
                button = await page.query_selector(selector)
                if button and await button.is_visible():
                    print(f"Found download button: {selector}")
                    
                    # 버튼 위치로 스크롤
                    await button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    
                    # 클릭
                    await button.click()
                    download_clicked = True
                    print(f"  Clicked: {selector}")
                    break
            except:
                continue
        
        if not download_clicked:
            print("[WARNING] Could not find download button")
            
            # JavaScript로 직접 다운로드 함수 호출 시도
            print("Trying JavaScript function calls...")
            js_functions = [
                'doExcelDown()',
                'excelDownload()',
                'fnExcelDown()',
                'downloadExcel()',
                'excelDown()'
            ]
            
            for func in js_functions:
                try:
                    await page.evaluate(f'if(typeof {func.replace("()", "")} === "function") {func}')
                    print(f"  Called: {func}")
                    download_clicked = True
                    break
                except:
                    continue
        
        if download_clicked:
            try:
                # 다운로드 대기 (최대 30초)
                print("Waiting for download to start...")
                download = await asyncio.wait_for(download_promise, timeout=30)
                
                # 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"longtermcare_facilities_{timestamp}.xlsx"
                filepath = os.path.join(self.download_dir, filename)
                
                await download.save_as(filepath)
                print(f"[SUCCESS] File saved: {filepath}")
                
                return filepath
                
            except asyncio.TimeoutError:
                print("[ERROR] Download timeout - file may be generating")
                
        return None
    
    async def test_direct_url(self, page):
        """직접 URL 접근 테스트"""
        print("\n[ALTERNATIVE] Testing direct URL...")
        print("="*50)
        
        # 제공된 직접 URL
        direct_url = "https://longtermcare.or.kr/npbs/r/a/201/selectXLtcoSrch.web?siDoCd=41&si_gun_gu_cd=480"
        print(f"Direct URL: {direct_url}")
        
        await page.goto(direct_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 페이지 분석
        title = await page.title()
        print(f"Page title: {title}")
        
        # 결과가 이미 표시되어 있는지 확인
        has_results = await page.evaluate('''() => {
            const tables = document.querySelectorAll('table');
            const rows = document.querySelectorAll('tr');
            return {
                tables: tables.length,
                rows: rows.length
            };
        }''')
        
        print(f"Found {has_results['tables']} tables, {has_results['rows']} rows")
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"logs/screenshots/longtermcare_direct_{timestamp}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
        
        return has_results['rows'] > 1
    
    async def run(self):
        """메인 실행 함수"""
        
        # 디렉토리 생성
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs("logs/screenshots", exist_ok=True)
        
        async with async_playwright() as p:
            # 브라우저 설정
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            # 다운로드 경로 설정
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. 페이지 구조 분석
                await self.analyze_page_structure(page)
                
                # 2. 시설 검색
                search_success = await self.search_facilities(page)
                
                if search_success:
                    # 3. 엑셀 다운로드
                    file_path = await self.download_excel(page)
                    
                    if file_path:
                        print(f"\n[COMPLETE] Download successful: {file_path}")
                    else:
                        print("\n[WARNING] Download may have failed")
                else:
                    print("\n[INFO] No search results, trying direct URL...")
                    
                    # 4. 직접 URL 시도
                    await self.test_direct_url(page)
                
                # 스크린샷 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(
                    path=f"logs/screenshots/longtermcare_final_{timestamp}.png",
                    full_page=True
                )
                
                print("\n[INFO] Browser will remain open for 15 seconds...")
                await page.wait_for_timeout(15000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                
                # 에러 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(
                    path=f"logs/screenshots/longtermcare_error_{timestamp}.png",
                    full_page=True
                )
                
            finally:
                await browser.close()

async def main():
    downloader = LongTermCareDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("""
    ============================================
       장기요양보험 사이트 다운로드 테스트
    ============================================
    Target: longtermcare.or.kr
    Task: Search facilities and download Excel
    ============================================
    """)
    
    asyncio.run(main())
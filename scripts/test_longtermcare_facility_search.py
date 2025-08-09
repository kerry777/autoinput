#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양보험 민원상담실 - 장기요양기관 찾기
실제 페이지 구조에 맞춘 자동화 스크립트
URL: https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd

class LongTermCareFacilitySearch:
    """장기요양기관 검색 및 다운로드 자동화"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
        self.output_dir = "data/longtermcare/facilities"
        self.screenshots_dir = "logs/screenshots/facilities"
        self.download_dir = "downloads/longtermcare/facilities"
        self.search_results = []
        
    async def initialize_directories(self):
        """디렉토리 생성"""
        for dir_path in [self.output_dir, self.screenshots_dir, self.download_dir]:
            os.makedirs(dir_path, exist_ok=True)
        print("[INIT] Directories created")
    
    async def search_facilities(self, page, sido="전체", sigungu="전체", service_type="전체"):
        """장기요양기관 검색"""
        print("\n" + "="*60)
        print("  장기요양기관 검색")
        print("="*60)
        
        # 페이지 직접 이동
        print(f"\n[NAVIGATION] Going to: {self.base_url}")
        await page.goto(self.base_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(
            path=f"{self.screenshots_dir}/initial_{timestamp}.png",
            full_page=True
        )
        print("[SCREENSHOT] Initial page captured")
        
        # 1. 지역 선택
        print("\n[STEP 1] Setting search criteria...")
        
        # 시도 선택
        if sido != "전체":
            try:
                sido_select = await page.query_selector('select[name="siDoCd"], select#siDoCd')
                if sido_select:
                    await page.select_option(sido_select, value=sido)
                    print(f"  Selected 시도: {sido}")
                    await page.wait_for_timeout(1000)
                    
                    # 시군구 로딩 대기
                    if sigungu != "전체":
                        await page.wait_for_function('''() => {
                            const select = document.querySelector('select[name="siGunGuCd"], select#siGunGuCd');
                            return select && select.options.length > 1;
                        }''', timeout=5000)
                        
                        sigungu_select = await page.query_selector('select[name="siGunGuCd"], select#siGunGuCd')
                        if sigungu_select:
                            await page.select_option(sigungu_select, value=sigungu)
                            print(f"  Selected 시군구: {sigungu}")
            except Exception as e:
                print(f"  [WARNING] Could not select location: {e}")
        
        # 2. 급여종류 선택 (체크박스들)
        print("\n[STEP 2] Selecting service types...")
        
        # 치매전담형 장기요양기관
        dementia_checkbox = await page.query_selector('input[type="checkbox"][value="치매전담형"]')
        if dementia_checkbox:
            is_checked = await dementia_checkbox.is_checked()
            if not is_checked:
                await dementia_checkbox.check()
                print("  ✓ 치매전담형 장기요양기관")
        
        # 기타 체크박스들 (노인요양시설, 치매전담형노인요양공동생활가정 등)
        checkboxes = [
            "노인요양시설 내 치매전담실",
            "치매전담형노인요양공동생활가정",
            "주야간보호 내 치매전담실",
            "인지활동형 프로그램 제공기관",
            "방문요양",
            "주야간보호",
            "종일 방문요양",
            "단기보호"
        ]
        
        for checkbox_label in checkboxes[:4]:  # 처음 4개만 선택 (너무 많으면 부하)
            checkbox = await page.query_selector(f'label:has-text("{checkbox_label}") input[type="checkbox"]')
            if not checkbox:
                checkbox = await page.query_selector(f'input[type="checkbox"][value*="{checkbox_label}"]')
            
            if checkbox:
                is_checked = await checkbox.is_checked()
                if not is_checked:
                    await checkbox.check()
                    print(f"  ✓ {checkbox_label}")
                    await page.wait_for_timeout(200)
        
        # 3. 동의체크서비스 선택
        print("\n[STEP 3] Additional options...")
        
        # 통합재가서비스 체크박스
        integrated_checkbox = await page.query_selector('input#통합재가서비스, input[type="checkbox"][value="통합재가서비스"]')
        if integrated_checkbox:
            await integrated_checkbox.check()
            print("  ✓ 통합재가서비스")
        
        # 4. 시범사업 옵션
        # 주야간보호기관 내 단기보호 시범사업
        pilot_checkbox = await page.query_selector('input[type="checkbox"]:has-text("주야간보호기관 내 단기보호 시범사업")')
        if pilot_checkbox:
            await pilot_checkbox.check()
            print("  ✓ 주야간보호기관 내 단기보호 시범사업")
        
        # 5. 검색 버튼 클릭
        print("\n[STEP 4] Searching...")
        
        search_button = await page.query_selector('button.btn.btn-danger:has-text("검색"), button:has-text("검색")')
        if not search_button:
            search_button = await page.query_selector('button.검색, a.btn_search')
        
        if search_button:
            await search_button.click()
            print("  Clicked search button")
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)
        else:
            print("  [WARNING] Search button not found")
        
        # 검색 결과 스크린샷
        await page.screenshot(
            path=f"{self.screenshots_dir}/search_results_{timestamp}.png",
            full_page=True
        )
        print("[SCREENSHOT] Search results captured")
    
    async def extract_search_results(self, page):
        """검색 결과 추출"""
        print("\n[EXTRACTION] Extracting search results...")
        
        # 결과 테이블 찾기
        results = await page.evaluate('''() => {
            const data = [];
            
            // 테이블 찾기 (다양한 선택자 시도)
            const tables = document.querySelectorAll('table.table, table.tbl_list, table.list_table, table');
            
            for (const table of tables) {
                const rows = table.querySelectorAll('tbody tr');
                
                if (rows.length > 0) {
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length > 3) {  // 데이터가 있는 행만
                            const rowData = {
                                번호: cells[0]?.textContent?.trim() || '',
                                기관명: cells[1]?.textContent?.trim() || '',
                                급여종류: cells[2]?.textContent?.trim() || '',
                                주소: cells[3]?.textContent?.trim() || '',
                                전화번호: cells[4]?.textContent?.trim() || '',
                                정원: cells[5]?.textContent?.trim() || '',
                                현원: cells[6]?.textContent?.trim() || '',
                                대기: cells[7]?.textContent?.trim() || ''
                            };
                            
                            // 빈 데이터 제거
                            if (rowData.기관명 && rowData.기관명 !== '') {
                                data.push(rowData);
                            }
                        }
                    });
                }
            }
            
            return data;
        }''')
        
        if results:
            print(f"  Found {len(results)} facilities")
            self.search_results.extend(results)
            
            # 처음 3개 표시
            for i, facility in enumerate(results[:3]):
                print(f"    {i+1}. {facility.get('기관명', 'N/A')} - {facility.get('급여종류', 'N/A')}")
        else:
            print("  No results found")
        
        return results
    
    async def navigate_pages(self, page, max_pages=2):
        """페이지 네비게이션 (안전하게 2페이지만)"""
        print("\n[PAGINATION] Processing pages...")
        
        for page_num in range(1, max_pages + 1):
            print(f"\n  Page {page_num}:")
            
            if page_num == 1:
                # 첫 페이지는 이미 로드됨
                await self.extract_search_results(page)
            else:
                # 다음 페이지로 이동
                next_page_link = await page.query_selector(f'a:has-text("{page_num}")')
                
                if not next_page_link:
                    # JavaScript 페이지네이션 시도
                    try:
                        await page.evaluate(f'''() => {{
                            if (typeof goPage === 'function') goPage({page_num});
                            else if (typeof fn_goPage === 'function') fn_goPage({page_num});
                            else if (typeof movePage === 'function') movePage({page_num});
                        }}''')
                        print(f"    Navigated to page {page_num} via JavaScript")
                    except:
                        print(f"    Could not navigate to page {page_num}")
                        break
                else:
                    await next_page_link.click()
                    print(f"    Clicked page {page_num} link")
                
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(3000)  # 차단 방지
                
                # 현재 페이지 데이터 추출
                await self.extract_search_results(page)
    
    async def download_excel(self, page):
        """엑셀 다운로드"""
        print("\n[DOWNLOAD] Attempting Excel download...")
        
        try:
            # 다운로드 버튼 찾기
            download_selectors = [
                'button:has-text("엑셀")',
                'a:has-text("엑셀")',
                'button.btn-excel',
                'a.btn-excel',
                'img[alt*="엑셀"]',
                'button[onclick*="excel"]',
                'a[onclick*="excel"]'
            ]
            
            download_button = None
            for selector in download_selectors:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    download_button = btn
                    print(f"  Found download button: {selector}")
                    break
            
            if download_button:
                # 다운로드 준비
                download_promise = page.wait_for_event('download', timeout=10000)
                
                # 버튼 클릭
                await download_button.click()
                
                # 다운로드 완료 대기
                download = await download_promise
                
                # 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"facilities_{timestamp}.xlsx"
                filepath = os.path.join(self.download_dir, filename)
                
                await download.save_as(filepath)
                print(f"  [SUCCESS] Downloaded: {filename}")
                
                return filepath
            else:
                print("  [INFO] Download button not found")
                
                # JavaScript 함수 직접 호출
                await page.evaluate('''() => {
                    if (typeof doExcelDown === 'function') doExcelDown();
                    else if (typeof excelDownload === 'function') excelDownload();
                    else if (typeof fnExcelDown === 'function') fnExcelDown();
                }''')
                
        except asyncio.TimeoutError:
            print("  [INFO] Download timeout - may require manual action")
        except Exception as e:
            print(f"  [ERROR] Download failed: {e}")
        
        return None
    
    async def save_results(self):
        """결과 저장"""
        if not self.search_results:
            print("\n[SAVE] No results to save")
            return
        
        print(f"\n[SAVE] Saving {len(self.search_results)} facilities...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 저장
        json_file = f"{self.output_dir}/facilities_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.search_results, f, ensure_ascii=False, indent=2)
        print(f"  JSON saved: {json_file}")
        
        # CSV 저장
        csv_file = f"{self.output_dir}/facilities_{timestamp}.csv"
        df = pd.DataFrame(self.search_results)
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"  CSV saved: {csv_file}")
        
        # Excel 저장
        excel_file = f"{self.output_dir}/facilities_{timestamp}.xlsx"
        df.to_excel(excel_file, index=False)
        print(f"  Excel saved: {excel_file}")
    
    async def run(self):
        """메인 실행"""
        await self.initialize_directories()
        
        print("\n" + "="*70)
        print("   장기요양기관 검색 자동화")
        print("="*70)
        print("URL:", self.base_url)
        print("목표: 기관 검색 후 2페이지 데이터 수집 및 엑셀 다운로드")
        print("="*70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR'
            )
            
            page = await context.new_page()
            
            try:
                # 검색 실행
                await self.search_facilities(page)
                
                # 페이지 네비게이션 (2페이지만)
                await self.navigate_pages(page, max_pages=2)
                
                # 엑셀 다운로드 시도
                await self.download_excel(page)
                
                # 결과 저장
                await self.save_results()
                
                # 결과 요약
                print("\n" + "="*70)
                print("   검색 완료")
                print("="*70)
                print(f"  Total facilities found: {len(self.search_results)}")
                print(f"  Data saved to: {self.output_dir}")
                print(f"  Downloads saved to: {self.download_dir}")
                
                print("\n[INFO] Browser will remain open for 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                
                # 에러 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(
                    path=f"{self.screenshots_dir}/error_{timestamp}.png",
                    full_page=True
                )
                
            finally:
                await browser.close()
                print("\n[COMPLETE] Process finished")

async def main():
    searcher = LongTermCareFacilitySearch()
    await searcher.run()

if __name__ == "__main__":
    print("""
    ============================================
       장기요양기관 찾기 자동화
    ============================================
    실제 페이지 구조 기반 정확한 자동화
    안전하게 2페이지씩 데이터 수집
    ============================================
    """)
    
    asyncio.run(main())
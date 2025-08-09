#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양보험 검색서비스 데이터 수집
민원상담실 > 검색서비스 4개 메뉴 자동화
- 장기요양기관 검색
- 등급판정결과 조회
- 장기요양인정서 재발급
- 기타 검색 서비스
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd

class LongTermCareSearchServices:
    """장기요양보험 검색서비스 자동화"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.output_dir = "data/longtermcare/search_services"
        self.screenshots_dir = "logs/screenshots/longtermcare"
        self.results = {}
        
    async def initialize_directories(self):
        """디렉토리 생성"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        print("[INIT] Directories created")
    
    async def navigate_to_search_services(self, page):
        """검색서비스 메뉴로 이동"""
        print("\n[NAVIGATION] Going to search services...")
        
        # 메인 페이지 접속
        await page.goto(self.base_url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # 민원상담실 메뉴 찾기
        print("Looking for 민원상담실 menu...")
        
        # 여러 방법으로 메뉴 찾기
        menu_selectors = [
            'a:has-text("민원상담실")',
            'a:has-text("민원")',
            'a[href*="minwon"]',
            '.menu:has-text("민원")',
            'li:has-text("민원상담실")'
        ]
        
        for selector in menu_selectors:
            menu = await page.query_selector(selector)
            if menu:
                await menu.hover()  # 마우스 오버로 서브메뉴 표시
                await page.wait_for_timeout(500)
                print(f"  Found: {selector}")
                break
        
        # 검색서비스 서브메뉴 찾기
        search_menu = await page.query_selector('a:has-text("검색서비스")')
        if search_menu:
            await search_menu.click()
            await page.wait_for_load_state('networkidle')
            print("  Clicked 검색서비스")
    
    async def search_facilities(self, page):
        """1. 장기요양기관 검색"""
        print("\n" + "="*60)
        print("  [SERVICE 1] 장기요양기관 검색")
        print("="*60)
        
        # URL 직접 이동 (더 확실함)
        url = f"{self.base_url}/npbs/r/a/201/selectLtcoSrch.web"
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        results = []
        
        # 시도 선택 (서울)
        try:
            await page.select_option('select#siDoCd', '11')  # 11 = 서울
            await page.wait_for_timeout(1000)
            
            # 시군구 선택 (강남구)
            await page.select_option('select#siGunGuCd', '680')  # 680 = 강남구
            await page.wait_for_timeout(1000)
            
            # 검색 버튼 클릭
            search_btn = await page.query_selector('a.btn_search, button.btn_search')
            if search_btn:
                await search_btn.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)
            
            # 2페이지까지만 데이터 수집 (차단 방지)
            for page_num in range(1, 3):
                print(f"\n  Page {page_num}:")
                
                # 테이블 데이터 추출
                table_data = await page.evaluate('''() => {
                    const rows = document.querySelectorAll('table tbody tr');
                    const data = [];
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length > 0) {
                            const rowData = {
                                번호: cells[0]?.textContent?.trim(),
                                기관명: cells[1]?.textContent?.trim(),
                                급여종류: cells[2]?.textContent?.trim(),
                                주소: cells[3]?.textContent?.trim(),
                                전화번호: cells[4]?.textContent?.trim(),
                                정원: cells[5]?.textContent?.trim()
                            };
                            data.push(rowData);
                        }
                    });
                    
                    return data;
                }''')
                
                if table_data:
                    results.extend(table_data)
                    print(f"    Collected {len(table_data)} items")
                
                # 다음 페이지로 이동
                if page_num < 2:
                    next_btn = await page.query_selector(f'a:has-text("{page_num + 1}")')
                    if not next_btn:
                        # JavaScript 페이지네이션
                        await page.evaluate(f'if(typeof goPage === "function") goPage({page_num + 1})')
                    else:
                        await next_btn.click()
                    
                    await page.wait_for_load_state('networkidle')
                    await page.wait_for_timeout(2000)
            
            # 결과 저장
            if results:
                await self.save_data(results, "facilities_search")
                self.results['facilities'] = len(results)
                
                # 엑셀 다운로드 시도
                await self.try_excel_download(page, "facilities")
                
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
        
        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(path=f"{self.screenshots_dir}/facilities_{timestamp}.png")
    
    async def search_grade_results(self, page):
        """2. 등급판정결과 조회"""
        print("\n" + "="*60)
        print("  [SERVICE 2] 등급판정결과 조회")
        print("="*60)
        
        # URL 이동
        url = f"{self.base_url}/npbs/r/a/202/selectLtcoGradeJudge.web"
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # 샘플 검색 (실제로는 개인정보가 필요하므로 구조만 파악)
        print("  Page structure analysis...")
        
        # 입력 필드 확인
        fields = await page.evaluate('''() => {
            const inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
            return Array.from(inputs).map(input => ({
                name: input.name,
                id: input.id,
                placeholder: input.placeholder,
                type: input.type
            }));
        }''')
        
        print(f"  Found {len(fields)} input fields:")
        for field in fields:
            print(f"    - {field}")
        
        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(path=f"{self.screenshots_dir}/grade_results_{timestamp}.png")
        
        self.results['grade_results'] = 'Structure analyzed'
    
    async def search_certificate_reissue(self, page):
        """3. 장기요양인정서 재발급"""
        print("\n" + "="*60)
        print("  [SERVICE 3] 장기요양인정서 재발급")
        print("="*60)
        
        # URL 이동
        url = f"{self.base_url}/npbs/r/a/203/selectLtcoCertReissue.web"
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # 페이지 구조 분석
        print("  Analyzing reissue form...")
        
        # 폼 구조 확인
        form_structure = await page.evaluate('''() => {
            const form = document.querySelector('form');
            if (!form) return null;
            
            const fields = [];
            form.querySelectorAll('input, select, textarea').forEach(elem => {
                fields.push({
                    tag: elem.tagName,
                    type: elem.type,
                    name: elem.name,
                    required: elem.required
                });
            });
            
            return {
                action: form.action,
                method: form.method,
                fields: fields
            };
        }''')
        
        if form_structure:
            print(f"  Form structure:")
            print(f"    Action: {form_structure.get('action', 'N/A')}")
            print(f"    Fields: {len(form_structure.get('fields', []))}")
        
        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(path=f"{self.screenshots_dir}/certificate_reissue_{timestamp}.png")
        
        self.results['certificate_reissue'] = 'Form analyzed'
    
    async def search_other_services(self, page):
        """4. 기타 검색 서비스"""
        print("\n" + "="*60)
        print("  [SERVICE 4] 기타 검색 서비스")
        print("="*60)
        
        # 복지용구 사업소 검색
        url = f"{self.base_url}/npbs/r/a/204/selectWelfareToolBiz.web"
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        results = []
        
        try:
            # 지역 선택 (서울)
            sido_select = await page.query_selector('select[name="siDoCd"]')
            if sido_select:
                await page.select_option('select[name="siDoCd"]', '11')
                await page.wait_for_timeout(1000)
            
            # 검색 실행
            search_btn = await page.query_selector('a.btn_search, button:has-text("검색")')
            if search_btn:
                await search_btn.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)
            
            # 데이터 수집 (2페이지만 - 차단 방지)
            for page_num in range(1, 3):
                print(f"\n  Page {page_num}:")
                
                # 테이블 데이터 추출
                table_data = await page.evaluate('''() => {
                    const rows = document.querySelectorAll('table tbody tr');
                    const data = [];
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length > 1) {  // 데이터 행만
                            const rowData = {};
                            cells.forEach((cell, idx) => {
                                rowData[`column_${idx}`] = cell.textContent.trim();
                            });
                            data.push(rowData);
                        }
                    });
                    
                    return data;
                }''')
                
                if table_data:
                    results.extend(table_data)
                    print(f"    Collected {len(table_data)} items")
                
                # 다음 페이지
                if page_num < 2:
                    try:
                        await page.evaluate(f'goPage({page_num + 1})')
                        await page.wait_for_load_state('networkidle')
                        await page.wait_for_timeout(2000)
                    except:
                        print(f"    No more pages")
                        break
            
            # 결과 저장
            if results:
                await self.save_data(results, "welfare_tools")
                self.results['welfare_tools'] = len(results)
                
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
        
        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await page.screenshot(path=f"{self.screenshots_dir}/other_services_{timestamp}.png")
    
    async def try_excel_download(self, page, service_name):
        """엑셀 다운로드 시도"""
        print(f"\n  [DOWNLOAD] Trying Excel download for {service_name}...")
        
        # 다운로드 버튼 찾기
        download_selectors = [
            'a:has-text("엑셀")',
            'button:has-text("엑셀")',
            'a[onclick*="excel"]',
            'button[onclick*="excel"]',
            'img[alt*="엑셀"]',
            'a.btn_excel'
        ]
        
        for selector in download_selectors:
            btn = await page.query_selector(selector)
            if btn and await btn.is_visible():
                print(f"    Found download button: {selector}")
                
                try:
                    # 다운로드 준비
                    download_promise = page.wait_for_event('download', timeout=10000)
                    
                    # 버튼 클릭
                    await btn.click()
                    
                    # 다운로드 대기
                    download = await download_promise
                    
                    # 파일 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{service_name}_{timestamp}.xlsx"
                    filepath = os.path.join(self.output_dir, filename)
                    
                    await download.save_as(filepath)
                    print(f"    [SUCCESS] Downloaded: {filename}")
                    
                    return True
                    
                except asyncio.TimeoutError:
                    print(f"    [INFO] Download timeout - trying JavaScript")
                    
                    # JavaScript 함수 직접 호출
                    js_functions = ['doExcelDown()', 'excelDownload()', 'fnExcelDown()']
                    for func in js_functions:
                        try:
                            await page.evaluate(f'if(typeof {func.replace("()", "")} === "function") {func}')
                            print(f"    Called: {func}")
                            await page.wait_for_timeout(3000)
                            break
                        except:
                            continue
                except Exception as e:
                    print(f"    [ERROR] Download failed: {str(e)}")
                
                break
        
        return False
    
    async def save_data(self, data, filename_prefix):
        """데이터 저장 (JSON, CSV, Excel)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 저장
        json_file = f"{self.output_dir}/{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"    Saved JSON: {json_file}")
        
        # CSV 저장
        if data:
            csv_file = f"{self.output_dir}/{filename_prefix}_{timestamp}.csv"
            df = pd.DataFrame(data)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"    Saved CSV: {csv_file}")
            
            # Excel 저장
            excel_file = f"{self.output_dir}/{filename_prefix}_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            print(f"    Saved Excel: {excel_file}")
    
    async def run(self):
        """메인 실행"""
        await self.initialize_directories()
        
        print("\n" + "="*70)
        print("   장기요양보험 검색서비스 데이터 수집")
        print("="*70)
        print("\n목표: 4개 검색서비스에서 각 2페이지씩 데이터 수집 (차단 방지)")
        print("노하우 축적 + 실제 활용 데이터 확보\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. 장기요양기관 검색
                await self.search_facilities(page)
                
                # 2. 등급판정결과 조회 (구조 분석만)
                await self.search_grade_results(page)
                
                # 3. 장기요양인정서 재발급 (구조 분석만)
                await self.search_certificate_reissue(page)
                
                # 4. 기타 검색 서비스 (복지용구 등)
                await self.search_other_services(page)
                
                # 결과 요약
                print("\n" + "="*70)
                print("   수집 결과 요약")
                print("="*70)
                
                for service, result in self.results.items():
                    print(f"  {service}: {result}")
                
                print(f"\n  Output directory: {self.output_dir}")
                print(f"  Screenshots: {self.screenshots_dir}")
                
                # 최종 요약 저장
                summary_file = f"{self.output_dir}/collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'timestamp': datetime.now().isoformat(),
                        'results': self.results,
                        'services_tested': 4,
                        'pages_per_service': 2
                    }, f, ensure_ascii=False, indent=2)
                
                print(f"\n  Summary saved: {summary_file}")
                
                print("\n[INFO] Browser will remain open for 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                
                # 에러 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=f"{self.screenshots_dir}/error_{timestamp}.png")
                
            finally:
                await browser.close()
                print("\n[COMPLETE] Data collection finished")

async def main():
    scraper = LongTermCareSearchServices()
    await scraper.run()

if __name__ == "__main__":
    print("""
    ============================================
       장기요양보험 검색서비스 자동화
    ============================================
    목표:
    1. 4개 검색서비스 테스트
    2. 각 서비스에서 3페이지씩 데이터 수집
    3. 엑셀 다운로드 기능 테스트
    4. 노하우 축적 및 활용 데이터 확보
    ============================================
    """)
    
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양보험 교육 관리 페이지 스크래핑
페이지네이션 처리 및 데이터 수집
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd

class LongTermCareEducationScraper:
    """장기요양보험 교육 데이터 수집"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.results = []
        self.output_dir = "data/longtermcare"
        
    async def analyze_page_type(self, page, url):
        """페이지 유형 분석"""
        print(f"\n[ANALYSIS] Checking page structure...")
        print(f"URL: {url}")
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 페이지 제목
        title = await page.title()
        print(f"Title: {title}")
        
        # 테이블 존재 확인
        tables = await page.query_selector_all('table')
        print(f"Tables found: {len(tables)}")
        
        # 페이지네이션 확인
        pagination = await page.query_selector('.pagination, .paging, .page_list')
        has_pagination = pagination is not None
        print(f"Pagination: {'Yes' if has_pagination else 'No'}")
        
        # 검색 폼 확인
        search_form = await page.query_selector('form')
        has_search = search_form is not None
        print(f"Search form: {'Yes' if has_search else 'No'}")
        
        return {
            'title': title,
            'has_tables': len(tables) > 0,
            'has_pagination': has_pagination,
            'has_search': has_search
        }
    
    async def extract_table_data(self, page):
        """테이블 데이터 추출"""
        print("\n[EXTRACT] Extracting table data...")
        
        # 모든 테이블 찾기
        tables = await page.query_selector_all('table')
        
        all_data = []
        
        for table_idx, table in enumerate(tables):
            print(f"Processing table {table_idx + 1}...")
            
            # 테이블 데이터 추출
            table_data = await page.evaluate('''(table) => {
                const data = [];
                const headers = [];
                
                // 헤더 추출
                const headerCells = table.querySelectorAll('thead th, thead td');
                headerCells.forEach(cell => {
                    headers.push(cell.textContent.trim());
                });
                
                // 헤더가 없으면 첫 번째 행을 헤더로
                if (headers.length === 0) {
                    const firstRow = table.querySelector('tr');
                    if (firstRow) {
                        firstRow.querySelectorAll('th, td').forEach(cell => {
                            headers.push(cell.textContent.trim());
                        });
                    }
                }
                
                // 데이터 행 추출
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const rowData = {};
                    const cells = row.querySelectorAll('td');
                    
                    cells.forEach((cell, idx) => {
                        const header = headers[idx] || `column_${idx}`;
                        rowData[header] = cell.textContent.trim();
                    });
                    
                    if (Object.keys(rowData).length > 0) {
                        data.push(rowData);
                    }
                });
                
                return {
                    headers: headers,
                    data: data
                };
            }''', table)
            
            if table_data and table_data['data']:
                print(f"  - Extracted {len(table_data['data'])} rows")
                all_data.extend(table_data['data'])
        
        return all_data
    
    async def handle_pagination(self, page, max_pages=10):
        """페이지네이션 처리"""
        print("\n[PAGINATION] Processing multiple pages...")
        
        all_results = []
        current_page = 1
        
        while current_page <= max_pages:
            print(f"\nPage {current_page}:")
            
            # 현재 페이지 데이터 추출
            page_data = await self.extract_table_data(page)
            if page_data:
                all_results.extend(page_data)
                print(f"  Total collected: {len(all_results)} items")
            
            # 다음 페이지 버튼 찾기
            next_button = None
            
            # 다양한 페이지네이션 셀렉터
            pagination_selectors = [
                f'a:has-text("{current_page + 1}")',  # 페이지 번호
                'a:has-text("다음")',
                'a:has-text("next")',
                'a.next',
                '.pagination .next',
                'a[title="다음"]',
                'img[alt="다음"]',
                f'a[onclick*="goPage({current_page + 1})"]',
                f'a[href*="page={current_page + 1}"]'
            ]
            
            for selector in pagination_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        next_button = button
                        break
                except:
                    continue
            
            if next_button:
                print(f"  Moving to page {current_page + 1}...")
                
                # 스크롤 후 클릭
                await next_button.scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                await next_button.click()
                
                # 페이지 로드 대기
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(2000)
                
                current_page += 1
            else:
                print("  No more pages")
                break
        
        return all_results
    
    async def save_results(self, data, filename_prefix):
        """결과 저장"""
        print("\n[SAVE] Saving results...")
        
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 저장
        json_file = f"{self.output_dir}/{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  JSON saved: {json_file}")
        
        # CSV 저장 (pandas 사용)
        if data:
            csv_file = f"{self.output_dir}/{filename_prefix}_{timestamp}.csv"
            df = pd.DataFrame(data)
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"  CSV saved: {csv_file}")
            
            # Excel 저장
            excel_file = f"{self.output_dir}/{filename_prefix}_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            print(f"  Excel saved: {excel_file}")
        
        return {
            'json': json_file,
            'csv': csv_file if data else None,
            'excel': excel_file if data else None
        }
    
    async def scrape_education_list(self, page):
        """교육 목록 스크래핑"""
        url1 = "https://longtermcare.or.kr/npbs/r/e/505/selectRftrEduAdminList?menuId=npe0000002612"
        
        print("\n" + "="*60)
        print("  SCRAPING: 요양보호사 교육관리")
        print("="*60)
        
        # 페이지 분석
        page_info = await self.analyze_page_type(page, url1)
        
        # 데이터 수집
        if page_info['has_pagination']:
            data = await self.handle_pagination(page, max_pages=5)
        else:
            data = await self.extract_table_data(page)
        
        # 저장
        if data:
            files = await self.save_results(data, "education_list")
            print(f"\n[SUCCESS] Collected {len(data)} records")
            return files
        else:
            print("\n[WARNING] No data collected")
            return None
    
    async def scrape_medical_education(self, page):
        """의료급여 교육 스크래핑"""
        url2 = "https://longtermcare.or.kr/npbs/r/e/501/openMdcareMcpcEduAdmin.web?menuId=npe0000001100"
        
        print("\n" + "="*60)
        print("  SCRAPING: 의료급여 교육관리")
        print("="*60)
        
        # 페이지 분석
        page_info = await self.analyze_page_type(page, url2)
        
        # 데이터 수집
        if page_info['has_pagination']:
            data = await self.handle_pagination(page, max_pages=5)
        else:
            data = await self.extract_table_data(page)
        
        # 저장
        if data:
            files = await self.save_results(data, "medical_education")
            print(f"\n[SUCCESS] Collected {len(data)} records")
            return files
        else:
            print("\n[WARNING] No data collected")
            return None
    
    async def run_advanced_scraping(self):
        """고급 스크래핑 실행"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=300
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. 요양보호사 교육 목록
                result1 = await self.scrape_education_list(page)
                
                # 2. 의료급여 교육
                result2 = await self.scrape_medical_education(page)
                
                # 결과 요약
                print("\n" + "="*60)
                print("  SCRAPING SUMMARY")
                print("="*60)
                
                if result1:
                    print("\n요양보호사 교육:")
                    for key, value in result1.items():
                        if value:
                            print(f"  {key}: {value}")
                
                if result2:
                    print("\n의료급여 교육:")
                    for key, value in result2.items():
                        if value:
                            print(f"  {key}: {value}")
                
                print("\n[INFO] Browser will remain open for inspection...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                
                # 에러 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(
                    path=f"logs/screenshots/error_{timestamp}.png",
                    full_page=True
                )
                
            finally:
                await browser.close()

class AdvancedPaginationHandler:
    """고급 페이지네이션 처리"""
    
    @staticmethod
    async def detect_pagination_type(page):
        """페이지네이션 유형 감지"""
        
        patterns = {
            'number_based': {
                'selectors': ['.pagination a', '.paging a', 'a.page-link'],
                'type': 'click_number'
            },
            'javascript_based': {
                'selectors': ['a[onclick*="goPage"]', 'a[href="javascript:"]'],
                'type': 'javascript'
            },
            'ajax_based': {
                'selectors': ['[data-page]', '[data-ajax]'],
                'type': 'ajax'
            },
            'scroll_based': {
                'check': 'window.infiniteScroll',
                'type': 'infinite_scroll'
            }
        }
        
        for pattern_name, pattern in patterns.items():
            if 'selectors' in pattern:
                for selector in pattern['selectors']:
                    element = await page.query_selector(selector)
                    if element:
                        return pattern['type']
            elif 'check' in pattern:
                has_infinite = await page.evaluate(f'{pattern["check"]} !== undefined')
                if has_infinite:
                    return pattern['type']
        
        return 'unknown'
    
    @staticmethod
    async def handle_javascript_pagination(page, page_num):
        """JavaScript 기반 페이지네이션 처리"""
        
        # goPage 함수 호출
        await page.evaluate(f'''
            if (typeof goPage === 'function') {{
                goPage({page_num});
            }} else if (typeof fn_goPage === 'function') {{
                fn_goPage({page_num});
            }} else if (typeof movePage === 'function') {{
                movePage({page_num});
            }}
        ''')
        
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)
    
    @staticmethod
    async def handle_ajax_pagination(page, page_num):
        """AJAX 기반 페이지네이션 처리"""
        
        # AJAX 요청 감지
        async with page.expect_response(lambda r: 'list' in r.url or 'page' in r.url) as response_info:
            # 페이지 번호 클릭
            await page.click(f'[data-page="{page_num}"]')
        
        response = await response_info.value
        await page.wait_for_timeout(1000)

async def main():
    """메인 실행"""
    
    print("""
    ============================================
       장기요양보험 교육 데이터 수집
    ============================================
    기능:
    1. 페이지네이션 자동 처리
    2. 테이블 데이터 추출
    3. JSON/CSV/Excel 저장
    
    난이도: 중상 (기술적으로 도전적)
    ============================================
    """)
    
    print("\n[INFO] 이 작업은 기술적으로 복잡합니다:")
    print("- 동적 페이지네이션 처리")
    print("- 다양한 테이블 구조 파싱")
    print("- 대량 데이터 수집 및 저장")
    print("\n하지만 필요한 기능이므로 단계적으로 구현합니다.\n")
    
    scraper = LongTermCareEducationScraper()
    await scraper.run_advanced_scraping()

if __name__ == "__main__":
    asyncio.run(main())
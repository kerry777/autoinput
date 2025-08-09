#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
페이지네이션 테스트 - 장기요양보험 교육 페이지
https://longtermcare.or.kr/npbs/r/e/501/openMdcareMcpcEduAdmin.web
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

class PaginationTester:
    """페이지네이션 테스트"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr/npbs/r/e/501/openMdcareMcpcEduAdmin.web?menuId=npe0000001100"
        self.data_dir = "data/pagination_test"
        self.screenshots_dir = "logs/screenshots/pagination"
        self.results = []
        
    async def initialize(self):
        """디렉토리 초기화"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        print("[INIT] Directories ready")
    
    async def analyze_page_structure(self, page):
        """페이지 구조 분석"""
        print("\n[페이지 구조 분석]")
        
        # 테이블 찾기
        tables = await page.query_selector_all('table')
        print(f"테이블 수: {len(tables)}")
        
        # 페이지네이션 요소 찾기
        pagination_elements = await page.query_selector_all('.pagination, .paging, [class*="page"], [id*="page"]')
        print(f"페이지네이션 관련 요소: {len(pagination_elements)}")
        
        # 페이지 번호 링크 찾기
        page_links = await page.query_selector_all('a[href*="page"], a[onclick*="page"], a[onclick*="Page"]')
        print(f"페이지 링크: {len(page_links)}")
        
        # 다음/이전 버튼 찾기
        nav_buttons = await page.query_selector_all('a[title*="다음"], a[title*="이전"], a:has-text("다음"), a:has-text("이전")')
        print(f"네비게이션 버튼: {len(nav_buttons)}")
        
        return {
            'tables': len(tables),
            'pagination_elements': len(pagination_elements),
            'page_links': len(page_links),
            'nav_buttons': len(nav_buttons)
        }
    
    async def extract_table_data(self, page, page_num):
        """테이블 데이터 추출"""
        print(f"\n[페이지 {page_num} 데이터 추출]")
        
        data = []
        
        # 메인 테이블 찾기
        tables = await page.query_selector_all('table')
        
        for table_idx, table in enumerate(tables):
            # 헤더 추출
            headers = []
            header_cells = await table.query_selector_all('thead th, thead td')
            if not header_cells:
                # thead가 없으면 첫 번째 tr에서 찾기
                first_row = await table.query_selector('tr')
                if first_row:
                    header_cells = await first_row.query_selector_all('th')
            
            for cell in header_cells:
                text = await cell.text_content()
                headers.append(text.strip() if text else '')
            
            # 데이터 행 추출
            rows = await table.query_selector_all('tbody tr, tr')
            print(f"  테이블 {table_idx+1}: {len(rows)}개 행")
            
            for row_idx, row in enumerate(rows):
                # th가 있는 행은 헤더로 간주하고 건너뛰기
                th_cells = await row.query_selector_all('th')
                if len(th_cells) > 0 and row_idx == 0:
                    continue
                
                cells = await row.query_selector_all('td')
                if cells:
                    row_data = {}
                    for cell_idx, cell in enumerate(cells):
                        text = await cell.text_content()
                        key = headers[cell_idx] if cell_idx < len(headers) else f"column_{cell_idx}"
                        row_data[key] = text.strip() if text else ''
                    
                    if any(row_data.values()):  # 빈 행 제외
                        row_data['page'] = page_num
                        row_data['table_index'] = table_idx
                        data.append(row_data)
        
        print(f"  추출된 데이터: {len(data)}개")
        return data
    
    async def click_next_page(self, page, current_page_num):
        """다음 페이지로 이동"""
        print(f"\n[페이지 {current_page_num} → {current_page_num + 1} 이동 시도]")
        
        # 방법 1: 페이지 번호 직접 클릭
        next_page_num = current_page_num + 1
        page_link = await page.query_selector(f'a:has-text("{next_page_num}")')
        
        if page_link:
            # 현재 URL 저장
            current_url = page.url
            
            await page_link.click()
            await page.wait_for_timeout(2000)
            
            # URL 변경 확인
            new_url = page.url
            if new_url != current_url:
                print(f"  [SUCCESS] URL 변경됨")
                return True
            
            # 또는 테이블 내용 변경 확인
            await page.wait_for_timeout(1000)
            return True
        
        # 방법 2: "다음" 버튼 클릭
        next_button = await page.query_selector('a[title*="다음"], a:has-text("다음")')
        if next_button:
            is_disabled = await next_button.get_attribute('disabled')
            if not is_disabled:
                await next_button.click()
                await page.wait_for_timeout(2000)
                print(f"  [SUCCESS] 다음 버튼 클릭")
                return True
        
        # 방법 3: JavaScript 함수 호출
        js_result = await page.evaluate(f'''() => {{
            // 페이지 이동 함수들 시도
            if (typeof goPage === 'function') {{
                goPage({next_page_num});
                return 'goPage called';
            }}
            if (typeof fn_paging === 'function') {{
                fn_paging({next_page_num});
                return 'fn_paging called';
            }}
            if (typeof doPaging === 'function') {{
                doPaging({next_page_num});
                return 'doPaging called';
            }}
            return 'no function found';
        }}''')
        
        if js_result != 'no function found':
            await page.wait_for_timeout(2000)
            print(f"  [SUCCESS] JavaScript: {js_result}")
            return True
        
        print(f"  [FAILED] 다음 페이지로 이동 실패")
        return False
    
    async def run(self, max_pages=2):
        """페이지네이션 테스트 실행"""
        await self.initialize()
        
        print("\n" + "="*60)
        print("   페이지네이션 테스트")
        print("="*60)
        print(f"URL: {self.base_url}")
        print(f"최대 페이지: {max_pages}")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. 첫 페이지 로드
                print("\n[1] 페이지 로드 중...")
                await page.goto(self.base_url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 스크린샷
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(
                    path=f"{self.screenshots_dir}/page_1_{timestamp}.png"
                )
                
                # 2. 페이지 구조 분석
                structure = await self.analyze_page_structure(page)
                
                # 3. 페이지별 데이터 수집
                all_data = []
                
                for page_num in range(1, max_pages + 1):
                    print(f"\n{'='*40}")
                    print(f"  페이지 {page_num}")
                    print(f"{'='*40}")
                    
                    # 데이터 추출
                    page_data = await self.extract_table_data(page, page_num)
                    all_data.extend(page_data)
                    
                    # 스크린샷
                    await page.screenshot(
                        path=f"{self.screenshots_dir}/page_{page_num}_{timestamp}.png"
                    )
                    
                    # 다음 페이지로 이동
                    if page_num < max_pages:
                        success = await self.click_next_page(page, page_num)
                        if not success:
                            print(f"[WARNING] 페이지 {page_num + 1}로 이동 실패")
                            break
                        
                        # 페이지 로드 대기
                        await page.wait_for_timeout(2000)
                
                # 4. 결과 저장
                print(f"\n[결과 저장]")
                
                # JSON으로 저장
                output_file = f"{self.data_dir}/scraped_data_{timestamp}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=2)
                print(f"  JSON 저장: {output_file}")
                
                # CSV로도 저장
                if all_data:
                    import csv
                    csv_file = f"{self.data_dir}/scraped_data_{timestamp}.csv"
                    
                    # 모든 키 수집
                    all_keys = set()
                    for item in all_data:
                        all_keys.update(item.keys())
                    
                    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                        writer.writeheader()
                        writer.writerows(all_data)
                    print(f"  CSV 저장: {csv_file}")
                
                # 5. 요약
                print(f"\n{'='*60}")
                print(f"   수집 완료")
                print(f"{'='*60}")
                print(f"총 수집 데이터: {len(all_data)}개")
                print(f"페이지 구조: {structure}")
                
                # 샘플 데이터 출력
                if all_data:
                    print(f"\n[샘플 데이터 - 첫 번째 항목]")
                    for key, value in all_data[0].items():
                        print(f"  {key}: {value[:50] if len(str(value)) > 50 else value}")
                
                print(f"\n[INFO] Browser will remain open for 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
                print("\n[COMPLETE] Test finished")

async def main():
    """메인 실행"""
    print("""
    ============================================
       페이지네이션 테스트
    ============================================
    장기요양보험 교육 페이지의 페이지네이션을
    테스트하고 데이터를 수집합니다.
    
    안전을 위해 2페이지만 수집합니다.
    ============================================
    """)
    
    tester = PaginationTester()
    
    # 2페이지만 테스트 (안전을 위해)
    await tester.run(max_pages=2)

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
페이지네이션 스크래퍼 - 개선된 버전
안전하게 데이터를 수집하고 저장
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import csv
import time

class PaginationScraper:
    """페이지네이션을 처리하는 스크래퍼"""
    
    def __init__(self, url, max_pages=2, delay_between_pages=3):
        self.url = url
        self.max_pages = max_pages  # 안전을 위해 제한
        self.delay = delay_between_pages  # 페이지 간 대기 시간
        self.data_dir = "data/scraped"
        self.screenshots_dir = "logs/screenshots/scraping"
        self.all_data = []
        self.metadata = {
            'url': url,
            'start_time': None,
            'end_time': None,
            'pages_scraped': 0,
            'total_items': 0
        }
        
    async def initialize(self):
        """초기화"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.metadata['start_time'] = datetime.now().isoformat()
        print("[INIT] 디렉토리 준비 완료")
    
    async def detect_pagination_type(self, page):
        """페이지네이션 타입 감지"""
        print("\n[페이지네이션 타입 감지]")
        
        # 타입 1: 숫자 링크 (1, 2, 3...)
        number_links = await page.query_selector_all('a:has-text("2"), a:has-text("3")')
        
        # 타입 2: 다음/이전 버튼
        nav_buttons = await page.query_selector_all('a[title*="다음"], a:has-text("다음"), a:has-text(">")')
        
        # 타입 3: JavaScript 함수
        js_functions = await page.evaluate('''() => {
            const funcs = [];
            if (typeof goPage !== 'undefined') funcs.push('goPage');
            if (typeof fn_paging !== 'undefined') funcs.push('fn_paging');
            if (typeof doPaging !== 'undefined') funcs.push('doPaging');
            if (typeof movePage !== 'undefined') funcs.push('movePage');
            return funcs;
        }''')
        
        pagination_type = {
            'has_number_links': len(number_links) > 0,
            'has_nav_buttons': len(nav_buttons) > 0,
            'js_functions': js_functions,
            'type': 'unknown'
        }
        
        if len(number_links) > 0:
            pagination_type['type'] = 'number_links'
        elif len(js_functions) > 0:
            pagination_type['type'] = 'javascript'
        elif len(nav_buttons) > 0:
            pagination_type['type'] = 'nav_buttons'
        
        print(f"  타입: {pagination_type['type']}")
        print(f"  숫자 링크: {pagination_type['has_number_links']}")
        print(f"  네비게이션 버튼: {pagination_type['has_nav_buttons']}")
        print(f"  JS 함수: {pagination_type['js_functions']}")
        
        return pagination_type
    
    async def extract_structured_data(self, page, page_num):
        """구조화된 데이터 추출"""
        print(f"\n[페이지 {page_num} 데이터 추출]")
        
        extracted_data = []
        
        # 메인 데이터 테이블 찾기 (보통 가장 큰 테이블)
        tables = await page.query_selector_all('table')
        
        for table_idx, table in enumerate(tables):
            # 테이블 크기 확인
            rows = await table.query_selector_all('tr')
            if len(rows) < 2:  # 헤더만 있는 테이블 건너뛰기
                continue
            
            print(f"  테이블 {table_idx + 1}: {len(rows)}개 행 발견")
            
            # 헤더 추출
            headers = []
            header_row = await table.query_selector('thead tr, tr:first-child')
            if header_row:
                header_cells = await header_row.query_selector_all('th, td')
                for cell in header_cells:
                    text = await cell.text_content()
                    if text:
                        headers.append(text.strip().replace('\n', ' ').replace('\t', ' '))
            
            if not headers:
                headers = [f"컬럼{i+1}" for i in range(10)]  # 기본 헤더
            
            # 데이터 행 추출
            data_rows = await table.query_selector_all('tbody tr, tr:not(:first-child)')
            
            for row_idx, row in enumerate(data_rows):
                # 빈 행 확인
                text_content = await row.text_content()
                if not text_content or text_content.strip() == '':
                    continue
                
                cells = await row.query_selector_all('td')
                if not cells:
                    continue
                
                row_data = {
                    '_page': page_num,
                    '_table': table_idx + 1,
                    '_row': row_idx + 1
                }
                
                for cell_idx, cell in enumerate(cells):
                    text = await cell.text_content()
                    if text:
                        text = text.strip().replace('\n', ' ').replace('\t', ' ')
                        
                    # 링크 확인
                    link = await cell.query_selector('a')
                    if link:
                        href = await link.get_attribute('href')
                        onclick = await link.get_attribute('onclick')
                        if href or onclick:
                            text = f"{text} [링크]"
                    
                    key = headers[cell_idx] if cell_idx < len(headers) else f"컬럼{cell_idx + 1}"
                    row_data[key] = text if text else ''
                
                # 빈 데이터가 아닌 경우만 추가
                if any(v for k, v in row_data.items() if not k.startswith('_') and v):
                    extracted_data.append(row_data)
        
        print(f"  추출 완료: {len(extracted_data)}개 항목")
        return extracted_data
    
    async def navigate_to_page(self, page, target_page_num, pagination_type):
        """특정 페이지로 이동"""
        print(f"\n[페이지 {target_page_num}로 이동]")
        
        current_url = page.url
        
        # 방법 1: 숫자 링크 클릭
        if pagination_type['type'] == 'number_links':
            page_link = await page.query_selector(f'a:has-text("{target_page_num}")')
            if page_link:
                await page_link.click()
                await page.wait_for_timeout(self.delay * 1000)
                print(f"  [SUCCESS] 페이지 {target_page_num} 링크 클릭")
                return True
        
        # 방법 2: JavaScript 함수 호출
        if pagination_type['type'] == 'javascript' and pagination_type['js_functions']:
            func_name = pagination_type['js_functions'][0]
            result = await page.evaluate(f'{func_name}({target_page_num})')
            await page.wait_for_timeout(self.delay * 1000)
            print(f"  [SUCCESS] JavaScript {func_name}({target_page_num}) 호출")
            return True
        
        # 방법 3: 다음 버튼 클릭 (순차적으로만 가능)
        if pagination_type['type'] == 'nav_buttons' and target_page_num == 2:
            next_btn = await page.query_selector('a[title*="다음"], a:has-text("다음"), a:has-text(">")')
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(self.delay * 1000)
                print(f"  [SUCCESS] 다음 버튼 클릭")
                return True
        
        print(f"  [FAILED] 페이지 이동 실패")
        return False
    
    async def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 메타데이터 업데이트
        self.metadata['end_time'] = datetime.now().isoformat()
        self.metadata['total_items'] = len(self.all_data)
        
        # JSON 저장
        json_file = f"{self.data_dir}/data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': self.metadata,
                'data': self.all_data
            }, f, ensure_ascii=False, indent=2)
        print(f"\n[저장] JSON: {json_file}")
        
        # CSV 저장
        if self.all_data:
            csv_file = f"{self.data_dir}/data_{timestamp}.csv"
            
            # 모든 키 수집
            all_keys = set()
            for item in self.all_data:
                all_keys.update(item.keys())
            
            # _로 시작하는 메타 필드를 앞으로
            meta_keys = sorted([k for k in all_keys if k.startswith('_')])
            data_keys = sorted([k for k in all_keys if not k.startswith('_')])
            fieldnames = meta_keys + data_keys
            
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.all_data)
            print(f"[저장] CSV: {csv_file}")
        
        # 요약 파일
        summary_file = f"{self.data_dir}/summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("   스크래핑 요약\n")
            f.write("="*60 + "\n\n")
            f.write(f"URL: {self.metadata['url']}\n")
            f.write(f"시작: {self.metadata['start_time']}\n")
            f.write(f"종료: {self.metadata['end_time']}\n")
            f.write(f"수집 페이지: {self.metadata['pages_scraped']}\n")
            f.write(f"총 항목: {self.metadata['total_items']}\n")
            
            if self.all_data:
                f.write(f"\n[샘플 데이터]\n")
                for key, value in self.all_data[0].items():
                    f.write(f"  {key}: {value}\n")
        
        print(f"[저장] 요약: {summary_file}")
    
    async def run(self):
        """메인 실행"""
        await self.initialize()
        
        print("\n" + "="*60)
        print("   페이지네이션 스크래핑")
        print("="*60)
        print(f"URL: {self.url}")
        print(f"최대 페이지: {self.max_pages}")
        print(f"페이지 간 대기: {self.delay}초")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 디버깅을 위해 화면 표시
                slow_mo=500
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 첫 페이지 로드
                print("\n[페이지 로드]")
                await page.goto(self.url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 페이지네이션 타입 감지
                pagination_type = await self.detect_pagination_type(page)
                
                # 각 페이지 처리
                for page_num in range(1, self.max_pages + 1):
                    print(f"\n{'='*40}")
                    print(f"  페이지 {page_num}/{self.max_pages}")
                    print(f"{'='*40}")
                    
                    # 스크린샷
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await page.screenshot(
                        path=f"{self.screenshots_dir}/page_{page_num}_{timestamp}.png"
                    )
                    
                    # 데이터 추출
                    page_data = await self.extract_structured_data(page, page_num)
                    self.all_data.extend(page_data)
                    self.metadata['pages_scraped'] = page_num
                    
                    # 다음 페이지로 이동
                    if page_num < self.max_pages:
                        success = await self.navigate_to_page(page, page_num + 1, pagination_type)
                        if not success:
                            print(f"[WARNING] 페이지 {page_num + 1} 이동 실패. 중단.")
                            break
                        
                        # 안전을 위한 추가 대기
                        print(f"  대기 중... ({self.delay}초)")
                        await page.wait_for_timeout(self.delay * 1000)
                
                # 결과 저장
                await self.save_results()
                
                # 요약 출력
                print(f"\n{'='*60}")
                print(f"   완료")
                print(f"{'='*60}")
                print(f"수집 페이지: {self.metadata['pages_scraped']}")
                print(f"총 데이터: {len(self.all_data)}개")
                
                print("\n[INFO] 브라우저가 10초 후 닫힙니다...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                import traceback
                traceback.print_exc()
                
            finally:
                await browser.close()
                print("\n[COMPLETE] 스크래핑 완료")

async def main():
    """메인"""
    print("""
    ============================================
       안전한 페이지네이션 스크래핑
    ============================================
    - 2페이지만 수집 (차단 방지)
    - 페이지 간 3초 대기
    - 구조화된 데이터 저장
    ============================================
    """)
    
    # 교육 페이지 URL
    url = "https://longtermcare.or.kr/npbs/r/e/501/openMdcareMcpcEduAdmin.web?menuId=npe0000001100"
    
    scraper = PaginationScraper(
        url=url,
        max_pages=2,  # 안전을 위해 2페이지만
        delay_between_pages=3  # 3초 대기
    )
    
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main())
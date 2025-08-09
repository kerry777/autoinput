#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양기관 전국 17개 시도별 다운로드
각 시도별로 검색 후 팝업에서 엑셀 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import time

class LongTermCareAllRegionsDownloader:
    """전국 17개 시도 장기요양기관 다운로드"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
        self.download_dir = "downloads/longtermcare/regions"
        self.screenshots_dir = "logs/screenshots/regions"
        
        # 전국 17개 시도 (select option value와 이름)
        self.regions = [
            ("11", "서울특별시"),
            ("26", "부산광역시"),
            ("27", "대구광역시"),
            ("28", "인천광역시"),
            ("29", "광주광역시"),
            ("30", "대전광역시"),
            ("31", "울산광역시"),
            ("36", "세종특별자치시"),
            ("41", "경기도"),
            ("42", "강원도"),
            ("43", "충청북도"),
            ("44", "충청남도"),
            ("45", "전라북도"),
            ("46", "전라남도"),
            ("47", "경상북도"),
            ("48", "경상남도"),
            ("50", "제주특별자치도")
        ]
        
        self.download_results = {}
        
    async def initialize_directories(self):
        """디렉토리 생성"""
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        print("[INIT] Directories created")
    
    async def download_region(self, page, region_code, region_name):
        """특정 시도의 데이터 다운로드"""
        print(f"\n{'='*60}")
        print(f"  [{region_name}] 데이터 다운로드")
        print(f"{'='*60}")
        
        try:
            # 1. 페이지 이동 (매번 새로 로드)
            print(f"[STEP 1] Loading page...")
            await page.goto(self.base_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # 2. 시도만 선택 (다른 조건은 선택하지 않음)
            print(f"[STEP 2] Selecting ONLY region: {region_name} ({region_code})")
            
            # 다양한 방법으로 시도 선택 박스 찾기
            sido_select = None
            
            # 방법 1: name 속성으로
            sido_select = await page.query_selector('select[name="siDoCd"]')
            
            # 방법 2: id로
            if not sido_select:
                sido_select = await page.query_selector('select#siDoCd')
            
            # 방법 3: label 텍스트로
            if not sido_select:
                sido_select = await page.query_selector('select:near(:text("시도"))')
            
            # 방법 4: 첫 번째 select 요소
            if not sido_select:
                selects = await page.query_selector_all('select')
                if selects:
                    sido_select = selects[0]
                    print(f"  Using first select element")
            
            if sido_select:
                # select 요소가 보이는지 확인
                is_visible = await sido_select.is_visible()
                if not is_visible:
                    print(f"  Select element found but not visible")
                
                await page.select_option(sido_select, value=region_code)
                await page.wait_for_timeout(1000)
                print(f"  Selected region - No other filters applied")
            else:
                print(f"  [ERROR] Could not find region selector")
                
                # 페이지의 모든 select 요소 디버깅
                all_selects = await page.query_selector_all('select')
                print(f"  Debug: Found {len(all_selects)} select elements on page")
                for i, sel in enumerate(all_selects):
                    name = await sel.get_attribute('name')
                    id_attr = await sel.get_attribute('id')
                    print(f"    Select {i}: name='{name}', id='{id_attr}'")
                
                return False
            
            # 3. 검색 버튼 클릭 (다른 조건 없이)
            print(f"[STEP 3] Clicking search button...")
            
            search_button = await page.query_selector('button:has-text("검색")')
            if not search_button:
                # 다른 선택자 시도
                search_button = await page.query_selector('button.btn-danger, button.검색, a.btn_search')
            
            if search_button:
                # 팝업 대기 준비
                popup_promise = page.wait_for_event('popup')
                
                # 검색 버튼 클릭
                await search_button.click()
                
                # 팝업 창 대기
                print(f"[STEP 4] Waiting for popup window...")
                try:
                    popup = await asyncio.wait_for(popup_promise, timeout=10)
                    print(f"  Popup opened")
                    
                    # 팝업 창에서 작업
                    await popup.wait_for_load_state('networkidle')
                    await popup.wait_for_timeout(2000)
                    
                    # 팝업 스크린샷
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await popup.screenshot(
                        path=f"{self.screenshots_dir}/popup_{region_code}_{timestamp}.png"
                    )
                    
                    # 4. 팝업에서 다운로드 버튼 찾기
                    print(f"[STEP 5] Looking for download button in popup...")
                    
                    download_selectors = [
                        'button:has-text("다운로드")',
                        'a:has-text("다운로드")',
                        'button:has-text("엑셀")',
                        'a:has-text("엑셀")',
                        'button.btn-excel',
                        'a.btn-excel',
                        'img[alt*="엑셀"]',
                        'img[alt*="다운로드"]'
                    ]
                    
                    download_button = None
                    for selector in download_selectors:
                        btn = await popup.query_selector(selector)
                        if btn and await btn.is_visible():
                            download_button = btn
                            print(f"    Found: {selector}")
                            break
                    
                    if download_button:
                        # 다운로드 준비
                        download_promise = popup.wait_for_event('download', timeout=15000)
                        
                        # 다운로드 버튼 클릭
                        await download_button.click()
                        print(f"[STEP 6] Download button clicked")
                        
                        # 다운로드 완료 대기
                        download = await download_promise
                        
                        # 파일 저장
                        filename = f"{region_code}_{region_name}_{timestamp}.xlsx"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        await download.save_as(filepath)
                        print(f"  [SUCCESS] Downloaded: {filename}")
                        
                        self.download_results[region_name] = {
                            'status': 'success',
                            'file': filename
                        }
                        
                        # 팝업 닫기
                        await popup.close()
                        
                        return True
                    else:
                        print(f"  [WARNING] Download button not found in popup")
                        
                        # JavaScript로 시도
                        await popup.evaluate('''() => {
                            if (typeof doExcelDown === 'function') doExcelDown();
                            else if (typeof excelDownload === 'function') excelDownload();
                        }''')
                        
                        await popup.wait_for_timeout(3000)
                        await popup.close()
                        
                except asyncio.TimeoutError:
                    print(f"  [WARNING] Popup timeout - trying direct download")
                    
                    # 팝업 없이 직접 다운로드 시도
                    await page.evaluate('''() => {
                        if (typeof doExcelDown === 'function') doExcelDown();
                        else if (typeof excelDownload === 'function') excelDownload();
                    }''')
                    
            else:
                print(f"  [ERROR] Search button not found")
                return False
                
        except Exception as e:
            print(f"  [ERROR] Failed for {region_name}: {str(e)}")
            self.download_results[region_name] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
        
        return False
    
    async def download_all_regions(self, page, start_from=0, max_regions=None):
        """모든 시도 다운로드 (안전하게 처리)"""
        
        total_regions = len(self.regions)
        end_index = min(start_from + (max_regions or total_regions), total_regions)
        
        print(f"\n{'='*70}")
        print(f"  전국 시도별 다운로드 시작")
        print(f"  대상: {start_from + 1}번째부터 {end_index}번째 시도")
        print(f"{'='*70}")
        
        success_count = 0
        fail_count = 0
        
        for i in range(start_from, end_index):
            region_code, region_name = self.regions[i]
            
            print(f"\n[{i+1}/{total_regions}] Processing {region_name}...")
            
            # 다운로드 실행
            success = await self.download_region(page, region_code, region_name)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # 다음 지역 전 대기 (서버 부하 방지)
            if i < end_index - 1:
                wait_time = 5  # 5초 대기
                print(f"\n  Waiting {wait_time} seconds before next region...")
                await page.wait_for_timeout(wait_time * 1000)
        
        return success_count, fail_count
    
    async def run(self, batch_size=5):
        """메인 실행 (배치 처리)"""
        await self.initialize_directories()
        
        print("\n" + "="*70)
        print("   전국 17개 시도 장기요양기관 다운로드")
        print("="*70)
        print(f"총 {len(self.regions)}개 시도")
        print(f"배치 크기: {batch_size}개씩 처리")
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
            
            # 팝업 허용
            context.on('page', lambda page: print(f"[POPUP] New page opened: {page.url}"))
            
            page = await context.new_page()
            
            try:
                total_success = 0
                total_fail = 0
                
                # 배치별로 처리
                for batch_num in range(0, len(self.regions), batch_size):
                    print(f"\n{'='*70}")
                    print(f"  배치 {batch_num // batch_size + 1} 시작")
                    print(f"{'='*70}")
                    
                    success, fail = await self.download_all_regions(
                        page, 
                        start_from=batch_num,
                        max_regions=batch_size
                    )
                    
                    total_success += success
                    total_fail += fail
                    
                    # 배치 간 대기 (더 긴 대기)
                    if batch_num + batch_size < len(self.regions):
                        wait_time = 10  # 10초 대기
                        print(f"\n  Waiting {wait_time} seconds before next batch...")
                        await page.wait_for_timeout(wait_time * 1000)
                
                # 최종 결과
                print("\n" + "="*70)
                print("   다운로드 완료")
                print("="*70)
                print(f"성공: {total_success}개 시도")
                print(f"실패: {total_fail}개 시도")
                
                # 상세 결과
                print("\n[상세 결과]")
                for region_name, result in self.download_results.items():
                    status = "✓" if result['status'] == 'success' else "✗"
                    print(f"  {status} {region_name}: {result.get('file', result.get('error', 'Unknown'))}")
                
                print(f"\n다운로드 경로: {self.download_dir}")
                
                print("\n[INFO] Browser will remain open for 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] {str(e)}")
                
            finally:
                await browser.close()
                print("\n[COMPLETE] Process finished")

async def main():
    """메인 실행"""
    
    print("""
    ============================================
       전국 장기요양기관 다운로드
    ============================================
    주의사항:
    1. 17개 시도 전체 다운로드는 시간이 걸립니다
    2. 서버 부하 방지를 위해 5개씩 배치 처리
    3. 각 다운로드 간 5초 대기
    4. 배치 간 10초 대기
    
    예상 소요시간: 약 10-15분
    ============================================
    """)
    
    # 사용자 확인
    print("\n전체 17개 시도를 다운로드하시겠습니까?")
    print("테스트를 원하시면 batch_size=3으로 시작하세요.")
    
    downloader = LongTermCareAllRegionsDownloader()
    
    # 테스트: 3개만 다운로드
    # await downloader.run(batch_size=3)
    
    # 전체: 5개씩 배치 처리
    await downloader.run(batch_size=5)

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전국 17개 시도 장기요양기관 엑셀 다운로드 (최종 버전)
정확한 버튼 ID를 사용한 안정적인 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import time

class FinalRegionDownloader:
    """최종 전국 시도별 다운로드"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
        self.download_dir = "downloads/longtermcare/final"
        self.screenshots_dir = "logs/screenshots/final"
        
        # 전국 17개 시도
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
        
        self.results = {}
        
    async def initialize(self):
        """초기화"""
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        print("[INIT] Directories ready")
    
    async def download_region(self, page, context, region_code, region_name):
        """특정 시도 다운로드"""
        print(f"\n{'='*60}")
        print(f"  {region_name} ({region_code})")
        print(f"{'='*60}")
        
        try:
            # 1. 페이지 새로고침
            print("[1] Loading page...")
            await page.goto(self.base_url, wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # 2. 시도 선택
            print(f"[2] Selecting {region_name}...")
            await page.select_option('select[name="siDoCd"]', value=region_code)
            await page.wait_for_timeout(1000)
            
            # 3. 검색 버튼 클릭으로 팝업 열기
            print("[3] Looking for search button...")
            search_btn = await page.query_selector('#btn_search_pop')
            
            if not search_btn:
                print("[ERROR] Search button not found")
                return False
            
            # 검색 버튼 클릭
            print("[4] Clicking search button...")
            await search_btn.click()
            
            # 팝업 대기 - context.pages 사용
            print("[5] Waiting for popup window...")
            await page.wait_for_timeout(5000)  # 팝업이 열릴 시간 대기
            
            # 열린 페이지들 확인
            all_pages = context.pages
            if len(all_pages) > 1:
                popup = all_pages[-1]  # 마지막 열린 페이지가 팝업
                print(f"[6] Popup opened: {popup.url[:50]}...")
                
                # 팝업 로드 대기
                await popup.wait_for_load_state('networkidle', timeout=30000)
                await popup.wait_for_timeout(3000)  # 데이터 로드 완료 대기
                
                # 7. 다운로드 버튼 클릭
                print("[7] Looking for download button...")
                download_btn = await popup.query_selector('#btn_map_excel')
                
                if download_btn:
                    print("[8] Found download button!")
                    
                    # 다운로드 이벤트 준비 - 타임아웃 30초
                    download_promise = popup.wait_for_event('download', timeout=30000)
                    
                    # 버튼 클릭
                    await download_btn.click()
                    print("[9] Clicked download button")
                    
                    try:
                        # 다운로드 완료 대기
                        download = await download_promise
                        
                        # 파일 저장
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{region_code}_{region_name}_{timestamp}.xlsx"
                        filepath = os.path.join(self.download_dir, filename)
                        
                        await download.save_as(filepath)
                        print(f"[SUCCESS] Saved: {filename}")
                        
                        self.results[region_name] = {
                            'status': 'success',
                            'file': filename
                        }
                        
                        # 팝업 닫기
                        await popup.close()
                        return True
                        
                    except asyncio.TimeoutError:
                        print("[WARNING] Download timeout")
                        
                        # JavaScript로 다운로드 함수 직접 호출
                        await popup.evaluate('''() => {
                            if (typeof doExcelDown === 'function') doExcelDown();
                            else if (typeof excelDownload === 'function') excelDownload();
                            else document.querySelector('#btn_map_excel')?.click();
                        }''')
                        
                        await popup.wait_for_timeout(3000)
                        await popup.close()
                        
                else:
                    print("[WARNING] Download button not found")
                    
                    # 스크린샷 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await popup.screenshot(
                        path=f"{self.screenshots_dir}/popup_{region_code}_{timestamp}.png"
                    )
                    
                    self.results[region_name] = {
                        'status': 'failed',
                        'error': 'Download button not found'
                    }
                    
                    await popup.close()
                    return False
                    
            else:
                print("[ERROR] No popup opened")
                self.results[region_name] = {
                    'status': 'failed',
                    'error': 'No popup opened'
                }
                return False
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            self.results[region_name] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
        
        return False
    
    async def download_all(self, page, context, start_idx=0, count=None):
        """모든 시도 다운로드"""
        
        if count is None:
            count = len(self.regions) - start_idx
        
        end_idx = min(start_idx + count, len(self.regions))
        
        print(f"\n{'='*70}")
        print(f"  다운로드 시작: {start_idx+1}번째부터 {end_idx}번째까지")
        print(f"{'='*70}")
        
        success = 0
        failed = 0
        
        for i in range(start_idx, end_idx):
            region_code, region_name = self.regions[i]
            
            print(f"\n[{i+1}/{len(self.regions)}] {region_name}")
            
            result = await self.download_region(page, context, region_code, region_name)
            
            if result:
                success += 1
            else:
                failed += 1
            
            # 다음 지역 전 대기
            if i < end_idx - 1:
                wait = 5
                print(f"\n  >> Waiting {wait} seconds...")
                await page.wait_for_timeout(wait * 1000)
        
        return success, failed
    
    async def run(self, test_mode=False):
        """실행"""
        await self.initialize()
        
        print("\n" + "="*70)
        print("   전국 17개 시도 장기요양기관 다운로드")
        print("="*70)
        
        if test_mode:
            print(">> TEST MODE: 처음 3개 시도만 다운로드")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=1000  # 더 천천히 실행
            )
            
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
                permissions=[],  # 위치 정보 등 권한 거부
                geolocation=None  # 위치 정보 제공 안 함
            )
            
            page = await context.new_page()
            
            try:
                if test_mode:
                    # 테스트: 처음 3개만
                    success, failed = await self.download_all(page, context, 0, 3)
                else:
                    # 전체 실행
                    total_success = 0
                    total_failed = 0
                    
                    # 5개씩 배치 처리
                    batch_size = 5
                    for batch_start in range(0, len(self.regions), batch_size):
                        print(f"\n{'='*70}")
                        print(f"  배치 {batch_start//batch_size + 1}")
                        print(f"{'='*70}")
                        
                        s, f = await self.download_all(
                            page, context, batch_start, batch_size
                        )
                        
                        total_success += s
                        total_failed += f
                        
                        # 배치 간 대기
                        if batch_start + batch_size < len(self.regions):
                            wait = 10
                            print(f"\n  >> Batch complete. Waiting {wait} seconds...")
                            await page.wait_for_timeout(wait * 1000)
                    
                    success = total_success
                    failed = total_failed
                
                # 결과 출력
                print("\n" + "="*70)
                print("   다운로드 완료")
                print("="*70)
                print(f"성공: {success}")
                print(f"실패: {failed}")
                
                print("\n[상세 결과]")
                for region, result in self.results.items():
                    status = "✓" if result['status'] == 'success' else "✗"
                    detail = result.get('file', result.get('error', ''))
                    print(f"  {status} {region}: {detail}")
                
                print(f"\n파일 저장 위치: {self.download_dir}")
                
                print("\n[INFO] Browser will remain open for 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[CRITICAL ERROR] {str(e)}")
                
            finally:
                await browser.close()
                print("\n[COMPLETE] All done!")

async def main():
    """메인"""
    print("""
    ============================================
       전국 17개 시도 다운로드 (최종)
    ============================================
    옵션:
    1. 테스트 모드 (3개 시도)
    2. 전체 실행 (17개 시도)
    ============================================
    """)
    
    downloader = FinalRegionDownloader()
    
    # 테스트 모드로 시작 (3개만)
    await downloader.run(test_mode=True)
    
    # 전체 실행하려면:
    # await downloader.run(test_mode=False)

if __name__ == "__main__":
    asyncio.run(main())
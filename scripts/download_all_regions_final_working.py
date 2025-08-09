#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전국 17개 시도 장기요양기관 엑셀 다운로드 (최종 작동 버전)
async with expect_download 방식 적용
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

class FinalRegionDownloader:
    """전국 시도별 다운로드 - 최종 버전"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
        self.download_dir = "downloads/longtermcare/regions"
        self.screenshots_dir = "logs/screenshots/regions"
        
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
        """디렉토리 초기화"""
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
            await page.wait_for_timeout(3000)
            
            # 2. 시도 선택
            print(f"[2] Selecting {region_name}...")
            await page.select_option('select[name="siDoCd"]', value=region_code)
            await page.wait_for_timeout(2000)
            
            # 3. 검색 버튼 클릭
            print("[3] Clicking search button...")
            search_btn = await page.query_selector('#btn_search_pop')
            
            if not search_btn:
                print("[ERROR] Search button not found")
                self.results[region_name] = {'status': 'failed', 'error': 'No search button'}
                return False
            
            # 현재 페이지 수 기록
            pages_before = len(context.pages)
            
            # 검색 버튼 클릭
            await search_btn.click()
            
            # 4. 팝업 대기 (데이터가 많아서 시간이 걸림)
            print("[4] Waiting for popup (may take 10-15 seconds)...")
            max_wait = 20
            waited = 0
            popup = None
            
            while waited < max_wait:
                await page.wait_for_timeout(1000)
                waited += 1
                
                if len(context.pages) > pages_before:
                    popup = context.pages[-1]
                    print(f"[5] Popup opened after {waited} seconds")
                    break
                
                if waited % 5 == 0:
                    print(f"    Still waiting... ({waited}/{max_wait}s)")
            
            if not popup:
                print("[ERROR] No popup after 20 seconds")
                self.results[region_name] = {'status': 'failed', 'error': 'No popup'}
                return False
            
            # 5. 팝업 로드 대기
            print("[6] Waiting for popup to load...")
            await popup.wait_for_timeout(5000)
            
            # 6. 다운로드 버튼 찾기
            print("[7] Looking for download button...")
            download_btn = await popup.query_selector('#btn_map_excel')
            
            if not download_btn:
                # 다른 선택자로 시도
                download_btn = await popup.query_selector('button.btnLayer#btn_map_excel')
            
            if download_btn:
                print("[8] Found download button, starting download...")
                
                # async with expect_download 사용 (작동 확인된 방법)
                try:
                    async with popup.expect_download(timeout=30000) as download_info:
                        await download_btn.click()
                    
                    download = await download_info.value
                    print(f"[9] Download started: {download.suggested_filename}")
                    
                    # 파일 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{region_code}_{region_name}_{timestamp}.xlsx"
                    filepath = os.path.join(self.download_dir, filename)
                    
                    await download.save_as(filepath)
                    print(f"[SUCCESS] Saved: {filename}")
                    
                    # 파일 크기 확인
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        print(f"    File size: {file_size:,} bytes")
                    
                    self.results[region_name] = {
                        'status': 'success',
                        'file': filename,
                        'size': file_size
                    }
                    
                    # 팝업 닫기
                    await popup.close()
                    return True
                    
                except Exception as e:
                    print(f"[WARNING] Download error: {str(e)}")
                    
                    # JavaScript로 재시도
                    print("    Trying JavaScript click...")
                    await popup.evaluate('''() => {
                        const btn = document.querySelector('#btn_map_excel');
                        if (btn) btn.click();
                    }''')
                    
                    await popup.wait_for_timeout(5000)
                    await popup.close()
                    
                    self.results[region_name] = {
                        'status': 'partial',
                        'error': 'JavaScript fallback'
                    }
                    
            else:
                print("[ERROR] Download button not found")
                
                # 스크린샷 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await popup.screenshot(
                    path=f"{self.screenshots_dir}/error_{region_code}_{timestamp}.png"
                )
                
                self.results[region_name] = {
                    'status': 'failed',
                    'error': 'No download button'
                }
                
                await popup.close()
                return False
                
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            self.results[region_name] = {
                'status': 'failed',
                'error': str(e)
            }
            return False
        
        return False
    
    async def run(self, test_mode=False, start_from=0, headless=True):
        """실행"""
        await self.initialize()
        
        print("\n" + "="*70)
        print("   전국 17개 시도 장기요양기관 다운로드")
        print("="*70)
        
        if test_mode:
            print(">> TEST MODE: 3개 시도만 다운로드")
        
        if headless:
            print(">> HEADLESS MODE: 더 빠른 실행")
        else:
            print(">> BROWSER MODE: 화면 표시")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,  # headless 모드 설정
                slow_mo=200 if headless else 1000,  # headless일 때 더 빠르게
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
                permissions=[],  # 위치 권한 거부
                geolocation=None
            )
            
            page = await context.new_page()
            
            try:
                # 처리할 지역 결정
                if test_mode:
                    regions_to_process = self.regions[start_from:start_from+3]
                else:
                    regions_to_process = self.regions[start_from:]
                
                success = 0
                failed = 0
                
                for i, (region_code, region_name) in enumerate(regions_to_process):
                    print(f"\n[{i+1}/{len(regions_to_process)}] Processing {region_name}...")
                    
                    result = await self.download_region(page, context, region_code, region_name)
                    
                    if result:
                        success += 1
                    else:
                        failed += 1
                    
                    # 다음 지역 전 대기 (서버 부하 방지)
                    if i < len(regions_to_process) - 1:
                        wait = 5
                        print(f"\n  >> Waiting {wait} seconds before next region...")
                        await page.wait_for_timeout(wait * 1000)
                
                # 결과 출력
                print("\n" + "="*70)
                print("   다운로드 완료")
                print("="*70)
                print(f"성공: {success}")
                print(f"실패: {failed}")
                
                print("\n[상세 결과]")
                for region, result in self.results.items():
                    if result['status'] == 'success':
                        status = "✓"
                        detail = f"{result['file']} ({result.get('size', 0):,} bytes)"
                    else:
                        status = "✗"
                        detail = result.get('error', 'Unknown error')
                    print(f"  {status} {region}: {detail}")
                
                print(f"\n파일 저장 위치: {self.download_dir}")
                
                # 전체 다운로드 크기 계산
                total_size = sum(r.get('size', 0) for r in self.results.values() if r['status'] == 'success')
                if total_size > 0:
                    print(f"총 다운로드 크기: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
                
                print("\n[INFO] Browser will remain open for 10 seconds...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[CRITICAL ERROR] {str(e)}")
                
            finally:
                await browser.close()
                print("\n[COMPLETE] All done!")

async def main():
    """메인 실행"""
    print("""
    ============================================
       전국 17개 시도 다운로드 (최종 작동 버전)
    ============================================
    주의사항:
    - 각 지역당 15-20초 소요 (팝업 로딩 시간)
    - 전체 17개 지역: 약 10-15분 소요
    ============================================
    
    실행 모드:
    1. 화면 표시 모드 - 진행 과정을 보면서 실행 (느림)
    2. Headless 모드 - 백그라운드 실행 (빠름)
    
    테스트 옵션:
    - 테스트 모드 (처음 3개 시도)
    - 전체 다운로드 (17개 시도)
    """)
    
    downloader = FinalRegionDownloader()
    
    # === 실행 옵션 선택 ===
    
    # 옵션 1: 화면 표시 + 테스트 모드 (3개만, 진행 과정 확인 가능)
    # await downloader.run(test_mode=True, headless=False)
    
    # 옵션 2: Headless + 테스트 모드 (3개만, 빠른 실행)
    await downloader.run(test_mode=True, headless=True)
    
    # 옵션 3: 화면 표시 + 전체 실행 (17개, 진행 과정 확인 가능)
    # await downloader.run(test_mode=False, headless=False)
    
    # 옵션 4: Headless + 전체 실행 (17개, 빠른 실행)
    # await downloader.run(test_mode=False, headless=True)
    
    # 옵션 5: 특정 위치부터 시작 (예: 4번째 지역부터)
    # await downloader.run(test_mode=False, start_from=3, headless=True)

if __name__ == "__main__":
    asyncio.run(main())
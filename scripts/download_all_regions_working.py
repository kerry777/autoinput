#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전국 17개 시도 장기요양기관 엑셀 다운로드 (작동 버전)
타이밍 이슈 해결 버전
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import time

class RegionDownloader:
    """전국 시도별 다운로드"""
    
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
            
            # 4. 새 창이 열릴 때까지 대기 (최대 15초)
            print("[4] Waiting for popup window...")
            max_wait = 15
            waited = 0
            popup = None
            
            while waited < max_wait:
                await page.wait_for_timeout(1000)
                waited += 1
                
                if len(context.pages) > pages_before:
                    # 새 페이지 발견
                    popup = context.pages[-1]
                    print(f"[5] Popup opened after {waited} seconds")
                    break
                
                if waited % 3 == 0:
                    print(f"    Waiting... ({waited}/{max_wait}s)")
            
            if not popup:
                print("[ERROR] No popup opened after 15 seconds")
                self.results[region_name] = {'status': 'failed', 'error': 'No popup'}
                return False
            
            # 5. 팝업 로드 대기
            print("[6] Waiting for popup to load...")
            try:
                await popup.wait_for_load_state('networkidle', timeout=30000)
            except:
                print("    Continuing despite timeout...")
            
            await popup.wait_for_timeout(3000)
            
            # 6. 다운로드 버튼 찾기
            print("[7] Looking for download button...")
            download_btn = None
            
            # 여러 방법으로 버튼 찾기
            selectors = [
                '#btn_map_excel',
                'button#btn_map_excel',
                'button.btnLayer#btn_map_excel',
                'button:has-text("다운로드")'
            ]
            
            for selector in selectors:
                try:
                    btn = await popup.query_selector(selector)
                    if btn:
                        download_btn = btn
                        print(f"    Found with: {selector}")
                        break
                except:
                    continue
            
            if download_btn:
                print("[8] Clicking download button...")
                
                # 다운로드 이벤트 준비
                download_promise = popup.wait_for_event('download', timeout=30000)
                
                # 버튼 클릭
                await download_btn.click()
                
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
                    print("[WARNING] Download timeout - trying JavaScript")
                    
                    # JavaScript로 클릭 시도
                    try:
                        await popup.evaluate('''() => {
                            const btn = document.querySelector('#btn_map_excel');
                            if (btn) btn.click();
                        }''')
                        await popup.wait_for_timeout(5000)
                    except:
                        pass
                    
                    await popup.close()
                    
                    self.results[region_name] = {
                        'status': 'partial',
                        'error': 'Download timeout'
                    }
                    
            else:
                print("[WARNING] Download button not found")
                
                # 스크린샷 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                try:
                    await popup.screenshot(
                        path=f"{self.screenshots_dir}/popup_{region_code}_{timestamp}.png"
                    )
                except:
                    pass
                
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
                slow_mo=1000,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                accept_downloads=True,
                viewport={'width': 1920, 'height': 1080},
                locale='ko-KR',
                permissions=[],  # 위치 권한 거부
                geolocation=None
            )
            
            # 새 페이지 이벤트 감지
            def on_page(page):
                print(f"[NEW PAGE] {page.url[:50]}...")
            
            context.on('page', on_page)
            
            page = await context.new_page()
            
            try:
                regions_to_process = self.regions[:3] if test_mode else self.regions
                success = 0
                failed = 0
                
                for i, (region_code, region_name) in enumerate(regions_to_process):
                    print(f"\n[{i+1}/{len(regions_to_process)}] Processing {region_name}...")
                    
                    result = await self.download_region(page, context, region_code, region_name)
                    
                    if result:
                        success += 1
                    else:
                        failed += 1
                    
                    # 다음 지역 전 대기
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
       전국 17개 시도 다운로드 (작동 버전)
    ============================================
    옵션:
    1. 테스트 모드 (3개 시도)
    2. 전체 실행 (17개 시도)
    ============================================
    """)
    
    downloader = RegionDownloader()
    
    # 테스트 모드로 시작 (3개만)
    await downloader.run(test_mode=True)
    
    # 전체 실행하려면:
    # await downloader.run(test_mode=False)

if __name__ == "__main__":
    asyncio.run(main())
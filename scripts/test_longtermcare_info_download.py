#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양보험 정보 다운로드 페이지 자동화
요양기관 등 정보 다운로드 서비스
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd

class LongTermCareInfoDownloader:
    """장기요양보험 정보 다운로드 자동화"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.output_dir = "data/longtermcare/info_downloads"
        self.screenshots_dir = "logs/screenshots/longtermcare"
        self.download_dir = "downloads/longtermcare/info"
        
    async def initialize_directories(self):
        """디렉토리 생성"""
        for dir_path in [self.output_dir, self.screenshots_dir, self.download_dir]:
            os.makedirs(dir_path, exist_ok=True)
        print("[INIT] Directories created")
    
    async def find_info_download_page(self, page):
        """정보 다운로드 페이지 찾기"""
        print("\n[NAVIGATION] Finding info download page...")
        
        # 메인 페이지 접속
        await page.goto(self.base_url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # 정보 다운로드 관련 메뉴 찾기
        menu_keywords = [
            "정보다운로드",
            "자료실",
            "다운로드센터",
            "정보공개",
            "공공데이터",
            "통계자료"
        ]
        
        found_menu = False
        for keyword in menu_keywords:
            menu = await page.query_selector(f'a:has-text("{keyword}")')
            if menu:
                print(f"  Found menu: {keyword}")
                await menu.click()
                await page.wait_for_load_state('networkidle')
                found_menu = True
                break
        
        if not found_menu:
            print("  [INFO] Trying direct URLs...")
            # 직접 URL 시도
            possible_urls = [
                "/npbs/openData/main.web",
                "/npbs/d/m/000/moveBoardView?menuId=npe0000002450",
                "/npbs/reference/main.web",
                "/npbs/e/b/101/npeb101m01.web"
            ]
            
            for url_path in possible_urls:
                try:
                    await page.goto(self.base_url + url_path, wait_until='networkidle')
                    await page.wait_for_timeout(2000)
                    
                    # 다운로드 관련 요소 확인
                    download_elements = await page.query_selector_all('a[href*="download"], a[href*="excel"], button:has-text("다운로드")')
                    if download_elements:
                        print(f"  Found download page at: {url_path}")
                        found_menu = True
                        break
                except:
                    continue
        
        return found_menu
    
    async def analyze_download_categories(self, page):
        """다운로드 가능한 카테고리 분석"""
        print("\n[ANALYSIS] Analyzing download categories...")
        
        categories = []
        
        # 카테고리 탭이나 메뉴 찾기
        tab_selectors = [
            '.tab-menu li',
            '.category-list li',
            '.menu-tab a',
            'ul.tabs li',
            '.board-tab li'
        ]
        
        for selector in tab_selectors:
            tabs = await page.query_selector_all(selector)
            if tabs:
                print(f"  Found {len(tabs)} categories")
                for tab in tabs:
                    text = await tab.text_content()
                    if text:
                        categories.append(text.strip())
                        print(f"    - {text.strip()}")
                break
        
        # 테이블이나 리스트에서 다운로드 항목 찾기
        download_items = await page.query_selector_all('tr:has(a[href*="download"]), tr:has(a[href*="excel"]), tr:has(button:has-text("다운로드"))')
        
        if download_items:
            print(f"\n  Found {len(download_items)} downloadable items")
            
            # 처음 5개만 표시
            for i, item in enumerate(download_items[:5]):
                item_text = await item.text_content()
                if item_text:
                    # 첫 100자만 표시
                    print(f"    {i+1}. {item_text[:100].strip()}...")
        
        return categories
    
    async def download_facility_info(self, page):
        """요양기관 정보 다운로드"""
        print("\n" + "="*60)
        print("  [DOWNLOAD 1] 요양기관 정보")
        print("="*60)
        
        try:
            # 요양기관 정보 찾기
            facility_keywords = ["요양기관", "장기요양기관", "시설현황", "기관현황"]
            
            download_link = None
            for keyword in facility_keywords:
                # 링크 찾기
                link = await page.query_selector(f'a:has-text("{keyword}")')
                if link:
                    # 다운로드 링크인지 확인
                    href = await link.get_attribute('href')
                    if href and ('download' in href or 'excel' in href or '.xls' in href):
                        download_link = link
                        print(f"  Found download link: {keyword}")
                        break
                
                # 같은 행에 다운로드 버튼이 있는지 확인
                row = await page.query_selector(f'tr:has-text("{keyword}")')
                if row:
                    download_btn = await row.query_selector('a[href*="download"], button:has-text("다운로드"), a[href*="excel"]')
                    if download_btn:
                        download_link = download_btn
                        print(f"  Found download button for: {keyword}")
                        break
            
            if download_link:
                # 다운로드 실행
                await self.execute_download(page, download_link, "facility_info")
            else:
                print("  [INFO] Facility info download not found")
                
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
    
    async def download_service_codes(self, page):
        """급여제공코드 다운로드"""
        print("\n" + "="*60)
        print("  [DOWNLOAD 2] 급여제공코드")
        print("="*60)
        
        try:
            # 급여제공코드 관련 항목 찾기
            code_keywords = ["급여제공코드", "급여코드", "서비스코드", "청구코드"]
            
            download_link = None
            for keyword in code_keywords:
                link = await page.query_selector(f'a:has-text("{keyword}")')
                if link:
                    href = await link.get_attribute('href')
                    if href and ('download' in href or 'excel' in href):
                        download_link = link
                        print(f"  Found download link: {keyword}")
                        break
                
                # 테이블 행에서 찾기
                row = await page.query_selector(f'tr:has-text("{keyword}")')
                if row:
                    download_btn = await row.query_selector('a[href*="download"], button:has-text("다운로드")')
                    if download_btn:
                        download_link = download_btn
                        print(f"  Found download button for: {keyword}")
                        break
            
            if download_link:
                await self.execute_download(page, download_link, "service_codes")
            else:
                print("  [INFO] Service codes download not found")
                
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
    
    async def download_statistics(self, page):
        """통계자료 다운로드"""
        print("\n" + "="*60)
        print("  [DOWNLOAD 3] 통계자료")
        print("="*60)
        
        try:
            # 통계자료 관련 항목 찾기
            stat_keywords = ["통계", "현황", "연보", "월보"]
            
            downloaded_count = 0
            max_downloads = 2  # 2개만 다운로드 (차단 방지)
            
            for keyword in stat_keywords:
                if downloaded_count >= max_downloads:
                    break
                
                # 해당 키워드를 포함하는 모든 행 찾기
                rows = await page.query_selector_all(f'tr:has-text("{keyword}")')
                
                for row in rows[:1]:  # 각 카테고리에서 1개씩만
                    if downloaded_count >= max_downloads:
                        break
                    
                    # 행 내용 확인
                    row_text = await row.text_content()
                    print(f"  Found: {row_text[:80].strip()}...")
                    
                    # 다운로드 링크 찾기
                    download_btn = await row.query_selector('a[href*="download"], a[href*="excel"], button:has-text("다운로드")')
                    
                    if download_btn:
                        await self.execute_download(page, download_btn, f"statistics_{keyword}_{downloaded_count}")
                        downloaded_count += 1
                        
                        # 다운로드 간 대기 (차단 방지)
                        await page.wait_for_timeout(3000)
            
            print(f"  Total downloaded: {downloaded_count} files")
            
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
    
    async def execute_download(self, page, element, file_prefix):
        """다운로드 실행"""
        try:
            print(f"    Downloading {file_prefix}...")
            
            # 다운로드 이벤트 준비
            download_promise = page.wait_for_event('download', timeout=10000)
            
            # 요소 클릭
            await element.click()
            
            try:
                # 다운로드 대기
                download = await download_promise
                
                # 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 원본 파일명 가져오기
                suggested_filename = download.suggested_filename
                extension = suggested_filename.split('.')[-1] if '.' in suggested_filename else 'xlsx'
                
                filename = f"{file_prefix}_{timestamp}.{extension}"
                filepath = os.path.join(self.download_dir, filename)
                
                await download.save_as(filepath)
                print(f"    [SUCCESS] Saved: {filename}")
                
                return filepath
                
            except asyncio.TimeoutError:
                print(f"    [INFO] Download timeout - may be generating or requires additional action")
                
                # JavaScript 함수 직접 호출 시도
                await page.evaluate('''() => {
                    if (typeof doDownload === 'function') doDownload();
                    if (typeof excelDownload === 'function') excelDownload();
                    if (typeof fileDownload === 'function') fileDownload();
                }''')
                
                await page.wait_for_timeout(3000)
                
        except Exception as e:
            print(f"    [ERROR] Download failed: {str(e)}")
            
        return None
    
    async def navigate_pages(self, page):
        """페이지 네비게이션 (2페이지만)"""
        print("\n[PAGINATION] Checking for multiple pages...")
        
        # 페이지네이션 확인
        pagination = await page.query_selector('.pagination, .paging, .page-list')
        
        if pagination:
            print("  Pagination found")
            
            # 2페이지로 이동
            page2_link = await page.query_selector('a:has-text("2")')
            if page2_link:
                print("  Moving to page 2...")
                await page2_link.click()
                await page.wait_for_load_state('networkidle')
                await page.wait_for_timeout(3000)  # 차단 방지
                
                # 2페이지에서도 다운로드 시도
                await self.download_statistics(page)
        else:
            print("  No pagination found")
    
    async def run(self):
        """메인 실행"""
        await self.initialize_directories()
        
        print("\n" + "="*70)
        print("   장기요양보험 정보 다운로드 자동화")
        print("="*70)
        print("\n목표: 요양기관 정보, 급여코드, 통계자료 다운로드")
        print("전략: 2페이지씩, 3초 간격으로 안전하게 수집\n")
        
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
                # 정보 다운로드 페이지 찾기
                found = await self.find_info_download_page(page)
                
                if found:
                    # 스크린샷 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    await page.screenshot(
                        path=f"{self.screenshots_dir}/info_download_page_{timestamp}.png",
                        full_page=True
                    )
                    
                    # 카테고리 분석
                    categories = await self.analyze_download_categories(page)
                    
                    # 다운로드 실행 (3초 간격)
                    await self.download_facility_info(page)
                    await page.wait_for_timeout(3000)
                    
                    await self.download_service_codes(page)
                    await page.wait_for_timeout(3000)
                    
                    await self.download_statistics(page)
                    await page.wait_for_timeout(3000)
                    
                    # 2페이지 확인
                    await self.navigate_pages(page)
                    
                else:
                    print("\n[WARNING] Info download page not found")
                    print("Please check the screenshot for manual navigation")
                
                # 결과 요약
                print("\n" + "="*70)
                print("   다운로드 완료")
                print("="*70)
                print(f"  Downloads saved to: {self.download_dir}")
                print(f"  Screenshots saved to: {self.screenshots_dir}")
                
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
    downloader = LongTermCareInfoDownloader()
    await downloader.run()

if __name__ == "__main__":
    print("""
    ============================================
       장기요양보험 정보 다운로드 자동화
    ============================================
    대상: 요양기관 정보, 급여코드, 통계자료
    방법: 안전한 다운로드 (2페이지, 3초 간격)
    ============================================
    """)
    
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
장기요양보험 통합 다운로드 스크립트
여러 download_all_regions 스크립트들을 하나로 통합
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import time
from typing import Optional, List, Dict

class LongTermCareUnifiedDownloader:
    """장기요양보험 사이트 통합 다운로드 자동화"""
    
    def __init__(self, mode='headless', download_dir='downloads/longtermcare'):
        """
        Args:
            mode: 'headless' 또는 'browser' 모드
            download_dir: 다운로드 디렉토리 경로
        """
        self.base_url = "https://longtermcare.or.kr"
        self.search_url = "/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
        self.download_dir = download_dir
        self.mode = mode
        self.regions = self._get_all_regions()
        
    def _get_all_regions(self) -> Dict[str, str]:
        """모든 지역 코드와 이름 반환"""
        return {
            '11': '서울특별시',
            '26': '부산광역시', 
            '27': '대구광역시',
            '28': '인천광역시',
            '29': '광주광역시',
            '30': '대전광역시',
            '31': '울산광역시',
            '36': '세종특별자치시',
            '41': '경기도',
            '42': '강원도',
            '43': '충청북도',
            '44': '충청남도',
            '45': '전라북도',
            '46': '전라남도',
            '47': '경상북도',
            '48': '경상남도',
            '50': '제주특별자치도'
        }
    
    async def setup_browser(self, playwright):
        """브라우저 설정"""
        os.makedirs(self.download_dir, exist_ok=True)
        
        browser_args = {
            'headless': self.mode == 'headless',
            'args': ['--disable-blink-features=AutomationControlled'],
            'downloads_path': self.download_dir
        }
        
        browser = await playwright.chromium.launch(**browser_args)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        page = await context.new_page()
        return browser, context, page
    
    async def search_region(self, page, region_code: str, region_name: str):
        """특정 지역 검색 및 결과 확인"""
        print(f"\n[검색] {region_name} (코드: {region_code})")
        
        # 페이지 로드
        url = self.base_url + self.search_url
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # 시도 선택
        await page.select_option('select#siDoCd', region_code)
        await page.wait_for_timeout(1000)
        
        # 검색 버튼 클릭
        search_button = await page.query_selector('button.btn_search, a.btn_search')
        if search_button:
            await search_button.click()
            await page.wait_for_timeout(3000)
            
            # 결과 확인
            result_count = await self._get_result_count(page)
            return result_count > 0
        
        return False
    
    async def _get_result_count(self, page) -> int:
        """검색 결과 수 확인"""
        try:
            count_element = await page.query_selector('.total_num, .result_count')
            if count_element:
                count_text = await count_element.inner_text()
                # 숫자 추출
                import re
                numbers = re.findall(r'\d+', count_text.replace(',', ''))
                if numbers:
                    return int(numbers[0])
        except:
            pass
        return 0
    
    async def download_excel(self, page, region_name: str) -> bool:
        """엑셀 다운로드 실행"""
        try:
            # 엑셀 다운로드 버튼 찾기
            excel_button = await page.query_selector(
                'button[onclick*="excel"], a[onclick*="excel"], button.btn_excel'
            )
            
            if excel_button:
                # 다운로드 시작
                async with page.expect_download() as download_info:
                    await excel_button.click()
                    download = await download_info.value
                    
                    # 파일 저장
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{region_name}_{timestamp}.xlsx"
                    filepath = os.path.join(self.download_dir, filename)
                    
                    await download.save_as(filepath)
                    print(f"  ✓ 다운로드 완료: {filename}")
                    return True
        except Exception as e:
            print(f"  ✗ 다운로드 실패: {e}")
        
        return False
    
    async def download_all_regions(self, regions: Optional[List[str]] = None):
        """모든 지역 또는 지정된 지역 다운로드"""
        async with async_playwright() as playwright:
            browser, context, page = await self.setup_browser(playwright)
            
            try:
                # 다운로드할 지역 목록
                if regions:
                    target_regions = {k: v for k, v in self.regions.items() 
                                    if k in regions or v in regions}
                else:
                    target_regions = self.regions
                
                results = {}
                success_count = 0
                
                for code, name in target_regions.items():
                    # 검색 실행
                    has_results = await self.search_region(page, code, name)
                    
                    if has_results:
                        # 다운로드 실행
                        success = await self.download_excel(page, name)
                        if success:
                            success_count += 1
                            results[name] = 'success'
                        else:
                            results[name] = 'download_failed'
                    else:
                        results[name] = 'no_results'
                        print(f"  - {name}: 검색 결과 없음")
                    
                    # 다음 검색을 위한 대기
                    await page.wait_for_timeout(1000)
                
                # 결과 저장
                self._save_results(results, success_count)
                
            finally:
                await browser.close()
    
    async def download_single_region(self, region_identifier: str):
        """단일 지역 다운로드"""
        # 지역 코드 또는 이름으로 찾기
        region_code = None
        region_name = None
        
        if region_identifier in self.regions:
            region_code = region_identifier
            region_name = self.regions[region_identifier]
        else:
            for code, name in self.regions.items():
                if name == region_identifier:
                    region_code = code
                    region_name = name
                    break
        
        if not region_code:
            print(f"지역을 찾을 수 없습니다: {region_identifier}")
            return
        
        async with async_playwright() as playwright:
            browser, context, page = await self.setup_browser(playwright)
            
            try:
                has_results = await self.search_region(page, region_code, region_name)
                if has_results:
                    await self.download_excel(page, region_name)
                else:
                    print(f"{region_name}: 검색 결과가 없습니다")
            finally:
                await browser.close()
    
    def _save_results(self, results: Dict, success_count: int):
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(self.download_dir, f'download_results_{timestamp}.json')
        
        summary = {
            'timestamp': timestamp,
            'total_regions': len(results),
            'success_count': success_count,
            'failed_count': len(results) - success_count,
            'results': results
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 다운로드 완료 ===")
        print(f"성공: {success_count}/{len(results)}")
        print(f"결과 저장: {result_file}")


async def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='장기요양보험 데이터 다운로드')
    parser.add_argument('--mode', choices=['headless', 'browser'], 
                       default='headless', help='실행 모드')
    parser.add_argument('--regions', nargs='+', 
                       help='다운로드할 지역 코드 또는 이름 (없으면 전체)')
    parser.add_argument('--output', default='downloads/longtermcare',
                       help='다운로드 디렉토리')
    
    args = parser.parse_args()
    
    # 다운로더 초기화
    downloader = LongTermCareUnifiedDownloader(
        mode=args.mode,
        download_dir=args.output
    )
    
    # 다운로드 실행
    if args.regions and len(args.regions) == 1:
        await downloader.download_single_region(args.regions[0])
    else:
        await downloader.download_all_regions(args.regions)


if __name__ == "__main__":
    asyncio.run(main())
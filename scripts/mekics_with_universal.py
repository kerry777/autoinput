#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS에 범용 다운로더 적용
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.universal_downloader import UniversalDownloadEngine
from playwright.async_api import async_playwright
import json


async def mekics_universal_download():
    """MEK-ICS에 범용 다운로더 적용"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    downloads_dir = data_dir / "downloads"
    
    # 범용 다운로더 생성
    downloader = UniversalDownloadEngine(downloads_dir)
    
    # 설정 로드
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(downloads_dir)
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("쿠키 로드 완료")
        
        page = await context.new_page()
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 범용 다운로더 테스트")
            print("="*60)
            
            # 매출현황조회 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 조건 설정
            print("\n[2] 조회 조건 설정...")
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date());
                    }
                }
            """)
            
            # 조회 실행
            print("\n[3] 데이터 조회...")
            await page.keyboard.press('F2')
            await page.wait_for_timeout(10000)
            
            # 데이터 개수 확인
            data_count = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0) {
                        return grids[0].getStore().getCount();
                    }
                    return 0;
                }
            """)
            print(f"  조회된 데이터: {data_count:,}건")
            
            # 범용 다운로더로 다운로드 시도
            print("\n[4] 범용 다운로더 실행...")
            
            # 다운로드 트리거 액션 정의
            async def trigger_excel_download(page):
                """엑셀 다운로드 트리거"""
                await page.evaluate("""
                    () => {
                        // 방법 1: downloadExcelXml 호출
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length > 0 && grids[0].downloadExcelXml) {
                            window.SAVE_AUTH = "true";
                            grids[0].downloadExcelXml(false, '매출현황');
                            return;
                        }
                        
                        // 방법 2: 엑셀 버튼 클릭
                        const btn = Ext.getCmp('uniBaseButton-1196');
                        if(btn) {
                            btn.handler.call(btn.scope || btn);
                        }
                    }
                """)
            
            # 범용 다운로더 실행 (모든 전략 시도)
            results = await downloader.download(
                page,
                trigger_action=trigger_excel_download
            )
            
            # 결과 출력
            print("\n[5] 다운로드 결과:")
            print("-"*40)
            
            success_count = 0
            for strategy, result in results.items():
                if result:
                    success_count += 1
                    print(f"✓ {strategy}: {result}")
                else:
                    print(f"✗ {strategy}: 실패")
            
            print(f"\n성공한 전략: {success_count}개")
            
            # 다운로드 폴더 확인
            all_files = list(downloads_dir.glob("*.*"))
            all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            print(f"\n다운로드 폴더: {downloads_dir}")
            print(f"총 파일 수: {len(all_files)}개")
            
            if all_files:
                print("\n최근 파일:")
                for file in all_files[:5]:
                    size = file.stat().st_size / (1024 * 1024)
                    print(f"  - {file.name} ({size:.2f} MB)")
            
            # 스크린샷
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"universal_test_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n스크린샷: {screenshot}")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(mekics_universal_download())
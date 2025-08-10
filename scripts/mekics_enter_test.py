#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 - 엑셀 버튼 후 바로 엔터
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def enter_test():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(data_dir)
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            print("\nMEK-ICS 엔터키 테스트\n")
            
            # 페이지 접속
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 설정
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 (2021년부터)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date(2025, 7, 10));
                    }
                }
            """)
            print("설정 완료")
            
            # 조회
            await page.evaluate("""
                () => {
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) queryBtn.fireEvent('click', queryBtn);
                }
            """)
            await page.keyboard.press('F2')
            print("조회 실행...")
            
            # 로딩 대기
            print("로딩 대기...")
            for i in range(30):
                await page.wait_for_timeout(1000)
                
                # 그리드 데이터 확인
                grid_status = await page.evaluate("""
                    () => {
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length > 0) {
                            const store = grids[0].getStore();
                            return {
                                count: store.getCount(),
                                loading: store.isLoading()
                            };
                        }
                        return {count: 0, loading: false};
                    }
                """)
                
                if not grid_status['loading'] and grid_status['count'] > 0:
                    print(f"로딩 완료: {grid_status['count']}건 ({i+1}초)")
                    break
                
                if i % 3 == 0:
                    print(f"  로딩 중... ({i+1}초)")
            
            # 안정화 대기
            await page.wait_for_timeout(2000)
            
            # 엑셀 다운로드
            print("\n엑셀 다운로드 시도...")
            
            # 방법 1: 엑셀 버튼 클릭 후 즉시 엔터
            print("방법 1: 엑셀 버튼 + 즉시 엔터")
            
            # 다운로드 전 파일 목록
            before_files = set(os.listdir(data_dir))
            
            # 엑셀 버튼 클릭
            await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        excelBtn.fireEvent('click', excelBtn);
                        return true;
                    }
                    return false;
                }
            """)
            print("  엑셀 버튼 클릭")
            
            # 짧은 대기 후 엔터
            await page.wait_for_timeout(500)
            await page.keyboard.press('Enter')
            print("  엔터키 입력")
            
            # 파일 생성 확인
            print("\n파일 생성 대기...")
            for i in range(30):
                await page.wait_for_timeout(1000)
                
                current_files = set(os.listdir(data_dir))
                new_files = current_files - before_files
                
                if new_files:
                    print(f"\n[SUCCESS] 새 파일 생성! ({i+1}초)")
                    for filename in new_files:
                        filepath = os.path.join(data_dir, filename)
                        filesize = os.path.getsize(filepath) / 1024
                        print(f"  파일: {filename} ({filesize:.2f} KB)")
                    break
                
                if i % 5 == 4:
                    print(f"  대기 중... ({i+1}초)")
            else:
                print("\n파일이 생성되지 않음")
                
                # 방법 2: 여러 번 엔터
                print("\n방법 2: 여러 번 엔터키")
                for j in range(3):
                    await page.keyboard.press('Enter')
                    print(f"  엔터 {j+1}회")
                    await page.wait_for_timeout(1000)
                
                # 다시 확인
                await page.wait_for_timeout(5000)
                current_files = set(os.listdir(data_dir))
                new_files = current_files - before_files
                
                if new_files:
                    print("\n[SUCCESS] 새 파일 생성!")
                    for filename in new_files:
                        print(f"  파일: {filename}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"enter_test_{timestamp}.png"
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
    asyncio.run(enter_test())
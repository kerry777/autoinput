#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 v2 - expect_download 없이
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import os
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def download_v2():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        # 브라우저 다운로드 경로 설정
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(data_dir.absolute())
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
        
        page = await context.new_page()
        
        # CDP로 다운로드 경로 설정
        client = await page.context.new_cdp_session(page)
        await client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': str(data_dir.absolute())
        })
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 매출현황 다운로드 v2")
            print("="*60)
            
            # 1. 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 2. 조회 조건 설정
            print("\n[2] 조회 조건 설정...")
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정 (대용량)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date(2025, 7, 10));
                    }
                }
            """)
            print("   설정: LOT=아니오, 구분=전체, 기간=2021.01.01~2025.08.10")
            
            # 3. 조회 실행
            print("\n[3] 조회 실행...")
            await page.evaluate("""
                () => {
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) queryBtn.fireEvent('click', queryBtn);
                }
            """)
            await page.keyboard.press('F2')
            
            # 4. 로딩 대기
            print("\n[4] 데이터 로딩 대기...")
            for i in range(30):
                await page.wait_for_timeout(1000)
                
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
                    print(f"   로딩 완료: {grid_status['count']:,}건 ({i+1}초)")
                    break
                
                if i % 3 == 2:
                    print(f"   로딩 중... ({i+1}초)")
            
            # 안정화 대기
            await page.wait_for_timeout(2000)
            
            # 5. 다운로드 전 파일 목록 저장
            print("\n[5] 다운로드 준비...")
            before_files = {}
            for file in data_dir.iterdir():
                if file.is_file():
                    before_files[file.name] = file.stat().st_mtime
            
            # 사용자 다운로드 폴더도 체크
            user_downloads = Path.home() / "Downloads"
            user_before_files = {}
            for file in user_downloads.iterdir():
                if file.is_file() and (file.suffix in ['.csv', '.xlsx', '.xls']):
                    user_before_files[file.name] = file.stat().st_mtime
            
            # 6. 엑셀 버튼 클릭
            print("\n[6] 엑셀 다운로드...")
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
            print("   엑셀 버튼 클릭")
            
            # 7. 팝업 처리 - 여러 방법 시도
            print("\n[7] 팝업 처리...")
            
            # 방법 1: 짧은 대기 후 바로 엔터
            await page.wait_for_timeout(1000)
            print("   엔터키 입력 (1차)")
            await page.keyboard.press('Enter')
            
            # 방법 2: 팝업 확인 후 처리
            await page.wait_for_timeout(1000)
            
            popup_check = await page.evaluate("""
                () => {
                    // 모든 종류의 팝업 체크
                    const allPopups = [];
                    
                    // MessageBox
                    const msgBoxes = Ext.ComponentQuery.query('messagebox');
                    msgBoxes.forEach(box => {
                        if(box.isVisible && box.isVisible()) {
                            allPopups.push({
                                type: 'messagebox',
                                message: box.msg || '',
                                buttons: box.query('button').map(btn => ({
                                    text: btn.getText(),
                                    itemId: btn.itemId
                                }))
                            });
                        }
                    });
                    
                    // Window
                    const windows = Ext.ComponentQuery.query('window');
                    windows.forEach(win => {
                        if(win.isVisible && win.isVisible() && win.modal) {
                            allPopups.push({
                                type: 'window',
                                title: win.title || '',
                                buttons: win.query('button').map(btn => ({
                                    text: btn.getText(),
                                    itemId: btn.itemId
                                }))
                            });
                        }
                    });
                    
                    return {
                        count: allPopups.length,
                        popups: allPopups
                    };
                }
            """)
            
            if popup_check['count'] > 0:
                print(f"   팝업 {popup_check['count']}개 감지")
                for popup in popup_check['popups']:
                    print(f"     - 타입: {popup['type']}")
                    print(f"     - 버튼: {popup.get('buttons', [])}")
                
                # 엔터키 다시 입력
                print("   엔터키 입력 (2차)")
                await page.keyboard.press('Enter')
            else:
                print("   팝업 감지 안됨 - 엔터키 한 번 더")
                await page.keyboard.press('Enter')
            
            # 8. 파일 생성 모니터링
            print("\n[7] 다운로드 대기 (최대 60초)...")
            download_found = False
            
            for i in range(60):
                await page.wait_for_timeout(1000)
                
                # data_dir 확인
                new_files = []
                for file in data_dir.iterdir():
                    if file.is_file() and file.name not in before_files:
                        new_files.append(file)
                    elif file.is_file() and file.stat().st_mtime > before_files[file.name]:
                        new_files.append(file)
                
                if new_files:
                    print(f"\n   [SUCCESS] 새 파일 발견! ({i+1}초)")
                    for file in new_files:
                        size_mb = file.stat().st_size / (1024 * 1024)
                        print(f"   파일: {file.name}")
                        print(f"   크기: {size_mb:.2f} MB")
                        print(f"   경로: {file}")
                    download_found = True
                    break
                
                # 사용자 다운로드 폴더도 확인
                user_new_files = []
                for file in user_downloads.iterdir():
                    if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                        if file.name not in user_before_files:
                            user_new_files.append(file)
                        elif file.stat().st_mtime > user_before_files[file.name]:
                            user_new_files.append(file)
                
                if user_new_files:
                    print(f"\n   [SUCCESS] 사용자 다운로드 폴더에 새 파일! ({i+1}초)")
                    for file in user_new_files:
                        size_mb = file.stat().st_size / (1024 * 1024)
                        print(f"   파일: {file.name}")
                        print(f"   크기: {size_mb:.2f} MB")
                        print(f"   경로: {file}")
                    download_found = True
                    break
                
                if i % 5 == 4:
                    print(f"   대기 중... ({i+1}초)")
            
            if not download_found:
                print("\n   [FAIL] 60초 동안 새 파일이 생성되지 않음")
            
            # 9. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"download_v2_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n[8] 스크린샷: {screenshot}")
            
            print("\n" + "="*60)
            print("테스트 완료")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(download_v2())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 - dialog 이벤트 핸들링
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


async def download_working():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(data_dir.absolute())
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True  # 중요: 다운로드 허용
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # Dialog 핸들러 설정 - 자동으로 수락
        page.on('dialog', lambda dialog: dialog.accept())
        print("Dialog 핸들러 설정 완료")
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 매출현황 다운로드 (Dialog 처리)")
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
            
            # 5. 엑셀 다운로드
            print("\n[5] 엑셀 다운로드...")
            
            # 다운로드 이벤트 대기 준비
            download_promise = page.wait_for_event('download', timeout=60000)
            
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
            print("   엑셀 버튼 클릭")
            
            # Dialog가 있으면 자동으로 accept 됨 (위에서 설정한 핸들러에 의해)
            
            # 추가로 ExtJS MessageBox 처리 (dialog로 처리 안될 경우)
            await page.wait_for_timeout(2000)
            
            # ExtJS MessageBox 확인 및 처리
            msgbox_handled = await page.evaluate("""
                () => {
                    const msgBoxes = Ext.ComponentQuery.query('messagebox');
                    for(let msgBox of msgBoxes) {
                        if(msgBox.isVisible && msgBox.isVisible()) {
                            // '예' 또는 '확인' 버튼 찾기
                            const buttons = msgBox.query('button');
                            for(let btn of buttons) {
                                const itemId = btn.itemId || '';
                                const text = btn.getText ? btn.getText() : '';
                                
                                // '예' 버튼 우선
                                if(itemId === 'yes' || text === '예' || text === 'Yes') {
                                    btn.fireEvent('click', btn);
                                    return {handled: true, clicked: text || itemId};
                                }
                                // '확인' 버튼
                                if(itemId === 'ok' || text === '확인' || text === 'OK') {
                                    btn.fireEvent('click', btn);
                                    return {handled: true, clicked: text || itemId};
                                }
                            }
                            
                            // 첫 번째 버튼 클릭 (보통 확인)
                            if(buttons.length > 0) {
                                buttons[0].fireEvent('click', buttons[0]);
                                return {handled: true, clicked: 'first button'};
                            }
                        }
                    }
                    return {handled: false};
                }
            """)
            
            if msgbox_handled['handled']:
                print(f"   ExtJS MessageBox 처리: {msgbox_handled['clicked']}")
            else:
                # 엔터키 시도
                print("   엔터키 입력")
                await page.keyboard.press('Enter')
            
            try:
                # 다운로드 대기
                print("   다운로드 대기 중...")
                download = await download_promise
                
                # 파일 저장
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                suggested_filename = download.suggested_filename
                
                if suggested_filename.endswith('.csv'):
                    save_path = data_dir / f"sales_{timestamp}.csv"
                else:
                    save_path = data_dir / f"sales_{timestamp}.xlsx"
                
                await download.save_as(str(save_path))
                
                file_size = os.path.getsize(save_path)
                file_size_mb = file_size / (1024 * 1024)
                
                print(f"\n   [SUCCESS] 다운로드 완료!")
                print(f"   원본 파일명: {suggested_filename}")
                print(f"   저장 파일명: {save_path.name}")
                print(f"   파일 크기: {file_size_mb:.2f} MB")
                print(f"   저장 경로: {save_path}")
                
            except asyncio.TimeoutError:
                print("   [TIMEOUT] 다운로드 타임아웃 (60초)")
                
                # 사용자 다운로드 폴더 확인
                user_downloads = Path.home() / "Downloads"
                recent_files = []
                
                for file in user_downloads.iterdir():
                    if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                        if datetime.now().timestamp() - file.stat().st_mtime < 120:
                            recent_files.append(file)
                
                if recent_files:
                    print("\n   사용자 다운로드 폴더에서 발견:")
                    for file in recent_files:
                        size_mb = file.stat().st_size / (1024 * 1024)
                        print(f"     - {file.name} ({size_mb:.2f} MB)")
            
            # 6. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"download_working_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n[6] 스크린샷: {screenshot}")
            
            print("\n" + "="*60)
            print("완료!")
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
    asyncio.run(download_working())
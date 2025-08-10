#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 테스트 - 다양한 방법 시도
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


async def test_download():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 다운로드 디렉토리 절대 경로
    download_path = str(data_dir.absolute())
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
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
        
        # CDP 세션으로 다운로드 경로 설정
        client = await page.context.new_cdp_session(page)
        await client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': download_path
        })
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 다운로드 테스트")
            print(f"다운로드 경로: {download_path}")
            print("="*60)
            
            # 매출현황 페이지 접속
            print("\n[1] 매출현황 조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A", timeout=30000)
            await page.wait_for_timeout(5000)
            
            # 조회 조건 설정
            print("\n[2] 조회 조건 설정...")
            
            # LOT표시 여부 '아니오'
            await page.evaluate("""
                () => {
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 구분 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2025, 7, 1));
                        dateFields[1].setValue(new Date(2025, 7, 10));
                    }
                }
            """)
            
            # 조회 실행
            print("\n[3] 조회 실행...")
            await page.evaluate("""
                () => {
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) queryBtn.fireEvent('click', queryBtn);
                }
            """)
            await page.keyboard.press('F2')
            await page.wait_for_timeout(8000)
            
            # 조회 결과 확인
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        return {count: store.getCount()};
                    }
                    return {count: 0};
                }
            """)
            print(f"   조회 건수: {grid_data['count']}건")
            
            # 다운로드 전 파일 목록
            print("\n[4] 다운로드 전 파일 확인...")
            before_files = set(os.listdir(download_path))
            
            # 엑셀 다운로드 시도
            print("\n[5] 엑셀 다운로드 시도...")
            
            # 엑셀 버튼 클릭
            excel_clicked = await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        excelBtn.fireEvent('click', excelBtn);
                        return true;
                    }
                    return false;
                }
            """)
            
            if excel_clicked:
                print("   엑셀 버튼 클릭 완료")
                await page.wait_for_timeout(2000)
                
                # 팝업 처리 - '예' 버튼 클릭
                popup_result = await page.evaluate("""
                    () => {
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        if(msgBoxes.length > 0) {
                            const buttons = msgBoxes[0].query('button');
                            
                            // 모든 버튼 정보
                            const allButtons = buttons.map(b => ({
                                text: b.getText(),
                                itemId: b.itemId
                            }));
                            
                            // '예' 버튼 찾아서 클릭
                            for(let btn of buttons) {
                                if(btn.itemId === 'yes' || btn.getText() === '예') {
                                    // 직접 핸들러 실행
                                    const handler = btn.handler;
                                    if(handler) {
                                        handler.call(btn.scope || btn, btn);
                                    } else {
                                        btn.fireEvent('click', btn);
                                    }
                                    return {
                                        success: true,
                                        clicked: '예',
                                        allButtons: allButtons
                                    };
                                }
                            }
                            
                            return {
                                success: false,
                                allButtons: allButtons
                            };
                        }
                        return {success: false, noPopup: true};
                    }
                """)
                
                print(f"   팝업 처리: {popup_result}")
                
                # 다운로드 대기 (파일 시스템 확인)
                print("\n[6] 다운로드 대기 (30초)...")
                for i in range(30):
                    await page.wait_for_timeout(1000)
                    
                    # 새 파일 확인
                    current_files = set(os.listdir(download_path))
                    new_files = current_files - before_files
                    
                    if new_files:
                        print(f"\n   [SUCCESS] 새 파일 발견! ({i+1}초)")
                        for filename in new_files:
                            filepath = os.path.join(download_path, filename)
                            filesize = os.path.getsize(filepath)
                            print(f"   파일: {filename}")
                            print(f"   크기: {filesize/1024:.2f} KB")
                        break
                    
                    if i % 5 == 4:
                        print(f"   대기 중... ({i+1}초)")
                
                else:
                    print("\n   [FAIL] 30초 동안 새 파일이 생성되지 않음")
                    
                    # Chrome 다운로드 폴더 확인
                    downloads_folder = os.path.expanduser("~/Downloads")
                    print(f"\n   사용자 다운로드 폴더 확인: {downloads_folder}")
                    
                    recent_files = []
                    for filename in os.listdir(downloads_folder):
                        filepath = os.path.join(downloads_folder, filename)
                        if os.path.isfile(filepath):
                            mtime = os.path.getmtime(filepath)
                            if time.time() - mtime < 60:  # 최근 1분 이내 파일
                                recent_files.append((filename, mtime))
                    
                    if recent_files:
                        print("   최근 다운로드 파일:")
                        for filename, mtime in sorted(recent_files, key=lambda x: x[1], reverse=True)[:5]:
                            print(f"     - {filename} ({time.ctime(mtime)})")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"download_debug_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[7] 스크린샷: {screenshot_path}")
            
            print("\n" + "="*60)
            print("테스트 완료")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저를 30초 후 종료합니다...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_download())
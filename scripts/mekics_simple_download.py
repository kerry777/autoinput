#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 단순 다운로드 - 팝업에서 예 버튼만 클릭
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


async def simple_download():
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
            print("\n매출현황 간단 다운로드 테스트\n")
            
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
                    
                    // 날짜 (긴 기간 - CSV 팝업이 뜨도록)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2024, 0, 1));  // 2024년 1월 1일
                        dateFields[1].setValue(new Date(2025, 7, 10)); // 2025년 8월 10일
                    }
                }
            """)
            
            print("설정 완료: LOT=아니오, 구분=전체, 날짜=2024.01.01~2025.08.10")
            
            # 조회
            await page.evaluate("""
                () => {
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) queryBtn.fireEvent('click', queryBtn);
                }
            """)
            await page.keyboard.press('F2')
            print("조회 실행 (대용량 데이터)...")
            await page.wait_for_timeout(15000)  # 대용량 데이터 로딩 대기
            
            # 엑셀 버튼 클릭
            print("\n엑셀 버튼 클릭...")
            await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        excelBtn.fireEvent('click', excelBtn);
                    }
                }
            """)
            
            # 팝업 대기
            await page.wait_for_timeout(2000)
            
            # 팝업에서 예 버튼 찾기
            print("팝업 처리 중...")
            popup_info = await page.evaluate("""
                () => {
                    const msgBoxes = Ext.ComponentQuery.query('messagebox');
                    if(msgBoxes.length > 0) {
                        const msgBox = msgBoxes[0];
                        const buttons = msgBox.query('button');
                        
                        // 버튼 정보 수집
                        const buttonInfo = buttons.map(btn => ({
                            text: btn.getText(),
                            itemId: btn.itemId,
                            index: buttons.indexOf(btn)
                        }));
                        
                        // 예 버튼을 인덱스로 클릭 (보통 두 번째)
                        if(buttons.length >= 2) {
                            // 예 버튼은 보통 두 번째 (0: 확인, 1: 예, 2: 아니오, 3: 취소)
                            buttons[1].fireEvent('click', buttons[1]);
                            return {
                                clicked: true,
                                clickedIndex: 1,
                                clickedText: buttons[1].getText(),
                                allButtons: buttonInfo
                            };
                        }
                        
                        return {clicked: false, buttons: buttonInfo};
                    }
                    return {noPopup: true};
                }
            """)
            
            print(f"팝업 정보: {popup_info}")
            
            if popup_info.get('clicked'):
                print(f"클릭한 버튼: [{popup_info['clickedIndex']}] {popup_info['clickedText']}")
                
                # 다운로드 대기
                print("\n다운로드 대기 중...")
                
                # 파일 생성 확인
                download_started = False
                for i in range(30):
                    await page.wait_for_timeout(1000)
                    
                    # 다운로드 폴더 확인
                    files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
                    recent_files = []
                    
                    for file in files:
                        mtime = file.stat().st_mtime
                        if datetime.now().timestamp() - mtime < 60:  # 1분 이내
                            recent_files.append(file)
                    
                    if recent_files:
                        print(f"\n다운로드 완료! ({i+1}초)")
                        for file in recent_files:
                            size_kb = file.stat().st_size / 1024
                            print(f"  파일: {file.name} ({size_kb:.2f} KB)")
                        download_started = True
                        break
                    
                    if i % 5 == 4:
                        print(f"  대기 중... ({i+1}초)")
                
                if not download_started:
                    print("\n다운로드가 시작되지 않았습니다.")
                    
                    # 사용자 다운로드 폴더도 확인
                    user_downloads = Path.home() / "Downloads"
                    recent = list(user_downloads.glob("*.csv")) + list(user_downloads.glob("*.xlsx"))
                    
                    print(f"\n사용자 다운로드 폴더 확인: {user_downloads}")
                    for file in recent[:5]:
                        mtime = file.stat().st_mtime
                        if datetime.now().timestamp() - mtime < 120:
                            print(f"  최근 파일: {file.name}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"simple_test_{timestamp}.png"
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
    asyncio.run(simple_download())
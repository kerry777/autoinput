#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 최종 버전
- 팝업 클릭으로 포커스 주고 엔터
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


async def download_final():
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
            print("\n" + "="*60)
            print("MEK-ICS 매출현황 다운로드 (최종 버전)")
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
                    
                    // 날짜 설정 (2021년부터 - 대용량)
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
            
            # 다운로드 이벤트 대기와 함께 처리
            try:
                async with page.expect_download(timeout=120000) as download_info:
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
                    
                    # 팝업 대기
                    await page.wait_for_timeout(2000)
                    
                    # 팝업 확인 및 클릭
                    popup_info = await page.evaluate("""
                        () => {
                            const msgBoxes = Ext.ComponentQuery.query('messagebox');
                            if(msgBoxes.length > 0) {
                                const msgBox = msgBoxes[0];
                                if(msgBox.isVisible && msgBox.isVisible()) {
                                    // 팝업의 엘리먼트 가져오기
                                    const el = msgBox.getEl();
                                    if(el) {
                                        // 팝업 중앙 좌표 계산
                                        const box = el.getBox();
                                        const x = box.x + box.width / 2;
                                        const y = box.y + box.height / 2;
                                        
                                        // 버튼 정보
                                        const buttons = msgBox.query('button').map(btn => ({
                                            text: btn.getText(),
                                            itemId: btn.itemId
                                        }));
                                        
                                        return {
                                            hasPopup: true,
                                            x: x,
                                            y: y,
                                            buttons: buttons,
                                            message: msgBox.msg || ''
                                        };
                                    }
                                }
                            }
                            return {hasPopup: false};
                        }
                    """)
                    
                    if popup_info['hasPopup']:
                        print(f"   CSV 팝업 감지")
                        print(f"   메시지: {popup_info.get('message', '')[:50]}")
                        print(f"   버튼: {popup_info.get('buttons', [])}")
                        
                        # 팝업 클릭 (포커스 주기)
                        if popup_info.get('x') and popup_info.get('y'):
                            print(f"   팝업 클릭 (포커스): ({popup_info['x']}, {popup_info['y']})")
                            await page.mouse.click(popup_info['x'], popup_info['y'])
                            await page.wait_for_timeout(500)
                        
                        # 엔터키 입력
                        print("   엔터키 입력 (확인)")
                        await page.keyboard.press('Enter')
                        
                        # 추가 대기
                        await page.wait_for_timeout(3000)
                    else:
                        print("   팝업 없음 (소량 데이터)")
                        # 소량일 경우 바로 다운로드 시작
                        await page.wait_for_timeout(2000)
                
                # 다운로드 완료
                download = await download_info.value
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if download.suggested_filename.endswith('.csv'):
                    save_path = data_dir / f"sales_final_{timestamp}.csv"
                else:
                    save_path = data_dir / f"sales_final_{timestamp}.xlsx"
                
                await download.save_as(str(save_path))
                
                file_size = os.path.getsize(save_path)
                file_size_mb = file_size / (1024 * 1024)
                
                print(f"\n   [SUCCESS] 다운로드 완료!")
                print(f"   파일: {save_path.name}")
                print(f"   크기: {file_size_mb:.2f} MB")
                
            except asyncio.TimeoutError:
                print("   [TIMEOUT] 다운로드 타임아웃")
                
                # 파일 시스템 확인
                files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
                recent = []
                for file in files:
                    if datetime.now().timestamp() - file.stat().st_mtime < 120:
                        recent.append(file)
                
                if recent:
                    print("\n   최근 생성 파일:")
                    for file in recent:
                        size_mb = file.stat().st_size / (1024 * 1024)
                        print(f"     - {file.name} ({size_mb:.2f} MB)")
            
            # 6. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"final_{timestamp}.png"
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
    asyncio.run(download_final())
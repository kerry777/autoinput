#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 - 로딩 팝업 대기 처리
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


async def download_with_loading():
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
            print("MEK-ICS 매출현황 다운로드 (로딩 대기 포함)")
            print("="*60)
            
            # 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 설정
            print("\n[2] 조회 조건 설정...")
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정 (대용량 - 2021년부터)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));  // 2021년 1월 1일
                        dateFields[1].setValue(new Date(2025, 7, 10)); // 2025년 8월 10일
                    }
                }
            """)
            print("   설정: LOT=아니오, 구분=전체, 기간=2021.01.01~2025.08.10")
            
            # 조회 실행
            print("\n[3] 조회 실행...")
            await page.evaluate("""
                () => {
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) queryBtn.fireEvent('click', queryBtn);
                }
            """)
            await page.keyboard.press('F2')
            
            # 로딩 팝업 대기
            print("\n[4] 로딩 대기...")
            
            # 로딩 팝업이 나타났다가 사라질 때까지 대기
            loading_complete = False
            for i in range(60):  # 최대 60초 대기
                await page.wait_for_timeout(1000)
                
                # 로딩 상태 확인
                loading_status = await page.evaluate("""
                    () => {
                        // 로딩 마스크 확인
                        const masks = Ext.ComponentQuery.query('loadmask');
                        const loadingMasks = masks.filter(m => m.isVisible && m.isVisible());
                        
                        // MessageBox 로딩 팝업 확인
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        const loadingBoxes = msgBoxes.filter(box => {
                            if(!box.isVisible()) return false;
                            const msg = box.msg || '';
                            return msg.includes('로딩') || msg.includes('처리') || 
                                   msg.includes('Loading') || msg.includes('Processing');
                        });
                        
                        // Window 타입 로딩 팝업 확인
                        const windows = Ext.ComponentQuery.query('window');
                        const loadingWindows = windows.filter(win => {
                            if(!win.isVisible()) return false;
                            const title = win.title || '';
                            const html = win.html || '';
                            return title.includes('로딩') || title.includes('처리') ||
                                   html.includes('로딩') || html.includes('처리');
                        });
                        
                        // 그리드 데이터 확인
                        const grids = Ext.ComponentQuery.query('grid');
                        let gridData = {count: 0, loading: false};
                        if(grids.length > 0) {
                            const store = grids[0].getStore();
                            gridData = {
                                count: store.getCount(),
                                loading: store.isLoading()
                            };
                        }
                        
                        return {
                            hasLoadingMask: loadingMasks.length > 0,
                            hasLoadingBox: loadingBoxes.length > 0,
                            hasLoadingWindow: loadingWindows.length > 0,
                            gridLoading: gridData.loading,
                            gridCount: gridData.count,
                            isLoading: loadingMasks.length > 0 || loadingBoxes.length > 0 || 
                                      loadingWindows.length > 0 || gridData.loading
                        };
                    }
                """)
                
                if loading_status['isLoading']:
                    print(f"   로딩 중... ({i+1}초)")
                elif loading_status['gridCount'] > 0:
                    print(f"   로딩 완료! 데이터 {loading_status['gridCount']}건")
                    loading_complete = True
                    break
                else:
                    if i % 5 == 0:
                        print(f"   대기 중... ({i+1}초)")
            
            if not loading_complete:
                print("   [WARNING] 로딩 확인 타임아웃")
            
            # 추가 안정화 대기
            await page.wait_for_timeout(2000)
            
            # 조회 결과 확인
            print("\n[5] 조회 결과 확인...")
            result = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        return {
                            count: store.getCount(),
                            total: store.getTotalCount()
                        };
                    }
                    return {count: 0};
                }
            """)
            print(f"   조회 건수: {result['count']}건")
            
            # 엑셀 다운로드
            print("\n[6] 엑셀 다운로드...")
            
            # 다운로드 이벤트와 함께 처리
            try:
                async with page.expect_download(timeout=60000) as download_info:
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
                    
                    # CSV 팝업 대기 및 처리
                    await page.wait_for_timeout(3000)  # 팝업 나타날 시간 대기
                    
                    # 팝업 확인 (여러 방법으로)
                    popup_check = await page.evaluate("""
                        () => {
                            // MessageBox 확인
                            const msgBoxes = Ext.ComponentQuery.query('messagebox');
                            for(let msgBox of msgBoxes) {
                                if(msgBox.isVisible && msgBox.isVisible()) {
                                    const buttons = msgBox.query('button');
                                    
                                    // 버튼 정보 수집
                                    const buttonInfo = buttons.map(btn => ({
                                        text: btn.getText ? btn.getText() : '',
                                        itemId: btn.itemId || ''
                                    }));
                                    
                                    // 메시지 내용
                                    const message = msgBox.msg || msgBox.message || '';
                                    
                                    return {
                                        hasPopup: true,
                                        type: 'messagebox',
                                        message: message,
                                        buttons: buttonInfo
                                    };
                                }
                            }
                            
                            // Window 타입 팝업 확인
                            const windows = Ext.ComponentQuery.query('window');
                            for(let win of windows) {
                                if(win.isVisible && win.isVisible() && win.modal) {
                                    const buttons = win.query('button');
                                    
                                    const buttonInfo = buttons.map(btn => ({
                                        text: btn.getText ? btn.getText() : '',
                                        itemId: btn.itemId || ''
                                    }));
                                    
                                    return {
                                        hasPopup: true,
                                        type: 'window',
                                        title: win.title || '',
                                        buttons: buttonInfo
                                    };
                                }
                            }
                            
                            return {hasPopup: false};
                        }
                    """)
                    
                    if popup_check.get('hasPopup'):
                        print(f"   CSV 팝업 감지: {popup_check.get('message', '')[:50]}")
                        print(f"   버튼들: {popup_check.get('buttons', [])}")
                        
                        # 엔터키로 확인
                        print("   엔터키로 팝업 확인...")
                        await page.keyboard.press('Enter')
                        
                        # 추가 대기
                        await page.wait_for_timeout(1000)
                        
                        # 팝업이 닫혔는지 확인
                        popup_closed = await page.evaluate("""
                            () => {
                                const msgBoxes = Ext.ComponentQuery.query('messagebox');
                                return msgBoxes.filter(box => box.isVisible()).length === 0;
                            }
                        """)
                        
                        if popup_closed:
                            print("   팝업 닫힘 확인")
                        else:
                            print("   [WARNING] 팝업이 아직 열려있음")
                    else:
                        print("   팝업 없음 (소량 데이터)")
                    
                    # 다운로드 대기
                    await page.wait_for_timeout(5000)
                
                # 다운로드 완료
                download = await download_info.value
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if download.suggested_filename.endswith('.csv'):
                    save_path = data_dir / f"sales_{timestamp}.csv"
                else:
                    save_path = data_dir / f"sales_{timestamp}.xlsx"
                
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
                        print(f"     - {file.name}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"loading_test_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n[7] 스크린샷: {screenshot}")
            
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
    asyncio.run(download_with_loading())
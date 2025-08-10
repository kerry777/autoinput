#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 다운로드 전용 스크립트
- 다운로드에 집중하여 안정성 향상
- 여러 다운로드 방법 시도
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, date
import time

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def download_sales_report():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        # 다운로드를 위해 헤드리스 모드 해제
        browser = await p.chromium.launch(
            headless=False,  # 다운로드 확인을 위해 브라우저 표시
            downloads_path=str(data_dir)
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        # 다운로드 핸들러 설정
        context.on("download", lambda download: print(f"   [DOWNLOAD] 시작: {download.suggested_filename}"))
        
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 타임아웃을 2분으로 설정
        page.set_default_timeout(120000)
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 매출현황 다운로드 전용")
            print("="*60)
            
            # 1. 매출현황 조회 페이지 접속
            print("\n[1] 매출현황 조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do", timeout=30000)
            await page.wait_for_timeout(3000)
            
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A", timeout=30000)
            await page.wait_for_timeout(5000)
            print("   페이지 로드 완료")
            
            # 2. 설정 (LOT표시 여부, 국내/해외 구분)
            print("\n[2] 조회 조건 설정...")
            
            # LOT표시 여부를 '아니오'로
            await page.evaluate("""
                () => {
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) {
                        noRadio.setValue(true);
                    }
                }
            """)
            
            # 국내/해외 구분을 '전체'로
            await page.evaluate("""
                () => {
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) {
                        allRadio.setValue(true);
                    }
                }
            """)
            
            # 3. 날짜 설정 (짧은 기간으로 테스트)
            print("\n[3] 날짜 설정 (2025.08.01 ~ 2025.08.10)...")
            
            await page.evaluate("""
                () => {
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    
                    if(dateFields.length >= 2) {
                        // 시작일
                        dateFields[0].setValue(new Date(2025, 7, 1));  // 2025년 8월 1일
                        // 종료일
                        dateFields[1].setValue(new Date(2025, 7, 10)); // 2025년 8월 10일
                    }
                }
            """)
            
            print("   날짜 설정 완료")
            
            # 4. 조회 실행
            print("\n[4] 조회 실행...")
            
            await page.evaluate("""
                () => {
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) {
                        queryBtn.fireEvent('click', queryBtn);
                    }
                }
            """)
            
            await page.keyboard.press('F2')
            
            # 데이터 로딩 대기
            print("\n[5] 데이터 로딩 대기...")
            await page.wait_for_timeout(10000)
            
            # 조회 결과 확인
            grid_data = await page.evaluate("""
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
            
            print(f"   조회 완료: {grid_data['count']}건")
            
            # 5. 다운로드 시도
            print("\n[6] 엑셀 다운로드 시도...")
            
            # 다운로드 시작 시간 기록
            download_start_time = time.time()
            
            # 방법 1: 엑셀 버튼 클릭 후 다운로드 대기
            print("   방법 1: 엑셀 버튼 클릭...")
            
            try:
                # 다운로드 이벤트와 함께 엑셀 버튼 클릭
                async with page.expect_download(timeout=120000) as download_info:  # 2분 대기
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
                    
                    print("   엑셀 버튼 클릭 완료")
                    
                    # 팝업 처리
                    await page.wait_for_timeout(2000)
                    
                    popup_handled = await page.evaluate("""
                        () => {
                            // MessageBox 팝업 확인
                            const msgBoxes = Ext.ComponentQuery.query('messagebox');
                            if(msgBoxes.length > 0) {
                                const msgBox = msgBoxes[0];
                                const buttons = msgBox.query('button');
                                
                                // 버튼 정보 수집
                                const buttonInfo = buttons.map(btn => ({
                                    text: btn.getText ? btn.getText() : '',
                                    itemId: btn.itemId || ''
                                }));
                                
                                // CSV 다운로드 팝업에서는 '예' 버튼을 클릭해야 함
                                for(let btn of buttons) {
                                    const text = btn.getText ? btn.getText() : '';
                                    const itemId = btn.itemId || '';
                                    
                                    // '예' 버튼 우선 클릭
                                    if(text === '예' || text === 'Yes' || itemId === 'yes') {
                                        btn.fireEvent('click', btn);
                                        return {
                                            clicked: true,
                                            buttonText: text,
                                            itemId: itemId,
                                            allButtons: buttonInfo
                                        };
                                    }
                                }
                                
                                // itemId로 찾기 (yes, ok 등)
                                for(let btn of buttons) {
                                    const itemId = btn.itemId || '';
                                    if(itemId === 'yes' || itemId === 'ok') {
                                        btn.fireEvent('click', btn);
                                        return {
                                            clicked: true,
                                            buttonText: btn.getText ? btn.getText() : '',
                                            itemId: itemId,
                                            allButtons: buttonInfo
                                        };
                                    }
                                }
                                
                                // 첫 번째 버튼이 보통 확인 (마지막이 취소인 경우가 많음)
                                if(buttons.length === 2) {
                                    const firstBtn = buttons[0];
                                    const firstText = firstBtn.getText ? firstBtn.getText() : '';
                                    
                                    // 첫 번째가 취소가 아니면 클릭
                                    if(!firstText.includes('취소') && !firstText.includes('Cancel')) {
                                        firstBtn.fireEvent('click', firstBtn);
                                        return {
                                            clicked: true,
                                            buttonText: firstText,
                                            position: 'first',
                                            allButtons: buttonInfo
                                        };
                                    }
                                }
                                
                                return {clicked: false, allButtons: buttonInfo};
                            }
                            
                            return {clicked: false};
                        }
                    """)
                    
                    if popup_handled.get('clicked'):
                        print(f"   CSV 다운로드 팝업 확인 클릭: {popup_handled.get('buttonText', '')}")
                        if popup_handled.get('allButtons'):
                            print(f"   팝업 버튼들: {popup_handled['allButtons']}")
                    else:
                        print("   팝업 처리 실패")
                        if popup_handled.get('allButtons'):
                            print(f"   발견된 버튼들: {popup_handled['allButtons']}")
                    
                    # 추가 대기
                    await page.wait_for_timeout(3000)
                
                # 다운로드 완료
                download = await download_info.value
                
                # 파일 저장
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                suggested_filename = download.suggested_filename
                
                if suggested_filename.endswith('.csv'):
                    save_path = data_dir / f"sales_download_{timestamp}.csv"
                else:
                    save_path = data_dir / f"sales_download_{timestamp}.xlsx"
                
                await download.save_as(str(save_path))
                
                # 파일 크기 확인
                import os
                file_size = os.path.getsize(save_path)
                file_size_mb = file_size / (1024 * 1024)
                
                download_time = time.time() - download_start_time
                
                print(f"\n   [SUCCESS] 다운로드 완료!")
                print(f"   파일명: {save_path.name}")
                print(f"   파일 크기: {file_size_mb:.2f} MB")
                print(f"   소요 시간: {download_time:.1f}초")
                
            except asyncio.TimeoutError:
                print("   [TIMEOUT] 다운로드 타임아웃")
                
                # 방법 2: 키보드 단축키 시도
                print("\n   방법 2: Alt+E 단축키 시도...")
                await page.keyboard.press('Alt+E')
                await page.wait_for_timeout(3000)
                
                # 방법 3: 다른 엑셀 버튼 찾기
                print("\n   방법 3: 다른 엑셀 버튼 찾기...")
                other_excel = await page.evaluate("""
                    () => {
                        const buttons = Ext.ComponentQuery.query('button');
                        for(let btn of buttons) {
                            const tooltip = btn.tooltip || '';
                            const text = btn.getText ? btn.getText() : '';
                            
                            if(tooltip.includes('엑셀') || tooltip.includes('Excel') ||
                               text.includes('엑셀') || text.includes('Excel')) {
                                btn.fireEvent('click', btn);
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if other_excel:
                    print("   다른 엑셀 버튼 클릭")
                    await page.wait_for_timeout(5000)
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"download_test_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[7] 스크린샷: {screenshot_path}")
            
            print("\n" + "="*60)
            print("다운로드 테스트 완료")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저를 30초 후 종료합니다...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    print("매출현황 다운로드 테스트를 시작합니다...")
    asyncio.run(download_sales_report())
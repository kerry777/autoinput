#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 조회 - 대용량 데이터 (2021.01.01 ~ 오늘)
헤드리스 모드로 실행, 타임아웃 증가
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def run_long_range():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        # 헤드리스 모드로 실행
        browser = await p.chromium.launch(
            headless=True,  # 헤드리스 모드
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
        
        # 기본 타임아웃을 60초로 증가
        page.set_default_timeout(60000)
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 매출현황 조회 - 대용량 데이터")
            print("기간: 2021.01.01 ~ 오늘")
            print("모드: 헤드리스")
            print("="*60)
            
            # 1. 매출현황 조회 페이지 접속
            print("\n[1] 매출현황 조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do", timeout=30000)
            await page.wait_for_timeout(3000)
            
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A", timeout=30000)
            await page.wait_for_timeout(5000)
            print("   페이지 로드 완료")
            
            # 2. LOT표시 여부를 '아니오'로 설정
            print("\n[2] LOT표시 여부 설정...")
            lot_result = await page.evaluate("""
                () => {
                    // 사용자가 제공한 ID로 직접 찾기
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) {
                        noRadio.setValue(true);
                        return {success: true};
                    }
                    
                    // 라벨로 찾기
                    const radios = Ext.ComponentQuery.query('radiofield');
                    for(let radio of radios) {
                        if(radio.boxLabel === '아니오') {
                            radio.setValue(true);
                            return {success: true};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if lot_result['success']:
                print("   [OK] LOT표시 '아니오' 선택")
            
            # 3. 국내/해외 구분을 '전체'로 설정
            print("\n[3] 국내/해외 구분 설정...")
            div_result = await page.evaluate("""
                () => {
                    // 사용자가 제공한 ID로 직접 찾기
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) {
                        allRadio.setValue(true);
                        return {success: true};
                    }
                    
                    // 라벨로 찾기
                    const radios = Ext.ComponentQuery.query('radiofield');
                    for(let radio of radios) {
                        if(radio.boxLabel === '전체') {
                            radio.setValue(true);
                            return {success: true};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if div_result['success']:
                print("   [OK] 국내/해외 구분 '전체' 선택")
            
            # 4. 날짜 설정 (2021.01.01 ~ 오늘)
            today = date.today()
            from_date = "2021.01.01"
            to_date = today.strftime("%Y.%m.%d")
            
            print(f"\n[4] 매출일 설정 ({from_date} ~ {to_date})...")
            
            date_result = await page.evaluate(f"""
                () => {{
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    
                    if(dateFields.length >= 2) {{
                        // 시작일: 2021년 1월 1일
                        dateFields[0].setValue(new Date(2021, 0, 1));  // JavaScript에서 월은 0부터
                        
                        // 종료일: 오늘
                        const today = new Date({today.year}, {today.month - 1}, {today.day});
                        dateFields[1].setValue(today);
                        
                        return {{
                            success: true,
                            from: dateFields[0].getValue().toLocaleDateString('ko-KR'),
                            to: dateFields[1].getValue().toLocaleDateString('ko-KR')
                        }};
                    }}
                    
                    return {{success: false, error: 'Date fields not found'}};
                }}
            """)
            
            if date_result['success']:
                print(f"   [OK] 날짜 설정: {date_result['from']} ~ {date_result['to']}")
            else:
                print(f"   [FAIL] 날짜 설정 실패: {date_result.get('error', '')}")
            
            # 5. 조회 실행
            print("\n[5] 조회 실행 (대용량 데이터 로딩 예상)...")
            
            # 조회 버튼 클릭
            query_result = await page.evaluate("""
                () => {
                    // ID로 직접 찾기
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) {
                        queryBtn.fireEvent('click', queryBtn);
                        return {success: true};
                    }
                    
                    // 텍스트로 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('조회') && text.includes('F2')) {
                            btn.fireEvent('click', btn);
                            return {success: true};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if query_result['success']:
                print("   [OK] 조회 버튼 클릭")
            
            # F2 키도 누르기
            await page.keyboard.press('F2')
            print("   F2 키 입력")
            
            # 대용량 데이터 로딩을 위해 충분한 시간 대기
            print("\n[6] 데이터 로딩 중... (최대 3분 대기)")
            
            # 로딩 상태 체크 (10초마다 확인, 최대 18번 = 3분)
            for i in range(18):
                await page.wait_for_timeout(10000)  # 10초 대기
                
                # 로딩 상태 확인
                loading_status = await page.evaluate("""
                    () => {
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length > 0) {
                            const store = grids[0].getStore();
                            return {
                                loading: store.isLoading(),
                                count: store.getCount()
                            };
                        }
                        return {loading: false, count: 0};
                    }
                """)
                
                if not loading_status['loading'] and loading_status['count'] > 0:
                    print(f"   데이터 로딩 완료! ({(i+1)*10}초 소요)")
                    break
                else:
                    print(f"   로딩 중... ({(i+1)*10}초 경과, 현재 {loading_status['count']}건)")
            
            # 7. 조회 결과 확인
            print("\n[7] 조회 결과 확인...")
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        const count = store.getCount();
                        const total = store.getTotalCount();
                        
                        // 처음 10건과 마지막 5건 샘플
                        const firstItems = store.getData().items.slice(0, 10);
                        const lastItems = store.getData().items.slice(-5);
                        
                        const firstSample = firstItems.map(item => ({
                            SALE_DATE: item.data.SALE_DATE,
                            CUST_NAME: item.data.CUST_NAME,
                            ITEM_NAME: item.data.ITEM_NAME,
                            SALE_AMT: item.data.SALE_AMT
                        }));
                        
                        const lastSample = lastItems.map(item => ({
                            SALE_DATE: item.data.SALE_DATE,
                            CUST_NAME: item.data.CUST_NAME,
                            ITEM_NAME: item.data.ITEM_NAME,
                            SALE_AMT: item.data.SALE_AMT
                        }));
                        
                        return {
                            success: true,
                            count: count,
                            total: total,
                            firstSample: firstSample,
                            lastSample: lastSample
                        };
                    }
                    
                    return {success: false, count: 0};
                }
            """)
            
            if grid_data['success']:
                print(f"   [OK] 조회 완료: {grid_data['count']:,}건")
                print(f"   전체 건수: {grid_data.get('total', grid_data['count']):,}건")
                
                if grid_data.get('firstSample'):
                    print("\n   처음 10건:")
                    for i, record in enumerate(grid_data['firstSample'], 1):
                        print(f"     {i}. {record.get('SALE_DATE', '')} | {record.get('ITEM_NAME', '')[:30]}")
                
                if grid_data.get('lastSample'):
                    print("\n   마지막 5건:")
                    for i, record in enumerate(grid_data['lastSample'], 1):
                        print(f"     {i}. {record.get('SALE_DATE', '')} | {record.get('ITEM_NAME', '')[:30]}")
            else:
                print("   [FAIL] 조회 결과 없음")
            
            # 8. 엑셀 다운로드
            print("\n[8] 엑셀 다운로드 (대용량 파일)...")
            
            # 엑셀 버튼 클릭
            excel_result = await page.evaluate("""
                () => {
                    // ID로 직접 찾기
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        excelBtn.fireEvent('click', excelBtn);
                        return {success: true};
                    }
                    
                    // 아이콘 클래스로 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const iconEl = btn.getEl() ? btn.getEl().down('.icon-excel') : null;
                        if(iconEl) {
                            btn.fireEvent('click', btn);
                            return {success: true};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if excel_result['success']:
                print("   엑셀 버튼 클릭")
                
                # 팝업 대기
                await page.wait_for_timeout(3000)
                
                # CSV 다운로드 팝업 확인
                print("   CSV 다운로드 팝업 확인...")
                popup_result = await page.evaluate("""
                    () => {
                        // MessageBox 또는 Window 팝업 확인
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        const windows = Ext.ComponentQuery.query('window');
                        
                        // MessageBox 확인
                        if(msgBoxes.length > 0) {
                            const buttons = msgBoxes[0].query('button');
                            for(let btn of buttons) {
                                const text = btn.getText ? btn.getText() : '';
                                if(text === '확인' || text === 'OK') {
                                    btn.fireEvent('click', btn);
                                    return {found: true, clicked: true, text: text};
                                }
                            }
                        }
                        
                        // Window 확인
                        for(let win of windows) {
                            if(win.isVisible()) {
                                const buttons = win.query('button');
                                for(let btn of buttons) {
                                    const text = btn.getText ? btn.getText() : '';
                                    if(text === '확인' || text === 'OK') {
                                        btn.fireEvent('click', btn);
                                        return {found: true, clicked: true, text: text};
                                    }
                                }
                            }
                        }
                        
                        return {found: false};
                    }
                """)
                
                if popup_result['found'] and popup_result['clicked']:
                    print(f"   [OK] CSV 다운로드 팝업 확인 클릭")
                
                # 대용량 파일 다운로드 대기 (최대 10분)
                print("   대용량 파일 다운로드 대기 중... (최대 10분)")
                print("   [INFO] 서버에서 파일 생성 중...")
                
                # 다운로드 전에 추가 대기
                await page.wait_for_timeout(5000)
                
                try:
                    async with page.expect_download(timeout=600000) as download_info:  # 10분 타임아웃
                        # 다운로드 트리거 재시도
                        await page.wait_for_timeout(2000)
                        
                        # 다운로드가 시작되지 않으면 엑셀 버튼 다시 클릭
                        retry_excel = await page.evaluate("""
                            () => {
                                const excelBtn = Ext.getCmp('uniBaseButton-1196');
                                if(excelBtn && !excelBtn.disabled) {
                                    excelBtn.fireEvent('click', excelBtn);
                                    return {retry: true};
                                }
                                return {retry: false};
                            }
                        """)
                        
                        if retry_excel['retry']:
                            print("   [INFO] 엑셀 버튼 재클릭")
                        
                        await page.wait_for_timeout(3000)
                    
                    download = await download_info.value
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    # 파일 확장자 확인
                    suggested_filename = download.suggested_filename
                    if suggested_filename.endswith('.csv'):
                        save_path = data_dir / f"sales_2021_to_today_{timestamp}.csv"
                        print("   [INFO] CSV 형식으로 다운로드")
                    else:
                        save_path = data_dir / f"sales_2021_to_today_{timestamp}.xlsx"
                        print("   [INFO] Excel 형식으로 다운로드")
                    
                    await download.save_as(str(save_path))
                    
                    # 파일 크기 확인
                    import os
                    file_size = os.path.getsize(save_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    print(f"   [OK] 파일 저장 완료")
                    print(f"       파일명: {save_path.name}")
                    print(f"       파일 크기: {file_size_mb:.2f} MB")
                    
                except asyncio.TimeoutError:
                    print("   [WARNING] 다운로드 타임아웃 (10분 초과)")
                    print("   [INFO] 브라우저 다운로드 폴더 확인 중...")
                    
                    # 다운로드 폴더에서 최신 파일 확인
                    import os
                    import glob
                    
                    download_patterns = [
                        str(data_dir / "*.csv"),
                        str(data_dir / "*.xlsx"),
                        str(data_dir / "*.xls")
                    ]
                    
                    latest_file = None
                    latest_time = 0
                    
                    for pattern in download_patterns:
                        files = glob.glob(pattern)
                        for file in files:
                            file_time = os.path.getmtime(file)
                            if file_time > latest_time:
                                latest_time = file_time
                                latest_file = file
                    
                    if latest_file:
                        # 최근 2분 이내 파일인지 확인
                        import time
                        if time.time() - latest_time < 120:
                            file_size = os.path.getsize(latest_file)
                            file_size_mb = file_size / (1024 * 1024)
                            print(f"   [OK] 다운로드 파일 발견!")
                            print(f"       파일명: {os.path.basename(latest_file)}")
                            print(f"       파일 크기: {file_size_mb:.2f} MB")
                        else:
                            print("   [FAIL] 최근 다운로드 파일 없음")
                except Exception as e:
                    print(f"   [ERROR] 다운로드 중 오류: {e}")
            
            # 9. 스크린샷 (헤드리스 모드에서도 가능)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"long_range_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[9] 스크린샷: {screenshot_path}")
            
            print("\n" + "="*60)
            print("대용량 매출현황 조회 완료!")
            print(f"조회 기간: {from_date} ~ {to_date}")
            print(f"조회 건수: {grid_data.get('count', 0):,}건")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저 종료...")
            await browser.close()


if __name__ == "__main__":
    print("대용량 데이터 조회를 시작합니다...")
    print("예상 소요 시간: 2~5분")
    asyncio.run(run_long_range())
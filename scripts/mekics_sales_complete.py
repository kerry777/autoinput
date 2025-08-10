#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 조회 완전 자동화
- LOT표시 여부: 아니오 (라디오 버튼)
- 국내/해외 구분: 전체 (라디오 버튼)
- 매출일: 2025.08.05 ~ 2025.08.09
- 조회 및 엑셀 다운로드
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def run_complete():
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
            print("MEK-ICS 매출현황 조회 완전 자동화")
            print("="*60)
            
            # 1. 매출현황 조회 페이지 접속
            print("\n[1] 매출현황 조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(3000)
            
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            print("   페이지 로드 완료")
            
            # 2. LOT표시 여부 라디오 버튼 확인
            print("\n[2] LOT표시 여부 설정...")
            
            # 라디오 버튼 찾기
            lot_radio_info = await page.evaluate("""
                () => {
                    const radios = Ext.ComponentQuery.query('radiofield');
                    const result = {
                        total: radios.length,
                        lotRadios: []
                    };
                    
                    radios.forEach(radio => {
                        const label = radio.boxLabel || '';
                        const id = radio.id;
                        const checked = radio.checked;
                        
                        // LOT 관련 라디오 버튼 찾기
                        const parentLabel = radio.up('fieldcontainer') ? 
                            (radio.up('fieldcontainer').getFieldLabel ? 
                             radio.up('fieldcontainer').getFieldLabel() : '') : '';
                        
                        if(parentLabel.includes('LOT') || label === '예' || label === '아니오') {
                            result.lotRadios.push({
                                id: id,
                                label: label,
                                checked: checked,
                                parentLabel: parentLabel
                            });
                        }
                    });
                    
                    return result;
                }
            """)
            
            print(f"   라디오 버튼 {lot_radio_info['total']}개 발견")
            
            if lot_radio_info['lotRadios']:
                print("   LOT 관련 라디오 버튼:")
                for radio in lot_radio_info['lotRadios']:
                    checked = "[선택됨]" if radio['checked'] else ""
                    print(f"     - {radio['label']} (id: {radio['id']}) {checked}")
                
                # '아니오' 라디오 버튼 선택
                lot_result = await page.evaluate("""
                    () => {
                        // ID로 직접 찾기 (사용자가 제공한 ID)
                        const noRadio = Ext.getCmp('radiofield-1078');
                        if(noRadio) {
                            noRadio.setValue(true);
                            return {success: true, method: 'by ID 1078'};
                        }
                        
                        // 라벨로 찾기
                        const radios = Ext.ComponentQuery.query('radiofield');
                        for(let radio of radios) {
                            if(radio.boxLabel === '아니오' || radio.boxLabel === 'No') {
                                radio.setValue(true);
                                return {success: true, method: 'by label', label: radio.boxLabel};
                            }
                        }
                        
                        return {success: false};
                    }
                """)
                
                if lot_result['success']:
                    print(f"   [OK] LOT표시 '아니오' 선택 ({lot_result.get('method', '')})")
                else:
                    print("   [INFO] LOT 라디오 버튼 설정 건너뜀")
            
            # 3. 국내/해외 구분 라디오 버튼 설정
            print("\n[3] 국내/해외 구분 설정...")
            
            div_result = await page.evaluate("""
                () => {
                    // ID로 직접 찾기 (사용자가 제공한 ID)
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) {
                        allRadio.setValue(true);
                        return {success: true, method: 'by ID 1081'};
                    }
                    
                    // 라벨로 찾기
                    const radios = Ext.ComponentQuery.query('radiofield');
                    for(let radio of radios) {
                        if(radio.boxLabel === '전체' || radio.boxLabel === 'All') {
                            radio.setValue(true);
                            return {success: true, method: 'by label', label: radio.boxLabel};
                        }
                    }
                    
                    // 콤보박스로 시도
                    const combos = Ext.ComponentQuery.query('combobox');
                    if(combos.length > 1) {
                        combos[1].setValue('');  // 두 번째 콤보를 전체로
                        return {success: true, method: 'combo'};
                    }
                    
                    return {success: false};
                }
            """)
            
            if div_result['success']:
                print(f"   [OK] 국내/해외 구분 '전체' 선택 ({div_result.get('method', '')})")
            
            # 4. 날짜 설정
            print("\n[4] 매출일 설정 (2025.08.05 ~ 2025.08.09)...")
            
            date_result = await page.evaluate("""
                () => {
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    
                    if(dateFields.length >= 2) {
                        // 시작일
                        dateFields[0].setValue(new Date(2025, 7, 5));  // 2025년 8월 5일
                        // 종료일
                        dateFields[1].setValue(new Date(2025, 7, 9));  // 2025년 8월 9일
                        
                        return {
                            success: true,
                            from: dateFields[0].getValue().toLocaleDateString('ko-KR'),
                            to: dateFields[1].getValue().toLocaleDateString('ko-KR')
                        };
                    }
                    
                    return {success: false, error: 'Date fields not found'};
                }
            """)
            
            if date_result['success']:
                print(f"   [OK] 날짜 설정: {date_result['from']} ~ {date_result['to']}")
            else:
                print(f"   [FAIL] 날짜 설정 실패: {date_result.get('error', '')}")
            
            # 5. 조회 실행
            print("\n[5] 조회 실행...")
            
            # ID로 조회 버튼 클릭 (사용자가 제공한 ID)
            query_result = await page.evaluate("""
                () => {
                    // ID로 직접 찾기
                    const queryBtn = Ext.getCmp('button-1217');
                    if(queryBtn) {
                        queryBtn.fireEvent('click', queryBtn);
                        return {success: true, method: 'by ID 1217'};
                    }
                    
                    // 텍스트로 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('조회') && text.includes('F2')) {
                            btn.fireEvent('click', btn);
                            return {success: true, method: 'by text', text: text};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if query_result['success']:
                print(f"   [OK] 조회 버튼 클릭 ({query_result.get('method', '')})")
            
            # F2 키도 누르기
            await page.keyboard.press('F2')
            print("   F2 키 입력")
            
            # 데이터 로딩 대기
            print("\n[6] 데이터 로딩 중...")
            await page.wait_for_timeout(7000)
            
            # 6. 조회 결과 확인
            print("\n[7] 조회 결과 확인...")
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        const count = store.getCount();
                        
                        // 샘플 데이터 (처음 5건)
                        const sample = [];
                        const items = store.getData().items.slice(0, 5);
                        
                        items.forEach(item => {
                            const record = {};
                            // 주요 필드만
                            ['SALE_DATE', 'CUST_NAME', 'ITEM_NAME', 'QTY', 'SALE_AMT', 'LOT_NO'].forEach(field => {
                                if(item.data[field] !== undefined) {
                                    record[field] = item.data[field];
                                }
                            });
                            sample.push(record);
                        });
                        
                        return {
                            success: true,
                            count: count,
                            total: store.getTotalCount(),
                            sample: sample
                        };
                    }
                    
                    return {success: false, count: 0};
                }
            """)
            
            if grid_data['success']:
                print(f"   [OK] 조회 완료: {grid_data['count']}건")
                
                if grid_data.get('sample') and len(grid_data['sample']) > 0:
                    print("\n   샘플 데이터 (처음 5건):")
                    for i, record in enumerate(grid_data['sample'], 1):
                        print(f"     {i}. {record}")
            else:
                print("   [FAIL] 조회 결과 없음")
            
            # 7. 엑셀 다운로드
            print("\n[8] 엑셀 다운로드...")
            
            # ID로 엑셀 버튼 클릭 (사용자가 제공한 ID)
            excel_result = await page.evaluate("""
                () => {
                    // ID로 직접 찾기
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        excelBtn.fireEvent('click', excelBtn);
                        return {success: true, method: 'by ID 1196'};
                    }
                    
                    // 아이콘 클래스로 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const iconEl = btn.getEl() ? btn.getEl().down('.icon-excel') : null;
                        if(iconEl) {
                            btn.fireEvent('click', btn);
                            return {success: true, method: 'by icon class'};
                        }
                    }
                    
                    // 툴팁으로 찾기
                    for(let btn of buttons) {
                        const tooltip = btn.tooltip || '';
                        if(tooltip.includes('엑셀')) {
                            btn.fireEvent('click', btn);
                            return {success: true, method: 'by tooltip'};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if excel_result['success']:
                print(f"   엑셀 버튼 클릭 ({excel_result.get('method', '')})")
                
                # 팝업이 나타날 수 있으므로 잠시 대기
                await page.wait_for_timeout(2000)
                
                # CSV 다운로드 관련 팝업 확인 및 확인 버튼 클릭
                print("   팝업 확인 중...")
                popup_result = await page.evaluate("""
                    () => {
                        // MessageBox 확인
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        if(msgBoxes.length > 0) {
                            const msgBox = msgBoxes[0];
                            // 확인 버튼 찾기
                            const buttons = msgBox.query('button');
                            for(let btn of buttons) {
                                const text = btn.getText ? btn.getText() : '';
                                if(text === '확인' || text === 'OK' || text === '예' || text === 'Yes') {
                                    btn.fireEvent('click', btn);
                                    return {found: true, clicked: true, text: text};
                                }
                            }
                            return {found: true, clicked: false};
                        }
                        
                        // Window 타입 팝업 확인
                        const windows = Ext.ComponentQuery.query('window');
                        for(let win of windows) {
                            if(win.isVisible() && win.title && 
                               (win.title.includes('CSV') || win.title.includes('엑셀') || win.title.includes('다운로드'))) {
                                // 확인 버튼 찾기
                                const buttons = win.query('button');
                                for(let btn of buttons) {
                                    const text = btn.getText ? btn.getText() : '';
                                    if(text === '확인' || text === 'OK' || text === '예') {
                                        btn.fireEvent('click', btn);
                                        return {found: true, clicked: true, text: text, title: win.title};
                                    }
                                }
                            }
                        }
                        
                        return {found: false};
                    }
                """)
                
                if popup_result['found']:
                    if popup_result['clicked']:
                        print(f"   [OK] 팝업 확인 버튼 클릭: {popup_result.get('text', '확인')}")
                        if popup_result.get('title'):
                            print(f"       팝업 제목: {popup_result['title']}")
                    else:
                        print("   [INFO] 팝업이 있지만 확인 버튼을 찾지 못함")
                else:
                    print("   [INFO] 팝업 없음")
                
                # 다운로드 대기
                try:
                    async with page.expect_download(timeout=10000) as download_info:
                        # 다운로드 트리거 후 대기
                        await page.wait_for_timeout(1000)
                    
                    download = await download_info.value
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    
                    # 파일 확장자 확인 (xlsx 또는 csv)
                    suggested_filename = download.suggested_filename
                    if suggested_filename.endswith('.csv'):
                        save_path = data_dir / f"sales_report_{timestamp}.csv"
                        print("   [INFO] CSV 형식으로 다운로드")
                    else:
                        save_path = data_dir / f"sales_report_{timestamp}.xlsx"
                        print("   [INFO] Excel 형식으로 다운로드")
                    
                    await download.save_as(str(save_path))
                    print(f"   [OK] 파일 저장: {save_path}")
                    
                except asyncio.TimeoutError:
                    print("   [INFO] 다운로드 대기 시간 초과 - 파일이 이미 다운로드되었을 수 있습니다")
                except Exception as e:
                    print(f"   [INFO] 다운로드 처리 중 예외: {e}")
            else:
                print("   [FAIL] 엑셀 버튼을 찾을 수 없음")
            
            # 8. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"complete_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[9] 스크린샷: {screenshot_path}")
            
            print("\n" + "="*60)
            print("매출현황 조회 자동화 완료!")
            print("설정:")
            print("  - LOT표시 여부: 아니오")
            print("  - 국내/해외 구분: 전체")
            print("  - 매출일: 2025.08.05 ~ 2025.08.09")
            print("  - 조회 결과: {}건".format(grid_data.get('count', 0)))
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 브라우저 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_complete())
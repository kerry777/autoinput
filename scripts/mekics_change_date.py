#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 조회 - 날짜 변경 및 조회
현재 열려있는 매출현황 조회 화면에서 작업
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def change_date_and_query():
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
            print("매출현황 조회 - 날짜 변경 및 조회 실행")
            print("="*60)
            
            # 매출현황 조회 페이지로 직접 이동 (이미 로그인된 상태)
            print("\n[1] 매출현황 조회 페이지 접속 시도...")
            
            # 먼저 메인 페이지로
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(3000)
            
            # 직접 URL로 이동 시도
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            print("[2] 페이지 로드 완료. 컴포넌트 확인...")
            
            # ExtJS 컴포넌트 확인
            components = await page.evaluate("""
                () => {
                    if(typeof Ext === 'undefined') {
                        return {error: 'ExtJS not loaded'};
                    }
                    
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    const combos = Ext.ComponentQuery.query('combobox');
                    const buttons = Ext.ComponentQuery.query('button');
                    const grids = Ext.ComponentQuery.query('grid');
                    
                    // 날짜 필드 상세 정보
                    const dateInfo = dateFields.map(field => ({
                        id: field.id,
                        name: field.name || '',
                        label: field.getFieldLabel ? field.getFieldLabel() : '',
                        value: field.getValue()
                    }));
                    
                    return {
                        dateFields: dateFields.length,
                        combos: combos.length,
                        buttons: buttons.length,
                        grids: grids.length,
                        dateInfo: dateInfo
                    };
                }
            """)
            
            print(f"   날짜 필드: {components.get('dateFields', 0)}개")
            print(f"   콤보박스: {components.get('combos', 0)}개")
            print(f"   버튼: {components.get('buttons', 0)}개")
            print(f"   그리드: {components.get('grids', 0)}개")
            
            if components.get('dateInfo'):
                print("\n   날짜 필드 정보:")
                for df in components['dateInfo']:
                    print(f"     - {df['label']}: {df['value']}")
            
            # 날짜 변경
            print("\n[3] 매출일 변경 (2025.08.05 ~ 2025.08.09)...")
            
            date_result = await page.evaluate("""
                () => {
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    
                    if(dateFields.length >= 2) {
                        // 시작일: 2025년 8월 5일 (화요일)
                        const fromDate = new Date(2025, 7, 5);  // JavaScript에서 월은 0부터 시작
                        dateFields[0].setValue(fromDate);
                        
                        // 종료일: 2025년 8월 9일 (토요일)
                        const toDate = new Date(2025, 7, 9);
                        dateFields[1].setValue(toDate);
                        
                        // 설정된 값 확인
                        const fromValue = dateFields[0].getValue();
                        const toValue = dateFields[1].getValue();
                        
                        return {
                            success: true,
                            from: fromValue ? fromValue.toLocaleDateString('ko-KR') : 'not set',
                            to: toValue ? toValue.toLocaleDateString('ko-KR') : 'not set'
                        };
                    } else {
                        // 날짜 필드가 부족한 경우 DOM에서 직접 시도
                        const fromInput = document.querySelector('input[name="SALE_FR_DATE"]');
                        const toInput = document.querySelector('input[name="SALE_TO_DATE"]');
                        
                        if(fromInput && toInput) {
                            fromInput.value = '2024.08.05';
                            toInput.value = '2024.08.09';
                            
                            // change 이벤트 발생
                            fromInput.dispatchEvent(new Event('change', { bubbles: true }));
                            toInput.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            return {
                                success: true,
                                from: '2024.08.05',
                                to: '2024.08.09',
                                method: 'DOM'
                            };
                        }
                        
                        return {success: false, error: 'Date fields not found'};
                    }
                }
            """)
            
            if date_result['success']:
                print(f"   [OK] 날짜 설정 완료")
                print(f"     시작일: {date_result['from']}")
                print(f"     종료일: {date_result['to']}")
            else:
                print(f"   [FAIL] 날짜 설정 실패: {date_result.get('error', 'Unknown error')}")
            
            # 구분 설정은 건드리지 않음 (사용자 요청)
            print("\n[4] 사업장 및 구분 설정 유지 (변경하지 않음)")
            
            # 조회 실행
            print("\n[5] 조회 실행 (F2)...")
            
            # F2 키 누르기
            await page.keyboard.press('F2')
            print("   F2 키 입력 완료")
            
            # 추가로 조회 버튼도 클릭 시도
            button_result = await page.evaluate("""
                () => {
                    const buttons = Ext.ComponentQuery.query('button');
                    
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        
                        // '조회' 텍스트를 포함하는 버튼 찾기
                        if(text.includes('조회') || text.includes('검색') || 
                           text.includes('Search') || tooltip.includes('조회')) {
                            btn.fireEvent('click', btn);
                            return {
                                success: true,
                                buttonText: text || tooltip
                            };
                        }
                    }
                    
                    return {success: false, error: 'Query button not found'};
                }
            """)
            
            if button_result['success']:
                print(f"   [OK] 조회 버튼 클릭: {button_result['buttonText']}")
            
            # 데이터 로딩 대기
            print("\n[6] 데이터 로딩 중...")
            await page.wait_for_timeout(7000)
            
            # 조회 결과 확인
            print("\n[7] 조회 결과 확인...")
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    
                    if(grids.length > 0) {
                        const grid = grids[0];
                        const store = grid.getStore();
                        const count = store.getCount();
                        
                        // 처음 5개 레코드 샘플
                        const sample = [];
                        const items = store.getData().items.slice(0, 5);
                        
                        items.forEach(item => {
                            // 주요 필드만 추출
                            const record = {};
                            const data = item.data;
                            
                            // 가능한 필드명들
                            const fields = ['CUST_NAME', 'SALE_DATE', 'SALE_AMT', 'ITEM_NAME', 'QTY'];
                            fields.forEach(field => {
                                if(data[field] !== undefined) {
                                    record[field] = data[field];
                                }
                            });
                            
                            sample.push(record);
                        });
                        
                        return {
                            success: true,
                            count: count,
                            total: store.getTotalCount(),
                            loading: store.isLoading(),
                            sample: sample
                        };
                    }
                    
                    return {success: false, count: 0, error: 'No grid found'};
                }
            """)
            
            if grid_data['success']:
                print(f"   [OK] 조회 완료")
                print(f"     레코드 수: {grid_data['count']}건")
                print(f"     전체 수: {grid_data.get('total', grid_data['count'])}건")
                
                if grid_data.get('sample') and len(grid_data['sample']) > 0:
                    print("\n   샘플 데이터 (처음 5건):")
                    for i, record in enumerate(grid_data['sample'], 1):
                        print(f"     {i}. {record}")
            else:
                print(f"   [FAIL] 조회 결과 없음: {grid_data.get('error', 'Unknown error')}")
            
            # 엑셀 다운로드
            print("\n[8] 엑셀 다운로드 시도...")
            
            # 다운로드 대기 설정
            download_promise = page.wait_for_event('download', timeout=10000)
            
            excel_result = await page.evaluate("""
                () => {
                    // 버튼에서 엑셀 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        
                        if(text.includes('엑셀') || text.includes('Excel') ||
                           tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                            btn.fireEvent('click', btn);
                            return {success: true, method: 'ExtJS button'};
                        }
                    }
                    
                    // DOM에서 직접 찾기
                    const elements = document.querySelectorAll('[title*="엑셀"], [tooltip*="엑셀"]');
                    if(elements.length > 0) {
                        elements[0].click();
                        return {success: true, method: 'DOM element'};
                    }
                    
                    // 아이콘 클래스로 찾기
                    const icons = document.querySelectorAll('[class*="excel"], [class*="xls"]');
                    if(icons.length > 0) {
                        icons[0].click();
                        return {success: true, method: 'Icon class'};
                    }
                    
                    return {success: false, error: 'Excel button not found'};
                }
            """)
            
            if excel_result['success']:
                print(f"   엑셀 버튼 클릭 ({excel_result['method']})")
                
                try:
                    download = await download_promise
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"매출현황_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   [OK] 엑셀 다운로드 완료: {save_path}")
                except asyncio.TimeoutError:
                    print("   [FAIL] 다운로드 시간 초과")
            else:
                print(f"   [FAIL] 엑셀 버튼을 찾을 수 없음")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"sales_query_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[9] 스크린샷 저장: {screenshot_path}")
            
            print("\n" + "="*60)
            print("매출현황 조회 완료!")
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
    asyncio.run(change_date_and_query())
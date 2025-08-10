#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 조회 - LOT표시 여부를 '아니오'로 설정
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def set_lot_no():
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
            print("매출현황 조회 - LOT표시 여부 설정")
            print("="*60)
            
            # 매출현황 조회 페이지로 직접 이동
            print("\n[1] 매출현황 조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(3000)
            
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            print("[2] 페이지 로드 완료")
            
            # 모든 콤보박스 확인하여 LOT 관련 찾기
            print("\n[3] LOT표시 여부 콤보박스 찾기...")
            lot_combo_info = await page.evaluate("""
                () => {
                    const combos = Ext.ComponentQuery.query('combobox');
                    let lotComboIndex = -1;
                    let lotComboInfo = null;
                    
                    combos.forEach((combo, idx) => {
                        const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                        const name = combo.getName ? combo.getName() : '';
                        
                        // LOT 관련 콤보박스 찾기
                        if(label.includes('LOT') || label.includes('lot') || 
                           name.includes('LOT') || name.includes('lot')) {
                            lotComboIndex = idx;
                            
                            // Store 데이터 확인
                            let options = [];
                            if(combo.getStore) {
                                const store = combo.getStore();
                                if(store && store.getData) {
                                    store.getData().items.forEach(item => {
                                        options.push({
                                            value: item.get(combo.valueField || 'value'),
                                            display: item.get(combo.displayField || 'text')
                                        });
                                    });
                                }
                            }
                            
                            lotComboInfo = {
                                index: idx,
                                label: label,
                                name: name,
                                currentValue: combo.getValue(),
                                currentDisplay: combo.getRawValue(),
                                options: options
                            };
                        }
                    });
                    
                    return {
                        found: lotComboIndex >= 0,
                        index: lotComboIndex,
                        info: lotComboInfo,
                        totalCombos: combos.length
                    };
                }
            """)
            
            if lot_combo_info['found']:
                print(f"   [OK] LOT 콤보박스 발견!")
                print(f"     인덱스: {lot_combo_info['index']}")
                print(f"     레이블: {lot_combo_info['info']['label']}")
                print(f"     현재값: {lot_combo_info['info']['currentDisplay']}")
                
                if lot_combo_info['info']['options']:
                    print("     옵션들:")
                    for opt in lot_combo_info['info']['options']:
                        print(f"       - {opt['display']} (값: {opt['value']})")
            else:
                print(f"   [INFO] LOT 콤보박스를 찾지 못함. 전체 {lot_combo_info['totalCombos']}개 콤보박스 확인")
                
                # 모든 콤보박스 레이블 출력
                all_combos = await page.evaluate("""
                    () => {
                        const combos = Ext.ComponentQuery.query('combobox');
                        return combos.map((combo, idx) => ({
                            index: idx,
                            label: combo.getFieldLabel ? combo.getFieldLabel() : '',
                            name: combo.getName ? combo.getName() : ''
                        }));
                    }
                """)
                
                print("\n   모든 콤보박스 목록:")
                for combo in all_combos:
                    if combo['label'] or combo['name']:
                        print(f"     [{combo['index']}] {combo['label']} (name: {combo['name']})")
                        # LOT 관련 찾기
                        if 'LOT' in combo['label'].upper() or 'LOT' in combo['name'].upper():
                            lot_combo_info['found'] = True
                            lot_combo_info['index'] = combo['index']
                            print(f"        >>> LOT 콤보박스 발견!")
            
            # LOT표시 여부를 '아니오'로 설정
            if lot_combo_info['found']:
                print("\n[4] LOT표시 여부를 '아니오'로 설정...")
                
                lot_result = await page.evaluate(f"""
                    () => {{
                        const combos = Ext.ComponentQuery.query('combobox');
                        const lotCombo = combos[{lot_combo_info['index']}];
                        
                        if(lotCombo) {{
                            // '아니오' 값 찾기
                            const store = lotCombo.getStore();
                            let noValue = 'N';  // 기본값
                            
                            if(store) {{
                                store.getData().items.forEach(item => {{
                                    const display = item.get(lotCombo.displayField || 'text');
                                    const value = item.get(lotCombo.valueField || 'value');
                                    
                                    if(display === '아니오' || display === 'No' || 
                                       display === 'N' || display === '아니요') {{
                                        noValue = value;
                                    }}
                                }});
                            }}
                            
                            // 값 설정
                            lotCombo.setValue(noValue);
                            lotCombo.fireEvent('change', lotCombo, noValue);
                            
                            return {{
                                success: true,
                                setValue: noValue,
                                newDisplay: lotCombo.getRawValue()
                            }};
                        }}
                        
                        return {{success: false}};
                    }}
                """)
                
                if lot_result['success']:
                    print(f"   [OK] LOT표시 여부 설정 완료")
                    print(f"     설정값: {lot_result['setValue']}")
                    print(f"     표시값: {lot_result['newDisplay']}")
                else:
                    print("   [FAIL] LOT표시 여부 설정 실패")
            
            # 국내/해외 구분을 '전체'로 설정
            print("\n[5] 국내/해외 구분을 '전체'로 설정...")
            div_result = await page.evaluate("""
                () => {
                    const combos = Ext.ComponentQuery.query('combobox');
                    
                    // 첫 번째 콤보박스(사업장 다음)가 보통 국내/해외 구분
                    if(combos.length > 1) {
                        const divCombo = combos[1];  // 두 번째 콤보박스
                        
                        // 전체 값 설정 (보통 빈 문자열)
                        divCombo.setValue('');
                        
                        return {
                            success: true,
                            newValue: divCombo.getRawValue() || '전체'
                        };
                    }
                    
                    return {success: false};
                }
            """)
            
            if div_result['success']:
                print(f"   [OK] 구분 설정: {div_result['newValue']}")
            
            # 날짜 설정
            print("\n[6] 매출일 설정 (2025.08.05 ~ 2025.08.09)...")
            date_result = await page.evaluate("""
                () => {
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2025, 7, 5));
                        dateFields[1].setValue(new Date(2025, 7, 9));
                        
                        return {
                            success: true,
                            from: dateFields[0].getValue().toLocaleDateString('ko-KR'),
                            to: dateFields[1].getValue().toLocaleDateString('ko-KR')
                        };
                    }
                    
                    return {success: false};
                }
            """)
            
            if date_result['success']:
                print(f"   [OK] 날짜: {date_result['from']} ~ {date_result['to']}")
            
            # 조회 실행
            print("\n[7] 조회 실행 (F2)...")
            await page.keyboard.press('F2')
            print("   F2 키 입력")
            
            # 조회 버튼도 클릭
            button_result = await page.evaluate("""
                () => {
                    const buttons = Ext.ComponentQuery.query('button');
                    
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('조회') || text.includes('검색')) {
                            btn.fireEvent('click', btn);
                            return {success: true, text: text};
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if button_result['success']:
                print(f"   조회 버튼 클릭: {button_result['text']}")
            
            # 데이터 로딩 대기
            print("\n[8] 데이터 로딩 중...")
            await page.wait_for_timeout(7000)
            
            # 결과 확인
            print("\n[9] 조회 결과 확인...")
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        const count = store.getCount();
                        
                        // 샘플 데이터
                        const sample = [];
                        const items = store.getData().items.slice(0, 3);
                        items.forEach(item => {
                            const data = {};
                            ['SALE_DATE', 'CUST_NAME', 'ITEM_NAME', 'QTY', 'SALE_AMT'].forEach(field => {
                                if(item.data[field] !== undefined) {
                                    data[field] = item.data[field];
                                }
                            });
                            sample.push(data);
                        });
                        
                        return {
                            count: count,
                            total: store.getTotalCount(),
                            sample: sample
                        };
                    }
                    
                    return {count: 0};
                }
            """)
            
            print(f"   조회 건수: {grid_data['count']}건")
            if grid_data.get('sample'):
                print("\n   샘플 데이터:")
                for i, record in enumerate(grid_data['sample'], 1):
                    print(f"     {i}. {record}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"lot_no_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[10] 스크린샷: {screenshot_path}")
            
            print("\n" + "="*60)
            print("완료: LOT표시 여부 '아니오' 설정 및 조회")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 브라우저 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(set_lot_no())
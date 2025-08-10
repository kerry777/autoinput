#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 조회 - 국내/해외 구분을 '전체'로 설정
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def set_division_all():
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
            print("매출현황 조회 - 국내/해외 구분 설정")
            print("="*60)
            
            # 매출현황 조회 페이지로 직접 이동
            print("\n[1] 매출현황 조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(3000)
            
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            print("[2] 페이지 로드 완료")
            
            # 콤보박스 확인
            print("\n[3] 콤보박스 확인...")
            combo_info = await page.evaluate("""
                () => {
                    const combos = Ext.ComponentQuery.query('combobox');
                    const result = [];
                    
                    combos.forEach((combo, idx) => {
                        const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                        const value = combo.getValue();
                        const rawValue = combo.getRawValue ? combo.getRawValue() : '';
                        const name = combo.getName ? combo.getName() : '';
                        
                        // Store의 데이터 확인
                        let storeData = [];
                        if(combo.getStore) {
                            const store = combo.getStore();
                            if(store && store.getData) {
                                store.getData().items.forEach(item => {
                                    storeData.push({
                                        value: item.get(combo.valueField || 'value'),
                                        display: item.get(combo.displayField || 'text')
                                    });
                                });
                            }
                        }
                        
                        result.push({
                            index: idx,
                            label: label,
                            name: name,
                            value: value,
                            rawValue: rawValue,
                            options: storeData
                        });
                    });
                    
                    return result;
                }
            """)
            
            print(f"   총 {len(combo_info)}개의 콤보박스 발견")
            
            # 국내/해외 구분 콤보박스 찾기
            division_combo_index = None
            for combo in combo_info[:10]:  # 처음 10개만 확인
                print(f"\n   콤보박스 {combo['index']}:")
                print(f"     레이블: {combo['label']}")
                print(f"     이름: {combo['name']}")
                print(f"     현재값: {combo['rawValue']} ({combo['value']})")
                
                # 국내/해외 구분 콤보박스 찾기
                if '구분' in combo['label'] or '국내' in combo['label'] or 'DIV' in combo['name'].upper():
                    division_combo_index = combo['index']
                    print(f"     >>> 이것이 국내/해외 구분 콤보박스입니다!")
                    
                    if combo['options']:
                        print(f"     옵션들:")
                        for opt in combo['options']:
                            print(f"       - {opt['display']} (값: {opt['value']})")
            
            # 국내/해외 구분을 '전체'로 설정
            print("\n[4] 국내/해외 구분을 '전체'로 설정...")
            
            if division_combo_index is not None:
                # 특정 인덱스의 콤보박스 설정
                division_result = await page.evaluate(f"""
                    () => {{
                        const combos = Ext.ComponentQuery.query('combobox');
                        const targetCombo = combos[{division_combo_index}];
                        
                        if(targetCombo) {{
                            // '전체' 옵션 찾기
                            const store = targetCombo.getStore();
                            let allValue = '';  // 기본값은 빈 문자열 (보통 전체)
                            
                            if(store) {{
                                store.getData().items.forEach(item => {{
                                    const display = item.get(targetCombo.displayField || 'text');
                                    const value = item.get(targetCombo.valueField || 'value');
                                    
                                    if(display === '전체' || display === 'ALL' || display === '모두') {{
                                        allValue = value;
                                    }}
                                }});
                            }}
                            
                            // 값 설정
                            targetCombo.setValue(allValue);
                            
                            // 변경 이벤트 발생
                            targetCombo.fireEvent('change', targetCombo, allValue);
                            targetCombo.fireEvent('select', targetCombo);
                            
                            return {{
                                success: true,
                                setValue: allValue,
                                newRawValue: targetCombo.getRawValue()
                            }};
                        }}
                        
                        return {{success: false, error: 'Combo not found'}};
                    }}
                """)
            else:
                # 모든 콤보박스에서 시도
                division_result = await page.evaluate("""
                    () => {
                        const combos = Ext.ComponentQuery.query('combobox');
                        
                        for(let combo of combos) {
                            const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                            const name = combo.getName ? combo.getName() : '';
                            
                            // 국내/해외 구분 관련 콤보박스 찾기
                            if(label.includes('구분') || label.includes('국내') || 
                               label.includes('해외') || name.toUpperCase().includes('DIV')) {
                                
                                // 전체 값 찾기
                                const store = combo.getStore();
                                let allValue = '';  // 기본값
                                
                                if(store) {
                                    store.getData().items.forEach(item => {
                                        const display = item.get(combo.displayField || 'text');
                                        const value = item.get(combo.valueField || 'value');
                                        
                                        if(display === '전체' || display === 'ALL' || 
                                           display === '모두' || value === '') {
                                            allValue = value;
                                        }
                                    });
                                }
                                
                                // 값 설정
                                combo.setValue(allValue);
                                combo.fireEvent('change', combo, allValue);
                                
                                return {
                                    success: true,
                                    label: label,
                                    setValue: allValue,
                                    newRawValue: combo.getRawValue()
                                };
                            }
                        }
                        
                        // 못 찾으면 첫 번째 콤보박스를 전체로
                        if(combos.length > 0) {
                            combos[0].setValue('');
                            return {
                                success: true,
                                label: 'First combo',
                                setValue: '',
                                newRawValue: combos[0].getRawValue()
                            };
                        }
                        
                        return {success: false, error: 'No division combo found'};
                    }
                """)
            
            if division_result['success']:
                print(f"   [OK] 구분 설정 완료")
                print(f"     설정값: {division_result.get('setValue', '')}")
                print(f"     표시값: {division_result.get('newRawValue', '전체')}")
            else:
                print(f"   [FAIL] 구분 설정 실패: {division_result.get('error', 'Unknown')}")
            
            # 날짜도 설정
            print("\n[5] 매출일 설정 (2025.08.05 ~ 2025.08.09)...")
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
                print(f"   [OK] 날짜 설정 완료")
                print(f"     {date_result['from']} ~ {date_result['to']}")
            
            # 조회 실행
            print("\n[6] 조회 실행 (F2)...")
            await page.keyboard.press('F2')
            print("   F2 키 입력 완료")
            
            # 데이터 로딩 대기
            await page.wait_for_timeout(7000)
            
            # 결과 확인
            print("\n[7] 조회 결과 확인...")
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        return {
                            count: store.getCount(),
                            total: store.getTotalCount()
                        };
                    }
                    
                    return {count: 0, total: 0};
                }
            """)
            
            print(f"   조회 결과: {grid_data['count']}건")
            
            # 엑셀 다운로드
            print("\n[8] 엑셀 다운로드 시도...")
            
            # 다운로드 이벤트 대기
            async with page.expect_download(timeout=10000) as download_info:
                # 엑셀 버튼 클릭
                excel_result = await page.evaluate("""
                    () => {
                        // ExtJS 버튼에서 찾기
                        const buttons = Ext.ComponentQuery.query('button');
                        for(let btn of buttons) {
                            const text = btn.getText ? btn.getText() : '';
                            const tooltip = btn.tooltip || '';
                            
                            if(text.includes('엑셀') || tooltip.includes('엑셀') || 
                               text.includes('Excel') || tooltip.includes('Excel')) {
                                btn.fireEvent('click', btn);
                                return {success: true, method: 'ExtJS button'};
                            }
                        }
                        
                        // 툴바 아이템에서 찾기
                        const tools = Ext.ComponentQuery.query('tool');
                        for(let tool of tools) {
                            if(tool.tooltip && tool.tooltip.includes('엑셀')) {
                                tool.fireEvent('click', tool);
                                return {success: true, method: 'Tool'};
                            }
                        }
                        
                        // DOM에서 직접 찾기
                        const elements = document.querySelectorAll('[title*="엑셀"], [tooltip*="엑셀"]');
                        if(elements.length > 0) {
                            elements[0].click();
                            return {success: true, method: 'DOM'};
                        }
                        
                        return {success: false};
                    }
                """)
                
                if excel_result['success']:
                    print(f"   엑셀 버튼 클릭 ({excel_result['method']})")
                    
                    try:
                        download = await download_info.value
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        save_path = data_dir / f"sales_all_{timestamp}.xlsx"
                        await download.save_as(str(save_path))
                        print(f"   [OK] 엑셀 저장: {save_path}")
                    except:
                        print("   [FAIL] 다운로드 실패")
                else:
                    print("   엑셀 버튼을 찾을 수 없음")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"division_all_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[9] 스크린샷: {screenshot_path}")
            
            print("\n" + "="*60)
            print("완료: 국내/해외 구분을 '전체'로 설정")
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
    asyncio.run(set_division_all())
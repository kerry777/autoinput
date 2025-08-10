#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 정확한 자동화
메인 프레임에서 작업
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def run():
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
            # 1. 메인 페이지
            print("1. Main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 2. 영업관리
            print("2. Sales module...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 매출관리 메뉴
            print("3. Sales Management menu...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.includes('매출관리')) {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(2000)
            
            # 4. 매출현황조회
            print("4. Sales Status Inquiry...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText === '매출현황조회') {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(5000)
            
            # 5. 현재 화면 분석
            print("\n5. Analyzing current screen...")
            screen_info = await page.evaluate("""
                () => {
                    const info = {
                        panels: Ext.ComponentQuery.query('panel').length,
                        forms: Ext.ComponentQuery.query('form').length,
                        dateFields: [],
                        combos: [],
                        buttons: [],
                        grids: Ext.ComponentQuery.query('grid').length
                    };
                    
                    // 날짜 필드
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    dateFields.forEach(field => {
                        info.dateFields.push({
                            id: field.id,
                            name: field.name || '',
                            label: field.getFieldLabel ? field.getFieldLabel() : '',
                            value: field.getValue ? field.getValue() : null
                        });
                    });
                    
                    // 콤보박스
                    const combos = Ext.ComponentQuery.query('combobox');
                    combos.forEach(combo => {
                        info.combos.push({
                            id: combo.id,
                            name: combo.name || '',
                            label: combo.getFieldLabel ? combo.getFieldLabel() : '',
                            value: combo.getRawValue ? combo.getRawValue() : ''
                        });
                    });
                    
                    // 버튼
                    const buttons = Ext.ComponentQuery.query('button');
                    buttons.slice(0, 15).forEach(btn => {
                        info.buttons.push({
                            id: btn.id,
                            text: btn.getText ? btn.getText() : '',
                            tooltip: btn.tooltip || ''
                        });
                    });
                    
                    return info;
                }
            """)
            
            print(f"   Panels: {screen_info['panels']}, Forms: {screen_info['forms']}, Grids: {screen_info['grids']}")
            print(f"   Date fields: {len(screen_info['dateFields'])}")
            print(f"   Combos: {len(screen_info['combos'])}")
            print(f"   Buttons: {len(screen_info['buttons'])}")
            
            # 6. 날짜 설정
            print("\n6. Setting dates...")
            if len(screen_info['dateFields']) >= 2:
                # ID를 사용한 직접 설정
                from_id = screen_info['dateFields'][0]['id']
                to_id = screen_info['dateFields'][1]['id']
                
                date_result = await page.evaluate(f"""
                    () => {{
                        const fromField = Ext.getCmp('{from_id}');
                        const toField = Ext.getCmp('{to_id}');
                        
                        if(fromField && toField) {{
                            fromField.setValue(new Date(2024, 7, 5));  // 2024.08.05
                            toField.setValue(new Date(2024, 7, 9));    // 2024.08.09
                            return 'Dates set: 2024.08.05 ~ 2024.08.09';
                        }}
                        return 'Date fields not found';
                    }}
                """)
                print(f"   {date_result}")
            else:
                print("   ERROR: Not enough date fields")
            
            # 7. 구분 설정
            print("\n7. Setting division...")
            if screen_info['combos']:
                # 첫 번째 콤보박스를 전체로
                combo_id = screen_info['combos'][0]['id']
                combo_result = await page.evaluate(f"""
                    () => {{
                        const combo = Ext.getCmp('{combo_id}');
                        if(combo) {{
                            combo.setValue('');  // 빈값 = 전체
                            return 'Division set to ALL';
                        }}
                        return 'Combo not found';
                    }}
                """)
                print(f"   {combo_result}")
            
            # 8. 조회 실행
            print("\n8. Execute query...")
            
            # 조회 버튼 찾기
            query_button = None
            for btn in screen_info['buttons']:
                if '조회' in btn['text'] or 'F2' in btn['text']:
                    query_button = btn
                    break
            
            if query_button:
                await page.evaluate(f"""
                    () => {{
                        const btn = Ext.getCmp('{query_button['id']}');
                        if(btn) {{
                            btn.fireEvent('click', btn);
                        }}
                    }}
                """)
                print(f"   Query button clicked: {query_button['text']}")
            else:
                # F2 키 사용
                await page.keyboard.press('F2')
                print("   F2 key pressed")
            
            # 데이터 로딩 대기
            print("   Waiting for data...")
            await page.wait_for_timeout(7000)
            
            # 9. 결과 확인
            print("\n9. Check results...")
            grid_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0) {
                        const grid = grids[0];
                        const store = grid.getStore();
                        return {
                            count: store.getCount(),
                            loading: store.isLoading()
                        };
                    }
                    return {count: 0};
                }
            """)
            print(f"   Records: {grid_data['count']}")
            
            # 10. 엑셀 다운로드
            print("\n10. Excel download...")
            
            # 엑셀 버튼 찾기
            excel_button = None
            for btn in screen_info['buttons']:
                if '엑셀' in btn['text'] or '엑셀' in btn.get('tooltip', ''):
                    excel_button = btn
                    break
            
            if excel_button:
                # 다운로드 대기 설정
                download_promise = page.wait_for_event('download', timeout=10000)
                
                await page.evaluate(f"""
                    () => {{
                        const btn = Ext.getCmp('{excel_button['id']}');
                        if(btn) {{
                            btn.fireEvent('click', btn);
                        }}
                    }}
                """)
                print(f"   Excel button clicked: {excel_button['text'] or excel_button['tooltip']}")
                
                try:
                    download = await download_promise
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"sales_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   Download complete: {save_path}")
                except:
                    print("   Download timeout - manual click may be needed")
            else:
                # 툴팁으로 찾기
                excel_result = await page.evaluate("""
                    () => {
                        // 툴팁이 '엑셀 다운로드'인 요소
                        const elements = document.querySelectorAll('[title="엑셀 다운로드"]');
                        if(elements.length > 0) {
                            elements[0].click();
                            return 'Excel element clicked';
                        }
                        
                        // 클래스명으로 찾기
                        const icons = document.querySelectorAll('[class*="excel"], [class*="xls"]');
                        if(icons.length > 0) {
                            icons[0].click();
                            return 'Excel icon clicked';
                        }
                        
                        return 'Excel button not found';
                    }
                """)
                print(f"   {excel_result}")
            
            # 11. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"sales_complete_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"\n11. Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("COMPLETE: Sales report automation finished")
            print("="*60)
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
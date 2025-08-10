#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 매출현황 화면 필드 분석
정확한 필드 선택자 찾기
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
sys.path.insert(0, str(project_root / "core" / "utils"))
from extjs_helper import MEKICSHelper


async def inspect_sales_screen():
    """매출현황 화면 필드 검사"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    # 설정 로드
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone'],
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("[OK] 쿠키 로드 완료")
        
        page = await context.new_page()
        extjs = MEKICSHelper(page)
        
        try:
            print("="*80)
            print("MEK-ICS 매출현황 화면 필드 분석")
            print("="*80)
            
            # 메인 페이지 접속
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            await extjs.wait_for_extjs()
            
            # 영업관리 모듈
            await extjs.navigate_to_module('영업관리')
            await page.wait_for_timeout(5000)
            
            # 매출관리 확장
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for (let node of nodes) {
                        if (node.innerText && node.innerText.includes('매출관리')) {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(2000)
            
            # 매출현황조회 클릭
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for (let node of nodes) {
                        if (node.innerText && node.innerText === '매출현황조회') {
                            node.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            await page.wait_for_timeout(5000)
            
            print("\n매출현황조회 화면 진입 완료\n")
            print("-"*80)
            
            # 모든 필드 분석
            fields_info = await page.evaluate("""
                () => {
                    const result = {
                        dateFields: [],
                        comboBoxes: [],
                        textFields: [],
                        buttons: [],
                        grids: []
                    };
                    
                    // 날짜 필드
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    dateFields.forEach((field, idx) => {
                        result.dateFields.push({
                            index: idx,
                            name: field.getName ? field.getName() : '',
                            label: field.getFieldLabel ? field.getFieldLabel() : '',
                            value: field.getValue ? field.getValue() : '',
                            id: field.getId ? field.getId() : '',
                            itemId: field.itemId || ''
                        });
                    });
                    
                    // 콤보박스
                    const combos = Ext.ComponentQuery.query('combobox');
                    combos.forEach((combo, idx) => {
                        result.comboBoxes.push({
                            index: idx,
                            name: combo.getName ? combo.getName() : '',
                            label: combo.getFieldLabel ? combo.getFieldLabel() : '',
                            value: combo.getValue ? combo.getValue() : '',
                            displayValue: combo.getRawValue ? combo.getRawValue() : '',
                            store: combo.getStore ? (combo.getStore().getData ? combo.getStore().getData().items.map(item => item.data) : []) : [],
                            id: combo.getId ? combo.getId() : '',
                            itemId: combo.itemId || ''
                        });
                    });
                    
                    // 텍스트 필드
                    const textFields = Ext.ComponentQuery.query('textfield');
                    textFields.forEach((field, idx) => {
                        result.textFields.push({
                            index: idx,
                            name: field.getName ? field.getName() : '',
                            label: field.getFieldLabel ? field.getFieldLabel() : '',
                            value: field.getValue ? field.getValue() : '',
                            id: field.getId ? field.getId() : '',
                            itemId: field.itemId || ''
                        });
                    });
                    
                    // 버튼
                    const buttons = Ext.ComponentQuery.query('button');
                    buttons.forEach((btn, idx) => {
                        const text = btn.getText ? btn.getText() : '';
                        result.buttons.push({
                            index: idx,
                            text: text,
                            tooltip: btn.tooltip || '',
                            iconCls: btn.iconCls || '',
                            id: btn.getId ? btn.getId() : '',
                            itemId: btn.itemId || ''
                        });
                    });
                    
                    // 그리드
                    const grids = Ext.ComponentQuery.query('grid');
                    grids.forEach((grid, idx) => {
                        result.grids.push({
                            index: idx,
                            title: grid.title || '',
                            columnCount: grid.getColumns ? grid.getColumns().length : 0,
                            recordCount: grid.getStore ? grid.getStore().getCount() : 0
                        });
                    });
                    
                    return result;
                }
            """)
            
            # 결과 출력
            print("\n[날짜 필드]")
            for field in fields_info['dateFields']:
                print(f"  {field['index']}. Label: '{field['label']}' | Name: '{field['name']}' | Value: {field['value']}")
                print(f"     ID: {field['id']} | ItemID: {field['itemId']}")
            
            print("\n[콤보박스]")
            for combo in fields_info['comboBoxes']:
                print(f"  {combo['index']}. Label: '{combo['label']}' | Name: '{combo['name']}'")
                print(f"     Value: '{combo['value']}' | Display: '{combo['displayValue']}'")
                print(f"     ID: {combo['id']} | ItemID: {combo['itemId']}")
                if combo['store']:
                    print(f"     Store Items: {combo['store'][:3]}")  # 처음 3개만
            
            print("\n[텍스트 필드]")
            for field in fields_info['textFields'][:10]:  # 처음 10개만
                if field['label']:  # 레이블이 있는 것만
                    print(f"  {field['index']}. Label: '{field['label']}' | Name: '{field['name']}'")
            
            print("\n[버튼]")
            for btn in fields_info['buttons'][:20]:  # 처음 20개만
                if btn['text']:  # 텍스트가 있는 것만
                    print(f"  {btn['index']}. Text: '{btn['text']}' | Tooltip: '{btn['tooltip']}'")
            
            print("\n[그리드]")
            for grid in fields_info['grids']:
                print(f"  {grid['index']}. Title: '{grid['title']}' | Columns: {grid['columnCount']} | Records: {grid['recordCount']}")
            
            # 날짜 설정 테스트
            print("\n" + "="*80)
            print("날짜 필드 설정 테스트")
            print("="*80)
            
            if len(fields_info['dateFields']) >= 2:
                print(f"\n날짜 필드 {len(fields_info['dateFields'])}개 발견")
                
                # 첫 번째와 두 번째 날짜 필드에 값 설정
                date_set_result = await page.evaluate("""
                    () => {
                        const dateFields = Ext.ComponentQuery.query('datefield');
                        const results = [];
                        
                        if (dateFields[0]) {
                            dateFields[0].setValue(new Date(2024, 7, 5)); // 8월 5일
                            results.push('첫 번째 날짜: 2024-08-05');
                        }
                        
                        if (dateFields[1]) {
                            dateFields[1].setValue(new Date(2024, 7, 9)); // 8월 9일  
                            results.push('두 번째 날짜: 2024-08-09');
                        }
                        
                        return results;
                    }
                """)
                
                for result in date_set_result:
                    print(f"  {result}")
            
            # 콤보박스 테스트
            if fields_info['comboBoxes']:
                print(f"\n콤보박스 {len(fields_info['comboBoxes'])}개 발견")
                
                # 국내/해외 구분 찾기
                for combo in fields_info['comboBoxes']:
                    if '구분' in combo['label'] or 'DIV' in combo['name'].upper():
                        print(f"\n구분 콤보박스 발견: {combo['label']}")
                        print(f"  현재 값: {combo['displayValue']}")
                        
                        # 전체로 변경 시도
                        combo_result = await page.evaluate(f"""
                            () => {{
                                const combos = Ext.ComponentQuery.query('combobox');
                                const targetCombo = combos[{combo['index']}];
                                if (targetCombo) {{
                                    // 빈 값으로 설정 (보통 전체)
                                    targetCombo.setValue('');
                                    return '전체로 변경 시도';
                                }}
                                return '실패';
                            }}
                        """)
                        print(f"  결과: {combo_result}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"field_inspection_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"\n스크린샷 저장: {screenshot_path}")
            
            # JSON 저장
            json_path = data_dir / f"field_inspection_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(fields_info, f, ensure_ascii=False, indent=2)
            print(f"필드 정보 저장: {json_path}")
            
            print("\n분석 완료!")
            
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저를 30초 후 닫습니다...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(inspect_sales_screen())
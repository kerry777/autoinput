#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 - 탭 구조 이해 버전
메뉴 클릭 시 하단에 탭이 추가되는 구조
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
            print("\n1. Loading main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 2. 영업관리 모듈
            print("2. Clicking Sales module...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 매출관리 메뉴 확장
            print("3. Expanding Sales Management menu...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.includes('매출관리')) {
                            node.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            await page.wait_for_timeout(2000)
            
            # 4. 매출현황조회 메뉴 클릭 (새 탭 열림)
            print("4. Clicking Sales Status Inquiry (opens new tab)...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText === '매출현황조회') {
                            // 더블클릭으로 열기
                            const event = new MouseEvent('dblclick', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            node.dispatchEvent(event);
                            return 'double clicked';
                        }
                    }
                    return 'not found';
                }
            """)
            await page.wait_for_timeout(5000)
            
            # 5. 탭 패널 확인 및 활성 탭 변경
            print("\n5. Checking tab panel...")
            tab_info = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length > 0) {
                        const tabpanel = tabpanels[0];
                        const tabs = [];
                        
                        tabpanel.items.each(tab => {
                            tabs.push({
                                title: tab.title,
                                id: tab.id,
                                active: tab === tabpanel.getActiveTab()
                            });
                        });
                        
                        // 매출현황조회 탭 찾아서 활성화
                        tabpanel.items.each(tab => {
                            if(tab.title && tab.title.includes('매출현황')) {
                                tabpanel.setActiveTab(tab);
                                return;
                            }
                        });
                        
                        return {
                            totalTabs: tabs.length,
                            tabs: tabs,
                            activeTab: tabpanel.getActiveTab().title
                        };
                    }
                    return {totalTabs: 0};
                }
            """)
            
            print(f"   Total tabs: {tab_info.get('totalTabs', 0)}")
            if tab_info.get('tabs'):
                for tab in tab_info['tabs']:
                    active = " (ACTIVE)" if tab['active'] else ""
                    print(f"     - {tab['title']}{active}")
            print(f"   Current active tab: {tab_info.get('activeTab', 'none')}")
            
            # 6. 활성 탭의 컴포넌트 확인
            print("\n6. Analyzing active tab components...")
            active_tab_info = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length > 0) {
                        const activeTab = tabpanels[0].getActiveTab();
                        
                        // 활성 탭 내의 컴포넌트 찾기
                        const dateFields = activeTab.query('datefield');
                        const combos = activeTab.query('combobox');
                        const buttons = activeTab.query('button');
                        const grids = activeTab.query('grid');
                        
                        const result = {
                            tabTitle: activeTab.title,
                            dateFieldCount: dateFields.length,
                            comboCount: combos.length,
                            buttonCount: buttons.length,
                            gridCount: grids.length,
                            dateFields: [],
                            combos: [],
                            buttons: []
                        };
                        
                        // 날짜 필드 상세
                        dateFields.forEach(field => {
                            result.dateFields.push({
                                id: field.id,
                                name: field.name || '',
                                label: field.getFieldLabel ? field.getFieldLabel() : '',
                                value: field.getValue ? field.getValue() : null
                            });
                        });
                        
                        // 콤보박스 상세
                        combos.slice(0, 5).forEach(combo => {
                            result.combos.push({
                                id: combo.id,
                                name: combo.name || '',
                                label: combo.getFieldLabel ? combo.getFieldLabel() : ''
                            });
                        });
                        
                        // 버튼 상세
                        buttons.slice(0, 10).forEach(btn => {
                            result.buttons.push({
                                id: btn.id,
                                text: btn.getText ? btn.getText() : '',
                                tooltip: btn.tooltip || ''
                            });
                        });
                        
                        return result;
                    }
                    return {error: 'No tab panel found'};
                }
            """)
            
            print(f"   Active tab: {active_tab_info.get('tabTitle', 'unknown')}")
            print(f"   Components in active tab:")
            print(f"     - Date fields: {active_tab_info.get('dateFieldCount', 0)}")
            print(f"     - Combos: {active_tab_info.get('comboCount', 0)}")
            print(f"     - Buttons: {active_tab_info.get('buttonCount', 0)}")
            print(f"     - Grids: {active_tab_info.get('gridCount', 0)}")
            
            if active_tab_info.get('dateFields'):
                print("\n   Date fields:")
                for df in active_tab_info['dateFields']:
                    print(f"     - {df['label']} ({df['name']}): {df['value']}")
            
            if active_tab_info.get('buttons'):
                print("\n   Buttons:")
                for btn in active_tab_info['buttons']:
                    text = btn['text'] or btn['tooltip']
                    if text:
                        print(f"     - {text}")
            
            # 7. 날짜 설정 (활성 탭에서)
            if active_tab_info.get('dateFieldCount', 0) >= 2:
                print("\n7. Setting dates in active tab...")
                date_result = await page.evaluate("""
                    () => {
                        const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                        const activeTab = tabpanel.getActiveTab();
                        const dateFields = activeTab.query('datefield');
                        
                        if(dateFields.length >= 2) {
                            // 첫 번째 = 시작일
                            dateFields[0].setValue(new Date(2024, 7, 5));  // 2024.08.05
                            // 두 번째 = 종료일
                            dateFields[1].setValue(new Date(2024, 7, 9));  // 2024.08.09
                            
                            return 'Dates set: 2024.08.05 ~ 2024.08.09';
                        }
                        return 'Not enough date fields';
                    }
                """)
                print(f"   {date_result}")
            
            # 8. 구분 설정 (활성 탭에서)
            if active_tab_info.get('comboCount', 0) > 0:
                print("\n8. Setting division in active tab...")
                combo_result = await page.evaluate("""
                    () => {
                        const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                        const activeTab = tabpanel.getActiveTab();
                        const combos = activeTab.query('combobox');
                        
                        if(combos.length > 0) {
                            // 첫 번째 콤보를 전체로
                            combos[0].setValue('');
                            return 'Division set to ALL';
                        }
                        return 'No combo found';
                    }
                """)
                print(f"   {combo_result}")
            
            # 9. 조회 실행 (활성 탭에서)
            print("\n9. Execute query in active tab...")
            query_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const buttons = activeTab.query('button');
                    
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('조회') || text.includes('F2')) {
                            btn.fireEvent('click', btn);
                            return `Query button clicked: ${text}`;
                        }
                    }
                    
                    return 'Query button not found';
                }
            """)
            print(f"   {query_result}")
            
            # F2 키도 시도
            await page.keyboard.press('F2')
            print("   F2 key pressed")
            
            await page.wait_for_timeout(7000)
            
            # 10. 그리드 데이터 확인 (활성 탭에서)
            print("\n10. Check grid data in active tab...")
            grid_data = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const grids = activeTab.query('grid');
                    
                    if(grids.length > 0) {
                        const grid = grids[0];
                        const store = grid.getStore();
                        return {
                            count: store.getCount(),
                            total: store.getTotalCount()
                        };
                    }
                    return {count: 0, total: 0};
                }
            """)
            print(f"   Records: {grid_data['count']} / Total: {grid_data['total']}")
            
            # 11. 엑셀 다운로드 (활성 탭에서)
            print("\n11. Excel download from active tab...")
            
            # 다운로드 대기 설정
            download_promise = page.wait_for_event('download', timeout=10000)
            
            excel_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    
                    // 툴팁으로 엑셀 버튼 찾기
                    const buttons = activeTab.query('button');
                    for(let btn of buttons) {
                        const tooltip = btn.tooltip || '';
                        if(tooltip.includes('엑셀')) {
                            btn.fireEvent('click', btn);
                            return `Excel button clicked: ${tooltip}`;
                        }
                    }
                    
                    // 툴바 아이템 확인
                    const tools = activeTab.query('tool');
                    for(let tool of tools) {
                        if(tool.tooltip && tool.tooltip.includes('엑셀')) {
                            tool.fireEvent('click', tool);
                            return 'Excel tool clicked';
                        }
                    }
                    
                    return 'Excel button not found';
                }
            """)
            print(f"   {excel_result}")
            
            if "clicked" in excel_result:
                try:
                    download = await download_promise
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"sales_report_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   Download saved: {save_path}")
                except:
                    print("   Download timeout")
            
            # 12. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"sales_tab_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n12. Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("COMPLETE: Sales report automation with tab structure")
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
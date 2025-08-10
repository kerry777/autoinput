#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 최종 작동 버전
정확한 메뉴 텍스트: '매출현황 조회' (공백 포함)
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
            print("\n[1] Loading main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 2. 영업관리 모듈 (4번째 아이콘)
            print("[2] Clicking Sales module...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 매출관리 메뉴 확장 (인덱스 10)
            print("[3] Expanding Sales Management menu...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[10]) {
                        nodes[10].click();
                        return true;
                    }
                    return false;
                }
            """)
            await page.wait_for_timeout(3000)
            
            # 4. '매출현황 조회' 찾아서 더블클릭 (공백 포함)
            print("[4] Double-clicking '매출현황 조회'...")
            menu_result = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        // 정확한 텍스트 매칭 (공백 포함)
                        if(node.innerText && node.innerText.trim() === '매출현황 조회') {
                            // 더블클릭 이벤트
                            const dblClick = new MouseEvent('dblclick', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            node.dispatchEvent(dblClick);
                            return 'Found and double-clicked: 매출현황 조회';
                        }
                    }
                    
                    // 대체 검색 (부분 매칭)
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.includes('매출현황')) {
                            const dblClick = new MouseEvent('dblclick', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            node.dispatchEvent(dblClick);
                            return `Partial match clicked: ${node.innerText}`;
                        }
                    }
                    
                    return 'Menu not found';
                }
            """)
            print(f"   {menu_result}")
            
            # 탭이 열릴 때까지 대기
            await page.wait_for_timeout(5000)
            
            # 5. 새로 열린 탭 확인 및 활성화
            print("\n[5] Checking and activating new tab...")
            tab_result = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length === 0) return 'No tabpanel';
                    
                    const mainTab = tabpanels[0];
                    const tabs = [];
                    let salesTab = null;
                    
                    mainTab.items.each(tab => {
                        tabs.push(tab.title);
                        // 매출현황 탭 찾기
                        if(tab.title && (tab.title.includes('매출현황') || 
                                        tab.title.includes('매출 현황'))) {
                            salesTab = tab;
                        }
                    });
                    
                    if(salesTab) {
                        mainTab.setActiveTab(salesTab);
                        return {
                            success: true,
                            tabs: tabs,
                            activeTab: salesTab.title
                        };
                    }
                    
                    // 마지막 탭을 활성화 (새로 열린 탭일 가능성)
                    if(tabs.length > 1) {
                        const lastTab = mainTab.items.getAt(tabs.length - 1);
                        mainTab.setActiveTab(lastTab);
                        return {
                            success: true,
                            tabs: tabs,
                            activeTab: lastTab.title
                        };
                    }
                    
                    return {success: false, tabs: tabs};
                }
            """)
            
            if(isinstance(tab_result, dict)):
                print(f"   Success: {tab_result.get('success', False)}")
                print(f"   Tabs: {tab_result.get('tabs', [])}")
                print(f"   Active tab: {tab_result.get('activeTab', 'none')}")
            
            await page.wait_for_timeout(3000)
            
            # 6. 활성 탭에서 컴포넌트 확인
            print("\n[6] Checking components in active tab...")
            components = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    if(!tabpanel) return {error: 'No tabpanel'};
                    
                    const activeTab = tabpanel.getActiveTab();
                    if(!activeTab) return {error: 'No active tab'};
                    
                    const dateFields = activeTab.query('datefield');
                    const combos = activeTab.query('combobox');
                    const buttons = activeTab.query('button');
                    const grids = activeTab.query('grid');
                    
                    return {
                        tabTitle: activeTab.title,
                        dateFields: dateFields.length,
                        combos: combos.length,
                        buttons: buttons.length,
                        grids: grids.length
                    };
                }
            """)
            
            print(f"   Tab: {components.get('tabTitle', 'unknown')}")
            print(f"   Date fields: {components.get('dateFields', 0)}")
            print(f"   Combos: {components.get('combos', 0)}")
            print(f"   Buttons: {components.get('buttons', 0)}")
            print(f"   Grids: {components.get('grids', 0)}")
            
            # 7. 날짜 설정 (2024.08.05 ~ 2024.08.09)
            if components.get('dateFields', 0) >= 2:
                print("\n[7] Setting dates...")
                date_result = await page.evaluate("""
                    () => {
                        const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                        const activeTab = tabpanel.getActiveTab();
                        const dateFields = activeTab.query('datefield');
                        
                        if(dateFields.length >= 2) {
                            // 시작일
                            dateFields[0].setValue(new Date(2024, 7, 5));
                            // 종료일
                            dateFields[1].setValue(new Date(2024, 7, 9));
                            
                            return 'Dates set: 2024.08.05 ~ 2024.08.09';
                        }
                        
                        return 'Not enough date fields';
                    }
                """)
                print(f"   {date_result}")
            
            # 8. 구분을 '전체'로 설정
            if components.get('combos', 0) > 0:
                print("\n[8] Setting division to ALL...")
                combo_result = await page.evaluate("""
                    () => {
                        const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                        const activeTab = tabpanel.getActiveTab();
                        const combos = activeTab.query('combobox');
                        
                        if(combos.length > 0) {
                            // 첫 번째 콤보를 전체로 (빈 값)
                            combos[0].setValue('');
                            return 'Division set to ALL';
                        }
                        
                        return 'No combos found';
                    }
                """)
                print(f"   {combo_result}")
            
            # 9. 조회 실행 (F2)
            print("\n[9] Executing query...")
            
            # F2 키 누르기
            await page.keyboard.press('F2')
            print("   F2 key pressed")
            
            # 조회 버튼도 시도
            button_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const buttons = activeTab.query('button');
                    
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('조회') || text.includes('검색')) {
                            btn.fireEvent('click', btn);
                            return `Query button clicked: ${text}`;
                        }
                    }
                    
                    return 'No query button found';
                }
            """)
            print(f"   {button_result}")
            
            # 데이터 로딩 대기
            print("   Waiting for data to load...")
            await page.wait_for_timeout(7000)
            
            # 10. 조회 결과 확인
            print("\n[10] Checking query results...")
            grid_data = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const grids = activeTab.query('grid');
                    
                    if(grids.length > 0) {
                        const grid = grids[0];
                        const store = grid.getStore();
                        const count = store.getCount();
                        
                        // 첫 3개 레코드 샘플
                        const sample = [];
                        const items = store.getData().items.slice(0, 3);
                        items.forEach(item => {
                            // 주요 필드만 추출
                            const data = {};
                            const keys = Object.keys(item.data).slice(0, 5);
                            keys.forEach(key => {
                                data[key] = item.data[key];
                            });
                            sample.push(data);
                        });
                        
                        return {
                            count: count,
                            total: store.getTotalCount(),
                            loading: store.isLoading(),
                            sample: sample
                        };
                    }
                    
                    return {count: 0, total: 0};
                }
            """)
            
            print(f"   Records: {grid_data.get('count', 0)} / Total: {grid_data.get('total', 0)}")
            if grid_data.get('sample'):
                print("   Sample data (first 3 records):")
                for i, record in enumerate(grid_data['sample']):
                    print(f"     Record {i+1}: {record}")
            
            # 11. 엑셀 다운로드
            print("\n[11] Downloading Excel...")
            
            # 다운로드 대기 설정
            download_promise = page.wait_for_event('download', timeout=10000)
            
            excel_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    
                    // 버튼에서 엑셀 찾기
                    const buttons = activeTab.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        
                        if(text.includes('엑셀') || text.includes('Excel') ||
                           tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                            btn.fireEvent('click', btn);
                            return 'Excel button clicked';
                        }
                    }
                    
                    // 툴에서 찾기
                    const tools = activeTab.query('tool');
                    for(let tool of tools) {
                        if(tool.tooltip && tool.tooltip.includes('엑셀')) {
                            tool.fireEvent('click', tool);
                            return 'Excel tool clicked';
                        }
                    }
                    
                    // DOM에서 직접 찾기
                    const elements = activeTab.getEl().dom.querySelectorAll('[title*="엑셀"], [tooltip*="엑셀"]');
                    if(elements.length > 0) {
                        elements[0].click();
                        return 'Excel element clicked';
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
                    print(f"   ✓ Excel saved: {save_path}")
                except asyncio.TimeoutError:
                    print("   × Download timeout")
            
            # 12. 최종 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"sales_complete_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[12] Final screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("SALES REPORT AUTOMATION COMPLETE!")
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
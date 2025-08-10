#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 최종 솔루션
왼쪽 트리 메뉴 클릭 -> 오른쪽에 탭 생성 -> 탭에서 작업
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
            print("Cookie loaded")
        
        page = await context.new_page()
        
        try:
            # 1. 메인 페이지
            print("\n[1] Main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 2. 영업관리 모듈 클릭 (4번째 아이콘)
            print("[2] Sales module (14)...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 왼쪽 트리에서 매출관리 확장
            print("[3] Expand '매출관리'...")
            expand_result = await page.evaluate("""
                () => {
                    // 매출관리 노드 찾기
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.trim() === '매출관리') {
                            // 노드 클릭으로 확장
                            node.click();
                            return 'expanded';
                        }
                    }
                    return 'not found';
                }
            """)
            print(f"   {expand_result}")
            await page.wait_for_timeout(2000)
            
            # 4. 매출현황조회 더블클릭으로 탭 열기
            print("[4] Double-click '매출현황조회' to open tab...")
            open_result = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.trim() === '매출현황조회') {
                            // 더블클릭 이벤트
                            const dblClickEvent = new MouseEvent('dblclick', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            node.dispatchEvent(dblClickEvent);
                            return 'double-clicked';
                        }
                    }
                    return 'not found';
                }
            """)
            print(f"   {open_result}")
            
            # 탭이 열릴 때까지 대기
            await page.wait_for_timeout(5000)
            
            # 5. 탭 확인 및 매출현황조회 탭 활성화
            print("\n[5] Check tabs and activate '매출현황조회'...")
            tab_result = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length === 0) return 'No tabpanel';
                    
                    const mainTabPanel = tabpanels[0];
                    const tabs = [];
                    let salesTab = null;
                    
                    // 모든 탭 확인
                    mainTabPanel.items.each(tab => {
                        tabs.push(tab.title);
                        // 매출현황 관련 탭 찾기
                        if(tab.title && (tab.title.includes('매출현황') || tab.title.includes('매출 현황'))) {
                            salesTab = tab;
                        }
                    });
                    
                    if(salesTab) {
                        // 매출현황 탭 활성화
                        mainTabPanel.setActiveTab(salesTab);
                        return {
                            status: 'activated',
                            tabs: tabs,
                            activeTab: salesTab.title
                        };
                    }
                    
                    return {
                        status: 'not found',
                        tabs: tabs
                    };
                }
            """)
            
            if isinstance(tab_result, dict):
                print(f"   Status: {tab_result.get('status', 'unknown')}")
                print(f"   Tabs: {tab_result.get('tabs', [])}")
                print(f"   Active: {tab_result.get('activeTab', 'none')}")
            else:
                print(f"   {tab_result}")
            
            await page.wait_for_timeout(3000)
            
            # 6. 활성 탭에서 컴포넌트 확인
            print("\n[6] Analyze components in active tab...")
            components = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    if(!tabpanel) return {error: 'No tabpanel'};
                    
                    const activeTab = tabpanel.getActiveTab();
                    if(!activeTab) return {error: 'No active tab'};
                    
                    // 활성 탭 내의 모든 컴포넌트 찾기
                    const dateFields = activeTab.query('datefield');
                    const textFields = activeTab.query('textfield');
                    const combos = activeTab.query('combobox');
                    const buttons = activeTab.query('button');
                    const grids = activeTab.query('grid');
                    
                    const result = {
                        tabTitle: activeTab.title,
                        dateFields: dateFields.length,
                        textFields: textFields.length,
                        combos: combos.length,
                        buttons: buttons.length,
                        grids: grids.length,
                        dateFieldInfo: [],
                        buttonInfo: []
                    };
                    
                    // 날짜 필드 정보
                    dateFields.forEach((field, idx) => {
                        result.dateFieldInfo.push({
                            index: idx,
                            id: field.id,
                            name: field.name || '',
                            label: field.getFieldLabel ? field.getFieldLabel() : ''
                        });
                    });
                    
                    // 버튼 정보 (처음 10개)
                    buttons.slice(0, 10).forEach(btn => {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        if(text || tooltip) {
                            result.buttonInfo.push(text || tooltip);
                        }
                    });
                    
                    return result;
                }
            """)
            
            print(f"   Tab: {components.get('tabTitle', 'unknown')}")
            print(f"   Date fields: {components.get('dateFields', 0)}")
            print(f"   Text fields: {components.get('textFields', 0)}")
            print(f"   Combos: {components.get('combos', 0)}")
            print(f"   Buttons: {components.get('buttons', 0)}")
            print(f"   Grids: {components.get('grids', 0)}")
            
            # 7. 날짜 설정
            if components.get('dateFields', 0) >= 2:
                print("\n[7] Set dates (2024.08.05 ~ 2024.08.09)...")
                date_result = await page.evaluate("""
                    () => {
                        const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                        const activeTab = tabpanel.getActiveTab();
                        const dateFields = activeTab.query('datefield');
                        
                        if(dateFields.length >= 2) {
                            dateFields[0].setValue(new Date(2024, 7, 5));  // 08.05
                            dateFields[1].setValue(new Date(2024, 7, 9));  // 08.09
                            
                            const from = dateFields[0].getValue();
                            const to = dateFields[1].getValue();
                            
                            return `Set: ${from} ~ ${to}`;
                        }
                        return 'Not enough date fields';
                    }
                """)
                print(f"   {date_result}")
            
            # 8. 구분 설정
            if components.get('combos', 0) > 0:
                print("\n[8] Set division to 'ALL'...")
                combo_result = await page.evaluate("""
                    () => {
                        const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                        const activeTab = tabpanel.getActiveTab();
                        const combos = activeTab.query('combobox');
                        
                        for(let combo of combos) {
                            const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                            if(label.includes('구분')) {
                                combo.setValue('');  // 전체
                                return `Set ${label} to ALL`;
                            }
                        }
                        
                        // 첫 번째 콤보 사용
                        if(combos.length > 0) {
                            combos[0].setValue('');
                            return 'Set first combo to ALL';
                        }
                        
                        return 'No combo';
                    }
                """)
                print(f"   {combo_result}")
            
            # 9. 조회 실행
            print("\n[9] Execute query...")
            
            # 조회 버튼 찾기
            query_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const buttons = activeTab.query('button');
                    
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        
                        if(text.includes('조회') || text.includes('검색') || 
                           text.includes('F2') || tooltip.includes('조회')) {
                            btn.fireEvent('click', btn);
                            return `Clicked: ${text || tooltip}`;
                        }
                    }
                    
                    return 'Query button not found';
                }
            """)
            print(f"   {query_result}")
            
            # F2 키도 누르기
            await page.keyboard.press('F2')
            print("   F2 pressed")
            
            # 데이터 로딩 대기
            print("   Loading data...")
            await page.wait_for_timeout(7000)
            
            # 10. 데이터 확인
            print("\n[10] Check data...")
            grid_info = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const grids = activeTab.query('grid');
                    
                    if(grids.length > 0) {
                        const grid = grids[0];
                        const store = grid.getStore();
                        const count = store.getCount();
                        
                        // 샘플 데이터
                        const sample = [];
                        const items = store.getData().items.slice(0, 3);
                        items.forEach(item => {
                            const data = item.data;
                            sample.push(Object.keys(data).slice(0, 5));
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
            print(f"   Records: {grid_info.get('count', 0)}")
            
            # 11. 엑셀 다운로드
            print("\n[11] Excel download...")
            
            # 엑셀 버튼 클릭
            excel_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    
                    // 버튼에서 찾기
                    const buttons = activeTab.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        
                        if(text.includes('엑셀') || text.includes('Excel') ||
                           tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                            btn.fireEvent('click', btn);
                            return `Excel clicked: ${text || tooltip}`;
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
                    
                    // DOM에서 직접 찾기 (툴팁)
                    const elements = activeTab.getEl().dom.querySelectorAll('[title*="엑셀"]');
                    if(elements.length > 0) {
                        elements[0].click();
                        return 'Excel element clicked';
                    }
                    
                    return 'Excel not found';
                }
            """)
            print(f"   {excel_result}")
            
            # 다운로드 대기
            if "clicked" in excel_result:
                try:
                    async with page.expect_download(timeout=10000) as download_info:
                        await page.wait_for_timeout(1000)
                    download = await download_info.value
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"sales_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   Saved: {save_path}")
                except:
                    print("   Download failed")
            
            # 12. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"final_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[12] Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("SUCCESS: Sales report automation complete!")
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
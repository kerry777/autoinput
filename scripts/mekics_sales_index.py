#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 - 인덱스 기반 접근
트리 메뉴 항목을 인덱스로 정확히 클릭
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
            
            # 2. 영업관리 모듈
            print("[2] Sales module...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 트리 메뉴 확인
            print("[3] Check tree menu...")
            tree_items = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const items = [];
                    nodes.forEach((node, idx) => {
                        if(node.innerText) {
                            items.push({
                                index: idx,
                                text: node.innerText.trim()
                            });
                        }
                    });
                    return items;
                }
            """)
            
            print(f"   Found {len(tree_items)} menu items")
            
            # 4. 인덱스 10번 (매출관리) 클릭하여 확장
            print("\n[4] Click index 10 to expand...")
            expand_result = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[10]) {
                        nodes[10].click();
                        return 'clicked index 10';
                    }
                    return 'index 10 not found';
                }
            """)
            print(f"   {expand_result}")
            await page.wait_for_timeout(3000)
            
            # 5. 확장된 메뉴 확인
            print("\n[5] Check expanded menu...")
            tree_items_after = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const items = [];
                    nodes.forEach((node, idx) => {
                        if(node.innerText) {
                            items.push({
                                index: idx,
                                text: node.innerText.trim()
                            });
                        }
                    });
                    return items;
                }
            """)
            
            print(f"   Now {len(tree_items_after)} menu items")
            if len(tree_items_after) > len(tree_items):
                print("   Sub-menu expanded!")
                # 새로 추가된 항목들 출력
                for i in range(len(tree_items), min(len(tree_items_after), len(tree_items) + 10)):
                    print(f"     [{i}] {tree_items_after[i]['text']}")
            
            # 6. 매출현황조회 더블클릭 (보통 첫 번째 서브메뉴)
            print("\n[6] Double-click sales inquiry menu...")
            # 인덱스 11이 매출현황조회일 가능성이 높음
            open_result = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    // 매출관리 다음 항목 더블클릭
                    if(nodes[11]) {
                        const dblClick = new MouseEvent('dblclick', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        nodes[11].dispatchEvent(dblClick);
                        return `Double-clicked index 11: ${nodes[11].innerText}`;
                    }
                    return 'index 11 not found';
                }
            """)
            print(f"   {open_result}")
            await page.wait_for_timeout(5000)
            
            # 7. 탭 확인
            print("\n[7] Check tabs...")
            tab_info = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length > 0) {
                        const mainTab = tabpanels[0];
                        const tabs = [];
                        let targetTab = null;
                        
                        mainTab.items.each(tab => {
                            tabs.push(tab.title);
                            // 새로 열린 탭 찾기 (시스템이 아닌 탭)
                            if(tab.title && !tab.title.includes('시스템') && 
                               !tab.title.includes('Home') && !tab.title.includes('즐겨찾기')) {
                                targetTab = tab;
                            }
                        });
                        
                        if(targetTab) {
                            mainTab.setActiveTab(targetTab);
                            return {
                                tabs: tabs,
                                activeTab: targetTab.title,
                                activated: true
                            };
                        }
                        
                        return {tabs: tabs, activated: false};
                    }
                    return {error: 'No tabpanel'};
                }
            """)
            
            print(f"   Tabs: {tab_info.get('tabs', [])}")
            print(f"   Active: {tab_info.get('activeTab', 'none')}")
            print(f"   Activated: {tab_info.get('activated', False)}")
            
            await page.wait_for_timeout(3000)
            
            # 8. 활성 탭에서 작업
            print("\n[8] Work in active tab...")
            
            # 날짜 설정
            date_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    if(!tabpanel) return 'No tabpanel';
                    
                    const activeTab = tabpanel.getActiveTab();
                    const dateFields = activeTab.query('datefield');
                    
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2024, 7, 5));  // 2024.08.05
                        dateFields[1].setValue(new Date(2024, 7, 9));  // 2024.08.09
                        return `Dates set: ${dateFields.length} fields`;
                    }
                    
                    return `Only ${dateFields.length} date fields`;
                }
            """)
            print(f"   Dates: {date_result}")
            
            # 구분 설정
            combo_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const combos = activeTab.query('combobox');
                    
                    if(combos.length > 0) {
                        combos[0].setValue('');  // 전체
                        return `Combo set: ${combos.length} combos`;
                    }
                    
                    return 'No combos';
                }
            """)
            print(f"   Division: {combo_result}")
            
            # 9. 조회 실행
            print("\n[9] Execute query...")
            
            # F2 키 누르기
            await page.keyboard.press('F2')
            print("   F2 pressed")
            
            # 또는 조회 버튼 클릭
            query_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const buttons = activeTab.query('button');
                    
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('조회')) {
                            btn.fireEvent('click', btn);
                            return `Query button clicked: ${text}`;
                        }
                    }
                    
                    return 'No query button';
                }
            """)
            print(f"   {query_result}")
            
            print("   Loading data...")
            await page.wait_for_timeout(7000)
            
            # 10. 데이터 확인
            print("\n[10] Check data...")
            data_info = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    const grids = activeTab.query('grid');
                    
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        return {
                            records: store.getCount(),
                            loading: store.isLoading()
                        };
                    }
                    
                    return {records: 0};
                }
            """)
            print(f"   Records: {data_info.get('records', 0)}")
            
            # 11. 엑셀 다운로드
            print("\n[11] Excel download...")
            excel_result = await page.evaluate("""
                () => {
                    const tabpanel = Ext.ComponentQuery.query('tabpanel')[0];
                    const activeTab = tabpanel.getActiveTab();
                    
                    // 툴팁으로 찾기
                    const elements = activeTab.getEl().dom.querySelectorAll('[title*="엑셀"], [tooltip*="엑셀"]');
                    if(elements.length > 0) {
                        elements[0].click();
                        return 'Excel element clicked';
                    }
                    
                    // 버튼에서 찾기
                    const buttons = activeTab.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        if(text.includes('엑셀') || tooltip.includes('엑셀')) {
                            btn.fireEvent('click', btn);
                            return 'Excel button clicked';
                        }
                    }
                    
                    return 'Excel not found';
                }
            """)
            print(f"   {excel_result}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"sales_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[12] Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("COMPLETE!")
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
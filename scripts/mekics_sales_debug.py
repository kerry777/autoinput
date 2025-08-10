#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 디버깅 버전
각 단계별 상세 확인
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
            # 메인 페이지
            print("\n[STEP 1] Loading main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 영업관리 모듈
            print("\n[STEP 2] Clicking Sales module (14)...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 왼쪽 트리 메뉴 확인
            print("\n[STEP 3] Checking left tree menu...")
            tree_items = await page.evaluate("""
                () => {
                    const items = [];
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    nodes.forEach(node => {
                        if(node.innerText) {
                            items.push(node.innerText.trim());
                        }
                    });
                    return items;
                }
            """)
            print(f"   Tree items found: {len(tree_items)}")
            for item in tree_items[:10]:  # 처음 10개만
                print(f"     - {item}")
            
            # 매출관리 클릭
            print("\n[STEP 4] Clicking '매출관리'...")
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
            
            # 매출현황조회 클릭
            print("\n[STEP 5] Clicking '매출현황조회'...")
            click_result = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText === '매출현황조회') {
                            node.click();
                            return 'clicked';
                        }
                    }
                    return 'not found';
                }
            """)
            print(f"   Result: {click_result}")
            await page.wait_for_timeout(5000)
            
            # 화면 상태 확인
            print("\n[STEP 6] Analyzing screen after menu click...")
            
            # 프레임 확인
            frames = page.frames
            print(f"   Frames: {len(frames)}")
            for i, frame in enumerate(frames):
                if "about:blank" not in frame.url:
                    print(f"     Frame {i}: {frame.url}")
            
            # 탭 패널 확인
            tab_info = await page.evaluate("""
                () => {
                    const tabs = Ext.ComponentQuery.query('tabpanel');
                    if(tabs.length > 0) {
                        const activeTab = tabs[0].getActiveTab();
                        return {
                            tabCount: tabs[0].items.length,
                            activeTitle: activeTab ? activeTab.title : 'none'
                        };
                    }
                    return {tabCount: 0};
                }
            """)
            print(f"   Tabs: {tab_info}")
            
            # 패널 확인
            panel_info = await page.evaluate("""
                () => {
                    const panels = Ext.ComponentQuery.query('panel');
                    const result = [];
                    panels.slice(0, 5).forEach(panel => {
                        if(panel.title) {
                            result.push(panel.title);
                        }
                    });
                    return result;
                }
            """)
            print(f"   Panel titles: {panel_info}")
            
            # 모든 컴포넌트 타입 확인
            print("\n[STEP 7] Checking all ExtJS components...")
            components = await page.evaluate("""
                () => {
                    const result = {};
                    
                    // 각 타입별 컴포넌트 수
                    result.datefields = Ext.ComponentQuery.query('datefield').length;
                    result.textfields = Ext.ComponentQuery.query('textfield').length;
                    result.combos = Ext.ComponentQuery.query('combobox').length;
                    result.buttons = Ext.ComponentQuery.query('button').length;
                    result.grids = Ext.ComponentQuery.query('grid').length;
                    result.forms = Ext.ComponentQuery.query('form').length;
                    result.panels = Ext.ComponentQuery.query('panel').length;
                    
                    // 날짜 필드 상세
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    result.dateDetails = dateFields.map(f => ({
                        id: f.id,
                        name: f.name || '',
                        label: f.getFieldLabel ? f.getFieldLabel() : '',
                        visible: f.isVisible()
                    }));
                    
                    // 텍스트 필드 중 날짜 관련
                    const textFields = Ext.ComponentQuery.query('textfield');
                    result.dateTextFields = [];
                    textFields.forEach(f => {
                        if(f.name && (f.name.includes('DATE') || f.name.includes('일'))) {
                            result.dateTextFields.push({
                                id: f.id,
                                name: f.name,
                                label: f.getFieldLabel ? f.getFieldLabel() : '',
                                visible: f.isVisible()
                            });
                        }
                    });
                    
                    return result;
                }
            """)
            
            print(f"   Component counts:")
            print(f"     - Date fields: {components['datefields']}")
            print(f"     - Text fields: {components['textfields']}")
            print(f"     - Combos: {components['combos']}")
            print(f"     - Buttons: {components['buttons']}")
            print(f"     - Grids: {components['grids']}")
            print(f"     - Forms: {components['forms']}")
            print(f"     - Panels: {components['panels']}")
            
            if components['dateDetails']:
                print(f"\n   Date field details:")
                for df in components['dateDetails']:
                    print(f"     - {df}")
            
            if components['dateTextFields']:
                print(f"\n   Date-related text fields:")
                for tf in components['dateTextFields']:
                    print(f"     - {tf}")
            
            # DOM 직접 확인
            print("\n[STEP 8] Checking DOM directly...")
            dom_info = await page.evaluate("""
                () => {
                    const result = {};
                    
                    // name 속성으로 찾기
                    result.saleFromDate = document.querySelector('input[name="SALE_FR_DATE"]') !== null;
                    result.saleToDate = document.querySelector('input[name="SALE_TO_DATE"]') !== null;
                    
                    // 모든 input 중 DATE를 포함하는 것
                    const dateInputs = document.querySelectorAll('input[name*="DATE"]');
                    result.dateInputCount = dateInputs.length;
                    result.dateInputs = [];
                    dateInputs.forEach(input => {
                        result.dateInputs.push({
                            name: input.name,
                            type: input.type,
                            value: input.value,
                            visible: input.offsetParent !== null
                        });
                    });
                    
                    return result;
                }
            """)
            
            print(f"   DOM Check:")
            print(f"     - SALE_FR_DATE exists: {dom_info['saleFromDate']}")
            print(f"     - SALE_TO_DATE exists: {dom_info['saleToDate']}")
            print(f"     - Date inputs found: {dom_info['dateInputCount']}")
            if dom_info['dateInputs']:
                for inp in dom_info['dateInputs']:
                    print(f"       * {inp}")
            
            # 화면 HTML 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            page_html = await page.content()
            html_file = data_dir / f"debug_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_html)
            print(f"\n[STEP 9] HTML saved: {html_file}")
            
            # 스크린샷
            screenshot_path = data_dir / f"debug_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[STEP 10] Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("DEBUG ANALYSIS COMPLETE")
            print("Check the screenshot and HTML file for current screen state")
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
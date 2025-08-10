#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 iframe 접근 버전
매출현황 조회 화면이 iframe으로 로드됨: /mekics/sales/ssa450skrv.do
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
            print("Cookies loaded")
        
        page = await context.new_page()
        
        try:
            # 1. 메인 페이지 로드
            print("\n[1] Loading main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 2. 영업관리 모듈 선택
            print("[2] Selecting Sales module...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 매출관리 메뉴 확장
            print("[3] Expanding Sales Management menu...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    // 인덱스 10이 매출관리
                    if(nodes[10]) {
                        nodes[10].click();
                        return true;
                    }
                    return false;
                }
            """)
            await page.wait_for_timeout(3000)
            
            # 4. 매출현황 조회 메뉴 찾아서 더블클릭
            print("[4] Opening Sales Status Inquiry...")
            menu_result = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let i = 0; i < nodes.length; i++) {
                        const text = nodes[i].innerText ? nodes[i].innerText.trim() : '';
                        // 여러 가능한 텍스트 패턴 확인
                        if(text === '매출현황 조회' || 
                           text === '매출현황조회' || 
                           text.includes('매출현황')) {
                            // 더블클릭
                            const dblClick = new MouseEvent('dblclick', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            nodes[i].dispatchEvent(dblClick);
                            return `Clicked: ${text} at index ${i}`;
                        }
                    }
                    
                    // 못 찾으면 인덱스로 시도 (보통 11 또는 12)
                    if(nodes[11]) {
                        const dblClick = new MouseEvent('dblclick', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        nodes[11].dispatchEvent(dblClick);
                        return `Clicked index 11: ${nodes[11].innerText}`;
                    }
                    
                    return 'Menu not found';
                }
            """)
            print(f"   {menu_result}")
            
            # 탭이 열리고 iframe이 로드될 때까지 대기
            await page.wait_for_timeout(5000)
            
            # 5. iframe 찾기
            print("\n[5] Looking for iframe...")
            
            # 먼저 탭 활성화
            tab_result = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length > 0) {
                        const mainTab = tabpanels[0];
                        // 마지막 탭이 새로 열린 탭
                        const lastTab = mainTab.items.getAt(mainTab.items.length - 1);
                        if(lastTab) {
                            mainTab.setActiveTab(lastTab);
                            return `Activated tab: ${lastTab.title}`;
                        }
                    }
                    return 'No tabs';
                }
            """)
            print(f"   {tab_result}")
            
            await page.wait_for_timeout(3000)
            
            # iframe 확인
            iframe_info = await page.evaluate("""
                () => {
                    const iframes = document.querySelectorAll('iframe');
                    const result = [];
                    iframes.forEach(iframe => {
                        if(iframe.src && iframe.src.includes('ssa450skrv')) {
                            result.push({
                                id: iframe.id,
                                name: iframe.name,
                                src: iframe.src
                            });
                        }
                    });
                    return result;
                }
            """)
            
            if iframe_info:
                print(f"   Found iframe: {iframe_info[0]}")
                
                # 6. iframe 내부 접근
                print("\n[6] Accessing iframe content...")
                
                # iframe 선택자
                iframe_selector = f'iframe[src*="ssa450skrv"]'
                frame_element = await page.query_selector(iframe_selector)
                
                if frame_element:
                    frame = await frame_element.content_frame()
                    
                    if frame:
                        print("   Successfully accessed iframe")
                        
                        # 7. iframe 내부에서 컴포넌트 확인
                        print("\n[7] Checking components in iframe...")
                        components = await frame.evaluate("""
                            () => {
                                if(typeof Ext === 'undefined') {
                                    return {error: 'ExtJS not loaded in iframe'};
                                }
                                
                                const dateFields = Ext.ComponentQuery.query('datefield');
                                const combos = Ext.ComponentQuery.query('combobox');
                                const buttons = Ext.ComponentQuery.query('button');
                                const grids = Ext.ComponentQuery.query('grid');
                                
                                return {
                                    dateFields: dateFields.length,
                                    combos: combos.length,
                                    buttons: buttons.length,
                                    grids: grids.length
                                };
                            }
                        """)
                        
                        print(f"   Date fields: {components.get('dateFields', 0)}")
                        print(f"   Combos: {components.get('combos', 0)}")
                        print(f"   Buttons: {components.get('buttons', 0)}")
                        print(f"   Grids: {components.get('grids', 0)}")
                        
                        # 8. 날짜 설정
                        if components.get('dateFields', 0) >= 2:
                            print("\n[8] Setting dates in iframe...")
                            date_result = await frame.evaluate("""
                                () => {
                                    const dateFields = Ext.ComponentQuery.query('datefield');
                                    if(dateFields.length >= 2) {
                                        // 시작일 2024.08.05
                                        dateFields[0].setValue(new Date(2024, 7, 5));
                                        // 종료일 2024.08.09
                                        dateFields[1].setValue(new Date(2024, 7, 9));
                                        return 'Dates set: 2024.08.05 ~ 2024.08.09';
                                    }
                                    return 'Not enough date fields';
                                }
                            """)
                            print(f"   {date_result}")
                        
                        # 9. 구분 설정
                        if components.get('combos', 0) > 0:
                            print("\n[9] Setting division in iframe...")
                            combo_result = await frame.evaluate("""
                                () => {
                                    const combos = Ext.ComponentQuery.query('combobox');
                                    if(combos.length > 0) {
                                        // 첫 번째 콤보를 전체로
                                        combos[0].setValue('');
                                        return 'Division set to ALL';
                                    }
                                    return 'No combos';
                                }
                            """)
                            print(f"   {combo_result}")
                        
                        # 10. 조회 실행
                        print("\n[10] Executing query in iframe...")
                        
                        # F2 키 누르기 (iframe에서)
                        await frame.keyboard.press('F2')
                        print("   F2 pressed in iframe")
                        
                        # 조회 버튼 클릭
                        button_result = await frame.evaluate("""
                            () => {
                                const buttons = Ext.ComponentQuery.query('button');
                                for(let btn of buttons) {
                                    const text = btn.getText ? btn.getText() : '';
                                    if(text.includes('조회') || text.includes('검색')) {
                                        btn.fireEvent('click', btn);
                                        return `Query button clicked: ${text}`;
                                    }
                                }
                                return 'No query button';
                            }
                        """)
                        print(f"   {button_result}")
                        
                        # 데이터 로딩 대기
                        print("   Waiting for data...")
                        await page.wait_for_timeout(7000)
                        
                        # 11. 결과 확인
                        print("\n[11] Checking results in iframe...")
                        grid_data = await frame.evaluate("""
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
                        print(f"   Records: {grid_data.get('count', 0)} / Total: {grid_data.get('total', 0)}")
                        
                        # 12. 엑셀 다운로드
                        print("\n[12] Excel download from iframe...")
                        
                        # 다운로드 대기 설정
                        download_promise = page.wait_for_event('download', timeout=10000)
                        
                        excel_result = await frame.evaluate("""
                            () => {
                                // 버튼에서 찾기
                                const buttons = Ext.ComponentQuery.query('button');
                                for(let btn of buttons) {
                                    const text = btn.getText ? btn.getText() : '';
                                    const tooltip = btn.tooltip || '';
                                    
                                    if(text.includes('엑셀') || tooltip.includes('엑셀')) {
                                        btn.fireEvent('click', btn);
                                        return 'Excel button clicked';
                                    }
                                }
                                
                                // DOM에서 찾기
                                const elements = document.querySelectorAll('[title*="엑셀"]');
                                if(elements.length > 0) {
                                    elements[0].click();
                                    return 'Excel element clicked';
                                }
                                
                                return 'Excel not found';
                            }
                        """)
                        print(f"   {excel_result}")
                        
                        if "clicked" in excel_result:
                            try:
                                download = await download_promise
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                save_path = data_dir / f"sales_{timestamp}.xlsx"
                                await download.save_as(str(save_path))
                                print(f"   ✓ Saved: {save_path}")
                            except asyncio.TimeoutError:
                                print("   × Download timeout")
                    else:
                        print("   Could not access iframe content")
                else:
                    print("   iframe element not found")
            else:
                print("   No iframe with ssa450skrv found")
            
            # 13. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"iframe_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n[13] Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("COMPLETE: Sales report automation with iframe")
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
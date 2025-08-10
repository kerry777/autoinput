#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 메뉴 테스트
각 메뉴를 더블클릭해서 어떤 탭이 열리는지 확인
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def test_menus():
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
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 영업관리
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            print("\n" + "="*60)
            print("TESTING MENU ITEMS")
            print("="*60)
            
            # 매출관리 확장
            print("\n[1] Expanding 매출관리...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[10]) nodes[10].click();
                }
            """)
            await page.wait_for_timeout(3000)
            
            # 인덱스 11 더블클릭 (연간고객체결내역)
            print("\n[2] Double-clicking index 11...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[11]) {
                        const text = nodes[11].innerText;
                        console.log('Menu text:', text);
                        const dblClick = new MouseEvent('dblclick', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        nodes[11].dispatchEvent(dblClick);
                    }
                }
            """)
            await page.wait_for_timeout(5000)
            
            # 열린 탭 확인
            tab_info_11 = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length > 0) {
                        const tabs = [];
                        tabpanels[0].items.each(tab => {
                            tabs.push(tab.title);
                        });
                        return tabs;
                    }
                    return [];
                }
            """)
            print(f"   Tabs after index 11: {tab_info_11}")
            
            # iframe 확인
            iframe_11 = await page.evaluate("""
                () => {
                    const iframes = document.querySelectorAll('iframe');
                    const result = [];
                    iframes.forEach(iframe => {
                        if(iframe.src && !iframe.src.includes('about:blank')) {
                            result.push(iframe.src);
                        }
                    });
                    return result;
                }
            """)
            print(f"   iframes: {iframe_11}")
            
            # 인덱스 12 더블클릭 (연간고객체결현황)
            print("\n[3] Double-clicking index 12...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[12]) {
                        const text = nodes[12].innerText;
                        console.log('Menu text:', text);
                        const dblClick = new MouseEvent('dblclick', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        nodes[12].dispatchEvent(dblClick);
                    }
                }
            """)
            await page.wait_for_timeout(5000)
            
            # 열린 탭 확인
            tab_info_12 = await page.evaluate("""
                () => {
                    const tabpanels = Ext.ComponentQuery.query('tabpanel');
                    if(tabpanels.length > 0) {
                        const tabs = [];
                        tabpanels[0].items.each(tab => {
                            tabs.push(tab.title);
                        });
                        return tabs;
                    }
                    return [];
                }
            """)
            print(f"   Tabs after index 12: {tab_info_12}")
            
            # iframe 확인
            iframe_12 = await page.evaluate("""
                () => {
                    const iframes = document.querySelectorAll('iframe');
                    const result = [];
                    iframes.forEach(iframe => {
                        if(iframe.src && !iframe.src.includes('about:blank')) {
                            result.push(iframe.src);
                        }
                    });
                    return result;
                }
            """)
            print(f"   iframes: {iframe_12}")
            
            # 매출현황 조회를 직접 찾기
            print("\n[4] Searching for exact '매출현황 조회' text...")
            search_result = await page.evaluate("""
                () => {
                    // 모든 텍스트 노드 검색
                    const result = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    while(node = walker.nextNode()) {
                        const text = node.nodeValue.trim();
                        if(text.includes('매출현황') || text.includes('매출 현황')) {
                            result.push({
                                text: text,
                                parent: node.parentElement.tagName,
                                className: node.parentElement.className
                            });
                        }
                    }
                    
                    return result;
                }
            """)
            
            if search_result:
                print("   Found texts containing '매출현황':")
                for item in search_result:
                    print(f"     - {item}")
            
            # ssa450skrv iframe이 있는지 확인
            print("\n[5] Looking for ssa450skrv iframe...")
            ssa_iframe = await page.evaluate("""
                () => {
                    const iframes = document.querySelectorAll('iframe');
                    for(let iframe of iframes) {
                        if(iframe.src && iframe.src.includes('ssa450skrv')) {
                            return {
                                found: true,
                                src: iframe.src,
                                id: iframe.id,
                                visible: iframe.offsetParent !== null
                            };
                        }
                    }
                    return {found: false};
                }
            """)
            
            if ssa_iframe['found']:
                print(f"   ssa450skrv iframe found: {ssa_iframe}")
                
                # iframe 내부 작업
                print("\n[6] Working in ssa450skrv iframe...")
                iframe_selector = 'iframe[src*="ssa450skrv"]'
                frame_element = await page.query_selector(iframe_selector)
                
                if frame_element:
                    frame = await frame_element.content_frame()
                    if frame:
                        # 날짜 설정
                        date_result = await frame.evaluate("""
                            () => {
                                if(typeof Ext !== 'undefined') {
                                    const dateFields = Ext.ComponentQuery.query('datefield');
                                    if(dateFields.length >= 2) {
                                        dateFields[0].setValue(new Date(2024, 7, 5));
                                        dateFields[1].setValue(new Date(2024, 7, 9));
                                        return `Dates set: ${dateFields.length} fields`;
                                    }
                                }
                                return 'No date fields';
                            }
                        """)
                        print(f"   {date_result}")
                        
                        # 조회
                        await frame.keyboard.press('F2')
                        print("   F2 pressed")
                        
                        await page.wait_for_timeout(5000)
                        
                        # 데이터 확인
                        data = await frame.evaluate("""
                            () => {
                                if(typeof Ext !== 'undefined') {
                                    const grids = Ext.ComponentQuery.query('grid');
                                    if(grids.length > 0) {
                                        const store = grids[0].getStore();
                                        return store.getCount();
                                    }
                                }
                                return 0;
                            }
                        """)
                        print(f"   Records: {data}")
                        
                        # 엑셀 다운로드
                        excel = await frame.evaluate("""
                            () => {
                                const buttons = document.querySelectorAll('button');
                                for(let btn of buttons) {
                                    if(btn.title && btn.title.includes('엑셀')) {
                                        btn.click();
                                        return 'Excel clicked';
                                    }
                                }
                                return 'No excel button';
                            }
                        """)
                        print(f"   {excel}")
            else:
                print("   ssa450skrv iframe not found")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=str(data_dir / f"test_{timestamp}.png"))
            print(f"\nScreenshot: test_{timestamp}.png")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(test_menus())
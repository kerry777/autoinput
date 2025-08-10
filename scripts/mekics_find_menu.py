#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황조회 메뉴 찾기
매출관리 하위 메뉴를 모두 펼쳐서 확인
"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def find_menu():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
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
            print("FINDING SALES INQUIRY MENU")
            print("="*60)
            
            # 초기 메뉴 목록
            print("\n[STEP 1] Initial menu items:")
            items_before = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const items = [];
                    nodes.forEach((node, idx) => {
                        items.push(`[${idx}] ${node.innerText.trim()}`);
                    });
                    return items;
                }
            """)
            
            for item in items_before:
                print(f"  {item}")
            
            # 인덱스 10 (매출관리) 클릭
            print(f"\n[STEP 2] Click index 10 (매출관리)...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[10]) nodes[10].click();
                }
            """)
            await page.wait_for_timeout(3000)
            
            # 확장된 메뉴 확인
            print("\n[STEP 3] Expanded menu items:")
            items_after = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const items = [];
                    nodes.forEach((node, idx) => {
                        items.push({
                            index: idx,
                            text: node.innerText.trim()
                        });
                    });
                    return items;
                }
            """)
            
            # 매출관리 하위 메뉴만 표시
            print("\nSub-menus under 매출관리:")
            for i in range(10, len(items_after)):
                item = items_after[i]
                print(f"  [{item['index']}] {item['text']}")
                
                # 매출현황 관련 메뉴 찾기
                text = item['text']
                if '매출' in text and '현황' in text:
                    print(f"     ^^ FOUND: This might be sales status inquiry!")
                elif '매출' in text and '조회' in text:
                    print(f"     ^^ FOUND: This might be sales inquiry!")
            
            # 더 많은 하위 메뉴가 있는지 확인
            print("\n[STEP 4] Try expanding sub-menus...")
            
            # 인덱스 11 클릭해보기
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[11]) nodes[11].click();
                }
            """)
            await page.wait_for_timeout(2000)
            
            items_expanded = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const items = [];
                    nodes.forEach((node, idx) => {
                        items.push({
                            index: idx,
                            text: node.innerText.trim()
                        });
                    });
                    return items;
                }
            """)
            
            if len(items_expanded) > len(items_after):
                print("\nMore sub-menus found:")
                for i in range(len(items_after), len(items_expanded)):
                    item = items_expanded[i]
                    print(f"  [{item['index']}] {item['text']}")
                    
                    # 매출현황조회 찾기
                    if '매출현황' in item['text'] or '매출 현황' in item['text']:
                        print(f"     ^^ TARGET FOUND! Index: {item['index']}")
            
            # 스크린샷
            await page.screenshot(path=str(data_dir / "menu_expanded.png"))
            print("\nScreenshot saved: menu_expanded.png")
            
            print("\n" + "="*60)
            print("MENU SEARCH COMPLETE")
            print("="*60)
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(find_menu())
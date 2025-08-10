#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 모든 메뉴 출력
매출관리 하위의 모든 메뉴를 확인
"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def check_all_menus():
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
            
            print("\n" + "="*80)
            print("ALL MENU ITEMS IN SALES MODULE")
            print("="*80)
            
            # 초기 메뉴
            print("\n[Before expanding]")
            items = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const result = [];
                    nodes.forEach((node, idx) => {
                        const text = node.innerText ? node.innerText.trim() : '';
                        // HTML 엔티티 디코딩
                        const div = document.createElement('div');
                        div.innerHTML = text;
                        const decoded = div.textContent || div.innerText || '';
                        result.push({
                            index: idx,
                            text: decoded,
                            hasChildren: node.parentElement.querySelector('.x-tree-ec-icon') !== null
                        });
                    });
                    return result;
                }
            """)
            
            for item in items:
                expandable = " [+]" if item['hasChildren'] else ""
                print(f"  [{item['index']:2d}] {item['text']}{expandable}")
            
            # 매출관리 확장 (인덱스 10)
            print(f"\n[Expanding index 10]")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    if(nodes[10]) nodes[10].click();
                }
            """)
            await page.wait_for_timeout(3000)
            
            # 확장 후 메뉴
            print("\n[After expanding 매출관리]")
            items_expanded = await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    const result = [];
                    nodes.forEach((node, idx) => {
                        const text = node.innerText ? node.innerText.trim() : '';
                        const div = document.createElement('div');
                        div.innerHTML = text;
                        const decoded = div.textContent || div.innerText || '';
                        result.push({
                            index: idx,
                            text: decoded,
                            hasChildren: node.parentElement.querySelector('.x-tree-ec-icon') !== null
                        });
                    });
                    return result;
                }
            """)
            
            for item in items_expanded:
                expandable = " [+]" if item['hasChildren'] else ""
                # 새로 추가된 항목 강조
                if item['index'] >= len(items):
                    print(f"  [{item['index']:2d}] {item['text']}{expandable} <-- NEW")
                else:
                    print(f"  [{item['index']:2d}] {item['text']}{expandable}")
            
            # 매출현황 관련 메뉴 찾기
            print("\n[Searching for 매출현황]")
            for item in items_expanded:
                text = item['text'].lower()
                if '매출' in text:
                    print(f"  Found: [{item['index']}] {item['text']}")
            
            # 하위 메뉴가 있는 항목들 더 확장해보기
            print("\n[Trying to expand sub-menus]")
            for item in items_expanded:
                if item['hasChildren'] and item['index'] > 10:
                    print(f"\nExpanding [{item['index']}] {item['text']}...")
                    await page.evaluate(f"""
                        () => {{
                            const nodes = document.querySelectorAll('.x-tree-node-text');
                            if(nodes[{item['index']}]) nodes[{item['index']}].click();
                        }}
                    """)
                    await page.wait_for_timeout(2000)
                    
                    # 확장된 내용 확인
                    sub_items = await page.evaluate("""
                        () => {
                            const nodes = document.querySelectorAll('.x-tree-node-text');
                            const result = [];
                            nodes.forEach((node, idx) => {
                                result.push({
                                    index: idx,
                                    text: node.innerText ? node.innerText.trim() : ''
                                });
                            });
                            return result;
                        }
                    """)
                    
                    # 새로 나타난 항목만 출력
                    for sub in sub_items[len(items_expanded):]:
                        print(f"    -> [{sub['index']}] {sub['text']}")
                        if '매출현황' in sub['text'] or '매출 현황' in sub['text']:
                            print(f"       ^^^ TARGET FOUND!")
                    
                    # 다시 닫기
                    await page.evaluate(f"""
                        () => {{
                            const nodes = document.querySelectorAll('.x-tree-node-text');
                            if(nodes[{item['index']}]) nodes[{item['index']}].click();
                        }}
                    """)
                    await page.wait_for_timeout(1000)
            
            # 스크린샷
            await page.screenshot(path=str(data_dir / "all_menus.png"))
            print("\n\nScreenshot saved: all_menus.png")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(check_all_menus())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 트리 메뉴 확인
"""

import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def check():
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
            print("TREE MENU ITEMS")
            print("="*60)
            
            # 모든 트리 노드 텍스트 가져오기
            tree_items = await page.evaluate("""
                () => {
                    const result = [];
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    nodes.forEach((node, index) => {
                        if(node.innerText) {
                            result.push({
                                index: index,
                                text: node.innerText.trim(),
                                className: node.className
                            });
                        }
                    });
                    return result;
                }
            """)
            
            print(f"\nTotal tree items: {len(tree_items)}")
            print("\nAll items:")
            for item in tree_items:
                print(f"  [{item['index']}] {item['text']}")
            
            # 매출 관련 항목 찾기
            print("\n" + "-"*40)
            print("Sales-related items:")
            for item in tree_items:
                text = item['text']
                if '매출' in text or '판매' in text or '영업' in text:
                    print(f"  [{item['index']}] {text} <-- FOUND")
            
            # 스크린샷
            await page.screenshot(path=str(data_dir / "tree_check.png"))
            print("\nScreenshot: tree_check.png")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(check())
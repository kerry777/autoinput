#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 프레임 구조 상세 확인
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def check_frames():
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
            
            # 매출관리 -> 매출현황조회
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.includes('매출관리')) {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(2000)
            
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText === '매출현황조회') {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(5000)
            
            print("="*80)
            print("FRAME STRUCTURE ANALYSIS")
            print("="*80)
            
            # 모든 프레임 확인
            frames = page.frames
            print(f"\nTotal frames: {len(frames)}")
            
            for i, frame in enumerate(frames):
                print(f"\n[Frame {i}]")
                print(f"URL: {frame.url}")
                
                if "about:blank" not in frame.url:
                    # 프레임 내용 분석
                    analysis = await frame.evaluate("""
                        () => {
                            const result = {
                                hasExtJS: typeof Ext !== 'undefined',
                                title: document.title,
                                forms: document.querySelectorAll('form').length,
                                inputs: document.querySelectorAll('input').length,
                                buttons: document.querySelectorAll('button').length,
                                grids: document.querySelectorAll('.x-grid').length,
                                trees: document.querySelectorAll('.x-tree').length
                            };
                            
                            // ExtJS 컴포넌트 확인
                            if(typeof Ext !== 'undefined') {
                                result.extDateFields = Ext.ComponentQuery.query('datefield').length;
                                result.extCombos = Ext.ComponentQuery.query('combobox').length;
                                result.extButtons = Ext.ComponentQuery.query('button').length;
                                result.extGrids = Ext.ComponentQuery.query('grid').length;
                                
                                // 날짜 필드 상세
                                const dateFields = Ext.ComponentQuery.query('datefield');
                                result.dateFieldDetails = dateFields.map(f => ({
                                    name: f.name || '',
                                    label: f.getFieldLabel ? f.getFieldLabel() : '',
                                    value: f.getValue ? f.getValue() : null
                                }));
                            }
                            
                            // 특정 요소 확인
                            result.hasSaleDate = document.querySelector('input[name*="SALE"]') !== null;
                            result.hasQueryButton = Array.from(document.querySelectorAll('button')).some(b => 
                                b.innerText && b.innerText.includes('조회')
                            );
                            
                            return result;
                        }
                    """)
                    
                    print(f"  Title: {analysis['title']}")
                    print(f"  ExtJS: {analysis['hasExtJS']}")
                    print(f"  Forms: {analysis['forms']}, Inputs: {analysis['inputs']}, Buttons: {analysis['buttons']}")
                    print(f"  Grids: {analysis['grids']}, Trees: {analysis['trees']}")
                    
                    if analysis['hasExtJS']:
                        print(f"  ExtJS Components:")
                        print(f"    - DateFields: {analysis['extDateFields']}")
                        print(f"    - Combos: {analysis['extCombos']}")
                        print(f"    - Buttons: {analysis['extButtons']}")
                        print(f"    - Grids: {analysis['extGrids']}")
                        
                        if analysis['dateFieldDetails']:
                            print(f"    - Date Field Details:")
                            for df in analysis['dateFieldDetails']:
                                print(f"      * {df['label']} ({df['name']}): {df['value']}")
                    
                    print(f"  Has Sale Date Input: {analysis['hasSaleDate']}")
                    print(f"  Has Query Button: {analysis['hasQueryButton']}")
                    
                    # 이 프레임이 매출현황 화면인지 판단
                    if analysis['extDateFields'] > 0 or analysis['hasSaleDate']:
                        print(f"  >>> THIS IS THE SALES INQUIRY FRAME <<<")
                        
                        # HTML 저장
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        frame_html = await frame.content()
                        html_file = data_dir / f"sales_frame_{i}_{timestamp}.html"
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(frame_html)
                        print(f"  HTML saved: {html_file}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"frame_analysis_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\nScreenshot: {screenshot_path}")
            
            print("\n" + "="*80)
            print("ANALYSIS COMPLETE")
            print("="*80)
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(check_frames())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 프레임 소스 추출 및 분석
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def analyze():
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
            print("프레임 구조 분석")
            print("="*80)
            
            # 모든 프레임 확인
            frames = page.frames
            print(f"\n총 프레임 수: {len(frames)}")
            
            for i, frame in enumerate(frames):
                print(f"\n[프레임 {i}]")
                print(f"URL: {frame.url}")
                
                if i > 0 and "about:blank" not in frame.url:  # 빈 프레임 제외
                    # 프레임 내 HTML 저장
                    frame_html = await frame.content()
                    frame_file = data_dir / f"frame_{i}_content.html"
                    with open(frame_file, 'w', encoding='utf-8') as f:
                        f.write(frame_html)
                    print(f"HTML 저장: {frame_file}")
                    
                    # 프레임 내 중요 요소 분석
                    analysis = await frame.evaluate("""
                        () => {
                            const result = {
                                dateFields: [],
                                buttons: [],
                                combos: [],
                                grids: []
                            };
                            
                            // 날짜 입력 필드
                            const dateInputs = document.querySelectorAll('input[type="text"][name*="DATE"], input[class*="date"]');
                            dateInputs.forEach(input => {
                                result.dateFields.push({
                                    name: input.name,
                                    id: input.id,
                                    value: input.value,
                                    placeholder: input.placeholder
                                });
                            });
                            
                            // 버튼
                            const buttons = document.querySelectorAll('button, a[class*="btn"]');
                            buttons.forEach(btn => {
                                const text = btn.innerText || btn.textContent || '';
                                if(text) {
                                    result.buttons.push({
                                        text: text.trim(),
                                        title: btn.title || '',
                                        onclick: btn.onclick ? 'yes' : 'no'
                                    });
                                }
                            });
                            
                            // ExtJS 컴포넌트
                            if(typeof Ext !== 'undefined') {
                                const extDateFields = Ext.ComponentQuery.query('datefield');
                                extDateFields.forEach(field => {
                                    result.dateFields.push({
                                        extjs: true,
                                        name: field.name,
                                        label: field.getFieldLabel ? field.getFieldLabel() : '',
                                        value: field.getValue ? field.getValue() : ''
                                    });
                                });
                                
                                const extButtons = Ext.ComponentQuery.query('button');
                                extButtons.forEach(btn => {
                                    result.buttons.push({
                                        extjs: true,
                                        text: btn.getText ? btn.getText() : '',
                                        tooltip: btn.tooltip || ''
                                    });
                                });
                            }
                            
                            return result;
                        }
                    """)
                    
                    print("\n날짜 필드:")
                    for field in analysis['dateFields']:
                        print(f"  - {field}")
                    
                    print("\n버튼 (처음 10개):")
                    for btn in analysis['buttons'][:10]:
                        print(f"  - {btn}")
            
            # 메인 페이지 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"analysis_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n전체 스크린샷: {screenshot_path}")
            
            # 메인 페이지 HTML도 저장
            main_html = await page.content()
            main_file = data_dir / f"main_page_{timestamp}.html"
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(main_html)
            print(f"메인 HTML: {main_file}")
            
            print("\n분석 완료! HTML 파일과 스크린샷을 확인하세요.")
            
        except Exception as e:
            print(f"오류: {e}")
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze())
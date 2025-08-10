#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 - 프레임 구조 고려
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
        browser = await p.chromium.launch(headless=False)
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
            
            # 매출관리 -> 매출현황조회
            try:
                await page.click('text="매출관리"', timeout=5000)
            except:
                # JavaScript로 시도
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
            
            try:
                await page.click('text="매출현황조회"', timeout=5000)
            except:
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
            
            print("\n[Frame Check]")
            frames = page.frames
            print(f"Total frames: {len(frames)}")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")
            
            # 메인 프레임에서 작업
            main_frame = frames[0] if frames else page
            
            # 프레임에서 날짜 필드 찾기
            print("\n[Setting dates in main frame]")
            date_result = await main_frame.evaluate("""
                () => {
                    const dateFields = document.querySelectorAll('input[name*="DATE"]');
                    const result = [];
                    
                    dateFields.forEach(field => {
                        result.push({name: field.name, value: field.value});
                    });
                    
                    // ExtJS로 설정
                    if(typeof Ext !== 'undefined') {
                        const fromDate = Ext.ComponentQuery.query('datefield[name="SALE_FR_DATE"]')[0];
                        const toDate = Ext.ComponentQuery.query('datefield[name="SALE_TO_DATE"]')[0];
                        
                        if(fromDate) {
                            fromDate.setValue('2024.08.05');
                            result.push('From date set');
                        }
                        if(toDate) {
                            toDate.setValue('2024.08.09');
                            result.push('To date set');
                        }
                    }
                    
                    return result;
                }
            """)
            print(f"Date fields: {date_result}")
            
            # 조회 버튼 클릭
            print("\n[Click Query button]")
            query_clicked = await main_frame.evaluate("""
                () => {
                    // 조회 버튼 찾기
                    const buttons = document.querySelectorAll('button');
                    for(let btn of buttons) {
                        if(btn.innerText && btn.innerText.includes('조회')) {
                            btn.click();
                            return 'Query button clicked';
                        }
                    }
                    
                    // ExtJS 버튼
                    if(typeof Ext !== 'undefined') {
                        const queryBtn = Ext.ComponentQuery.query('button[text="조회"]')[0];
                        if(queryBtn) {
                            queryBtn.fireEvent('click', queryBtn);
                            return 'ExtJS query button clicked';
                        }
                    }
                    
                    return 'Query button not found';
                }
            """)
            print(query_clicked)
            
            # F2도 시도
            await page.keyboard.press('F2')
            print("F2 pressed")
            
            await page.wait_for_timeout(5000)
            
            # 데이터 확인
            print("\n[Check data]")
            data_check = await main_frame.evaluate("""
                () => {
                    if(typeof Ext !== 'undefined') {
                        const grid = Ext.ComponentQuery.query('grid')[0];
                        if(grid && grid.getStore) {
                            const store = grid.getStore();
                            return {
                                count: store.getCount(),
                                loading: store.isLoading()
                            };
                        }
                    }
                    
                    // DOM에서 직접 확인
                    const rows = document.querySelectorAll('.x-grid-row');
                    return {
                        domRows: rows.length
                    };
                }
            """)
            print(f"Data: {data_check}")
            
            # 엑셀 다운로드
            print("\n[Excel download]")
            excel_result = await main_frame.evaluate("""
                () => {
                    // 엑셀 버튼/아이콘 찾기
                    const excelBtns = document.querySelectorAll('[title*="엑셀"], [class*="excel"]');
                    if(excelBtns.length > 0) {
                        excelBtns[0].click();
                        return 'Excel clicked';
                    }
                    
                    if(typeof Ext !== 'undefined') {
                        const excelBtn = Ext.ComponentQuery.query('button[text*="엑셀"]')[0];
                        if(excelBtn) {
                            excelBtn.fireEvent('click', excelBtn);
                            return 'ExtJS Excel clicked';
                        }
                    }
                    
                    return 'Excel not found';
                }
            """)
            print(excel_result)
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=str(data_dir / f"final_{timestamp}.png"))
            print(f"\nScreenshot saved: final_{timestamp}.png")
            
            print("\nDONE!")
            
        except Exception as e:
            print(f"ERROR: {e}")
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
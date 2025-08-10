#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 직접 조회
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def run_sales_direct():
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
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone'],
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("[OK] Cookie loaded")
        
        page = await context.new_page()
        
        try:
            print("\n[1] Main page...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            print("\n[2] Click Sales module icon (4th icon)...")
            # 영업관리 모듈 직접 클릭 - 화면에서 4번째 아이콘
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            print("\n[3] Wait for tree menu and click Sales Management...")
            # 트리 메뉴에서 매출관리 찾아 클릭
            await page.wait_for_selector('.x-tree-node-text')
            
            # 매출관리 클릭
            sales_mgmt = await page.query_selector('text="매출관리"')
            if sales_mgmt:
                await sales_mgmt.click()
                print("   - Sales Management expanded")
                await page.wait_for_timeout(2000)
            
            print("\n[4] Click Sales Status Inquiry...")
            # 매출현황조회 클릭
            sales_inquiry = await page.query_selector('text="매출현황조회"')
            if sales_inquiry:
                await sales_inquiry.click()
                print("   - Sales Status Inquiry clicked")
                await page.wait_for_timeout(5000)
            
            print("\n[5] Check loaded fields...")
            # 필드 확인
            fields = await page.evaluate("""
                () => {
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    const combos = Ext.ComponentQuery.query('combobox');
                    const buttons = Ext.ComponentQuery.query('button');
                    
                    return {
                        dateCount: dateFields.length,
                        comboCount: combos.length,
                        buttonCount: buttons.length,
                        dates: dateFields.map(f => ({
                            label: f.getFieldLabel ? f.getFieldLabel() : '',
                            value: f.getValue ? f.getValue() : ''
                        })),
                        combos: combos.slice(0, 10).map(c => ({
                            label: c.getFieldLabel ? c.getFieldLabel() : '',
                            value: c.getRawValue ? c.getRawValue() : ''
                        }))
                    };
                }
            """)
            
            print(f"   - Date fields: {fields['dateCount']}")
            print(f"   - Combo boxes: {fields['comboCount']}")
            print(f"   - Buttons: {fields['buttonCount']}")
            
            if fields['dates']:
                print("\n   Date fields found:")
                for i, date in enumerate(fields['dates']):
                    print(f"     {i}. {date['label']}: {date['value']}")
            
            print("\n[6] Set date range (08.05 ~ 08.09)...")
            if fields['dateCount'] >= 2:
                await page.evaluate("""
                    () => {
                        const dateFields = Ext.ComponentQuery.query('datefield');
                        if(dateFields[0]) dateFields[0].setValue(new Date(2024, 7, 5));
                        if(dateFields[1]) dateFields[1].setValue(new Date(2024, 7, 9));
                    }
                """)
                print("   - Dates set: 2024.08.05 ~ 2024.08.09")
            
            print("\n[7] Set division to 'All'...")
            await page.evaluate("""
                () => {
                    // 국내/해외 구분 콤보박스 찾기
                    const combos = Ext.ComponentQuery.query('combobox');
                    for(let combo of combos) {
                        const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                        if(label.includes('구분') || label.includes('국내')) {
                            combo.setValue('');  // 빈값이 전체
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            print("\n[8] Click Query button (F2)...")
            # F2 키 또는 조회 버튼
            await page.keyboard.press('F2')
            await page.wait_for_timeout(5000)
            
            print("\n[9] Check grid data...")
            grid_data = await page.evaluate("""
                () => {
                    const grid = Ext.ComponentQuery.query('grid')[0];
                    if(grid && grid.getStore) {
                        const store = grid.getStore();
                        return {
                            count: store.getCount(),
                            total: store.getTotalCount()
                        };
                    }
                    return {count: 0, total: 0};
                }
            """)
            print(f"   - Records: {grid_data['count']} / Total: {grid_data['total']}")
            
            print("\n[10] Download Excel...")
            # 다운로드 대기 설정
            download_promise = page.wait_for_event('download')
            
            # 엑셀 버튼 찾아 클릭
            excel_clicked = await page.evaluate("""
                () => {
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('엑셀') || text.includes('Excel')) {
                            btn.fireEvent('click', btn);
                            return true;
                        }
                    }
                    // 툴바 아이콘 확인
                    const tools = document.querySelectorAll('[class*="excel"]');
                    if(tools.length > 0) {
                        tools[0].click();
                        return true;
                    }
                    return false;
                }
            """)
            
            if excel_clicked:
                print("   - Excel button clicked")
                try:
                    download = await asyncio.wait_for(download_promise, timeout=10)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"sales_data_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   - Saved: {save_path}")
                except asyncio.TimeoutError:
                    print("   - Download timeout")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=str(data_dir / f"sales_final_{timestamp}.png"))
            
            print("\n[COMPLETE] Sales report automation finished!")
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_sales_direct())
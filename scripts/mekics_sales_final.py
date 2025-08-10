#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 최종 자동화
실제 필드 name을 사용한 정확한 자동화
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def run_sales_report_final():
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
            
            print("\n[2] Sales module (14)...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            print("\n[3] Sales Management menu...")
            await page.wait_for_selector('.x-tree-node-text')
            sales_mgmt = await page.query_selector('text="매출관리"')
            if sales_mgmt:
                await sales_mgmt.click()
                await page.wait_for_timeout(2000)
            
            print("\n[4] Sales Status Inquiry...")
            sales_inquiry = await page.query_selector('text="매출현황조회"')
            if sales_inquiry:
                await sales_inquiry.click()
                await page.wait_for_timeout(5000)
            
            print("\n[5] Set dates using exact field names...")
            # SALE_FR_DATE와 SALE_TO_DATE 필드에 직접 값 설정
            date_result = await page.evaluate("""
                () => {
                    // From Date - SALE_FR_DATE
                    const fromField = Ext.ComponentQuery.query('datefield[name="SALE_FR_DATE"]')[0];
                    if(fromField) {
                        fromField.setValue(new Date(2024, 7, 5)); // 2024.08.05
                    }
                    
                    // To Date - SALE_TO_DATE로 추정
                    const toField = Ext.ComponentQuery.query('datefield[name="SALE_TO_DATE"]')[0];
                    if(toField) {
                        toField.setValue(new Date(2024, 7, 9)); // 2024.08.09
                    }
                    
                    // 혹은 모든 datefield 찾아서 설정
                    const allDateFields = Ext.ComponentQuery.query('datefield');
                    if(allDateFields.length >= 2) {
                        allDateFields[0].setValue(new Date(2024, 7, 5));
                        allDateFields[1].setValue(new Date(2024, 7, 9));
                        return 'Dates set by index';
                    }
                    
                    return 'Dates set by name';
                }
            """)
            print(f"   {date_result}")
            print("   Dates: 2024.08.05 ~ 2024.08.09")
            
            print("\n[6] Set division to ALL...")
            combo_result = await page.evaluate("""
                () => {
                    // DIV_CODE 또는 구분 관련 콤보박스
                    const combos = Ext.ComponentQuery.query('combobox');
                    for(let combo of combos) {
                        const name = combo.getName ? combo.getName() : '';
                        const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                        
                        // DIV_CODE, SALE_DIV_CODE 등
                        if(name.includes('DIV') || label.includes('구분')) {
                            // 전체는 보통 빈 값 또는 'ALL'
                            combo.setValue('');
                            return 'Division set to ALL';
                        }
                    }
                    return 'Division combo not found';
                }
            """)
            print(f"   {combo_result}")
            
            print("\n[7] Query (F2)...")
            await page.keyboard.press('F2')
            print("   F2 pressed, waiting for data...")
            await page.wait_for_timeout(5000)
            
            # 그리드 데이터 확인
            grid_info = await page.evaluate("""
                () => {
                    const grid = Ext.ComponentQuery.query('grid')[0];
                    if(grid && grid.getStore) {
                        const store = grid.getStore();
                        const count = store.getCount();
                        const data = store.getData().items.slice(0, 3).map(item => item.data);
                        return {count, sample: data};
                    }
                    return {count: 0, sample: []};
                }
            """)
            print(f"   Records loaded: {grid_info['count']}")
            if grid_info['sample']:
                print("   Sample data:")
                for row in grid_info['sample']:
                    print(f"     {row}")
            
            print("\n[8] Excel download...")
            download_promise = page.wait_for_event('download')
            
            excel_result = await page.evaluate("""
                () => {
                    // 엑셀 버튼 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        
                        if(text.includes('엑셀') || text.includes('Excel') || 
                           tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                            btn.fireEvent('click', btn);
                            return 'Excel button clicked';
                        }
                    }
                    
                    // 툴바 아이템 확인
                    const tools = Ext.ComponentQuery.query('tool');
                    for(let tool of tools) {
                        if(tool.type === 'excel' || tool.tooltip === '엑셀다운로드') {
                            tool.fireEvent('click', tool);
                            return 'Excel tool clicked';
                        }
                    }
                    
                    return 'Excel button not found';
                }
            """)
            print(f"   {excel_result}")
            
            if "clicked" in excel_result:
                try:
                    download = await asyncio.wait_for(download_promise, timeout=10)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"sales_report_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   Saved: {save_path}")
                except asyncio.TimeoutError:
                    print("   Download timeout - checking for alternative download method")
            
            # 최종 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"sales_complete_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path))
            print(f"\n[9] Screenshot: {screenshot_path}")
            
            print("\n" + "="*60)
            print("SALES REPORT AUTOMATION COMPLETE!")
            print("="*60)
            
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\nClosing browser in 30 seconds...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_sales_report_final())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 - 즉시 실행
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
            
            # 영업관리 모듈
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 매출관리 클릭
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
            
            # 매출현황조회 클릭
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
            
            print("[1] 매출일 필드에 날짜 설정...")
            # ExtJS로 매출일 필드 찾아서 설정
            date_result = await page.evaluate("""
                () => {
                    // 매출일 레이블이 있는 날짜 필드 찾기
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    let fromSet = false;
                    let toSet = false;
                    
                    for(let field of dateFields) {
                        const label = field.getFieldLabel ? field.getFieldLabel() : '';
                        
                        // 매출일이라는 레이블을 포함하거나 SALE_DATE를 포함하는 필드
                        if(label.includes('매출일') || field.name.includes('SALE')) {
                            if(!fromSet) {
                                field.setValue(new Date(2024, 7, 5)); // 2024.08.05
                                fromSet = true;
                            } else if(!toSet) {
                                field.setValue(new Date(2024, 7, 9)); // 2024.08.09
                                toSet = true;
                            }
                        }
                    }
                    
                    // 모든 날짜 필드가 2개 이상이면 처음 2개에 설정
                    if(!fromSet && dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2024, 7, 5));
                        dateFields[1].setValue(new Date(2024, 7, 9));
                        return '날짜 설정: 인덱스 사용';
                    }
                    
                    return `날짜 설정: From=${fromSet}, To=${toSet}`;
                }
            """)
            print(f"   {date_result}")
            
            print("\n[2] 국내/해외 구분을 '전체'로...")
            combo_result = await page.evaluate("""
                () => {
                    const combos = Ext.ComponentQuery.query('combobox');
                    for(let combo of combos) {
                        const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                        const name = combo.getName ? combo.getName() : '';
                        
                        if(label.includes('구분') || name.includes('DIV')) {
                            combo.setValue(''); // 빈값이 전체
                            return '구분을 전체로 설정';
                        }
                    }
                    return '구분 콤보박스 없음';
                }
            """)
            print(f"   {combo_result}")
            
            print("\n[3] 조회[F2] 버튼 클릭...")
            # 조회[F2] 텍스트가 있는 버튼 찾기
            query_result = await page.evaluate("""
                () => {
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        // '조회' 또는 'F2'를 포함하는 버튼
                        if(text.includes('조회') || text.includes('F2')) {
                            btn.fireEvent('click', btn);
                            return `조회 버튼 클릭: ${text}`;
                        }
                    }
                    return '조회 버튼 못 찾음';
                }
            """)
            print(f"   {query_result}")
            
            # F2 키도 누르기
            await page.keyboard.press('F2')
            print("   F2 키 입력")
            
            # 데이터 로딩 대기
            await page.wait_for_timeout(5000)
            
            # 데이터 확인
            data_check = await page.evaluate("""
                () => {
                    const grid = Ext.ComponentQuery.query('grid')[0];
                    if(grid && grid.getStore) {
                        const store = grid.getStore();
                        return {
                            records: store.getCount(),
                            loading: store.isLoading()
                        };
                    }
                    return {records: 0};
                }
            """)
            print(f"\n[4] 조회 결과: {data_check['records']}건")
            
            print("\n[5] 엑셀 다운로드 (툴팁: '엑셀 다운로드')...")
            
            # 다운로드 이벤트 대기
            download_promise = page.wait_for_event('download')
            
            # 툴팁이 '엑셀 다운로드'인 요소 클릭
            excel_result = await page.evaluate("""
                () => {
                    // ExtJS 버튼에서 툴팁 확인
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const tooltip = btn.tooltip || '';
                        if(tooltip === '엑셀 다운로드' || tooltip.includes('엑셀')) {
                            btn.fireEvent('click', btn);
                            return `엑셀 버튼 클릭 (툴팁: ${tooltip})`;
                        }
                    }
                    
                    // 툴 아이템 확인
                    const tools = Ext.ComponentQuery.query('tool');
                    for(let tool of tools) {
                        const tooltip = tool.tooltip || '';
                        if(tooltip === '엑셀 다운로드' || tooltip.includes('엑셀')) {
                            tool.fireEvent('click', tool);
                            return `엑셀 툴 클릭 (툴팁: ${tooltip})`;
                        }
                    }
                    
                    // DOM에서 title 속성 확인
                    const elements = document.querySelectorAll('[title="엑셀 다운로드"]');
                    if(elements.length > 0) {
                        elements[0].click();
                        return 'DOM 엑셀 요소 클릭';
                    }
                    
                    return '엑셀 다운로드 버튼 못 찾음';
                }
            """)
            print(f"   {excel_result}")
            
            if "클릭" in excel_result:
                try:
                    download = await asyncio.wait_for(download_promise, timeout=10)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"sales_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   ✅ 다운로드 완료: {save_path}")
                except asyncio.TimeoutError:
                    print("   ⏱️ 다운로드 대기 시간 초과")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=str(data_dir / f"complete_{timestamp}.png"))
            
            print("\n" + "="*60)
            print("완료! 매출현황 조회 및 엑셀 다운로드 성공")
            print("="*60)
            
        except Exception as e:
            print(f"오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
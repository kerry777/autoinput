#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 엑셀 버튼 디버깅
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def debug_excel_button():
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
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            print("\n엑셀 버튼 디버깅")
            print("="*60)
            
            # 매출현황 페이지 접속
            print("\n[1] 매출현황 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 조건 설정 및 실행
            print("\n[2] 조회 실행...")
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정 (긴 기간 - CSV 팝업 유도)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));  // 2021년 1월 1일
                        dateFields[1].setValue(new Date(2025, 7, 10)); // 2025년 8월 10일
                    }
                }
            """)
            
            await page.keyboard.press('F2')
            
            # 로딩 대기
            print("   데이터 로딩 중...")
            for i in range(30):
                await page.wait_for_timeout(1000)
                status = await page.evaluate("""
                    () => {
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length > 0) {
                            const store = grids[0].getStore();
                            return {
                                count: store.getCount(),
                                loading: store.isLoading()
                            };
                        }
                        return {count: 0, loading: true};
                    }
                """)
                
                if not status['loading'] and status['count'] > 0:
                    print(f"   로딩 완료: {status['count']:,}건")
                    break
                if i % 5 == 4:
                    print(f"   {i+1}초 경과...")
            
            await page.wait_for_timeout(2000)
            
            # 모든 버튼 찾기
            print("\n[3] 모든 버튼 검색...")
            buttons_info = await page.evaluate("""
                () => {
                    const buttons = Ext.ComponentQuery.query('button');
                    const buttonList = [];
                    
                    buttons.forEach((btn, index) => {
                        const text = btn.getText ? btn.getText() : '';
                        const tooltip = btn.tooltip || '';
                        const iconCls = btn.iconCls || '';
                        
                        // 엑셀 관련 버튼만 필터링
                        if(text.includes('엑셀') || text.includes('Excel') || 
                           text.includes('다운') || text.includes('Down') ||
                           tooltip.includes('엑셀') || tooltip.includes('Excel') ||
                           iconCls.includes('excel') || iconCls.includes('download')) {
                            
                            buttonList.push({
                                index: index,
                                id: btn.id,
                                itemId: btn.itemId || '',
                                text: text,
                                tooltip: tooltip,
                                iconCls: iconCls,
                                visible: btn.isVisible ? btn.isVisible() : false,
                                disabled: btn.disabled,
                                handler: btn.handler ? 'YES' : 'NO'
                            });
                        }
                    });
                    
                    return buttonList;
                }
            """)
            
            print(f"\n엑셀 관련 버튼 {len(buttons_info)}개 발견:")
            for btn in buttons_info:
                print(f"\n버튼 #{btn['index']}:")
                print(f"  ID: {btn['id']}")
                print(f"  ItemID: {btn['itemId']}")
                print(f"  텍스트: {btn['text']}")
                print(f"  툴팁: {btn['tooltip']}")
                print(f"  아이콘: {btn['iconCls']}")
                print(f"  표시: {btn['visible']}")
                print(f"  비활성: {btn['disabled']}")
                print(f"  핸들러: {btn['handler']}")
            
            # 가장 유력한 버튼 클릭 시도
            if buttons_info:
                print("\n[4] 엑셀 버튼 클릭 시도...")
                
                # 첫 번째 visible 버튼 찾기
                target_btn = None
                for btn in buttons_info:
                    if btn['visible'] and not btn['disabled']:
                        target_btn = btn
                        break
                
                if target_btn:
                    print(f"\n선택된 버튼: {target_btn['id']} ({target_btn['text']})")
                    
                    # 클릭 시도
                    click_result = await page.evaluate(f"""
                        () => {{
                            const btn = Ext.getCmp('{target_btn['id']}');
                            if(btn) {{
                                // 여러 방법 시도
                                if(btn.handler) {{
                                    btn.handler.call(btn.scope || btn);
                                    return 'handler called';
                                }} else if(btn.fireEvent) {{
                                    btn.fireEvent('click', btn);
                                    return 'fireEvent called';
                                }} else {{
                                    btn.el.dom.click();
                                    return 'dom click';
                                }}
                            }}
                            return 'button not found';
                        }}
                    """)
                    
                    print(f"클릭 결과: {click_result}")
                    
                    # 팝업 대기
                    await page.wait_for_timeout(2000)
                    
                    # 팝업 확인
                    popup_info = await page.evaluate("""
                        () => {
                            const msgBoxes = Ext.ComponentQuery.query('messagebox');
                            if(msgBoxes.length > 0) {
                                const box = msgBoxes[0];
                                if(box.isVisible && box.isVisible()) {
                                    return {
                                        found: true,
                                        message: box.msg || '',
                                        buttons: box.query('button').map(b => b.getText())
                                    };
                                }
                            }
                            return {found: false};
                        }
                    """)
                    
                    if popup_info['found']:
                        print(f"\n[5] 팝업 발견!")
                        print(f"  메시지: {popup_info['message'][:100]}")
                        print(f"  버튼: {popup_info['buttons']}")
                        
                        # Enter 키 입력
                        print("\nEnter 키 입력...")
                        await page.keyboard.press('Enter')
                        
                        print("\n다운로드 대기 중...")
                        await page.wait_for_timeout(10000)
                    else:
                        print("\n팝업이 나타나지 않음")
                else:
                    print("\n활성화된 엑셀 버튼을 찾을 수 없음")
            else:
                print("\n엑셀 관련 버튼을 찾을 수 없음")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"debug_excel_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n스크린샷: {screenshot}")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저를 30초 후 종료합니다...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_excel_button())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 팝업 감지 테스트
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def detect_popup():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False
        )
        
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
            print("\n팝업 감지 테스트 시작\n")
            print("매출현황 페이지 접속 중...")
            
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            print("\n팝업을 띄워주세요. 감지를 시작합니다...\n")
            
            # 30초 동안 1초마다 팝업 체크
            for i in range(30):
                await page.wait_for_timeout(1000)
                
                # 모든 종류의 팝업 체크
                popup_info = await page.evaluate("""
                    () => {
                        const result = {
                            messageBoxes: [],
                            windows: [],
                            dialogs: [],
                            components: []
                        };
                        
                        // MessageBox 확인
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        msgBoxes.forEach(box => {
                            if(box.isVisible && box.isVisible()) {
                                const buttons = box.query('button').map(btn => ({
                                    text: btn.getText ? btn.getText() : '',
                                    itemId: btn.itemId || '',
                                    disabled: btn.disabled
                                }));
                                
                                result.messageBoxes.push({
                                    id: box.id,
                                    title: box.title || '',
                                    msg: box.msg || '',
                                    buttons: buttons,
                                    modal: box.modal
                                });
                            }
                        });
                        
                        // Window 확인
                        const windows = Ext.ComponentQuery.query('window');
                        windows.forEach(win => {
                            if(win.isVisible && win.isVisible() && win.id !== 'ext-element-3') {
                                const buttons = win.query('button').map(btn => ({
                                    text: btn.getText ? btn.getText() : '',
                                    itemId: btn.itemId || ''
                                }));
                                
                                result.windows.push({
                                    id: win.id,
                                    title: win.title || '',
                                    modal: win.modal,
                                    buttons: buttons
                                });
                            }
                        });
                        
                        // Dialog 확인
                        const dialogs = Ext.ComponentQuery.query('dialog');
                        dialogs.forEach(dlg => {
                            if(dlg.isVisible && dlg.isVisible()) {
                                result.dialogs.push({
                                    id: dlg.id,
                                    title: dlg.title || ''
                                });
                            }
                        });
                        
                        // 기타 플로팅 컴포넌트
                        const floatings = Ext.ComponentQuery.query('component[floating=true]');
                        floatings.forEach(comp => {
                            if(comp.isVisible && comp.isVisible()) {
                                result.components.push({
                                    xtype: comp.xtype,
                                    id: comp.id,
                                    cls: comp.cls || ''
                                });
                            }
                        });
                        
                        return result;
                    }
                """)
                
                # 팝업 발견 시 출력
                if popup_info['messageBoxes']:
                    print(f"\n[{i+1}초] MessageBox 감지!")
                    for box in popup_info['messageBoxes']:
                        print(f"  ID: {box['id']}")
                        print(f"  제목: {box['title']}")
                        print(f"  메시지: {box['msg'][:100]}")
                        print(f"  버튼: {box['buttons']}")
                        print(f"  Modal: {box['modal']}")
                
                if popup_info['windows']:
                    print(f"\n[{i+1}초] Window 감지!")
                    for win in popup_info['windows']:
                        print(f"  ID: {win['id']}")
                        print(f"  제목: {win['title']}")
                        print(f"  Modal: {win['modal']}")
                        print(f"  버튼: {win['buttons']}")
                
                if popup_info['dialogs']:
                    print(f"\n[{i+1}초] Dialog 감지!")
                    for dlg in popup_info['dialogs']:
                        print(f"  ID: {dlg['id']}")
                        print(f"  제목: {dlg['title']}")
                
                if popup_info['components']:
                    print(f"\n[{i+1}초] Floating Component 감지!")
                    for comp in popup_info['components']:
                        print(f"  Type: {comp['xtype']}")
                        print(f"  ID: {comp['id']}")
                
                # 팝업이 감지되면 스크린샷
                if any([popup_info['messageBoxes'], popup_info['windows'], 
                       popup_info['dialogs'], popup_info['components']]):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot = data_dir / f"popup_detected_{timestamp}.png"
                    await page.screenshot(path=str(screenshot))
                    print(f"  스크린샷: {screenshot}")
                    
                    # 엔터키 시도
                    print("\n엔터키 입력...")
                    await page.keyboard.press('Enter')
                    await page.wait_for_timeout(2000)
                    
                    # 팝업이 닫혔는지 확인
                    check_closed = await page.evaluate("""
                        () => {
                            const msgBoxes = Ext.ComponentQuery.query('messagebox');
                            const visibleBoxes = msgBoxes.filter(box => 
                                box.isVisible && box.isVisible()
                            );
                            return visibleBoxes.length === 0;
                        }
                    """)
                    
                    if check_closed:
                        print("팝업이 닫혔습니다!")
                    else:
                        print("팝업이 아직 열려있습니다.")
                else:
                    if i % 5 == 0:
                        print(f"대기 중... ({i+1}초)")
            
            print("\n30초 감지 완료")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저는 열어둡니다. 수동으로 닫아주세요.")
            await page.wait_for_timeout(60000)  # 1분 대기
            await browser.close()


if __name__ == "__main__":
    asyncio.run(detect_popup())
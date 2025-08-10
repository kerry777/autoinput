#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS Native Click - 네이티브 이벤트로 엑셀 버튼 클릭
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def native_click_test():
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
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            print("\nNative Click 테스트")
            print("="*60)
            
            # 매출현황 페이지 접속
            print("\n[1] 매출현황 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 실행
            print("\n[2] 대용량 데이터 조회...")
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정 (대용량)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date());
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
            
            # Native MouseEvent로 클릭
            print("\n[3] Native MouseEvent로 엑셀 버튼 클릭...")
            
            click_result = await page.evaluate("""
                () => {
                    // 엑셀 버튼 찾기
                    const btn = Ext.getCmp('uniBaseButton-1196');
                    if(!btn) return {success: false, error: 'Button not found'};
                    
                    // DOM element 가져오기
                    const element = btn.el ? btn.el.dom : document.getElementById('uniBaseButton-1196');
                    if(!element) return {success: false, error: 'DOM element not found'};
                    
                    // Native MouseEvent 생성
                    const event = new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        detail: 1,
                        screenX: 0,
                        screenY: 0,
                        clientX: element.getBoundingClientRect().left + 10,
                        clientY: element.getBoundingClientRect().top + 10,
                        ctrlKey: false,
                        altKey: false,
                        shiftKey: false,
                        metaKey: false,
                        button: 0,
                        relatedTarget: null
                    });
                    
                    // 이벤트 발생
                    element.dispatchEvent(event);
                    
                    // 추가로 handler도 호출
                    if(btn.handler) {
                        setTimeout(() => {
                            btn.handler.call(btn.scope || btn);
                        }, 100);
                    }
                    
                    return {success: true};
                }
            """)
            
            print(f"   결과: {click_result}")
            
            # 팝업 대기 및 처리
            print("\n[4] 팝업 대기...")
            await page.wait_for_timeout(3000)
            
            # 여러 번 팝업 체크
            for attempt in range(3):
                popup_info = await page.evaluate("""
                    () => {
                        // MessageBox 찾기
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        for(let box of msgBoxes) {
                            if(box.isVisible && box.isVisible()) {
                                const buttons = box.query('button').map(b => ({
                                    text: b.getText ? b.getText() : '',
                                    itemId: b.itemId || ''
                                }));
                                
                                // '예' 버튼 자동 클릭
                                for(let btn of box.query('button')) {
                                    if(btn.itemId === 'yes' || btn.getText() === '예') {
                                        btn.fireEvent('click', btn);
                                        return {
                                            found: true,
                                            clicked: true,
                                            message: box.msg || '',
                                            buttons: buttons
                                        };
                                    }
                                }
                                
                                return {
                                    found: true,
                                    clicked: false,
                                    message: box.msg || '',
                                    buttons: buttons
                                };
                            }
                        }
                        
                        // Window 타입 팝업 확인
                        const windows = Ext.ComponentQuery.query('window');
                        for(let win of windows) {
                            if(win.isVisible && win.isVisible() && win.modal) {
                                return {
                                    found: true,
                                    type: 'window',
                                    title: win.title || ''
                                };
                            }
                        }
                        
                        return {found: false};
                    }
                """)
                
                if popup_info['found']:
                    print(f"\n   [팝업 발견!]")
                    print(f"   타입: {popup_info.get('type', 'messagebox')}")
                    print(f"   메시지: {popup_info.get('message', '')[:100]}")
                    print(f"   버튼: {popup_info.get('buttons', [])}")
                    
                    if popup_info.get('clicked'):
                        print("   '예' 버튼 자동 클릭됨")
                    else:
                        print("   Enter 키 입력...")
                        await page.keyboard.press('Enter')
                    
                    break
                else:
                    if attempt == 0:
                        # 다시 한 번 엑셀 버튼 클릭 시도
                        print(f"   팝업 미발견 - 재시도 {attempt + 1}/3")
                        await page.evaluate("""
                            () => {
                                const btn = Ext.getCmp('uniBaseButton-1196');
                                if(btn) {
                                    btn.el.dom.click();
                                }
                            }
                        """)
                        await page.wait_for_timeout(2000)
            
            # 다운로드 확인
            print("\n[5] 다운로드 확인...")
            await page.wait_for_timeout(10000)
            
            # 파일 확인
            download_files = list(data_dir.glob("*.csv")) + list(data_dir.glob("*.xlsx"))
            recent_files = []
            for file in download_files:
                if datetime.now().timestamp() - file.stat().st_mtime < 60:
                    recent_files.append(file)
            
            if recent_files:
                print("\n   [다운로드 성공!]")
                for file in recent_files:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"   파일: {file.name}")
                    print(f"   크기: {size_mb:.2f} MB")
            else:
                print("\n   다운로드 파일을 찾을 수 없음")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"native_click_{timestamp}.png"
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
    asyncio.run(native_click_test())
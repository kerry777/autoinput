#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 최종 클릭 테스트 - 다양한 방법으로 엑셀 버튼 클릭
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def final_click_test():
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
            print("\n최종 엑셀 버튼 클릭 테스트")
            print("="*60)
            
            # 매출현황 페이지 접속
            print("\n[1] 매출현황 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 실행 (빠른 테스트를 위해 짧은 기간)
            print("\n[2] 조회 실행...")
            await page.evaluate("""
                () => {
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정 (대용량 - CSV 팝업 유도)
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
            
            # 여러 방법으로 엑셀 버튼 클릭 시도
            print("\n[3] 엑셀 버튼 클릭 시도...")
            
            methods = [
                {
                    "name": "방법 1: ExtJS handler 직접 호출",
                    "code": """
                        () => {
                            const btn = Ext.getCmp('uniBaseButton-1196');
                            if(btn && btn.handler) {
                                btn.handler.call(btn.scope || btn);
                                return true;
                            }
                            return false;
                        }
                    """
                },
                {
                    "name": "방법 2: ExtJS fireEvent",
                    "code": """
                        () => {
                            const btn = Ext.getCmp('uniBaseButton-1196');
                            if(btn) {
                                btn.fireEvent('click', btn);
                                return true;
                            }
                            return false;
                        }
                    """
                },
                {
                    "name": "방법 3: DOM element 직접 클릭",
                    "code": """
                        () => {
                            const btn = Ext.getCmp('uniBaseButton-1196');
                            if(btn && btn.el && btn.el.dom) {
                                btn.el.dom.click();
                                return true;
                            }
                            return false;
                        }
                    """
                },
                {
                    "name": "방법 4: querySelector로 아이콘 클릭",
                    "code": """
                        () => {
                            const icon = document.querySelector('#uniBaseButton-1196-btnIconEl');
                            if(icon) {
                                icon.click();
                                return true;
                            }
                            return false;
                        }
                    """
                },
                {
                    "name": "방법 5: XPath로 클릭",
                    "code": """
                        () => {
                            const xpath = '//*[@id="uniBaseButton-1196-btnIconEl"]';
                            const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                            if(result.singleNodeValue) {
                                result.singleNodeValue.click();
                                return true;
                            }
                            return false;
                        }
                    """
                }
            ]
            
            for method in methods:
                print(f"\n{method['name']}...")
                result = await page.evaluate(method['code'])
                
                if result:
                    print("   클릭 성공!")
                    
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
                                        buttons: box.query('button').map(b => ({
                                            text: b.getText(),
                                            itemId: b.itemId
                                        }))
                                    };
                                }
                            }
                            return {found: false};
                        }
                    """)
                    
                    if popup_info['found']:
                        print("   [SUCCESS] CSV 팝업 발견!")
                        print(f"   메시지: {popup_info['message'][:100]}")
                        print(f"   버튼: {popup_info['buttons']}")
                        
                        # '예' 버튼 클릭
                        yes_clicked = await page.evaluate("""
                            () => {
                                const msgBoxes = Ext.ComponentQuery.query('messagebox');
                                for(let msgBox of msgBoxes) {
                                    if(msgBox.isVisible && msgBox.isVisible()) {
                                        const buttons = msgBox.query('button');
                                        for(let btn of buttons) {
                                            if(btn.itemId === 'yes' || btn.getText() === '예') {
                                                if(btn.handler) {
                                                    btn.handler.call(btn.scope || btn);
                                                } else {
                                                    btn.fireEvent('click', btn);
                                                }
                                                return true;
                                            }
                                        }
                                    }
                                }
                                return false;
                            }
                        """)
                        
                        if yes_clicked:
                            print("   '예' 버튼 클릭 완료")
                        else:
                            print("   Enter 키 입력...")
                            await page.keyboard.press('Enter')
                        
                        # 다운로드 대기
                        print("\n다운로드 대기 중...")
                        await page.wait_for_timeout(10000)
                        
                        break  # 성공했으므로 종료
                    else:
                        print("   팝업이 나타나지 않음")
                else:
                    print("   클릭 실패")
            
            # 최후의 방법: Playwright의 locator 사용
            if not popup_info.get('found', False):
                print("\n[4] Playwright locator로 클릭...")
                
                try:
                    # ID로 찾기
                    button = page.locator('#uniBaseButton-1196')
                    if await button.count() > 0:
                        print("   버튼 발견 - 클릭...")
                        await button.click()
                        await page.wait_for_timeout(2000)
                    else:
                        # 아이콘으로 찾기
                        icon = page.locator('#uniBaseButton-1196-btnIconEl')
                        if await icon.count() > 0:
                            print("   아이콘 발견 - 클릭...")
                            await icon.click()
                            await page.wait_for_timeout(2000)
                        else:
                            # class로 찾기
                            excel_icon = page.locator('.icon-excel').first
                            if await excel_icon.count() > 0:
                                print("   엑셀 아이콘 발견 - 클릭...")
                                await excel_icon.click()
                                await page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"   Playwright locator 실패: {e}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"final_click_{timestamp}.png"
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
    asyncio.run(final_click_test())
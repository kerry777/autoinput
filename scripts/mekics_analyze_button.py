#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 엑셀 버튼 동작 분석
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def analyze_button():
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
        
        # 네트워크 요청 캡처
        network_logs = []
        
        async def log_request(request):
            if 'download' in request.url.lower() or 'excel' in request.url.lower():
                network_logs.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                })
                print(f"\n[REQUEST] {request.method} {request.url}")
                if request.post_data:
                    print(f"  POST Data: {request.post_data[:200]}")
        
        async def log_response(response):
            if 'download' in response.url.lower() or 'excel' in response.url.lower():
                headers = await response.all_headers()
                print(f"\n[RESPONSE] {response.status} {response.url}")
                print(f"  Headers: {headers}")
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        try:
            print("\n엑셀 버튼 동작 분석")
            print("="*60)
            
            # 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 실행
            print("\n[2] 조회 실행...")
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
            await page.wait_for_timeout(10000)
            
            # 엑셀 버튼 분석
            print("\n[3] 엑셀 버튼 분석...")
            
            button_info = await page.evaluate("""
                () => {
                    const btn = Ext.getCmp('uniBaseButton-1196');
                    if(!btn) return {found: false};
                    
                    // handler 함수 소스 코드 가져오기
                    let handlerSource = '';
                    if(btn.handler) {
                        handlerSource = btn.handler.toString();
                    }
                    
                    // listeners 확인
                    let listeners = {};
                    if(btn.listeners) {
                        for(let event in btn.listeners) {
                            if(typeof btn.listeners[event] === 'function') {
                                listeners[event] = btn.listeners[event].toString();
                            }
                        }
                    }
                    
                    // 버튼 설정 확인
                    return {
                        found: true,
                        id: btn.id,
                        xtype: btn.xtype,
                        tooltip: btn.tooltip,
                        iconCls: btn.iconCls,
                        handler: handlerSource,
                        listeners: listeners,
                        scope: btn.scope ? btn.scope.id : null,
                        // 추가 속성들
                        action: btn.action,
                        href: btn.href,
                        params: btn.params
                    };
                }
            """)
            
            if button_info['found']:
                print("\n엑셀 버튼 정보:")
                print(f"  ID: {button_info['id']}")
                print(f"  Tooltip: {button_info['tooltip']}")
                print(f"  IconCls: {button_info['iconCls']}")
                print(f"  Scope: {button_info['scope']}")
                
                if button_info['handler']:
                    print(f"\n  Handler 함수:")
                    print(f"  {button_info['handler'][:500]}")
                
                if button_info['listeners']:
                    print(f"\n  Listeners:")
                    for event, func in button_info['listeners'].items():
                        print(f"    {event}: {func[:200]}")
            
            # ExtJS 전역 함수 확인
            print("\n[4] ExtJS 전역 함수 확인...")
            
            global_funcs = await page.evaluate("""
                () => {
                    const funcs = {};
                    
                    // 일반적인 다운로드 함수명들
                    const commonNames = [
                        'doExcelDown', 'excelDownload', 'downloadExcel',
                        'exportExcel', 'fnExcelDown', 'excelDown',
                        'doDownload', 'download', 'exportData'
                    ];
                    
                    for(let name of commonNames) {
                        if(typeof window[name] === 'function') {
                            funcs[name] = window[name].toString().substring(0, 300);
                        }
                    }
                    
                    // Ext.Ajax 요청 확인
                    if(typeof Ext !== 'undefined' && Ext.Ajax) {
                        funcs['Ext.Ajax.request'] = 'Available';
                    }
                    
                    return funcs;
                }
            """)
            
            if global_funcs:
                print("\n발견된 전역 함수:")
                for name, code in global_funcs.items():
                    print(f"  {name}: {code}")
            
            # 버튼 클릭 시뮬레이션
            print("\n[5] 버튼 클릭 시뮬레이션...")
            
            # 네트워크 로그 초기화
            network_logs.clear()
            
            # 버튼 클릭
            click_result = await page.evaluate("""
                () => {
                    const btn = Ext.getCmp('uniBaseButton-1196');
                    if(btn) {
                        // 디버깅을 위해 handler 실행 전 로그
                        console.log('Button click simulation started');
                        
                        if(btn.handler) {
                            // handler 실행
                            const result = btn.handler.call(btn.scope || btn);
                            console.log('Handler executed:', result);
                            return {clicked: true, method: 'handler'};
                        } else {
                            btn.fireEvent('click', btn);
                            return {clicked: true, method: 'fireEvent'};
                        }
                    }
                    return {clicked: false};
                }
            """)
            
            print(f"  클릭 결과: {click_result}")
            
            # 네트워크 요청 대기
            await page.wait_for_timeout(5000)
            
            if network_logs:
                print("\n[6] 캡처된 네트워크 요청:")
                for log in network_logs:
                    print(f"\n  URL: {log['url']}")
                    print(f"  Method: {log['method']}")
                    if log['post_data']:
                        print(f"  POST Data: {log['post_data'][:500]}")
            
            # 콘솔 로그 확인
            print("\n[7] 콘솔 메시지 확인...")
            
            # 콘솔 메시지 리스너 추가
            page.on('console', lambda msg: print(f"  Console: {msg.text}"))
            
            # 다시 클릭해서 콘솔 메시지 확인
            await page.evaluate("""
                () => {
                    const btn = Ext.getCmp('uniBaseButton-1196');
                    if(btn && btn.handler) {
                        console.log('=== Button Handler Debug ===');
                        console.log('Button:', btn);
                        console.log('Handler:', btn.handler.toString());
                        console.log('Scope:', btn.scope);
                        console.log('Calling handler...');
                        btn.handler.call(btn.scope || btn);
                        console.log('Handler called');
                    }
                }
            """)
            
            await page.wait_for_timeout(3000)
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"analyze_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n스크린샷: {screenshot}")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n분석 완료. 30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze_button())
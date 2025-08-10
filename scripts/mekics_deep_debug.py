#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 심층 디버깅 - downloadExcelXml 함수 내부 분석
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def deep_debug():
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
        
        # 네트워크 요청 모니터링
        async def log_request(request):
            if 'download' in request.url.lower() or 'excel' in request.url.lower():
                print(f"\n[Network] {request.method} {request.url}")
                if request.post_data:
                    print(f"  Data: {request.post_data[:200]}")
        
        page.on('request', log_request)
        
        # 콘솔 로그 캡처
        page.on('console', lambda msg: print(f"[Console] {msg.text}"))
        
        try:
            print("\n심층 디버깅 시작")
            print("="*60)
            
            # 페이지 접속
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 실행
            await page.evaluate("""
                () => {
                    // 조건 설정
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date());
                    }
                }
            """)
            
            await page.keyboard.press('F2')
            await page.wait_for_timeout(10000)
            
            print("\n[1] downloadExcelXml 함수 분석...")
            
            # downloadExcelXml 함수 소스 가져오기
            func_analysis = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length === 0) return {error: 'No grid found'};
                    
                    const grid = grids[0];
                    const result = {};
                    
                    // downloadExcelXml 함수 확인
                    if(grid.downloadExcelXml) {
                        result.hasFunction = true;
                        result.functionSource = grid.downloadExcelXml.toString();
                    }
                    
                    // 관련 속성들
                    result.uniOpt = grid.uniOpt;
                    result.store = {
                        count: grid.getStore().getCount(),
                        proxy: grid.getStore().getProxy() ? {
                            type: grid.getStore().getProxy().type,
                            api: grid.getStore().getProxy().getApi ? 
                                Object.keys(grid.getStore().getProxy().getApi()) : []
                        } : null
                    };
                    
                    // 전역 변수들
                    result.globals = {
                        SAVE_AUTH: window.SAVE_AUTH,
                        PGM_ID: window.PGM_ID,
                        PGM_TITLE: window.PGM_TITLE,
                        UserInfo: window.UserInfo ? {
                            userID: window.UserInfo.userID,
                            userName: window.UserInfo.userName
                        } : null
                    };
                    
                    return result;
                }
            """)
            
            print("\n분석 결과:")
            print(f"  downloadExcelXml 존재: {func_analysis.get('hasFunction', False)}")
            print(f"  Store 데이터: {func_analysis.get('store', {})}")
            print(f"  전역 변수: {func_analysis.get('globals', {})}")
            
            if func_analysis.get('functionSource'):
                print(f"\n  함수 소스 (일부):")
                print(f"  {func_analysis['functionSource'][:500]}")
            
            print("\n[2] 실제 다운로드 시도 (모든 변수 설정)...")
            
            # 모든 필요 변수 설정 후 실행
            download_attempt = await page.evaluate("""
                () => {
                    try {
                        // 필수 전역 변수 설정
                        window.SAVE_AUTH = "true";
                        window.PGM_ID = window.PGM_ID || "ssa450skrv";
                        window.PGM_TITLE = window.PGM_TITLE || "매출현황 조회";
                        
                        // UserInfo 설정
                        if(!window.UserInfo) {
                            window.UserInfo = {
                                userID: "20210101",
                                userName: "사용자"
                            };
                        }
                        
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length === 0) return {error: 'No grid'};
                        
                        const grid = grids[0];
                        
                        // Store가 로드되었는지 확인
                        const store = grid.getStore();
                        if(store.getCount() === 0) {
                            return {error: 'No data in store'};
                        }
                        
                        console.log('Grid found, data count:', store.getCount());
                        console.log('Calling downloadExcelXml...');
                        
                        // downloadExcelXml 호출
                        if(grid.downloadExcelXml) {
                            // 다양한 시그니처 시도
                            
                            // 1. 기본 호출
                            grid.downloadExcelXml();
                            
                            // 2. false, title 전달
                            // grid.downloadExcelXml(false, '매출현황 조회');
                            
                            // 3. true, title 전달 (전체 데이터)
                            // grid.downloadExcelXml(true, '매출현황 조회');
                            
                            return {success: true, method: 'called'};
                        }
                        
                        return {error: 'No downloadExcelXml'};
                        
                    } catch(e) {
                        return {error: e.toString(), stack: e.stack};
                    }
                }
            """)
            
            print(f"\n다운로드 시도 결과: {download_attempt}")
            
            # 네트워크 요청 대기
            await page.wait_for_timeout(5000)
            
            print("\n[3] Ext.Ajax.request 직접 호출...")
            
            # Ext.Ajax.request를 직접 사용하여 다운로드
            ajax_attempt = await page.evaluate("""
                () => {
                    try {
                        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                        
                        // 실제 폼 데이터 구성
                        const formData = {
                            DIV_CODE: "01",
                            SALE_FR_DATE: "20210101",
                            SALE_TO_DATE: new Date().toISOString().slice(0,10).replace(/-/g,''),
                            NATION_INOUT: "3",
                            SALE_YN: "A",
                            INCLUDE_LOT_YN: "N",
                            SITE_CODE: "MICS",
                            pgmId: "ssa450skrv",
                            extAction: "ssa450skrvService",
                            extMethod: "selectList1",
                            fileName: `매출현황 조회-${timestamp}`
                        };
                        
                        // Ext.Ajax.request 사용
                        Ext.Ajax.request({
                            url: '/mekics/download/downloadExcel.do',
                            method: 'POST',
                            params: formData,
                            success: function(response) {
                                console.log('Ajax Success:', response);
                                
                                // Blob으로 변환하여 다운로드
                                const blob = new Blob([response.responseText], {
                                    type: 'application/vnd.ms-excel'
                                });
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = `sales_${timestamp}.csv`;
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                window.URL.revokeObjectURL(url);
                            },
                            failure: function(response) {
                                console.log('Ajax Failed:', response);
                            }
                        });
                        
                        return {success: true, method: 'Ext.Ajax.request'};
                        
                    } catch(e) {
                        return {error: e.toString()};
                    }
                }
            """)
            
            print(f"\nExt.Ajax 시도 결과: {ajax_attempt}")
            
            await page.wait_for_timeout(5000)
            
            print("\n[4] iframe 방식 시도...")
            
            # iframe을 사용한 다운로드 (브라우저 보안 우회)
            iframe_attempt = await page.evaluate("""
                () => {
                    try {
                        // 숨은 iframe 생성
                        const iframe = document.createElement('iframe');
                        iframe.style.display = 'none';
                        iframe.name = 'downloadFrame';
                        document.body.appendChild(iframe);
                        
                        // form 생성
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = '/mekics/download/downloadExcel.do';
                        form.target = 'downloadFrame';
                        
                        // 파라미터 추가
                        const params = {
                            DIV_CODE: "01",
                            SALE_FR_DATE: "20210101",
                            SALE_TO_DATE: new Date().toISOString().slice(0,10).replace(/-/g,''),
                            NATION_INOUT: "3",
                            SALE_YN: "A",
                            INCLUDE_LOT_YN: "N",
                            SITE_CODE: "MICS",
                            pgmId: "ssa450skrv",
                            extAction: "ssa450skrvService",
                            extMethod: "selectList1",
                            fileName: "매출현황 조회"
                        };
                        
                        for(const [key, value] of Object.entries(params)) {
                            const input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = key;
                            input.value = value;
                            form.appendChild(input);
                        }
                        
                        document.body.appendChild(form);
                        form.submit();
                        
                        // 정리
                        setTimeout(() => {
                            form.remove();
                            // iframe은 다운로드 완료까지 유지
                        }, 1000);
                        
                        return {success: true, method: 'iframe submit'};
                        
                    } catch(e) {
                        return {error: e.toString()};
                    }
                }
            """)
            
            print(f"\niframe 시도 결과: {iframe_attempt}")
            
            await page.wait_for_timeout(10000)
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"deep_debug_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n스크린샷: {screenshot}")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(deep_debug())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 최종 작동 버전
실제 다운로드 URL 사용: https://it.mek-ics.com/mekics/download/downloadExcel.do
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def final_working_download():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(data_dir)
        )
        
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
        
        # Response 핸들러 - 실제 다운로드 URL 감지
        download_success = False
        saved_file = None
        
        async def handle_response(response):
            nonlocal download_success, saved_file
            
            # 실제 다운로드 URL 확인
            if 'downloadExcel.do' in response.url or 'download' in response.url.lower():
                print(f"\n[Response] 다운로드 응답 감지!")
                print(f"  URL: {response.url}")
                print(f"  Status: {response.status}")
                
                headers = response.headers
                print(f"  Headers: {headers}")
                
                if response.status == 200:
                    try:
                        body = await response.body()
                        if len(body) > 1000:  # 최소 크기 확인
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            
                            # Content-Type으로 확장자 결정
                            content_type = headers.get('content-type', '')
                            if 'csv' in content_type or 'text' in content_type:
                                save_path = data_dir / f"sales_{timestamp}.csv"
                            else:
                                save_path = data_dir / f"sales_{timestamp}.xlsx"
                            
                            with open(save_path, 'wb') as f:
                                f.write(body)
                            
                            file_size = len(body) / (1024 * 1024)
                            print(f"\n[SUCCESS] 파일 저장 완료!")
                            print(f"  파일: {save_path.name}")
                            print(f"  크기: {file_size:.2f} MB")
                            print(f"  경로: {save_path}")
                            
                            download_success = True
                            saved_file = save_path
                    except Exception as e:
                        print(f"  Response body 저장 실패: {e}")
        
        page.on('response', handle_response)
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 다운로드 최종 작동 버전")
            print("="*60)
            
            # 1. 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 2. 조회 조건 설정
            print("\n[2] 조회 조건 설정...")
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
            print("   설정: LOT=아니오, 구분=전체, 기간=2021.01.01~오늘")
            
            # 3. 조회 실행
            print("\n[3] 조회 실행...")
            await page.keyboard.press('F2')
            
            # 4. 로딩 대기
            print("\n[4] 데이터 로딩 대기...")
            for i in range(60):
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
                        return {count: 0, loading: false};
                    }
                """)
                
                if not status['loading'] and status['count'] > 0:
                    print(f"   로딩 완료: {status['count']:,}건")
                    break
                
                if i % 5 == 4:
                    print(f"   로딩 중... ({i+1}초)")
            
            await page.wait_for_timeout(2000)
            
            # 5. 엑셀 버튼 클릭
            print("\n[5] 엑셀 다운로드...")
            
            # 엑셀 버튼 클릭
            await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        if(excelBtn.handler) {
                            excelBtn.handler.call(excelBtn.scope || excelBtn);
                        } else {
                            excelBtn.fireEvent('click', excelBtn);
                        }
                        return true;
                    }
                    return false;
                }
            """)
            print("   엑셀 버튼 클릭")
            
            # 6. 팝업 처리
            await page.wait_for_timeout(2000)
            
            # CSV 팝업에서 '예' 클릭
            popup_result = await page.evaluate("""
                () => {
                    const msgBoxes = Ext.ComponentQuery.query('messagebox');
                    for(let msgBox of msgBoxes) {
                        if(msgBox.isVisible && msgBox.isVisible()) {
                            const buttons = msgBox.query('button');
                            
                            // '예' 버튼 찾기
                            for(let btn of buttons) {
                                const text = btn.getText ? btn.getText() : '';
                                const itemId = btn.itemId || '';
                                
                                if(itemId === 'yes' || text === '예' || text === 'Yes') {
                                    if(btn.handler) {
                                        btn.handler.call(btn.scope || btn);
                                    } else {
                                        btn.fireEvent('click', btn);
                                    }
                                    return {handled: true, button: text || itemId};
                                }
                            }
                        }
                    }
                    return {handled: false};
                }
            """)
            
            if popup_result['handled']:
                print(f"   팝업 처리: '예' 클릭")
            else:
                print("   팝업 없음 또는 이미 처리됨")
            
            # 7. 다운로드 대기
            print("\n[6] 다운로드 대기...")
            for i in range(30):
                await page.wait_for_timeout(1000)
                if download_success:
                    break
                if i % 5 == 4:
                    print(f"   대기 중... ({i+1}초)")
            
            # 8. 직접 다운로드 URL 호출 (백업)
            if not download_success:
                print("\n[7] 직접 다운로드 URL 호출...")
                
                try:
                    # 실제 다운로드 URL
                    download_url = "https://it.mek-ics.com/mekics/download/downloadExcel.do"
                    print(f"   URL: {download_url}")
                    
                    # GET 요청
                    response = await context.request.get(download_url)
                    
                    if response.status == 200:
                        body = await response.body()
                        if len(body) > 1000:
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            
                            # 헤더로 파일 타입 결정
                            headers = await response.all_headers()
                            content_type = headers.get('content-type', '')
                            
                            if 'csv' in content_type or 'text' in content_type:
                                save_path = data_dir / f"sales_direct_{timestamp}.csv"
                            else:
                                save_path = data_dir / f"sales_direct_{timestamp}.xlsx"
                            
                            with open(save_path, 'wb') as f:
                                f.write(body)
                            
                            file_size = len(body) / (1024 * 1024)
                            print(f"\n[SUCCESS - Direct] 파일 저장 완료!")
                            print(f"  파일: {save_path.name}")
                            print(f"  크기: {file_size:.2f} MB")
                            print(f"  경로: {save_path}")
                            
                            download_success = True
                            saved_file = save_path
                        else:
                            print(f"   응답 크기가 너무 작음: {len(body)} bytes")
                    else:
                        print(f"   응답 상태: {response.status}")
                        
                except Exception as e:
                    print(f"   직접 다운로드 실패: {e}")
            
            # 9. POST 요청으로 재시도
            if not download_success:
                print("\n[8] POST 요청으로 재시도...")
                
                try:
                    # 현재 페이지에서 필요한 파라미터 추출
                    params = await page.evaluate("""
                        () => {
                            // 그리드 데이터나 폼 데이터 추출
                            const grid = Ext.ComponentQuery.query('grid')[0];
                            if(grid) {
                                const store = grid.getStore();
                                return {
                                    totalCount: store.getCount(),
                                    // 추가 파라미터가 필요하면 여기에
                                };
                            }
                            return {};
                        }
                    """)
                    
                    # POST 요청
                    response = await context.request.post(
                        "https://it.mek-ics.com/mekics/download/downloadExcel.do",
                        data=params
                    )
                    
                    if response.status == 200:
                        body = await response.body()
                        if len(body) > 1000:
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            save_path = data_dir / f"sales_post_{timestamp}.xlsx"
                            
                            with open(save_path, 'wb') as f:
                                f.write(body)
                            
                            print(f"\n[SUCCESS - POST] 파일 저장 완료!")
                            print(f"  파일: {save_path.name}")
                            print(f"  크기: {len(body) / (1024 * 1024):.2f} MB")
                            
                            download_success = True
                            saved_file = save_path
                            
                except Exception as e:
                    print(f"   POST 요청 실패: {e}")
            
            # 10. 최종 결과
            print("\n" + "="*60)
            if download_success:
                print("다운로드 성공!")
                if saved_file:
                    print(f"저장된 파일: {saved_file}")
            else:
                print("다운로드 실패")
                print("\n추가 확인 사항:")
                print("1. 개발자도구 Network 탭에서 정확한 요청 확인")
                print("2. Request Headers와 Parameters 확인")
                print("3. 세션/쿠키 유효성 확인")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(final_working_download())
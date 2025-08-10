#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 Ultimate - 3단계 백업 전략
1. page.wait_for_event("download") 
2. response에서 Content-Disposition 감지
3. context.request로 직접 재요청
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


async def ultimate_download():
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
        
        # 다운로드 응답 캡처를 위한 변수
        download_response = None
        download_url = None
        
        # Response 핸들러 - Content-Disposition 감지
        async def handle_response(response):
            nonlocal download_response, download_url
            headers = response.headers
            
            # Content-Disposition 헤더 확인
            if 'content-disposition' in headers:
                disposition = headers['content-disposition']
                if 'attachment' in disposition or 'filename' in disposition:
                    print(f"\n[Response] 다운로드 응답 감지!")
                    print(f"  URL: {response.url}")
                    print(f"  Status: {response.status}")
                    print(f"  Content-Disposition: {disposition}")
                    download_response = response
                    download_url = response.url
                    
                    # 즉시 응답 바디 저장
                    try:
                        body = await response.body()
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        
                        # 파일명 추출
                        filename = "download"
                        if 'filename=' in disposition:
                            parts = disposition.split('filename=')
                            if len(parts) > 1:
                                filename = parts[1].strip('"').strip("'").strip()
                        
                        # 확장자 결정
                        if '.csv' in filename or 'csv' in headers.get('content-type', ''):
                            save_path = data_dir / f"sales_{timestamp}.csv"
                        else:
                            save_path = data_dir / f"sales_{timestamp}.xlsx"
                        
                        with open(save_path, 'wb') as f:
                            f.write(body)
                        
                        file_size = len(body) / (1024 * 1024)
                        print(f"\n[SUCCESS - Response Body] 파일 저장 완료!")
                        print(f"  파일: {save_path.name}")
                        print(f"  크기: {file_size:.2f} MB")
                        print(f"  경로: {save_path}")
                        
                    except Exception as e:
                        print(f"  Response body 저장 실패: {e}")
        
        # Response 핸들러 등록
        page.on('response', handle_response)
        
        # Download 핸들러
        download_completed = False
        
        async def handle_download(download):
            nonlocal download_completed
            print(f"\n[Download Event] 다운로드 이벤트 발생!")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if download.suggested_filename.endswith('.csv'):
                save_path = data_dir / f"sales_{timestamp}.csv"
            else:
                save_path = data_dir / f"sales_{timestamp}.xlsx"
            
            await download.save_as(str(save_path))
            download_completed = True
            
            file_size = os.path.getsize(save_path) / (1024 * 1024)
            print(f"\n[SUCCESS - Download Event] 파일 저장 완료!")
            print(f"  파일: {save_path.name}")
            print(f"  크기: {file_size:.2f} MB")
        
        page.on('download', handle_download)
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 다운로드 Ultimate (3단계 백업 전략)")
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
            
            # 5. 엑셀 버튼 클릭 - handler 직접 호출 방식
            print("\n[5] 엑셀 다운로드...")
            
            excel_info = await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        // handler 직접 호출 (fireEvent 대신)
                        if(excelBtn.handler) {
                            excelBtn.handler.call(excelBtn.scope || excelBtn);
                            return {clicked: true, method: 'handler'};
                        } else {
                            excelBtn.fireEvent('click', excelBtn);
                            return {clicked: true, method: 'fireEvent'};
                        }
                    }
                    
                    // 백업: 텍스트로 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('엑셀') || text.includes('Excel')) {
                            if(btn.handler) {
                                btn.handler.call(btn.scope || btn);
                            } else {
                                btn.fireEvent('click', btn);
                            }
                            return {clicked: true, method: 'text search'};
                        }
                    }
                    return {clicked: false};
                }
            """)
            
            print(f"   엑셀 버튼: {excel_info}")
            
            # 6. 팝업 처리 - handler 직접 호출
            await page.wait_for_timeout(2000)
            
            popup_handled = await page.evaluate("""
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
                                    // handler 직접 호출
                                    if(btn.handler) {
                                        btn.handler.call(btn.scope || btn);
                                        return {handled: true, method: 'handler', button: text || itemId};
                                    } else {
                                        btn.fireEvent('click', btn);
                                        return {handled: true, method: 'fireEvent', button: text || itemId};
                                    }
                                }
                            }
                            
                            // 첫 번째 버튼 클릭 (보통 확인)
                            if(buttons.length > 0) {
                                if(buttons[0].handler) {
                                    buttons[0].handler.call(buttons[0].scope || buttons[0]);
                                } else {
                                    buttons[0].fireEvent('click', buttons[0]);
                                }
                                return {handled: true, method: 'first button'};
                            }
                        }
                    }
                    return {handled: false};
                }
            """)
            
            if popup_handled['handled']:
                print(f"   팝업 처리: {popup_handled}")
            else:
                print("   팝업 없음 - 엔터키 시도")
                await page.keyboard.press('Enter')
            
            # 7. 다운로드 대기
            print("\n[6] 다운로드 대기 (30초)...")
            await page.wait_for_timeout(30000)
            
            # 8. 백업 전략 3 - context.request로 직접 재요청
            if not download_completed and not download_response:
                print("\n[7] 백업 전략 - 직접 HTTP 요청...")
                
                # 가능한 다운로드 URL 패턴들
                candidate_urls = [
                    "https://it.mek-ics.com/mekics/sales/ssa450skrv_excel.do",
                    "https://it.mek-ics.com/mekics/sales/ssa450skrv_download.do",
                    "https://it.mek-ics.com/mekics/common/excelDown.do",
                    "https://it.mek-ics.com/mekics/common/csvDown.do",
                    # 실제 엔드포인트 확인 후 추가
                ]
                
                for url in candidate_urls:
                    try:
                        print(f"   시도: {url}")
                        response = await context.request.get(url)
                        
                        if response.status == 200:
                            body = await response.body()
                            if len(body) > 1000:  # 최소 크기 확인
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                save_path = data_dir / f"sales_backup_{timestamp}.xlsx"
                                
                                with open(save_path, 'wb') as f:
                                    f.write(body)
                                
                                print(f"\n[SUCCESS - Direct Request] 파일 저장!")
                                print(f"  파일: {save_path.name}")
                                print(f"  크기: {len(body) / (1024 * 1024):.2f} MB")
                                break
                    except Exception as e:
                        print(f"     실패: {e}")
            
            # 9. 최종 결과
            print("\n" + "="*60)
            if download_completed or download_response:
                print("다운로드 성공!")
            else:
                print("다운로드 실패 - 수동 작업 필요")
                print("\n네트워크 탭에서 실제 다운로드 URL을 확인해주세요:")
                print("1. F12 개발자도구 → Network 탭")
                print("2. 엑셀 버튼 클릭 시 발생하는 요청 확인")
                print("3. Response Headers에서 Content-Disposition 확인")
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
    asyncio.run(ultimate_download())
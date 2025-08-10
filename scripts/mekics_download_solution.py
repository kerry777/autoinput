#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 다운로드 최종 솔루션
실제 POST 요청 파라미터 사용
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


async def download_solution():
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
        
        # 다운로드 핸들러
        download_success = False
        saved_file = None
        
        async def handle_download(download):
            nonlocal download_success, saved_file
            print(f"\n[Download Event] 다운로드 이벤트 발생!")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 원본 파일명 확인
            suggested = download.suggested_filename
            print(f"  원본 파일명: {suggested}")
            
            if '.csv' in suggested:
                save_path = data_dir / f"sales_{timestamp}.csv"
            else:
                save_path = data_dir / f"sales_{timestamp}.xlsx"
            
            await download.save_as(str(save_path))
            
            file_size = os.path.getsize(save_path) / (1024 * 1024)
            print(f"\n[SUCCESS] 다운로드 완료!")
            print(f"  파일: {save_path.name}")
            print(f"  크기: {file_size:.2f} MB")
            print(f"  경로: {save_path}")
            
            download_success = True
            saved_file = save_path
        
        page.on('download', handle_download)
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 다운로드 솔루션")
            print("="*60)
            
            # 1. 페이지 접속
            print("\n[1] 매출현황 페이지 접속...")
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
                    
                    // 날짜 설정
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
            
            # 5. 방법 1: 엑셀 버튼 클릭으로 시도
            print("\n[5] 방법 1: 엑셀 버튼 클릭...")
            
            await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        if(excelBtn.handler) {
                            excelBtn.handler.call(excelBtn.scope || excelBtn);
                        } else {
                            excelBtn.fireEvent('click', excelBtn);
                        }
                    }
                }
            """)
            
            # 팝업 처리
            await page.wait_for_timeout(2000)
            
            await page.evaluate("""
                () => {
                    const msgBoxes = Ext.ComponentQuery.query('messagebox');
                    for(let msgBox of msgBoxes) {
                        if(msgBox.isVisible && msgBox.isVisible()) {
                            const buttons = msgBox.query('button');
                            for(let btn of buttons) {
                                const itemId = btn.itemId || '';
                                if(itemId === 'yes') {
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
            
            print("   팝업 처리 완료")
            
            # 다운로드 대기
            await page.wait_for_timeout(5000)
            
            # 6. 방법 2: 직접 POST 요청
            if not download_success:
                print("\n[6] 방법 2: 직접 POST 요청...")
                
                # 실제 Form Data - 두 세트 모두 포함
                timestamp = datetime.now().strftime("%Y-%m-%d %H%M")
                
                # 첫 번째 파라미터 세트 (검색 조건)
                form_data = {
                    "DIV_CODE": "01",
                    "SALE_CUSTOM_CODE": "",
                    "SALE_CUSTOM_NAME": "",
                    "PROJECT_NO": "",
                    "PROJECT_NAME": "",
                    "SALE_PRSN": "",
                    "ITEM_CODE": "",
                    "ITEM_NAME": "",
                    "undefined": ["undefined", "undefined"],
                    "SALE_FR_DATE": "20210101",
                    "SALE_TO_DATE": datetime.now().strftime("%Y%m%d"),
                    "TAX_TYPE": "",
                    "NATION_INOUT": "3",
                    "ITEM_ACCOUNT": "",
                    "SALE_YN": "A",
                    "ENCLUDE_YN": "Y",
                    "TXT_CREATE_LOC": "",
                    "BILL_TYPE": "",
                    "AGENT_TYPE": "",
                    "ITEM_GROUP_NAME": "",
                    "ITEM_GROUP_CODE": "",
                    "INOUT_TYPE_DETAIL": "",
                    "AREA_TYPE": "",
                    "MANAGE_CUSTOM": "",
                    "MANAGE_CUSTOM_NAME": "",
                    "ORDER_TYPE": "",
                    "ITEM_LEVEL1": "",
                    "ITEM_LEVEL2": "",
                    "ITEM_LEVEL3": "",
                    "BILL_FR_NO": "",
                    "BILL_TO_NO": "",
                    "PUB_FR_NUM": "",
                    "PUB_TO_NUM": "",
                    "ORDER_FR_NUM": "",
                    "ORDER_TO_NUM": "",
                    "SALE_FR_Q": "",
                    "SALE_TO_Q": "",
                    "INOUT_FR_DATE": "",
                    "INOUT_TO_DATE": "",
                    "REMARK": "",
                    "WH_CODE": "",
                    "WH_CELL_CODE": "",
                    "INCLUDE_LOT_YN": "N",
                    "SITE_CODE": "MICS",
                    # 두 번째 파라미터 세트 (엑셀 다운로드용)
                    "figId": "",
                    "pgmId": "ssa450skrv",
                    "extAction": "ssa450skrvService",
                    "extMethod": "selectList1",
                    "fileName": f"매출현황 조회-{timestamp}",
                    "onlyData": "false",
                    "isExportData": "false",
                    "exportData": ""
                }
                
                try:
                    # POST 요청
                    response = await context.request.post(
                        "https://it.mek-ics.com/mekics/download/downloadExcel.do",
                        form=form_data,
                        headers={
                            "Referer": "https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A",
                            "Origin": "https://it.mek-ics.com"
                        }
                    )
                    
                    print(f"   응답 상태: {response.status}")
                    
                    if response.status == 200:
                        body = await response.body()
                        print(f"   응답 크기: {len(body):,} bytes")
                        
                        if len(body) > 1000:
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            
                            # Content-Disposition에서 파일명 확인
                            headers = await response.all_headers()
                            disposition = headers.get('content-disposition', '')
                            
                            if 'csv' in disposition.lower() or 'csv' in headers.get('content-type', ''):
                                save_path = data_dir / f"sales_{timestamp}.csv"
                            else:
                                save_path = data_dir / f"sales_{timestamp}.xlsx"
                            
                            with open(save_path, 'wb') as f:
                                f.write(body)
                            
                            file_size = len(body) / (1024 * 1024)
                            print(f"\n[SUCCESS - POST] 다운로드 완료!")
                            print(f"  파일: {save_path.name}")
                            print(f"  크기: {file_size:.2f} MB")
                            print(f"  경로: {save_path}")
                            
                            download_success = True
                            saved_file = save_path
                            
                except Exception as e:
                    print(f"   POST 요청 실패: {e}")
            
            # 7. 방법 3: iframe 내 폼 제출
            if not download_success:
                print("\n[7] 방법 3: JavaScript로 폼 제출...")
                
                result = await page.evaluate("""
                    () => {
                        // 숨은 폼 생성
                        const form = document.createElement('form');
                        form.method = 'POST';
                        form.action = 'https://it.mek-ics.com/mekics/download/downloadExcel.do';
                        form.target = '_blank';
                        
                        // 파라미터 추가
                        const params = {
                            DIV_CODE: "01",
                            SALE_FR_DATE: "20210101",
                            SALE_TO_DATE: new Date().toISOString().slice(0,10).replace(/-/g,''),
                            NATION_INOUT: "3",
                            SALE_YN: "A",
                            ENCLUDE_YN: "Y",
                            INCLUDE_LOT_YN: "N",
                            SITE_CODE: "MICS"
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
                        
                        setTimeout(() => form.remove(), 100);
                        
                        return true;
                    }
                """)
                
                if result:
                    print("   폼 제출 완료")
                    await page.wait_for_timeout(5000)
            
            # 8. 최종 결과
            print("\n" + "="*60)
            if download_success:
                print("다운로드 성공!")
                if saved_file:
                    print(f"저장된 파일: {saved_file}")
                    
                    # 파일 내용 미리보기
                    with open(saved_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        lines = f.readlines()[:5]
                        print("\n파일 미리보기 (처음 5줄):")
                        for line in lines:
                            print(f"  {line.strip()[:100]}")
            else:
                print("다운로드 실패")
                print("\n세 가지 방법 모두 시도했지만 실패했습니다.")
                print("브라우저에서 수동으로 다운로드를 진행해주세요.")
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
    asyncio.run(download_solution())
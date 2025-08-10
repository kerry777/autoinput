#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 작동하는 다운로드 - 실제 POST 파라미터 사용
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


async def working_download():
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
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 작동하는 다운로드")
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
            print("   설정 완료")
            
            # 3. 조회 실행
            print("\n[3] 조회 실행...")
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
            
            # 4. 방법 1: 직접 폼 제출로 다운로드
            print("\n[4] 직접 폼 제출로 다운로드...")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H%M")
            today = datetime.now().strftime("%Y%m%d")
            
            # JavaScript로 폼 생성 및 제출
            download_result = await page.evaluate(f"""
                () => {{
                    // iframe 생성 (다운로드용)
                    const iframe = document.createElement('iframe');
                    iframe.style.display = 'none';
                    iframe.name = 'downloadFrame';
                    document.body.appendChild(iframe);
                    
                    // 폼 생성
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = '/mekics/download/downloadExcel.do';
                    form.target = 'downloadFrame';  // iframe으로 타겟 설정
                    
                    // 파라미터 추가 (사용자가 제공한 실제 파라미터)
                    const params = {{
                        // 검색 조건
                        "DIV_CODE": "01",
                        "SALE_CUSTOM_CODE": "",
                        "SALE_CUSTOM_NAME": "",
                        "PROJECT_NO": "",
                        "PROJECT_NAME": "",
                        "SALE_PRSN": "",
                        "ITEM_CODE": "",
                        "ITEM_NAME": "",
                        "SALE_FR_DATE": "20210101",
                        "SALE_TO_DATE": "{today}",
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
                        
                        // 엑셀 다운로드 파라미터
                        "figId": "",
                        "pgmId": "ssa450skrv",
                        "extAction": "ssa450skrvService",
                        "extMethod": "selectList1",
                        "fileName": "매출현황 조회-{timestamp}",
                        "onlyData": "false",
                        "isExportData": "false",
                        "exportData": ""
                    }};
                    
                    // hidden input 생성
                    for(const [key, value] of Object.entries(params)) {{
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = key;
                        input.value = value;
                        form.appendChild(input);
                    }}
                    
                    // undefined 파라미터 추가 (배열)
                    const undefinedValues = ["undefined", "undefined"];
                    undefinedValues.forEach(val => {{
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'undefined';
                        input.value = val;
                        form.appendChild(input);
                    }});
                    
                    document.body.appendChild(form);
                    
                    // 폼 제출
                    form.submit();
                    
                    // 정리
                    setTimeout(() => {{
                        form.remove();
                        // iframe은 남겨둠 (다운로드 진행 중)
                    }}, 1000);
                    
                    return {{success: true, timestamp: '{timestamp}'}};
                }}
            """)
            
            print(f"   폼 제출 완료: {download_result}")
            
            # 5. 다운로드 대기 및 확인
            print("\n[5] 다운로드 확인...")
            
            # 파일 시스템 모니터링
            download_found = False
            downloaded_file = None
            
            # 사용자 Downloads 폴더 모니터링
            user_downloads = Path.home() / "Downloads"
            before_files = set()
            for file in user_downloads.iterdir():
                if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                    before_files.add(file.name)
            
            # 모니터링
            for i in range(30):
                await page.wait_for_timeout(1000)
                
                # 사용자 Downloads 폴더 확인
                for file in user_downloads.iterdir():
                    if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                        if file.name not in before_files:
                            # 새 파일 발견
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            target = data_dir / f"sales_{timestamp}{file.suffix}"
                            
                            # 파일 복사
                            import shutil
                            shutil.copy2(file, target)
                            
                            download_found = True
                            downloaded_file = target
                            break
                
                if download_found:
                    break
                
                if i % 5 == 4:
                    print(f"   대기 중... {i+1}초")
            
            # 6. 결과 출력
            if download_found and downloaded_file:
                file_size = downloaded_file.stat().st_size / (1024 * 1024)
                print("\n" + "="*60)
                print("[SUCCESS] 다운로드 성공!")
                print(f"파일: {downloaded_file.name}")
                print(f"크기: {file_size:.2f} MB")
                print(f"경로: {downloaded_file}")
                print("="*60)
                
                # 파일 내용 미리보기
                try:
                    with open(downloaded_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        lines = f.readlines()[:3]
                        print("\n파일 미리보기:")
                        for line in lines:
                            print(f"  {line.strip()[:100]}")
                except:
                    pass
            else:
                print("\n" + "="*60)
                print("[FAIL] 다운로드 실패")
                print("브라우저의 Downloads 폴더를 확인해주세요")
                print("="*60)
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"working_{timestamp}.png"
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
    asyncio.run(working_download())
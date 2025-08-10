#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 강제 다운로드 - 다양한 우회 방법 시도
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import base64

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def force_download():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(data_dir / "downloads")
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
        
        # 다운로드 이벤트 처리
        async def handle_download(download):
            print(f"\n[DOWNLOAD EVENT] 파일 다운로드 감지!")
            print(f"  URL: {download.url}")
            filename = download.suggested_filename
            save_path = data_dir / "downloads" / filename
            save_path.parent.mkdir(exist_ok=True)
            await download.save_as(str(save_path))
            print(f"  저장됨: {save_path}")
            return save_path
        
        page.on('download', handle_download)
        
        try:
            print("\n강제 다운로드 시도")
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
                    
                    // 짧은 기간 설정
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2025, 7, 1));  // 8월 1일
                        dateFields[1].setValue(new Date(2025, 7, 10)); // 8월 10일
                    }
                }
            """)
            
            await page.keyboard.press('F2')
            
            print("   데이터 로딩 중...")
            await page.wait_for_timeout(10000)
            
            # 데이터 개수 확인
            data_count = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0) {
                        return grids[0].getStore().getCount();
                    }
                    return 0;
                }
            """)
            print(f"   조회된 데이터: {data_count}건")
            
            print("\n[3] 방법 1: Store 데이터 직접 추출 및 CSV 생성...")
            
            # Store에서 데이터 직접 추출
            extracted_data = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length === 0) return null;
                    
                    const grid = grids[0];
                    const store = grid.getStore();
                    const columns = grid.getColumns();
                    
                    // 컬럼 헤더 추출
                    const headers = columns
                        .filter(col => !col.hidden && col.dataIndex)
                        .map(col => col.text || col.dataIndex);
                    
                    // 데이터 추출
                    const rows = [];
                    store.each(record => {
                        const row = columns
                            .filter(col => !col.hidden && col.dataIndex)
                            .map(col => {
                                let value = record.get(col.dataIndex);
                                if(value === null || value === undefined) value = '';
                                return String(value);
                            });
                        rows.push(row);
                    });
                    
                    return {
                        headers: headers,
                        rows: rows,
                        count: rows.length
                    };
                }
            """)
            
            if extracted_data:
                print(f"   추출된 데이터: {extracted_data['count']}건")
                
                # CSV 파일 생성
                import csv
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                csv_file = data_dir / f"sales_data_{timestamp}.csv"
                
                with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(extracted_data['headers'])
                    writer.writerows(extracted_data['rows'])
                
                print(f"   CSV 파일 생성: {csv_file}")
            
            print("\n[4] 방법 2: CDP (Chrome DevTools Protocol) 다운로드 강제...")
            
            # CDP를 사용한 다운로드 시도
            client = await page.context.new_cdp_session(page)
            await client.send('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': str(data_dir / "downloads")
            })
            
            # 엑셀 버튼 클릭 (CDP 활성화 상태)
            click_result = await page.evaluate("""
                () => {
                    const btn = Ext.getCmp('uniBaseButton-1196');
                    if(btn) {
                        btn.handler.call(btn.scope || btn);
                        return true;
                    }
                    return false;
                }
            """)
            
            if click_result:
                print("   엑셀 버튼 클릭 (CDP 모드)")
                await page.wait_for_timeout(5000)
            
            print("\n[5] 방법 3: JavaScript Blob 다운로드...")
            
            # JavaScript에서 직접 Blob 생성 및 다운로드
            await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length === 0) return;
                    
                    const grid = grids[0];
                    const store = grid.getStore();
                    const columns = grid.getColumns();
                    
                    // CSV 생성
                    let csv = '';
                    
                    // 헤더
                    const headers = columns
                        .filter(col => !col.hidden && col.dataIndex)
                        .map(col => col.text || col.dataIndex);
                    csv += headers.join(',') + '\\n';
                    
                    // 데이터
                    store.each(record => {
                        const row = columns
                            .filter(col => !col.hidden && col.dataIndex)
                            .map(col => {
                                let value = record.get(col.dataIndex);
                                if(value === null || value === undefined) value = '';
                                // CSV 이스케이프
                                value = String(value).replace(/"/g, '""');
                                if(value.includes(',') || value.includes('"') || value.includes('\\n')) {
                                    value = '"' + value + '"';
                                }
                                return value;
                            });
                        csv += row.join(',') + '\\n';
                    });
                    
                    // BOM 추가 (Excel 한글 깨짐 방지)
                    const BOM = '\\uFEFF';
                    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
                    
                    // 다운로드 링크 생성
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'sales_data_' + new Date().getTime() + '.csv';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    
                    console.log('Blob download triggered');
                }
            """)
            
            print("   Blob 다운로드 트리거됨")
            await page.wait_for_timeout(3000)
            
            print("\n[6] 방법 4: fetch API로 직접 요청...")
            
            # fetch API 사용
            fetch_result = await page.evaluate("""
                async () => {
                    try {
                        const formData = new FormData();
                        formData.append('DIV_CODE', '01');
                        formData.append('SALE_FR_DATE', '20250801');
                        formData.append('SALE_TO_DATE', '20250810');
                        formData.append('NATION_INOUT', '3');
                        formData.append('SALE_YN', 'A');
                        formData.append('INCLUDE_LOT_YN', 'N');
                        formData.append('SITE_CODE', 'MICS');
                        formData.append('pgmId', 'ssa450skrv');
                        formData.append('extAction', 'ssa450skrvService');
                        formData.append('extMethod', 'selectList1');
                        
                        const response = await fetch('/mekics/download/downloadExcel.do', {
                            method: 'POST',
                            body: formData,
                            credentials: 'same-origin'
                        });
                        
                        if(response.ok) {
                            const blob = await response.blob();
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = 'sales_fetch.csv';
                            document.body.appendChild(a);
                            a.click();
                            return {success: true, status: response.status};
                        } else {
                            return {success: false, status: response.status};
                        }
                    } catch(e) {
                        return {error: e.toString()};
                    }
                }
            """)
            
            print(f"   Fetch 결과: {fetch_result}")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"force_download_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n스크린샷: {screenshot}")
            
            print("\n" + "="*60)
            print("다운로드 시도 완료")
            print("CSV 파일이 생성되었는지 확인하세요:")
            print(f"  {data_dir}")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(force_download())
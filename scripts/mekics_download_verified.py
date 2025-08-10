#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 검증된 다운로드 - 쿠키 사용
"""

import asyncio
import json
import csv
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def download_large_data():
    """대용량 데이터 다운로드"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    downloads_dir = data_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
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
            print("쿠키 로드 완료")
        
        page = await context.new_page()
        
        # 다운로드 이벤트 핸들러
        download_path = None
        
        async def handle_download(download):
            nonlocal download_path
            print(f"\n[다운로드 이벤트] 파일 다운로드 시작!")
            print(f"  URL: {download.url}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = download.suggested_filename or f"download_{timestamp}.csv"
            
            # 파일명 정리
            if "매출" not in filename:
                filename = f"매출현황_{timestamp}_{filename}"
            
            save_path = downloads_dir / filename
            
            try:
                await download.save_as(str(save_path))
                download_path = save_path
                print(f"  저장 완료: {filename}")
                return save_path
            except Exception as e:
                print(f"  저장 실패: {e}")
                # 실패해도 계속 진행
                pass
        
        page.on('download', handle_download)
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 대용량 다운로드 검증")
            print("="*60)
            
            # 매출현황조회 페이지 직접 접속
            print("\n[1] 매출현황조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # ExtJS 로드 확인
            extjs_ready = await page.evaluate("() => typeof Ext !== 'undefined'")
            if not extjs_ready:
                print("  ExtJS 로드 대기...")
                await page.wait_for_timeout(3000)
            
            # 조회 조건 설정 (대용량)
            print("\n[2] 대용량 데이터 조회 조건 설정...")
            print("  기간: 2021.01.01 ~ 오늘")
            
            setup_done = await page.evaluate("""
                () => {
                    try {
                        // LOT표시 '아니오'
                        const noRadio = Ext.getCmp('radiofield-1078');
                        if(noRadio) noRadio.setValue(true);
                        
                        // 국내/해외 '전체'
                        const allRadio = Ext.getCmp('radiofield-1081');
                        if(allRadio) allRadio.setValue(true);
                        
                        // 날짜 설정 (대용량)
                        const dateFields = Ext.ComponentQuery.query('datefield');
                        if(dateFields.length >= 2) {
                            dateFields[0].setValue(new Date(2021, 0, 1));  // 2021년 1월 1일
                            dateFields[1].setValue(new Date());  // 오늘
                        }
                        
                        return true;
                    } catch(e) {
                        console.error(e);
                        return false;
                    }
                }
            """)
            
            if setup_done:
                print("  조건 설정 완료")
            
            # 조회 실행
            print("\n[3] 데이터 조회 실행 (F2)...")
            await page.keyboard.press('F2')
            
            # CSV 팝업 대기
            print("\n[4] CSV 팝업 확인 (대용량 시 표시)...")
            csv_popup_found = False
            
            for i in range(15):
                await page.wait_for_timeout(1000)
                
                # CSV 팝업 확인
                popup_check = await page.evaluate("""
                    () => {
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        for(let box of msgBoxes) {
                            if(box.isVisible && box.isVisible()) {
                                const msg = box.msg || '';
                                if(msg.includes('CSV')) {
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                """)
                
                if popup_check:
                    csv_popup_found = True
                    print("  CSV 다운로드 팝업 감지!")
                    break
                
                if i % 3 == 2:
                    print(f"  대기 중... {i+1}초")
            
            if csv_popup_found:
                # CSV 다운로드 처리
                print("\n[5] CSV 다운로드 시작...")
                
                # '예' 버튼 클릭
                yes_clicked = await page.evaluate("""
                    () => {
                        const msgBoxes = Ext.ComponentQuery.query('messagebox');
                        for(let box of msgBoxes) {
                            if(box.isVisible && box.isVisible()) {
                                const buttons = box.query('button');
                                for(let btn of buttons) {
                                    if(btn.itemId === 'yes' || btn.getText() === '예') {
                                        btn.fireEvent('click', btn);
                                        return true;
                                    }
                                }
                            }
                        }
                        return false;
                    }
                """)
                
                if yes_clicked:
                    print("  '예' 버튼 클릭 완료")
                    
                    # 다운로드 완료 대기
                    print("  다운로드 대기 중...")
                    await page.wait_for_timeout(10000)
                    
                    if download_path:
                        # 파일 크기 확인
                        file_size = download_path.stat().st_size / (1024 * 1024)
                        
                        # 라인 수 확인
                        with open(download_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                            line_count = sum(1 for line in f) - 1
                        
                        print("\n" + "="*60)
                        print("다운로드 성공!")
                        print(f"파일: {download_path.name}")
                        print(f"크기: {file_size:.2f} MB")
                        print(f"데이터: {line_count:,}건")
                        print("="*60)
            
            else:
                # Store 데이터만 추출
                print("\n[5] Store 데이터 추출...")
                
                # 데이터 개수 확인
                data_info = await page.evaluate("""
                    () => {
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length > 0) {
                            const store = grids[0].getStore();
                            return {
                                current: store.getCount(),
                                total: store.getTotalCount ? store.getTotalCount() : store.getCount()
                            };
                        }
                        return {current: 0, total: 0};
                    }
                """)
                
                print(f"  현재 로드: {data_info['current']}건")
                print(f"  전체 데이터: {data_info['total']}건")
                
                if data_info['current'] > 0:
                    # Store 데이터 추출
                    extracted = await page.evaluate("""
                        () => {
                            const grids = Ext.ComponentQuery.query('grid');
                            if(grids.length === 0) return null;
                            
                            const grid = grids[0];
                            const store = grid.getStore();
                            const columns = grid.getColumns();
                            
                            const headers = [];
                            const dataIndexes = [];
                            
                            columns.forEach(col => {
                                if(!col.hidden && col.dataIndex) {
                                    headers.push(col.text || col.dataIndex);
                                    dataIndexes.push(col.dataIndex);
                                }
                            });
                            
                            const rows = [];
                            store.each(record => {
                                const row = [];
                                dataIndexes.forEach(dataIndex => {
                                    let value = record.get(dataIndex);
                                    if(value === null || value === undefined) {
                                        value = '';
                                    }
                                    row.push(String(value));
                                });
                                rows.push(row);
                            });
                            
                            return {headers, rows, count: rows.length};
                        }
                    """)
                    
                    if extracted:
                        # CSV 저장
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        csv_file = downloads_dir / f"매출현황_store_{timestamp}.csv"
                        
                        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(extracted['headers'])
                            writer.writerows(extracted['rows'])
                        
                        print(f"\n  Store 데이터 저장: {csv_file}")
                        print(f"  데이터: {extracted['count']}건")
                        
                        # Blob 다운로드 시도
                        print("\n[6] Blob 다운로드 시도...")
                        await page.evaluate("""
                            () => {
                                const grids = Ext.ComponentQuery.query('grid');
                                if(grids.length === 0) return;
                                
                                const grid = grids[0];
                                const store = grid.getStore();
                                const columns = grid.getColumns();
                                
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
                                            value = String(value).replace(/"/g, '""');
                                            if(value.includes(',') || value.includes('"') || value.includes('\\n')) {
                                                value = '"' + value + '"';
                                            }
                                            return value;
                                        });
                                    csv += row.join(',') + '\\n';
                                });
                                
                                // BOM 추가
                                const BOM = '\\uFEFF';
                                const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
                                
                                // 다운로드
                                const url = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = url;
                                a.download = 'sales_blob_' + new Date().getTime() + '.csv';
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                                window.URL.revokeObjectURL(url);
                            }
                        """)
                        
                        print("  Blob 다운로드 트리거됨")
                        await page.wait_for_timeout(3000)
            
            # 최종 파일 목록
            print("\n[최종 결과]")
            print("-"*40)
            
            files = list(downloads_dir.glob("*.csv")) + list(downloads_dir.glob("*.xlsx"))
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            print(f"다운로드 폴더: {downloads_dir}")
            print(f"파일 개수: {len(files)}개")
            
            if files:
                print("\n최근 파일:")
                for file in files[:5]:
                    size = file.stat().st_size / (1024 * 1024)
                    print(f"  - {file.name} ({size:.2f} MB)")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"verified_{timestamp}.png"
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
    asyncio.run(download_large_data())
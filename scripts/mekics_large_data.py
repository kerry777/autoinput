#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 대용량 데이터 다운로드 - 페이징 처리
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import csv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def extract_large_data():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    downloads_dir = data_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            print("\nMEK-ICS 대용량 데이터 추출")
            print("="*60)
            
            # 페이지 접속
            print("\n[1] 매출현황조회 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 조건 설정 (대용량)
            print("\n[2] 조회 조건 설정...")
            start_date = "20210101"  # 2021년 시작
            end_date = datetime.now().strftime('%Y%m%d')
            print(f"  날짜 설정: {start_date} ~ {end_date}")
            
            await page.evaluate(f"""
                () => {{
                    // LOT표시 '아니오'
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    // 국내/해외 '전체'
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 날짜 설정
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {{
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date());
                    }}
                }}
            """)
            
            # 조회 실행
            print("\n[3] 데이터 조회 실행...")
            await page.keyboard.press('F2')
            
            # CSV 팝업 처리 (대용량 시 나타남)
            print("  CSV 팝업 대기 중...")
            try:
                # CSV 팝업 감지
                csv_popup = await page.wait_for_selector('text="CSV 형태로 다운로드"', timeout=15000)
                if csv_popup:
                    print("\n[4] CSV 다운로드 팝업 감지!")
                    print("  대용량 데이터 감지 - CSV 다운로드 시도")
                    
                    # '예' 버튼 클릭
                    yes_button = await page.wait_for_selector('span.x-btn-inner:has-text("예")', timeout=2000)
                    if yes_button:
                        print("  '예' 버튼 클릭...")
                        
                        # 다운로드 준비
                        async with page.expect_download() as download_info:
                            await yes_button.click()
                            print("  다운로드 시작 대기...")
                            
                            # 다운로드 대기
                            download = await download_info.value
                            
                            # 파일 저장
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            save_path = downloads_dir / f"sales_large_{timestamp}.csv"
                            await download.save_as(str(save_path))
                            
                            file_size = save_path.stat().st_size / (1024 * 1024)
                            print(f"\n[성공] CSV 다운로드 완료!")
                            print(f"  파일: {save_path.name}")
                            print(f"  크기: {file_size:.2f} MB")
                            print(f"  경로: {save_path}")
                            
                            # 데이터 건수 확인
                            with open(save_path, 'r', encoding='utf-8-sig') as f:
                                line_count = sum(1 for line in f) - 1  # 헤더 제외
                            print(f"  데이터: {line_count:,}건")
                            
                            return save_path
                            
            except Exception as popup_error:
                print(f"  팝업 처리 실패: {popup_error}")
                print("  일반 조회로 전환...")
            
            # 팝업이 없거나 실패한 경우 - Store 데이터 확인
            await page.wait_for_timeout(10000)
            
            # Store 정보 확인
            store_info = await page.evaluate("""
                () => {
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0) {
                        const store = grids[0].getStore();
                        return {
                            currentCount: store.getCount(),
                            totalCount: store.getTotalCount ? store.getTotalCount() : store.getCount(),
                            pageSize: store.pageSize || store.getCount(),
                            currentPage: store.currentPage || 1
                        };
                    }
                    return null;
                }
            """)
            
            if store_info:
                print(f"\n[5] Store 정보:")
                print(f"  현재 로드: {store_info['currentCount']:,}건")
                print(f"  전체 데이터: {store_info['totalCount']:,}건")
                print(f"  페이지 크기: {store_info['pageSize']}")
                
                if store_info['totalCount'] > store_info['currentCount']:
                    print("\n[경고] 페이징 처리 필요!")
                    print("  전체 데이터를 받으려면 서버 다운로드가 필요합니다.")
                    
                    # 페이징으로 모든 데이터 수집 시도
                    print("\n[6] 페이징 데이터 수집 시도...")
                    
                    all_data = []
                    total_pages = (store_info['totalCount'] // store_info['pageSize']) + 1
                    
                    for page_num in range(1, min(total_pages + 1, 11)):  # 최대 10페이지
                        print(f"  페이지 {page_num}/{total_pages} 로드 중...")
                        
                        # 페이지 로드
                        page_data = await page.evaluate(f"""
                            () => {{
                                return new Promise((resolve) => {{
                                    const grid = Ext.ComponentQuery.query('grid')[0];
                                    const store = grid.getStore();
                                    
                                    // 페이지 로드
                                    store.loadPage({page_num}, {{
                                        callback: function(records, operation, success) {{
                                            if(success) {{
                                                // 현재 페이지 데이터 추출
                                                const data = [];
                                                store.each(record => {{
                                                    data.push(record.data);
                                                }});
                                                resolve(data);
                                            }} else {{
                                                resolve([]);
                                            }}
                                        }}
                                    }});
                                }});
                            }}
                        """)
                        
                        if page_data:
                            all_data.extend(page_data)
                            print(f"    {len(page_data)}건 수집")
                        
                        await page.wait_for_timeout(2000)
                    
                    print(f"\n  총 수집: {len(all_data)}건")
                    
                    if all_data:
                        # CSV 저장
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        csv_file = downloads_dir / f"sales_paging_{timestamp}.csv"
                        
                        # 헤더 추출
                        headers = list(all_data[0].keys()) if all_data else []
                        
                        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=headers)
                            writer.writeheader()
                            writer.writerows(all_data)
                        
                        print(f"\n[완료] 페이징 데이터 저장")
                        print(f"  파일: {csv_file}")
                else:
                    # 현재 Store 데이터만 추출
                    print("\n[7] 현재 Store 데이터 추출...")
                    extracted_data = await page.evaluate("""
                        () => {
                            const grids = Ext.ComponentQuery.query('grid');
                            if(grids.length === 0) return null;
                            
                            const grid = grids[0];
                            const store = grid.getStore();
                            
                            const data = [];
                            store.each(record => {
                                data.push(record.data);
                            });
                            
                            return data;
                        }
                    """)
                    
                    if extracted_data:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        csv_file = downloads_dir / f"sales_store_{timestamp}.csv"
                        
                        headers = list(extracted_data[0].keys()) if extracted_data else []
                        
                        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=headers)
                            writer.writeheader()
                            writer.writerows(extracted_data)
                        
                        print(f"  저장: {csv_file}")
                        print(f"  데이터: {len(extracted_data)}건")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"large_data_{timestamp}.png"
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
    asyncio.run(extract_large_data())
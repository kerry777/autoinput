#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 재고현황 다운로드 - 매출현황에서 습득한 노하우 적용
"""

import asyncio
import json
import csv
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from engine.universal_downloader import UniversalDownloadEngine


class MekicsInventoryDownloader:
    """재고현황 다운로드 - 검증된 Store 추출 방식 사용"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.downloads_dir = self.data_dir / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
    async def load_cookies(self, context):
        """저장된 쿠키 로드 (로그인 우회)"""
        cookie_file = self.data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("✓ 쿠키 로드 완료 (2FA 우회)")
            return True
        return False
    
    async def extract_store_data(self, page):
        """
        핵심 노하우: ExtJS Store 직접 추출
        서버 다운로드 실패해도 데이터는 이미 메모리에 있음!
        """
        return await page.evaluate("""
            () => {
                // 1. 그리드 찾기
                const grids = Ext.ComponentQuery.query('grid');
                if (grids.length === 0) return null;
                
                const grid = grids[0];
                const store = grid.getStore();
                const columns = grid.getColumns();
                
                // 2. 컬럼 헤더 추출
                const headers = columns
                    .filter(col => !col.hidden && col.dataIndex)
                    .map(col => col.text || col.dataIndex);
                
                // 3. 전체 데이터 추출 (페이징 무관)
                const rows = [];
                store.each(record => {
                    const row = columns
                        .filter(col => !col.hidden && col.dataIndex)
                        .map(col => {
                            let value = record.get(col.dataIndex);
                            // 숫자 포맷 처리
                            if (typeof value === 'number') {
                                value = value.toLocaleString('ko-KR');
                            }
                            return String(value || '');
                        });
                    rows.push(row);
                });
                
                return {
                    headers: headers,
                    rows: rows,
                    total: store.getTotalCount(),
                    count: rows.length
                };
            }
        """)
    
    async def save_to_csv(self, data, filename_prefix="재고현황"):
        """CSV 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{filename_prefix}_{timestamp}.csv"
        filepath = self.downloads_dir / filename
        
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data['headers'])
            writer.writerows(data['rows'])
        
        print(f"✓ CSV 저장 완료: {filepath}")
        print(f"  - 데이터 건수: {data['count']:,}건")
        print(f"  - 파일 크기: {filepath.stat().st_size / 1024:.1f} KB")
        return filepath
    
    async def trigger_blob_download(self, page, data):
        """브라우저에서 직접 다운로드 트리거"""
        await page.evaluate("""
            (data) => {
                // CSV 문자열 생성
                const BOM = '\\uFEFF';
                const headers = data.headers.join(',');
                const rows = data.rows.map(row => row.join(','));
                const csv = BOM + headers + '\\n' + rows.join('\\n');
                
                // Blob 생성 및 다운로드
                const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `재고현황_${new Date().toISOString().slice(0,10)}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                return true;
            }
        """, data)
        print("✓ 브라우저 다운로드 트리거 완료")
    
    async def run(self):
        """재고현황 다운로드 실행"""
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                downloads_path=str(self.downloads_dir)
            )
            
            context = await browser.new_context(
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            
            # 쿠키 로드
            await self.load_cookies(context)
            
            page = await context.new_page()
            
            try:
                print("\n" + "="*60)
                print("MEK-ICS 재고현황 다운로드")
                print("매출현황에서 검증된 방식 적용")
                print("="*60)
                
                # 1. 메인 페이지 접속
                print("\n[1] MEK-ICS 접속...")
                await page.goto("https://it.mek-ics.com/mekics/main/main.do")
                await page.wait_for_timeout(3000)
                
                # 2. 재고관리 모듈로 이동 
                print("\n[2] 재고관리 모듈 이동...")
                await page.evaluate("""
                    () => {
                        // 재고관리 모듈 ID는 보통 18
                        if (typeof changeModule === 'function') {
                            changeModule('18');
                        }
                    }
                """)
                await page.wait_for_timeout(3000)
                
                # 3. 품목별현재고현황 메뉴 클릭
                print("\n[3] 품목별현재고현황 메뉴 찾기...")
                menu_clicked = await page.evaluate("""
                    () => {
                        // 트리에서 메뉴 찾기
                        const tree = Ext.ComponentQuery.query('treepanel')[0];
                        if (tree) {
                            const store = tree.getStore();
                            const node = store.findNode('text', '품목별현재고현황', false);
                            if (node) {
                                tree.getSelectionModel().select(node);
                                tree.fireEvent('itemclick', tree, node);
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if not menu_clicked:
                    print("  ! 메뉴를 찾을 수 없음, URL 직접 이동 시도...")
                    # 직접 URL 이동 (URL은 실제 확인 필요)
                    await page.goto("https://it.mek-ics.com/mekics/inventory/siv200skrv.do")
                
                await page.wait_for_timeout(5000)
                
                # 4. 조회 조건 설정
                print("\n[4] 조회 조건 설정...")
                await page.evaluate("""
                    () => {
                        // 날짜 설정 (현재 날짜)
                        const dateFields = Ext.ComponentQuery.query('datefield');
                        if (dateFields.length > 0) {
                            dateFields[0].setValue(new Date());
                        }
                        
                        // 창고 전체 선택 (있는 경우)
                        const warehouseCombo = Ext.ComponentQuery.query('combo[fieldLabel*="창고"]')[0];
                        if (warehouseCombo) {
                            warehouseCombo.setValue('ALL');
                        }
                        
                        // 품목구분 전체 (있는 경우)
                        const itemTypeRadio = Ext.ComponentQuery.query('radiofield[boxLabel="전체"]')[0];
                        if (itemTypeRadio) {
                            itemTypeRadio.setValue(true);
                        }
                    }
                """)
                
                # 5. 조회 실행 (F2)
                print("\n[5] 데이터 조회 (F2)...")
                await page.keyboard.press('F2')
                
                # 데이터 로딩 대기
                print("  데이터 로딩 대기...")
                await page.wait_for_timeout(10000)
                
                # 로딩 완료 확인
                is_loaded = await page.evaluate("""
                    () => {
                        const grid = Ext.ComponentQuery.query('grid')[0];
                        return grid && grid.getStore().getCount() > 0;
                    }
                """)
                
                if not is_loaded:
                    print("  ! 데이터 로딩 실패, 재시도...")
                    await page.keyboard.press('F2')
                    await page.wait_for_timeout(10000)
                
                # 6. Store 데이터 추출 (핵심!)
                print("\n[6] ExtJS Store 데이터 추출...")
                data = await self.extract_store_data(page)
                
                if data and data['count'] > 0:
                    print(f"  ✓ 데이터 추출 성공: {data['count']:,}건")
                    
                    # 7. CSV 파일 저장
                    csv_file = await self.save_to_csv(data, "품목별현재고현황")
                    
                    # 8. 브라우저 다운로드도 트리거
                    await self.trigger_blob_download(page, data)
                    
                    # 9. 범용 다운로더도 시도 (백업)
                    print("\n[7] 범용 다운로더 백업 시도...")
                    downloader = UniversalDownloadEngine(str(self.downloads_dir))
                    
                    async def trigger_excel():
                        await page.evaluate("""
                            () => {
                                const btn = Ext.ComponentQuery.query('button[text*="Excel"]')[0] ||
                                           Ext.getCmp('excelDownloadButton');
                                if (btn) btn.fireEvent('click', btn);
                            }
                        """)
                    
                    backup_results = await downloader.download(page, trigger_action=trigger_excel)
                    
                    print("\n" + "="*60)
                    print("✅ 재고현황 다운로드 완료!")
                    print(f"  - 추출 데이터: {data['count']:,}건")
                    print(f"  - 저장 위치: {self.downloads_dir}")
                    print("="*60)
                    
                else:
                    print("  ✗ 데이터 추출 실패")
                
                # 스크린샷 저장
                screenshot = self.data_dir / f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot))
                print(f"\n스크린샷: {screenshot}")
                
            except Exception as e:
                print(f"\n오류 발생: {e}")
                import traceback
                traceback.print_exc()
            
            finally:
                print("\n30초 후 브라우저 종료...")
                await page.wait_for_timeout(30000)
                await browser.close()


async def main():
    """메인 실행 함수"""
    downloader = MekicsInventoryDownloader()
    await downloader.run()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MEK-ICS 재고현황 다운로드")
    print("오늘 습득한 노하우 100% 적용!")
    print("="*60)
    print("\n주요 적용 기술:")
    print("1. ExtJS Store 직접 추출 (서버 API 우회)")
    print("2. 쿠키 세션 재사용 (2FA 우회)")
    print("3. Blob 다운로드 트리거")
    print("4. UniversalDownloadEngine 백업")
    print("="*60)
    
    asyncio.run(main())
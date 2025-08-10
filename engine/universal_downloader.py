#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
범용 다운로드 엔진 - 모든 웹사이트 다운로드 대응
"""

from playwright.async_api import async_playwright
from pathlib import Path
import asyncio
import json
import time
import shutil
import os


class UniversalDownloadEngine:
    """모든 웹사이트에서 작동하는 다운로드 엔진"""
    
    def __init__(self, download_dir="downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.strategies = []
        
    async def download(self, page, trigger_selector=None, trigger_action=None):
        """
        범용 다운로드 실행
        
        Args:
            page: Playwright page 객체
            trigger_selector: 다운로드 버튼 선택자
            trigger_action: 다운로드 트리거 액션
        
        Returns:
            다운로드된 파일 경로 또는 데이터
        """
        
        results = {}
        
        # 전략 1: Playwright 다운로드 이벤트 캡처
        result1 = await self.strategy_playwright_download(page, trigger_selector, trigger_action)
        if result1:
            results['playwright'] = result1
        
        # 전략 2: 네트워크 응답 인터셉트
        result2 = await self.strategy_network_intercept(page, trigger_selector, trigger_action)
        if result2:
            results['network'] = result2
        
        # 전략 3: JavaScript 데이터 추출 (ExtJS, React, Vue 등)
        result3 = await self.strategy_javascript_extraction(page)
        if result3:
            results['javascript'] = result3
        
        # 전략 4: 파일 시스템 모니터링
        result4 = await self.strategy_filesystem_monitor(page, trigger_selector, trigger_action)
        if result4:
            results['filesystem'] = result4
        
        # 전략 5: CDP 다운로드 캡처
        result5 = await self.strategy_cdp_download(page, trigger_selector, trigger_action)
        if result5:
            results['cdp'] = result5
        
        return results
    
    async def strategy_playwright_download(self, page, trigger_selector, trigger_action):
        """전략 1: Playwright 기본 다운로드 이벤트"""
        try:
            download_path = None
            
            async def handle_download(download):
                nonlocal download_path
                filename = download.suggested_filename
                save_path = self.download_dir / filename
                
                try:
                    await download.save_as(str(save_path))
                    download_path = save_path
                    print(f"[Playwright] 다운로드 성공: {filename}")
                    return save_path
                except Exception as e:
                    print(f"[Playwright] 다운로드 실패: {e}")
                    # 실패해도 경로는 반환
                    await download.failure()
                    return None
            
            # 다운로드 이벤트 리스너 등록
            page.once('download', handle_download)
            
            # 다운로드 트리거
            if trigger_action:
                await trigger_action(page)
            elif trigger_selector:
                await page.click(trigger_selector)
            
            # 다운로드 대기
            await page.wait_for_timeout(5000)
            
            return download_path
            
        except Exception as e:
            print(f"[Playwright] 전략 실패: {e}")
            return None
    
    async def strategy_network_intercept(self, page, trigger_selector, trigger_action):
        """전략 2: 네트워크 응답 인터셉트"""
        try:
            captured_response = None
            
            async def handle_response(response):
                nonlocal captured_response
                
                # 다운로드 관련 응답 감지
                if any(keyword in response.url.lower() for keyword in ['download', 'export', 'excel', 'csv', 'pdf']):
                    if response.status == 200:
                        content = await response.body()
                        
                        # 파일명 추출
                        headers = response.headers
                        filename = "download"
                        
                        if 'content-disposition' in headers:
                            import re
                            match = re.search(r'filename[^;=\n]*=([\"\']?)([^\"\';]*)\1', headers['content-disposition'])
                            if match:
                                filename = match.group(2)
                        
                        # 확장자 추정
                        content_type = headers.get('content-type', '')
                        if 'excel' in content_type or 'spreadsheet' in content_type:
                            filename += '.xlsx'
                        elif 'csv' in content_type:
                            filename += '.csv'
                        elif 'pdf' in content_type:
                            filename += '.pdf'
                        
                        # 파일 저장
                        save_path = self.download_dir / filename
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        
                        captured_response = save_path
                        print(f"[Network] 응답 캡처 성공: {filename}")
            
            # 응답 리스너 등록
            page.on('response', handle_response)
            
            # 다운로드 트리거
            if trigger_action:
                await trigger_action(page)
            elif trigger_selector:
                await page.click(trigger_selector)
            
            # 응답 대기
            await page.wait_for_timeout(5000)
            
            # 리스너 제거
            page.remove_listener('response', handle_response)
            
            return captured_response
            
        except Exception as e:
            print(f"[Network] 전략 실패: {e}")
            return None
    
    async def strategy_javascript_extraction(self, page):
        """전략 3: JavaScript 프레임워크 데이터 추출"""
        try:
            # ExtJS 감지 및 추출
            extjs_data = await self.extract_extjs_data(page)
            if extjs_data:
                return extjs_data
            
            # React 감지 및 추출
            react_data = await self.extract_react_data(page)
            if react_data:
                return react_data
            
            # Vue 감지 및 추출
            vue_data = await self.extract_vue_data(page)
            if vue_data:
                return vue_data
            
            # 일반 테이블 추출
            table_data = await self.extract_table_data(page)
            if table_data:
                return table_data
            
            return None
            
        except Exception as e:
            print(f"[JavaScript] 전략 실패: {e}")
            return None
    
    async def extract_extjs_data(self, page):
        """ExtJS Grid 데이터 추출"""
        try:
            data = await page.evaluate("""
                () => {
                    // ExtJS 확인
                    if (typeof Ext === 'undefined') return null;
                    
                    // Grid 찾기
                    const grids = Ext.ComponentQuery.query('grid');
                    if (grids.length === 0) return null;
                    
                    const grid = grids[0];
                    const store = grid.getStore();
                    const columns = grid.getColumns();
                    
                    // 헤더 추출
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
                                return value !== null && value !== undefined ? String(value) : '';
                            });
                        rows.push(row);
                    });
                    
                    return {
                        type: 'extjs',
                        headers: headers,
                        rows: rows,
                        count: rows.length
                    };
                }
            """)
            
            if data and data['count'] > 0:
                # CSV 저장
                import csv
                from datetime import datetime
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"extjs_data_{timestamp}.csv"
                save_path = self.download_dir / filename
                
                with open(save_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(data['headers'])
                    writer.writerows(data['rows'])
                
                print(f"[ExtJS] 데이터 추출 성공: {data['count']}건")
                return save_path
            
            return None
            
        except:
            return None
    
    async def extract_react_data(self, page):
        """React 컴포넌트 데이터 추출"""
        try:
            data = await page.evaluate("""
                () => {
                    // React 확인
                    if (!window.React && !window.react) return null;
                    
                    // React 컴포넌트에서 데이터 추출 (예시)
                    const tables = document.querySelectorAll('table');
                    if (tables.length === 0) return null;
                    
                    // 테이블 데이터 추출
                    const table = tables[0];
                    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
                    const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr =>
                        Array.from(tr.querySelectorAll('td')).map(td => td.textContent)
                    );
                    
                    return {
                        type: 'react',
                        headers: headers,
                        rows: rows,
                        count: rows.length
                    };
                }
            """)
            
            if data and data['count'] > 0:
                # 데이터 저장 로직
                print(f"[React] 데이터 추출 성공: {data['count']}건")
                return data
            
            return None
            
        except:
            return None
    
    async def extract_vue_data(self, page):
        """Vue 컴포넌트 데이터 추출"""
        try:
            data = await page.evaluate("""
                () => {
                    // Vue 확인
                    if (!window.Vue && !window.vue) return null;
                    
                    // Vue 인스턴스 찾기
                    const app = document.querySelector('#app').__vue__;
                    if (!app) return null;
                    
                    // 데이터 추출 (구조에 따라 다름)
                    return null;
                }
            """)
            
            return data
            
        except:
            return None
    
    async def extract_table_data(self, page):
        """일반 HTML 테이블 데이터 추출"""
        try:
            data = await page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    if (tables.length === 0) return null;
                    
                    const table = tables[0];
                    const headers = Array.from(table.querySelectorAll('thead th, tr:first-child th')).map(th => th.textContent.trim());
                    const rows = Array.from(table.querySelectorAll('tbody tr, tr:not(:first-child)')).map(tr =>
                        Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim())
                    );
                    
                    return {
                        type: 'table',
                        headers: headers,
                        rows: rows,
                        count: rows.length
                    };
                }
            """)
            
            if data and data['count'] > 0:
                print(f"[Table] 데이터 추출 성공: {data['count']}건")
                return data
            
            return None
            
        except:
            return None
    
    async def strategy_filesystem_monitor(self, page, trigger_selector, trigger_action):
        """전략 4: 파일 시스템 모니터링"""
        try:
            # 모니터링할 폴더들
            user_downloads = Path.home() / "Downloads"
            
            # 초기 파일 목록
            initial_files = set()
            if user_downloads.exists():
                initial_files = set(user_downloads.glob('*'))
            
            # 다운로드 트리거
            if trigger_action:
                await trigger_action(page)
            elif trigger_selector:
                await page.click(trigger_selector)
            
            # 새 파일 감지
            await page.wait_for_timeout(5000)
            
            if user_downloads.exists():
                current_files = set(user_downloads.glob('*'))
                new_files = current_files - initial_files
                
                for file in new_files:
                    if file.is_file():
                        # 대상 폴더로 복사
                        target = self.download_dir / file.name
                        shutil.copy2(file, target)
                        print(f"[FileSystem] 새 파일 감지: {file.name}")
                        return target
            
            return None
            
        except Exception as e:
            print(f"[FileSystem] 전략 실패: {e}")
            return None
    
    async def strategy_cdp_download(self, page, trigger_selector, trigger_action):
        """전략 5: Chrome DevTools Protocol 다운로드"""
        try:
            # CDP 세션 생성
            client = await page.context.new_cdp_session(page)
            
            # 다운로드 동작 설정
            await client.send('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': str(self.download_dir)
            })
            
            # 다운로드 트리거
            if trigger_action:
                await trigger_action(page)
            elif trigger_selector:
                await page.click(trigger_selector)
            
            # 다운로드 대기
            await page.wait_for_timeout(5000)
            
            # 다운로드 폴더 확인
            files = list(self.download_dir.glob('*'))
            if files:
                latest_file = max(files, key=lambda x: x.stat().st_mtime)
                print(f"[CDP] 다운로드 감지: {latest_file.name}")
                return latest_file
            
            return None
            
        except Exception as e:
            print(f"[CDP] 전략 실패: {e}")
            return None


# 사용 예시
async def example_usage():
    """범용 다운로더 사용 예시"""
    
    downloader = UniversalDownloadEngine("downloads")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        # 웹사이트 접속
        await page.goto("https://example.com")
        
        # 다운로드 실행 (여러 전략 자동 시도)
        results = await downloader.download(
            page,
            trigger_selector='button#download',  # 또는
            trigger_action=lambda p: p.keyboard.press('Control+S')  # 또는 커스텀 액션
        )
        
        # 결과 확인
        for strategy, result in results.items():
            if result:
                print(f"성공한 전략: {strategy}")
                print(f"결과: {result}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
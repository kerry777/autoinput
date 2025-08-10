#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 범용 다운로드 솔루션 - 모든 다운로드에 대응
"""

import asyncio
import json
import time
import os
import shutil
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


class UniversalDownloader:
    """범용 다운로드 처리 클래스"""
    
    def __init__(self, download_dir):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.download_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
    async def setup_cdp_download(self, page):
        """CDP를 통한 다운로드 인터셉트 설정"""
        client = await page.context.new_cdp_session(page)
        
        # 다운로드 동작 설정
        await client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': str(self.download_dir)
        })
        
        # 네트워크 이벤트 활성화
        await client.send('Network.enable')
        
        # Fetch 도메인 활성화 (요청 인터셉트)
        await client.send('Fetch.enable', {
            'patterns': [
                {'urlPattern': '*', 'requestStage': 'Response'}
            ]
        })
        
        return client
    
    async def intercept_download_request(self, page):
        """네트워크 요청 인터셉트 및 수정"""
        
        # 요청 인터셉터 설정
        await page.route('**/*', lambda route: self.handle_route(route))
        
    async def handle_route(self, route):
        """라우트 핸들러"""
        request = route.request
        
        # 다운로드 관련 요청 감지
        if 'download' in request.url.lower() or 'excel' in request.url.lower():
            print(f"[인터셉트] 다운로드 요청: {request.url}")
            
            # 헤더 수정
            headers = {
                **request.headers,
                'X-Requested-With': 'XMLHttpRequest',
            }
            
            # 요청 계속 진행
            await route.continue_(headers=headers)
        else:
            await route.continue_()
    
    async def monitor_downloads_folder(self):
        """다운로드 폴더 모니터링"""
        # Windows Downloads 폴더
        user_downloads = Path.home() / "Downloads"
        chrome_temp = Path(os.environ.get('TEMP', '')) / "chrome_downloads"
        
        monitored_folders = [
            self.download_dir,
            user_downloads,
            chrome_temp,
            self.temp_dir
        ]
        
        # 초기 파일 목록
        initial_files = {}
        for folder in monitored_folders:
            if folder.exists():
                initial_files[folder] = set(folder.glob('*'))
        
        return initial_files, monitored_folders
    
    async def capture_actual_download(self, page):
        """실제 브라우저 다운로드 캡처"""
        
        # 다운로드 이벤트 핸들러
        download_files = []
        
        async def handle_download(download):
            print(f"\n[다운로드 캡처] 파일 다운로드 감지!")
            print(f"  URL: {download.url}")
            print(f"  제안 파일명: {download.suggested_filename}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = download.suggested_filename or f"download_{timestamp}"
            
            # 파일 저장
            save_path = self.download_dir / filename
            
            try:
                await download.save_as(str(save_path))
                download_files.append(save_path)
                print(f"  ✓ 저장 완료: {save_path}")
                return save_path
            except Exception as e:
                print(f"  ! 저장 실패: {e}")
                
                # 실패 시 대체 경로 시도
                try:
                    # 임시 경로에 저장
                    temp_path = self.temp_dir / filename
                    await download.save_as(str(temp_path))
                    
                    # 최종 경로로 이동
                    final_path = self.download_dir / filename
                    shutil.move(str(temp_path), str(final_path))
                    download_files.append(final_path)
                    print(f"  ✓ 대체 저장: {final_path}")
                    return final_path
                except:
                    # 경로 정보만 저장
                    await download.failure()
                    return None
        
        page.on('download', handle_download)
        return download_files


async def universal_download_solution():
    """범용 다운로드 솔루션 실행"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    downloads_dir = data_dir / "downloads"
    
    # 다운로더 인스턴스 생성
    downloader = UniversalDownloader(downloads_dir)
    
    # 설정 로드
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        # 브라우저 시작 (다운로드 설정 포함)
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--enable-logging',
                '--v=1',
                '--dump-dom',
                '--enable-network-service-in-process'
            ],
            downloads_path=str(downloads_dir)
        )
        
        # 컨텍스트 생성
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True,
            http_credentials=None,
            ignore_https_errors=True
        )
        
        # 기본 타임아웃 설정
        context.set_default_timeout(60000)
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("쿠키 로드 완료")
        
        # 페이지 생성
        page = await context.new_page()
        
        # CDP 설정
        cdp_client = await downloader.setup_cdp_download(page)
        
        # 다운로드 캡처 설정
        download_files = await downloader.capture_actual_download(page)
        
        # 요청 인터셉터 설정
        await downloader.intercept_download_request(page)
        
        try:
            print("\n" + "="*60)
            print("범용 다운로드 솔루션")
            print("="*60)
            
            # 폴더 모니터링 시작
            initial_files, monitored_folders = await downloader.monitor_downloads_folder()
            
            # 매출현황조회 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 조건 설정
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
            
            # 조회 실행
            print("\n[3] 데이터 조회...")
            await page.keyboard.press('F2')
            await page.wait_for_timeout(10000)
            
            # 방법 1: ExtJS downloadExcelXml 직접 호출
            print("\n[4] 방법 1: ExtJS 다운로드 함수 호출...")
            
            # CDP로 응답 캡처 준비
            response_data = {}
            
            async def handle_response(params):
                """CDP 응답 핸들러"""
                request_id = params.get('requestId')
                response = params.get('response', {})
                
                if 'download' in response.get('url', '').lower():
                    print(f"[CDP] 다운로드 응답 감지: {response.get('url')}")
                    
                    # 응답 본문 가져오기
                    try:
                        body = await cdp_client.send('Network.getResponseBody', {
                            'requestId': request_id
                        })
                        
                        # 파일로 저장
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"cdp_download_{timestamp}.csv"
                        save_path = downloads_dir / filename
                        
                        if body.get('base64Encoded'):
                            import base64
                            content = base64.b64decode(body['body'])
                        else:
                            content = body['body'].encode('utf-8')
                        
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        
                        print(f"  CDP 저장: {save_path}")
                        response_data['cdp_file'] = save_path
                        
                    except Exception as e:
                        print(f"  CDP 저장 실패: {e}")
            
            # CDP 응답 리스너 등록
            cdp_client.on('Network.responseReceived', handle_response)
            
            # downloadExcelXml 호출
            download_result = await page.evaluate("""
                () => {
                    try {
                        // 전역 변수 설정
                        window.SAVE_AUTH = "true";
                        
                        // 그리드 찾기
                        const grids = Ext.ComponentQuery.query('grid');
                        if(grids.length === 0) return {error: 'No grid'};
                        
                        const grid = grids[0];
                        
                        // downloadExcelXml 호출
                        if(grid.downloadExcelXml) {
                            grid.downloadExcelXml(false, '매출현황');
                            return {success: true, method: 'downloadExcelXml'};
                        }
                        
                        // Excel 버튼 클릭
                        const btn = Ext.getCmp('uniBaseButton-1196');
                        if(btn) {
                            btn.handler.call(btn.scope || btn);
                            return {success: true, method: 'button'};
                        }
                        
                        return {error: 'No method'};
                    } catch(e) {
                        return {error: e.toString()};
                    }
                }
            """)
            
            print(f"  결과: {download_result}")
            
            # 다운로드 대기
            await page.wait_for_timeout(5000)
            
            # 방법 2: 네트워크 응답 직접 캡처
            print("\n[5] 방법 2: 네트워크 응답 캡처...")
            
            # 페이지 리로드 후 재시도
            await page.reload()
            await page.wait_for_timeout(3000)
            
            # 네트워크 모니터링과 함께 다운로드 트리거
            async with page.expect_response(lambda r: 'download' in r.url) as response_info:
                # 다운로드 트리거
                await page.evaluate("""
                    () => {
                        const btn = document.querySelector('[data-qtip*="Excel"]') ||
                                   document.querySelector('[tooltip*="Excel"]') ||
                                   Ext.getCmp('uniBaseButton-1196');
                        if(btn) {
                            if(btn.click) btn.click();
                            else if(btn.handler) btn.handler.call(btn.scope || btn);
                        }
                    }
                """)
                
                try:
                    response = await response_info.value
                    print(f"  응답 캡처: {response.url}")
                    print(f"  상태: {response.status}")
                    
                    if response.status == 200:
                        # 응답 저장
                        content = await response.body()
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"network_download_{timestamp}.csv"
                        save_path = downloads_dir / filename
                        
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        
                        print(f"  네트워크 저장: {save_path}")
                except:
                    print("  네트워크 캡처 실패")
            
            # 방법 3: 파일 시스템 모니터링
            print("\n[6] 방법 3: 파일 시스템 모니터링...")
            
            # 새 파일 확인
            new_files = []
            for folder in monitored_folders:
                if folder.exists():
                    current_files = set(folder.glob('*'))
                    diff = current_files - initial_files.get(folder, set())
                    
                    for file in diff:
                        if file.is_file():
                            new_files.append(file)
                            print(f"  새 파일 감지: {file}")
                            
                            # downloads 폴더로 복사
                            if folder != downloads_dir:
                                target = downloads_dir / file.name
                                shutil.copy2(file, target)
                                print(f"  복사됨: {target}")
            
            # 최종 결과
            print("\n" + "="*60)
            print("다운로드 결과")
            print("="*60)
            
            all_downloads = list(downloads_dir.glob("*.*"))
            all_downloads.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            print(f"총 {len(all_downloads)}개 파일")
            for file in all_downloads[:10]:
                size = file.stat().st_size / 1024
                print(f"  - {file.name} ({size:.1f} KB)")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"universal_{timestamp}.png"
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
    asyncio.run(universal_download_solution())
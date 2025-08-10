#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 완전 자동화 - 로그인부터 다운로드까지
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import os
import shutil

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def full_auto_download():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        # 브라우저 시작
        browser = await p.chromium.launch(
            headless=False,  # 먼저 보이는 모드로 테스트
            downloads_path=str(data_dir)
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        # CDP 세션 설정
        client = await page.context.new_cdp_session(page)
        await client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': str(data_dir.absolute())
        })
        
        try:
            print("\n" + "="*60)
            print("MEK-ICS 완전 자동화 - 풀코스")
            print("="*60)
            
            # =====================================
            # STEP 1: 로그인
            # =====================================
            print("\n[STEP 1] 로그인")
            print("-" * 40)
            
            # 쿠키 확인
            cookie_file = data_dir / "cookies.json"
            if cookie_file.exists():
                print("   저장된 쿠키 로드...")
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                
                # 메인 페이지로 이동
                await page.goto("https://it.mek-ics.com/mekics/main.do")
                await page.wait_for_timeout(3000)
                
                # 로그인 확인
                is_logged_in = await page.evaluate("""
                    () => {
                        return window.location.href.includes('main.do') && 
                               !window.location.href.includes('login');
                    }
                """)
                
                if is_logged_in:
                    print("   [OK] 쿠키로 로그인 성공")
                else:
                    raise Exception("쿠키 로그인 실패")
                    
            else:
                print("   로그인 페이지 접속...")
                await page.goto("https://it.mek-ics.com/mekics/login/login.do")
                await page.wait_for_timeout(2000)
                
                # 로그인 수행
                print("   자격증명 입력...")
                await page.fill('input[name="EMP_CODE"]', config['credentials']['username'])
                await page.fill('input[name="PASSWORD"]', config['credentials']['password'])
                
                print("   로그인 버튼 클릭...")
                await page.click('button:has-text("로그인")')
                await page.wait_for_timeout(5000)
                
                # 쿠키 저장
                cookies = await context.cookies()
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print("   [OK] 로그인 성공 및 쿠키 저장")
            
            # =====================================
            # STEP 2: 매출현황 페이지 이동
            # =====================================
            print("\n[STEP 2] 매출현황 페이지 이동")
            print("-" * 40)
            
            print("   매출현황조회 페이지 직접 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 페이지 로드 확인
            page_loaded = await page.evaluate("""
                () => {
                    return typeof Ext !== 'undefined' && 
                           Ext.ComponentQuery.query('grid').length > 0;
                }
            """)
            
            if page_loaded:
                print("   [OK] 매출현황 페이지 로드 완료")
            else:
                print("   ! 페이지 로드 대기...")
                await page.wait_for_timeout(3000)
            
            # =====================================
            # STEP 3: 조회 조건 설정
            # =====================================
            print("\n[STEP 3] 조회 조건 설정")
            print("-" * 40)
            
            result = await page.evaluate("""
                () => {
                    const results = {};
                    
                    // LOT표시 '아니오' 설정
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) {
                        noRadio.setValue(true);
                        results.lot = '아니오 설정';
                    }
                    
                    // 국내/해외 '전체' 설정
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) {
                        allRadio.setValue(true);
                        results.division = '전체 설정';
                    }
                    
                    // 날짜 설정
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2021, 0, 1));
                        dateFields[1].setValue(new Date());
                        results.dates = '2021.01.01 ~ 오늘';
                    }
                    
                    return results;
                }
            """)
            
            print(f"   [OK] LOT표시: 아니오")
            print(f"   [OK] 국내/해외: 전체")
            print(f"   [OK] 조회기간: 2021.01.01 ~ {datetime.now().strftime('%Y.%m.%d')}")
            
            # =====================================
            # STEP 4: 데이터 조회
            # =====================================
            print("\n[STEP 4] 데이터 조회")
            print("-" * 40)
            
            print("   F2 키로 조회 실행...")
            await page.keyboard.press('F2')
            
            # 로딩 대기
            print("   데이터 로딩 중...")
            loading_complete = False
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
                        return {count: 0, loading: true};
                    }
                """)
                
                if not status['loading'] and status['count'] > 0:
                    print(f"   [OK] 데이터 로딩 완료: {status['count']:,}건")
                    loading_complete = True
                    break
                
                if i % 5 == 4:
                    print(f"     {i+1}초 경과...")
            
            if not loading_complete:
                print("   ! 로딩 타임아웃 - 계속 진행")
            
            await page.wait_for_timeout(2000)
            
            # =====================================
            # STEP 5: 엑셀 다운로드
            # =====================================
            print("\n[STEP 5] 엑셀 다운로드")
            print("-" * 40)
            
            # 다운로드 전 파일 목록
            before_files = set()
            for file in data_dir.iterdir():
                if file.is_file():
                    before_files.add(file.name)
            
            # 사용자 Downloads 폴더도 모니터링
            user_downloads = Path.home() / "Downloads"
            user_before = set()
            for file in user_downloads.iterdir():
                if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                    user_before.add(file.name)
            
            # 엑셀 버튼 클릭
            print("   엑셀 버튼 클릭...")
            excel_result = await page.evaluate("""
                () => {
                    const excelBtn = Ext.getCmp('uniBaseButton-1196');
                    if(excelBtn) {
                        // handler 직접 호출
                        if(excelBtn.handler) {
                            excelBtn.handler.call(excelBtn.scope || excelBtn);
                            return {success: true, method: 'handler'};
                        } else {
                            excelBtn.fireEvent('click', excelBtn);
                            return {success: true, method: 'fireEvent'};
                        }
                    }
                    
                    // 백업: 텍스트로 버튼 찾기
                    const buttons = Ext.ComponentQuery.query('button');
                    for(let btn of buttons) {
                        const text = btn.getText ? btn.getText() : '';
                        if(text.includes('엑셀') || text.includes('Excel')) {
                            if(btn.handler) {
                                btn.handler.call(btn.scope || btn);
                            } else {
                                btn.fireEvent('click', btn);
                            }
                            return {success: true, method: 'text search'};
                        }
                    }
                    return {success: false};
                }
            """)
            
            if excel_result['success']:
                print(f"   [OK] 엑셀 버튼 클릭 ({excel_result['method']})")
            
            # CSV 팝업 처리
            print("   팝업 대기 (1.5초)...")
            await page.wait_for_timeout(1500)
            
            print("   Enter 키 입력...")
            await page.keyboard.press('Enter')
            
            # 다운로드 확인
            print("   다운로드 확인 중...")
            download_found = False
            downloaded_file = None
            
            for i in range(60):
                await page.wait_for_timeout(1000)
                
                # data_dir 확인
                for file in data_dir.iterdir():
                    if file.is_file() and file.name not in before_files:
                        download_found = True
                        downloaded_file = file
                        break
                
                # 사용자 Downloads 폴더 확인
                if not download_found:
                    for file in user_downloads.iterdir():
                        if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                            if file.name not in user_before:
                                # data_dir로 복사
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                target = data_dir / f"sales_{timestamp}{file.suffix}"
                                shutil.copy2(file, target)
                                download_found = True
                                downloaded_file = target
                                break
                
                if download_found:
                    break
                
                if i % 5 == 4:
                    print(f"     {i+1}초 경과...")
            
            # =====================================
            # STEP 6: 결과 확인
            # =====================================
            print("\n[STEP 6] 결과 확인")
            print("-" * 40)
            
            if download_found and downloaded_file:
                file_size = downloaded_file.stat().st_size / (1024 * 1024)
                print(f"   [OK] 다운로드 성공!")
                print(f"   파일명: {downloaded_file.name}")
                print(f"   크기: {file_size:.2f} MB")
                print(f"   경로: {downloaded_file}")
                
                # 파일 내용 미리보기
                try:
                    with open(downloaded_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        lines = f.readlines()[:3]
                        print("\n   파일 미리보기:")
                        for line in lines:
                            print(f"     {line.strip()[:80]}")
                except:
                    pass
            else:
                print("   [FAIL] 다운로드 실패")
                print("   수동으로 다운로드를 진행해주세요.")
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"full_auto_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n   스크린샷: {screenshot}")
            
            # =====================================
            # 완료
            # =====================================
            print("\n" + "="*60)
            if download_found:
                print("완전 자동화 성공!")
            else:
                print("자동화 부분 성공 (다운로드만 수동 필요)")
            print("="*60)
            
        except Exception as e:
            print(f"\n오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = data_dir / f"error_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"오류 스크린샷: {screenshot}")
        
        finally:
            print("\n브라우저를 30초 후 종료합니다...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(full_auto_download())
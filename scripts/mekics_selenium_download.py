#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS Selenium 다운로드 - CDP를 활용한 강제 다운로드
"""

import time
import json
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import shutil


def setup_driver_with_download():
    """다운로드 설정이 포함된 드라이버 설정"""
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    downloads_dir = data_dir / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    # Chrome 옵션 설정
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": str(downloads_dir.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True
    })
    
    # CDP 명령 활성화
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    
    # CDP로 다운로드 동작 설정
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": str(downloads_dir.absolute())
    })
    
    return driver, downloads_dir


def load_cookies(driver):
    """저장된 쿠키 로드"""
    cookie_file = Path("sites/mekics/data/cookies.json")
    if cookie_file.exists():
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        # 먼저 사이트 접속
        driver.get("https://it.mek-ics.com/mekics/")
        time.sleep(2)
        
        # 쿠키 추가
        for cookie in cookies:
            # Selenium용 쿠키 형식으로 변환
            selenium_cookie = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie.get('domain', '.mek-ics.com'),
                'path': cookie.get('path', '/'),
                'secure': cookie.get('secure', False)
            }
            if 'expires' in cookie:
                selenium_cookie['expiry'] = int(cookie['expires'])
            
            try:
                driver.add_cookie(selenium_cookie)
            except:
                pass
        
        print("쿠키 로드 완료")
        return True
    return False


def main():
    driver = None
    try:
        print("\nMEK-ICS Selenium 다운로드 솔루션")
        print("="*60)
        
        # 드라이버 설정
        driver, downloads_dir = setup_driver_with_download()
        driver.maximize_window()
        
        # 쿠키 로드
        if not load_cookies(driver):
            print("쿠키 파일이 없습니다. 수동 로그인이 필요합니다.")
            return
        
        # 매출현황조회 페이지 접속
        print("\n[1] 매출현황조회 페이지 접속...")
        driver.get("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
        time.sleep(5)
        
        # ExtJS 로드 대기
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return typeof Ext !== 'undefined'")
        )
        
        # 조회 조건 설정
        print("\n[2] 조회 조건 설정...")
        driver.execute_script("""
            // LOT표시 '아니오'
            const noRadio = Ext.getCmp('radiofield-1078');
            if(noRadio) noRadio.setValue(true);
            
            // 국내/해외 '전체'
            const allRadio = Ext.getCmp('radiofield-1081');
            if(allRadio) allRadio.setValue(true);
            
            // 날짜 설정 (대용량 테스트)
            const dateFields = Ext.ComponentQuery.query('datefield');
            if(dateFields.length >= 2) {
                dateFields[0].setValue(new Date(2021, 0, 1));
                dateFields[1].setValue(new Date());
            }
        """)
        print("  설정 완료: 2021.01.01 ~ 오늘")
        
        # 조회 실행
        print("\n[3] 데이터 조회 실행 (F2)...")
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.F2)
        
        # CSV 팝업 처리
        print("\n[4] CSV 팝업 대기...")
        csv_popup_found = False
        
        for i in range(15):
            time.sleep(1)
            
            # ExtJS MessageBox 확인
            popup_visible = driver.execute_script("""
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
            """)
            
            if popup_visible:
                csv_popup_found = True
                print("  CSV 팝업 감지!")
                break
            
            if i % 3 == 2:
                print(f"  대기 중... {i+1}초")
        
        if csv_popup_found:
            print("\n[5] CSV 다운로드 시작...")
            
            # 다운로드 전 파일 목록
            before_files = set(os.listdir(downloads_dir))
            
            # '예' 버튼 클릭
            yes_clicked = driver.execute_script("""
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
            """)
            
            if yes_clicked:
                print("  '예' 버튼 클릭 완료")
                
                # 다운로드 대기
                print("\n[6] 다운로드 완료 대기...")
                download_complete = False
                downloaded_file = None
                
                for i in range(60):
                    time.sleep(1)
                    
                    # 새 파일 확인
                    current_files = set(os.listdir(downloads_dir))
                    new_files = current_files - before_files
                    
                    for file in new_files:
                        file_path = downloads_dir / file
                        # .crdownload 확인 (다운로드 중)
                        if not file.endswith('.crdownload'):
                            # 파일 크기 안정화 확인
                            size1 = file_path.stat().st_size
                            time.sleep(0.5)
                            size2 = file_path.stat().st_size
                            
                            if size1 == size2 and size1 > 0:
                                download_complete = True
                                downloaded_file = file_path
                                break
                    
                    if download_complete:
                        break
                    
                    if i % 5 == 4:
                        print(f"  대기 중... {i+1}초")
                
                if download_complete and downloaded_file:
                    file_size = downloaded_file.stat().st_size / (1024 * 1024)
                    
                    # 라인 수 확인
                    with open(downloaded_file, 'r', encoding='utf-8-sig') as f:
                        line_count = sum(1 for line in f) - 1
                    
                    print("\n" + "="*60)
                    print("[성공] 다운로드 완료!")
                    print(f"파일: {downloaded_file.name}")
                    print(f"크기: {file_size:.2f} MB")
                    print(f"데이터: {line_count:,}건")
                    print(f"경로: {downloaded_file}")
                    print("="*60)
                else:
                    print("\n다운로드 실패 - 대안 방법 시도")
                    
        else:
            print("\nCSV 팝업이 나타나지 않음 - 소량 데이터")
            
            # Store 데이터 추출
            print("\n[7] Store 데이터 직접 추출...")
            data_count = driver.execute_script("""
                const grids = Ext.ComponentQuery.query('grid');
                if(grids.length > 0) {
                    return grids[0].getStore().getCount();
                }
                return 0;
            """)
            
            print(f"  Store 데이터: {data_count}건")
            
            if data_count > 0:
                # 엑셀 버튼 강제 클릭
                print("\n[8] 엑셀 버튼 강제 실행...")
                
                # 다운로드 전 파일 목록
                before_files = set(os.listdir(downloads_dir))
                
                # downloadExcelXml 직접 호출
                driver.execute_script("""
                    window.SAVE_AUTH = "true";
                    const grids = Ext.ComponentQuery.query('grid');
                    if(grids.length > 0 && grids[0].downloadExcelXml) {
                        grids[0].downloadExcelXml(false, '매출현황');
                    }
                """)
                
                # 다운로드 확인
                time.sleep(5)
                current_files = set(os.listdir(downloads_dir))
                new_files = current_files - before_files
                
                if new_files:
                    print(f"  다운로드 파일: {new_files}")
        
        # 스크린샷
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot = Path("sites/mekics/data") / f"selenium_{timestamp}.png"
        driver.save_screenshot(str(screenshot))
        print(f"\n스크린샷: {screenshot}")
        
    except Exception as e:
        print(f"\n오류: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("\n30초 후 종료...")
            time.sleep(30)
            driver.quit()


if __name__ == "__main__":
    main()
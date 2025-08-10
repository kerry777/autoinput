#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 검증된 솔루션 - SuperClaude 분석 기반 개선
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
import os
import shutil
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


class MEKICSAutomation:
    """MEK-ICS 자동화 클래스"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = self.site_dir / "config" / "settings.json"
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.page = None
        self.context = None
        self.browser = None
        
    async def setup_browser(self, headless=False):
        """브라우저 설정"""
        logger.info("브라우저 설정 시작")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            downloads_path=str(self.data_dir)
        )
        
        self.context = await self.browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        # 쿠키 로드
        cookie_file = self.data_dir / "cookies.json"
        if cookie_file.exists():
            logger.info("저장된 쿠키 로드")
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
        
        self.page = await self.context.new_page()
        
        # CDP 세션 설정
        client = await self.page.context.new_cdp_session(self.page)
        await client.send('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': str(self.data_dir.absolute())
        })
        
    async def wait_for_extjs(self, timeout=10000):
        """ExtJS 로드 대기"""
        try:
            await self.page.wait_for_function(
                """() => {
                    return typeof Ext !== 'undefined' && 
                           Ext.isReady && 
                           !Ext.Ajax.isLoading();
                }""",
                timeout=timeout
            )
            logger.info("ExtJS 준비 완료")
            return True
        except PlaywrightTimeout:
            logger.warning("ExtJS 로드 타임아웃")
            return False
    
    async def login(self):
        """로그인 처리"""
        logger.info("로그인 프로세스 시작")
        
        # 메인 페이지로 이동하여 로그인 확인
        await self.page.goto("https://it.mek-ics.com/mekics/main.do")
        await self.page.wait_for_timeout(3000)
        
        # 로그인 상태 확인
        is_logged_in = await self.page.evaluate("""
            () => {
                return window.location.href.includes('main.do') && 
                       !window.location.href.includes('login');
            }
        """)
        
        if is_logged_in:
            logger.info("이미 로그인됨 (쿠키)")
            return True
        
        # 로그인 수행
        logger.info("로그인 페이지로 이동")
        await self.page.goto("https://it.mek-ics.com/mekics/login/login.do")
        await self.page.wait_for_timeout(2000)
        
        # 자격증명 입력
        await self.page.fill('input[name="EMP_CODE"]', self.config['credentials']['username'])
        await self.page.fill('input[name="PASSWORD"]', self.config['credentials']['password'])
        
        # 로그인 버튼 클릭
        await self.page.click('button:has-text("로그인")')
        await self.page.wait_for_timeout(5000)
        
        # 쿠키 저장
        cookies = await self.context.cookies()
        with open(self.data_dir / "cookies.json", 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        logger.info("로그인 성공 및 쿠키 저장")
        return True
    
    async def navigate_to_sales(self):
        """매출현황 페이지로 이동"""
        logger.info("매출현황 페이지로 이동")
        
        await self.page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
        await self.page.wait_for_timeout(5000)
        
        # ExtJS 로드 대기
        await self.wait_for_extjs()
        
        # 페이지 로드 확인
        page_loaded = await self.page.evaluate("""
            () => {
                return Ext.ComponentQuery.query('grid').length > 0;
            }
        """)
        
        if page_loaded:
            logger.info("매출현황 페이지 로드 완료")
        else:
            logger.warning("페이지 로드 확인 실패")
        
        return page_loaded
    
    async def set_search_conditions(self):
        """조회 조건 설정"""
        logger.info("조회 조건 설정")
        
        result = await self.page.evaluate("""
            () => {
                const results = {};
                
                // LOT표시 '아니오' - ID가 동적일 수 있으므로 여러 방법 시도
                let noRadio = Ext.getCmp('radiofield-1078');
                if(!noRadio) {
                    // 라벨 텍스트로 찾기
                    const radios = Ext.ComponentQuery.query('radiofield');
                    for(let r of radios) {
                        if(r.boxLabel === '아니오') {
                            noRadio = r;
                            break;
                        }
                    }
                }
                if(noRadio) {
                    noRadio.setValue(true);
                    results.lot = 'OK';
                }
                
                // 국내/해외 '전체'
                let allRadio = Ext.getCmp('radiofield-1081');
                if(!allRadio) {
                    const radios = Ext.ComponentQuery.query('radiofield');
                    for(let r of radios) {
                        if(r.boxLabel === '전체') {
                            allRadio = r;
                            break;
                        }
                    }
                }
                if(allRadio) {
                    allRadio.setValue(true);
                    results.division = 'OK';
                }
                
                // 날짜 설정
                const dateFields = Ext.ComponentQuery.query('datefield');
                if(dateFields.length >= 2) {
                    dateFields[0].setValue(new Date(2021, 0, 1));
                    dateFields[1].setValue(new Date());
                    results.dates = 'OK';
                }
                
                return results;
            }
        """)
        
        logger.info(f"조건 설정 결과: {result}")
        return result
    
    async def execute_query(self):
        """조회 실행"""
        logger.info("조회 실행 (F2)")
        
        await self.page.keyboard.press('F2')
        
        # 로딩 대기
        logger.info("데이터 로딩 대기...")
        for i in range(60):
            await self.page.wait_for_timeout(1000)
            
            status = await self.page.evaluate("""
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
                logger.info(f"로딩 완료: {status['count']:,}건")
                return status['count']
            
            if i % 5 == 4:
                logger.info(f"로딩 중... {i+1}초")
        
        logger.warning("로딩 타임아웃")
        return 0
    
    async def click_excel_button(self):
        """엑셀 버튼 클릭 - 여러 방법 시도"""
        logger.info("엑셀 버튼 클릭 시도")
        
        methods = [
            {
                "name": "텍스트 기반 검색",
                "code": """
                    () => {
                        // 툴팁으로 찾기
                        const buttons = Ext.ComponentQuery.query('button');
                        for(let btn of buttons) {
                            const tooltip = btn.tooltip || '';
                            if(tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                                if(btn.handler) {
                                    btn.handler.call(btn.scope || btn);
                                } else {
                                    btn.fireEvent('click', btn);
                                }
                                return {success: true, id: btn.id};
                            }
                        }
                        return {success: false};
                    }
                """
            },
            {
                "name": "아이콘 클래스로 찾기",
                "code": """
                    () => {
                        const buttons = Ext.ComponentQuery.query('button');
                        for(let btn of buttons) {
                            const iconCls = btn.iconCls || '';
                            if(iconCls.includes('excel') || iconCls.includes('download')) {
                                if(btn.isVisible && btn.isVisible() && !btn.disabled) {
                                    if(btn.handler) {
                                        btn.handler.call(btn.scope || btn);
                                    } else {
                                        btn.fireEvent('click', btn);
                                    }
                                    return {success: true, id: btn.id};
                                }
                            }
                        }
                        return {success: false};
                    }
                """
            },
            {
                "name": "ID 기반 (fallback)",
                "code": """
                    () => {
                        const btn = Ext.getCmp('uniBaseButton-1196');
                        if(btn && btn.isVisible && btn.isVisible()) {
                            if(btn.handler) {
                                btn.handler.call(btn.scope || btn);
                            } else {
                                btn.fireEvent('click', btn);
                            }
                            return {success: true, id: btn.id};
                        }
                        return {success: false};
                    }
                """
            }
        ]
        
        for method in methods:
            logger.info(f"시도: {method['name']}")
            result = await self.page.evaluate(method['code'])
            
            if result['success']:
                logger.info(f"성공! 버튼 ID: {result.get('id', 'unknown')}")
                return True
            
        # Playwright locator 시도
        try:
            logger.info("Playwright locator로 시도")
            excel_icon = self.page.locator('.icon-excel').first
            if await excel_icon.count() > 0:
                await excel_icon.click()
                logger.info("아이콘 클릭 성공")
                return True
        except Exception as e:
            logger.warning(f"Locator 실패: {e}")
        
        logger.error("모든 방법 실패")
        return False
    
    async def handle_popup(self):
        """팝업 처리"""
        logger.info("팝업 대기 및 처리")
        
        # 팝업 대기
        await self.page.wait_for_timeout(2000)
        
        # 여러 번 시도
        for attempt in range(3):
            popup_result = await self.page.evaluate("""
                () => {
                    // MessageBox 확인
                    const msgBoxes = Ext.ComponentQuery.query('messagebox');
                    for(let box of msgBoxes) {
                        if(box.isVisible && box.isVisible()) {
                            // 버튼 정보 수집
                            const buttons = box.query('button').map(b => ({
                                text: b.getText ? b.getText() : '',
                                itemId: b.itemId || ''
                            }));
                            
                            // '예' 버튼 클릭
                            for(let btn of box.query('button')) {
                                if(btn.itemId === 'yes' || btn.getText() === '예') {
                                    if(btn.handler) {
                                        btn.handler.call(btn.scope || btn);
                                    } else {
                                        btn.fireEvent('click', btn);
                                    }
                                    return {found: true, clicked: true, buttons: buttons};
                                }
                            }
                            
                            return {found: true, clicked: false, buttons: buttons};
                        }
                    }
                    
                    // Window 확인
                    const windows = Ext.ComponentQuery.query('window');
                    for(let win of windows) {
                        if(win.isVisible && win.isVisible() && win.modal) {
                            return {found: true, type: 'window'};
                        }
                    }
                    
                    return {found: false};
                }
            """)
            
            if popup_result['found']:
                logger.info(f"팝업 발견! 버튼: {popup_result.get('buttons', [])}")
                
                if not popup_result.get('clicked'):
                    logger.info("Enter 키 입력")
                    await self.page.keyboard.press('Enter')
                else:
                    logger.info("'예' 버튼 클릭됨")
                
                return True
            
            if attempt < 2:
                logger.info(f"팝업 미발견, 재시도 {attempt + 1}/3")
                await self.page.wait_for_timeout(1000)
        
        logger.warning("팝업이 나타나지 않음")
        return False
    
    async def monitor_download(self, timeout=60):
        """다운로드 모니터링"""
        logger.info("다운로드 모니터링 시작")
        
        # 다운로드 전 파일 목록
        before_files = set()
        for file in self.data_dir.iterdir():
            if file.is_file():
                before_files.add(file.name)
        
        # 사용자 Downloads 폴더도 모니터링
        user_downloads = Path.home() / "Downloads"
        user_before = set()
        for file in user_downloads.iterdir():
            if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                user_before.add(file.name)
        
        # 모니터링
        for i in range(timeout):
            await self.page.wait_for_timeout(1000)
            
            # data_dir 확인
            for file in self.data_dir.iterdir():
                if file.is_file() and file.name not in before_files:
                    logger.info(f"다운로드 완료: {file.name}")
                    return file
            
            # 사용자 Downloads 확인
            for file in user_downloads.iterdir():
                if file.is_file() and file.suffix in ['.csv', '.xlsx', '.xls']:
                    if file.name not in user_before:
                        # data_dir로 복사
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        target = self.data_dir / f"sales_{timestamp}{file.suffix}"
                        shutil.copy2(file, target)
                        logger.info(f"다운로드 완료 (복사): {target.name}")
                        return target
            
            if i % 5 == 4:
                logger.info(f"대기 중... {i+1}초")
        
        logger.warning("다운로드 타임아웃")
        return None
    
    async def run(self):
        """전체 프로세스 실행"""
        try:
            print("\n" + "="*60)
            print("MEK-ICS 검증된 자동화 솔루션")
            print("="*60)
            
            # 1. 브라우저 설정
            await self.setup_browser(headless=False)
            
            # 2. 로그인
            if not await self.login():
                raise Exception("로그인 실패")
            
            # 3. 매출현황 페이지 이동
            if not await self.navigate_to_sales():
                raise Exception("페이지 이동 실패")
            
            # 4. 조회 조건 설정
            conditions = await self.set_search_conditions()
            if not all(v == 'OK' for v in conditions.values()):
                logger.warning(f"일부 조건 설정 실패: {conditions}")
            
            # 5. 조회 실행
            count = await self.execute_query()
            if count == 0:
                logger.warning("데이터 없음")
            
            # 6. 엑셀 버튼 클릭
            if not await self.click_excel_button():
                raise Exception("엑셀 버튼 클릭 실패")
            
            # 7. 팝업 처리
            popup_found = await self.handle_popup()
            if not popup_found:
                logger.info("팝업 없음 (소량 데이터)")
            
            # 8. 다운로드 모니터링
            downloaded_file = await self.monitor_download()
            
            if downloaded_file:
                file_size = downloaded_file.stat().st_size / (1024 * 1024)
                print("\n" + "="*60)
                print("자동화 성공!")
                print(f"파일: {downloaded_file.name}")
                print(f"크기: {file_size:.2f} MB")
                print(f"경로: {downloaded_file}")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("다운로드 실패")
                print("수동 작업이 필요합니다")
                print("="*60)
            
            # 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = self.data_dir / f"verified_{timestamp}.png"
            await self.page.screenshot(path=str(screenshot))
            logger.info(f"스크린샷 저장: {screenshot}")
            
        except Exception as e:
            logger.error(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot = self.data_dir / f"error_{timestamp}.png"
            await self.page.screenshot(path=str(screenshot))
        
        finally:
            logger.info("30초 후 종료...")
            await self.page.wait_for_timeout(30000)
            await self.browser.close()
            await self.playwright.stop()


async def main():
    automation = MEKICSAutomation()
    await automation.run()


if __name__ == "__main__":
    asyncio.run(main())
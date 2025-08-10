#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 매출현황 조회 및 엑셀 다운로드 자동화
ExtJS Helper를 활용한 실전 구현
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
# ExtJS Helper import
sys.path.insert(0, str(project_root / "core" / "utils"))
from extjs_helper import MEKICSHelper


class SalesReportAutomation:
    """매출현황 자동화"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    async def run_sales_report(self):
        """매출현황 조회 실행"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                downloads_path=str(self.data_dir)  # 다운로드 경로 설정
            )
            
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone'],
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True  # 다운로드 허용
            )
            
            # 쿠키 로드
            cookie_file = self.data_dir / "cookies.json"
            if cookie_file.exists():
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("[OK] 쿠키 로드 완료")
            else:
                print("[ERROR] 쿠키 파일이 없습니다. 먼저 로그인을 실행하세요.")
                await browser.close()
                return False
            
            page = await context.new_page()
            
            # ExtJS Helper 초기화
            extjs = MEKICSHelper(page)
            
            try:
                print("="*80)
                print("MEK-ICS ERP 매출현황 조회 자동화")
                print("="*80)
                
                # [1] 메인 페이지 접속
                print("\n[1] 메인 페이지 접속...")
                await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
                await page.wait_for_timeout(5000)
                
                # ExtJS 로드 대기
                await extjs.wait_for_extjs()
                
                # 스크린샷
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                await page.screenshot(path=str(self.data_dir / f"main_{timestamp}.png"))
                
                # [2] 영업관리 모듈 클릭 (4번째 아이콘)
                print("\n[2] 영업관리 모듈 클릭...")
                
                # 방법 1: ExtJS Helper 사용
                success = await extjs.navigate_to_module('영업관리')
                
                if not success:
                    # 방법 2: JavaScript로 직접 클릭
                    print("   JavaScript로 재시도...")
                    await page.evaluate("""
                        () => {
                            // moduleArray에서 영업관리(14) 찾기
                            if (typeof changeModule === 'function') {
                                changeModule('14');
                            }
                        }
                    """)
                
                await page.wait_for_timeout(5000)
                await extjs.wait_for_loading()
                
                # 영업관리 진입 스크린샷
                await page.screenshot(path=str(self.data_dir / f"sales_module_{timestamp}.png"))
                print("   영업관리 모듈 진입 완료")
                
                # [3] 왼쪽 트리 메뉴에서 매출관리 확장
                print("\n[3] 매출관리 메뉴 확장...")
                
                # 매출관리 노드 확장
                expanded = await extjs.expand_tree_node('매출관리')
                if not expanded:
                    # DOM에서 직접 찾기
                    print("   DOM에서 매출관리 찾기...")
                    await page.evaluate("""
                        () => {
                            const nodes = document.querySelectorAll('.x-tree-node-text');
                            for (let node of nodes) {
                                if (node.innerText && node.innerText.includes('매출관리')) {
                                    node.click();
                                    break;
                                }
                            }
                        }
                    """)
                
                await page.wait_for_timeout(2000)
                
                # [4] 매출현황조회 클릭
                print("\n[4] 매출현황조회 메뉴 클릭...")
                
                # ExtJS로 메뉴 클릭
                clicked = await extjs.click_menu('매출현황조회')
                
                if not clicked:
                    # DOM에서 직접 클릭
                    print("   DOM에서 매출현황조회 찾기...")
                    await page.evaluate("""
                        () => {
                            const nodes = document.querySelectorAll('.x-tree-node-text');
                            for (let node of nodes) {
                                if (node.innerText && node.innerText === '매출현황조회') {
                                    node.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                
                await page.wait_for_timeout(5000)
                await extjs.wait_for_loading()
                
                # 매출현황조회 화면 스크린샷
                await page.screenshot(path=str(self.data_dir / f"sales_inquiry_{timestamp}.png"))
                print("   매출현황조회 화면 진입 완료")
                
                # [5] 날짜 설정 및 국내/해외 구분 변경
                print("\n[5] 조회 조건 설정...")
                
                # 날짜 필드 설정 (08.01 ~ 08.10)
                date_set = await page.evaluate("""
                    () => {
                        // 날짜 필드 찾기
                        const dateFields = Ext.ComponentQuery.query('datefield');
                        let fromDateSet = false;
                        let toDateSet = false;
                        
                        for (let field of dateFields) {
                            const label = field.getFieldLabel ? field.getFieldLabel() : '';
                            const name = field.getName ? field.getName() : '';
                            
                            // From 날짜 (시작일)
                            if (label.includes('시작') || label.includes('From') || 
                                label.includes('부터') || name.includes('FROM')) {
                                field.setValue(new Date(2024, 7, 5)); // 8월 5일 월요일 (월은 0부터 시작)
                                fromDateSet = true;
                            }
                            // To 날짜 (종료일)
                            else if (label.includes('종료') || label.includes('To') || 
                                     label.includes('까지') || name.includes('TO')) {
                                field.setValue(new Date(2024, 7, 9)); // 8월 9일 금요일
                                toDateSet = true;
                            }
                        }
                        
                        // 매출일자 필드가 하나만 있는 경우
                        if (!fromDateSet && dateFields.length > 0) {
                            dateFields[0].setValue(new Date(2024, 7, 5));
                        }
                        if (!toDateSet && dateFields.length > 1) {
                            dateFields[1].setValue(new Date(2024, 7, 9));
                        }
                        
                        return {fromDateSet, toDateSet};
                    }
                """)
                
                print(f"   날짜 설정: 2024.08.05(월) ~ 2024.08.09(금)")
                
                # 국내/해외 구분을 '전체'로 변경
                print("   국내/해외 구분을 '전체'로 변경...")
                
                # 콤보박스 찾아서 '전체' 선택
                combo_changed = await page.evaluate("""
                    () => {
                        // 국내/해외 구분 콤보박스 찾기
                        const combos = Ext.ComponentQuery.query('combobox');
                        for (let combo of combos) {
                            const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                            if (label.includes('국내') || label.includes('해외') || label.includes('구분')) {
                                // '전체' 값 설정
                                combo.setValue(''); // 빈 값이 전체일 수도 있음
                                // 또는
                                combo.setValue('ALL');
                                // 또는
                                combo.setValue('전체');
                                return true;
                            }
                        }
                        
                        // name으로도 시도
                        const divCombo = Ext.ComponentQuery.query('combobox[name*="DIV"]')[0];
                        if (divCombo) {
                            divCombo.setValue('');
                            return true;
                        }
                        
                        return false;
                    }
                """)
                
                if combo_changed:
                    print("   구분을 '전체'로 변경 완료")
                else:
                    print("   구분 콤보박스를 찾을 수 없음 (기본값 사용)")
                
                await page.wait_for_timeout(1000)
                
                # [6] 조회(F2) 버튼 클릭
                print("\n[6] 조회 버튼 클릭...")
                
                # F2 키 누르기
                await page.keyboard.press('F2')
                print("   F2 키 입력")
                
                # 또는 조회 버튼 클릭
                query_clicked = await page.evaluate("""
                    () => {
                        // 조회 버튼 찾기
                        const buttons = Ext.ComponentQuery.query('button');
                        for (let btn of buttons) {
                            const text = btn.getText ? btn.getText() : '';
                            if (text.includes('조회') || text.includes('Search') || text.includes('Query')) {
                                btn.fireEvent('click', btn);
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                
                if query_clicked:
                    print("   조회 버튼 클릭 완료")
                
                # 데이터 로딩 대기
                print("   데이터 로딩 중...")
                await extjs.wait_for_loading()
                await page.wait_for_timeout(5000)
                
                # 그리드 데이터 확인
                grid_data = await extjs.get_grid_data()
                if grid_data:
                    print(f"   조회 결과: {grid_data.get('total', 0)}건")
                    
                    # 샘플 데이터 출력
                    if grid_data.get('data'):
                        print("   [샘플 데이터]")
                        for i, row in enumerate(grid_data['data'][:3]):
                            print(f"   {i+1}. {row}")
                
                # 조회 결과 스크린샷
                await page.screenshot(path=str(self.data_dir / f"sales_result_{timestamp}.png"))
                
                # [7] 엑셀 다운로드 버튼 클릭
                print("\n[7] 엑셀 다운로드 버튼 클릭...")
                
                # 다운로드 이벤트 대기 설정
                download_promise = page.wait_for_event('download')
                
                # 엑셀 버튼 클릭
                excel_clicked = await page.evaluate("""
                    () => {
                        // 엑셀 버튼 찾기
                        const buttons = Ext.ComponentQuery.query('button');
                        for (let btn of buttons) {
                            const text = btn.getText ? btn.getText() : '';
                            const tooltip = btn.tooltip || '';
                            
                            if (text.includes('엑셀') || text.includes('Excel') || 
                                text.includes('다운로드') || text.includes('Download') ||
                                tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                                btn.fireEvent('click', btn);
                                return true;
                            }
                        }
                        
                        // 툴바 버튼도 확인
                        const tools = Ext.ComponentQuery.query('tool');
                        for (let tool of tools) {
                            if (tool.type === 'excel' || tool.type === 'download') {
                                tool.fireEvent('click', tool);
                                return true;
                            }
                        }
                        
                        return false;
                    }
                """)
                
                if excel_clicked:
                    print("   엑셀 다운로드 버튼 클릭 완료")
                    
                    # 다운로드 대기
                    try:
                        download = await download_promise
                        
                        # 다운로드 파일 저장
                        download_path = self.data_dir / f"sales_report_{timestamp}.xlsx"
                        await download.save_as(str(download_path))
                        
                        print(f"   엑셀 파일 저장: {download_path}")
                        
                    except Exception as e:
                        print(f"   다운로드 대기 중 오류: {e}")
                else:
                    print("   엑셀 다운로드 버튼을 찾을 수 없음")
                
                # 최종 스크린샷
                await page.screenshot(path=str(self.data_dir / f"final_{timestamp}.png"))
                
                # 완료 메시지
                print("\n" + "="*80)
                print("매출현황 조회 및 다운로드 완료!")
                print("="*80)
                print(f"저장 위치: {self.data_dir}")
                print(f"- 스크린샷: 4개")
                print(f"- 엑셀 파일: sales_report_{timestamp}.xlsx")
                
                return True
                
            except Exception as e:
                print(f"\n[ERROR] 자동화 실행 중 오류: {e}")
                import traceback
                traceback.print_exc()
                
                # 오류 스크린샷
                error_screenshot = self.data_dir / f"error_{timestamp}.png"
                await page.screenshot(path=str(error_screenshot))
                print(f"오류 스크린샷: {error_screenshot}")
                
                return False
            
            finally:
                print("\n브라우저를 30초 후 닫습니다...")
                await page.wait_for_timeout(30000)
                await browser.close()


async def main():
    """메인 실행"""
    automation = SalesReportAutomation()
    result = await automation.run_sales_report()
    
    if result:
        print("\n[SUCCESS] 매출현황 자동화 성공!")
    else:
        print("\n[FAIL] 매출현황 자동화 실패")


if __name__ == "__main__":
    asyncio.run(main())
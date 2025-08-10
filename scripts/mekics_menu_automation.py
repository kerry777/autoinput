#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 메뉴 자동화
영업, 생산, 구매 등 주요 메뉴 자동 클릭 및 데이터 수집
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


class MekicsMenuAutomation:
    """MEK-ICS 메뉴 자동화"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # ExtJS에서 발견한 메뉴 ID 매핑
        self.menu_mapping = {
            '기준정보': {'id': '11', 'selector': None},
            '인사/급여관리': {'id': '12', 'selector': None},
            '회계관리': {'id': '13', 'selector': None},
            '영업관리': {'id': '14', 'selector': None},
            '생산관리': {'id': '15', 'selector': None},
            '구매/자재': {'id': '16', 'selector': None},
            '재고관리': {'id': '18', 'selector': None},
            '원가관리': {'id': '21', 'selector': None},
            '품질관리': {'id': '65', 'selector': None},
            'AS': {'id': '64', 'selector': None},
            '장비관리': {'id': '32', 'selector': None},
            'TV현황판': {'id': '20', 'selector': None}
        }
        
        self.collected_data = {}
    
    async def navigate_menu(self, page, menu_name):
        """특정 메뉴로 이동"""
        try:
            print(f"\n[{menu_name}] 메뉴 접근 시도...")
            
            # JavaScript로 직접 메뉴 클릭 시도
            menu_id = self.menu_mapping.get(menu_name, {}).get('id')
            if menu_id:
                # ExtJS 스토어에서 메뉴 찾기 및 클릭
                js_code = f"""
                    // 메뉴 ID로 모듈 찾기
                    var moduleId = '{menu_id}';
                    var moduleArray = window.moduleArray || [];
                    var targetModule = null;
                    
                    for(var i = 0; i < moduleArray.length; i++) {{
                        if(moduleArray[i].id === moduleId) {{
                            targetModule = moduleArray[i];
                            break;
                        }}
                    }}
                    
                    if(targetModule) {{
                        console.log('Found module:', targetModule.title);
                        // 메뉴 클릭 이벤트 발생
                        if(window.changeModule) {{
                            window.changeModule(moduleId);
                            return true;
                        }}
                    }}
                    return false;
                """
                
                result = await page.evaluate(js_code)
                if result:
                    print(f"   JavaScript로 메뉴 클릭 성공")
                    await page.wait_for_timeout(3000)
                    
                    # 스크린샷
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot_path = self.data_dir / f"menu_{menu_name}_{timestamp}.png"
                    await page.screenshot(path=str(screenshot_path))
                    print(f"   스크린샷: {screenshot_path}")
                    
                    return True
            
            # DOM에서 직접 찾기 (폴백)
            print(f"   DOM에서 '{menu_name}' 텍스트 찾기...")
            
            # 다양한 선택자로 시도
            selectors = [
                f'text="{menu_name}"',
                f'*:has-text("{menu_name}")',
                f'[title="{menu_name}"]',
                f'img[title="{menu_name}"]',
                f'div:has-text("{menu_name}")'
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # 요소가 보이는지 확인
                        is_visible = await element.is_visible()
                        if is_visible:
                            await element.click()
                            print(f"   DOM 클릭 성공: {selector}")
                            await page.wait_for_timeout(3000)
                            
                            # 스크린샷
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            screenshot_path = self.data_dir / f"menu_{menu_name}_{timestamp}.png"
                            await page.screenshot(path=str(screenshot_path))
                            print(f"   스크린샷: {screenshot_path}")
                            
                            return True
                except:
                    continue
            
            print(f"   '{menu_name}' 메뉴를 찾을 수 없음")
            return False
            
        except Exception as e:
            print(f"   오류: {e}")
            return False
    
    async def extract_menu_data(self, page, menu_name):
        """메뉴 데이터 추출"""
        try:
            print(f"   데이터 추출 중...")
            
            # 현재 페이지 정보
            current_url = page.url
            page_title = await page.title()
            
            # 트리 메뉴 구조 추출
            tree_items = await page.query_selector_all('.x-tree-node-text')
            tree_data = []
            for item in tree_items[:20]:  # 처음 20개
                try:
                    text = await item.inner_text()
                    if text and text.strip():
                        tree_data.append(text.strip())
                except:
                    continue
            
            # 그리드/테이블 데이터 확인
            grid_data = []
            grids = await page.query_selector_all('.x-grid, .x-grid-view, table')
            if grids:
                print(f"   그리드/테이블 {len(grids)}개 발견")
                
                for grid in grids[:3]:  # 처음 3개 그리드
                    try:
                        # 헤더 추출
                        headers = await grid.query_selector_all('th, .x-column-header-text')
                        header_texts = []
                        for h in headers[:10]:
                            h_text = await h.inner_text()
                            if h_text:
                                header_texts.append(h_text.strip())
                        
                        # 데이터 행 추출
                        rows = await grid.query_selector_all('tr, .x-grid-row')
                        row_data = []
                        for row in rows[:5]:  # 처음 5행
                            cells = await row.query_selector_all('td, .x-grid-cell')
                            cell_texts = []
                            for cell in cells[:10]:
                                c_text = await cell.inner_text()
                                if c_text:
                                    cell_texts.append(c_text.strip())
                            if cell_texts:
                                row_data.append(cell_texts)
                        
                        if header_texts or row_data:
                            grid_data.append({
                                'headers': header_texts,
                                'rows': row_data
                            })
                    except:
                        continue
            
            # 결과 저장
            menu_data = {
                'menu_name': menu_name,
                'url': current_url,
                'title': page_title,
                'tree_items': tree_data,
                'grid_data': grid_data,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.collected_data[menu_name] = menu_data
            
            print(f"   트리 항목: {len(tree_data)}개")
            print(f"   그리드: {len(grid_data)}개")
            
            if tree_data:
                print(f"   샘플 트리: {tree_data[:3]}")
            
            return menu_data
            
        except Exception as e:
            print(f"   데이터 추출 오류: {e}")
            return None
    
    async def automate_menus(self):
        """메뉴 자동화 실행"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone'],
                viewport={'width': 1920, 'height': 1080}
            )
            
            # 쿠키 로드
            cookie_file = self.data_dir / "cookies.json"
            if cookie_file.exists():
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("[OK] 쿠키 로드 완료")
            
            page = await context.new_page()
            
            try:
                print("="*80)
                print("MEK-ICS ERP 메뉴 자동화")
                print("="*80)
                
                # 메인 페이지 접속
                print("\n[1] 메인 페이지 접속...")
                await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
                await page.wait_for_timeout(7000)
                
                # 초기 화면 캡처
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                main_screenshot = self.data_dir / f"main_initial_{timestamp}.png"
                await page.screenshot(path=str(main_screenshot))
                print(f"   메인 화면: {main_screenshot}")
                
                # JavaScript 환경 확인
                print("\n[2] ExtJS 환경 확인...")
                ext_check = await page.evaluate("""
                    {
                        extVersion: typeof Ext !== 'undefined' ? Ext.getVersion().version : null,
                        moduleCount: typeof moduleArray !== 'undefined' ? moduleArray.length : 0,
                        changeModuleExists: typeof changeModule === 'function'
                    }
                """)
                print(f"   ExtJS 버전: {ext_check.get('extVersion')}")
                print(f"   모듈 수: {ext_check.get('moduleCount')}")
                print(f"   changeModule 함수: {ext_check.get('changeModuleExists')}")
                
                # 주요 메뉴 순회
                target_menus = ['영업관리', '생산관리', '구매/자재', '재고관리', '품질관리']
                
                print("\n[3] 주요 메뉴 자동화 시작...")
                print("-"*80)
                
                for menu_name in target_menus:
                    # 메뉴 이동
                    success = await self.navigate_menu(page, menu_name)
                    
                    if success:
                        # 데이터 추출
                        await self.extract_menu_data(page, menu_name)
                        
                        # 메인으로 돌아가기
                        print(f"   메인 화면으로 복귀...")
                        await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
                        await page.wait_for_timeout(3000)
                    
                    print("-"*80)
                
                # 결과 저장
                print("\n[4] 수집 데이터 저장...")
                result_file = self.data_dir / f"menu_automation_result_{timestamp}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
                print(f"   저장 완료: {result_file}")
                
                # 요약 출력
                print("\n" + "="*80)
                print("자동화 결과 요약")
                print("="*80)
                print(f"처리된 메뉴: {len(self.collected_data)}개")
                
                for menu_name, data in self.collected_data.items():
                    print(f"\n[{menu_name}]")
                    print(f"  - URL: {data.get('url', '')}")
                    print(f"  - 트리 항목: {len(data.get('tree_items', []))}개")
                    print(f"  - 그리드: {len(data.get('grid_data', []))}개")
                
                print("\n" + "="*80)
                print("MEK-ICS ERP 메뉴 구조 파악 완료!")
                print("="*80)
                print("\n다음 단계:")
                print("1. 각 메뉴의 서브메뉴를 더 상세히 탐색")
                print("2. 실제 업무 데이터 (주문, 생산지시, 구매요청 등) 추출")
                print("3. 데이터 입력 자동화 구현")
                print("4. 리포트 생성 자동화")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] {e}")
                import traceback
                traceback.print_exc()
                return False
            
            finally:
                print("\n브라우저를 30초 후 닫습니다...")
                await page.wait_for_timeout(30000)
                await browser.close()


async def main():
    """메인 실행"""
    automation = MekicsMenuAutomation()
    await automation.automate_menus()


if __name__ == "__main__":
    asyncio.run(main())
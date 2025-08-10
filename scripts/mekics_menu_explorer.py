#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 메뉴 탐색 및 스크래핑
영업, 생산, 구매 등 주요 메뉴 구조 파악
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


class MekicsMenuExplorer:
    """MEK-ICS 메뉴 탐색기"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.menu_data = {
            'main_menus': [],
            'sub_menus': {},
            'menu_structure': {},
            'screenshots': []
        }
    
    async def explore_menus(self):
        """메뉴 구조 탐색"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone']
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
                print("="*70)
                print("MEK-ICS ERP 메뉴 구조 탐색")
                print("="*70)
                
                # 메인 페이지 접속
                print("\n[1] 메인 페이지 접속...")
                await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
                await page.wait_for_timeout(5000)
                
                # 전체 화면 스크린샷
                screenshot_path = self.data_dir / f"main_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"   메인 화면 캡처: {screenshot_path}")
                self.menu_data['screenshots'].append(str(screenshot_path))
                
                print("\n[2] 메인 메뉴 분석...")
                print("-"*70)
                
                # 다양한 메뉴 선택자 시도
                menu_selectors = [
                    # 일반적인 메뉴 선택자
                    '.gnb a',
                    '.gnb li',
                    '#gnb a',
                    '#gnb li',
                    '.menu a',
                    '.menu li',
                    '.nav a',
                    '.nav li',
                    'nav a',
                    'nav li',
                    
                    # 프레임 기반 선택자
                    'frame',
                    'iframe',
                    
                    # 클래스/ID 기반
                    '[class*="menu"] a',
                    '[class*="menu"] li',
                    '[id*="menu"] a',
                    '[id*="menu"] li',
                    
                    # 한글 텍스트 포함
                    'a:has-text("영업")',
                    'a:has-text("생산")',
                    'a:has-text("구매")',
                    'a:has-text("품질")',
                    'a:has-text("재고")',
                    
                    # 특정 속성
                    'a[href*="menu"]',
                    'a[onclick]',
                    'li[onclick]',
                    'div[onclick]',
                    'span[onclick]'
                ]
                
                # 프레임 확인
                frames = page.frames
                print(f"\n[프레임 정보]")
                print(f"   총 프레임 수: {len(frames)}")
                for i, frame in enumerate(frames):
                    print(f"   프레임 {i}: {frame.url}")
                
                # 각 프레임에서 메뉴 찾기
                for frame_idx, frame in enumerate(frames):
                    if frame_idx == 0:
                        print(f"\n[메인 프레임 탐색]")
                    else:
                        print(f"\n[프레임 {frame_idx} 탐색]")
                    
                    for selector in menu_selectors:
                        try:
                            elements = await frame.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                print(f"   {selector}: {len(elements)}개 발견")
                                
                                # 처음 10개 요소 분석
                                for i, elem in enumerate(elements[:10]):
                                    try:
                                        text = await elem.inner_text()
                                        if text and text.strip():
                                            # href나 onclick 속성 가져오기
                                            href = await elem.get_attribute('href') or ''
                                            onclick = await elem.get_attribute('onclick') or ''
                                            elem_id = await elem.get_attribute('id') or ''
                                            elem_class = await elem.get_attribute('class') or ''
                                            
                                            menu_item = {
                                                'text': text.strip(),
                                                'href': href,
                                                'onclick': onclick,
                                                'id': elem_id,
                                                'class': elem_class,
                                                'frame': frame_idx,
                                                'selector': selector
                                            }
                                            
                                            # 주요 메뉴인지 확인
                                            important_keywords = ['영업', '생산', '구매', '품질', '재고', '회계', '인사', '경영']
                                            is_important = any(keyword in text for keyword in important_keywords)
                                            
                                            if is_important:
                                                print(f"      [중요] {text.strip()}")
                                                self.menu_data['main_menus'].append(menu_item)
                                            else:
                                                print(f"      - {text.strip()[:30]}")
                                    except:
                                        continue
                        except:
                            continue
                
                # 모든 클릭 가능한 요소 찾기
                print("\n[3] 클릭 가능한 요소 분석...")
                clickable_elements = await page.query_selector_all('a, button, [onclick], [href]')
                print(f"   총 클릭 가능 요소: {len(clickable_elements)}개")
                
                important_elements = []
                for elem in clickable_elements:
                    try:
                        text = await elem.inner_text()
                        if text and any(k in text for k in ['영업', '생산', '구매', '품질', '재고', '회계']):
                            important_elements.append({
                                'text': text.strip(),
                                'tag': await elem.evaluate('el => el.tagName'),
                                'href': await elem.get_attribute('href') or '',
                                'onclick': await elem.get_attribute('onclick') or ''
                            })
                    except:
                        continue
                
                if important_elements:
                    print(f"\n[발견된 주요 메뉴]")
                    for elem in important_elements[:20]:
                        print(f"   - {elem['text'][:50]} ({elem['tag']})")
                
                # 주요 메뉴 클릭 시도
                print("\n[4] 주요 메뉴 접근 시도...")
                target_menus = ['영업', '생산', '구매']
                
                for menu_name in target_menus:
                    print(f"\n   [{menu_name}] 메뉴 찾기...")
                    
                    # 텍스트로 요소 찾기
                    menu_elem = await page.query_selector(f'*:has-text("{menu_name}")')
                    
                    if menu_elem:
                        try:
                            # 클릭 시도
                            await menu_elem.click()
                            await page.wait_for_timeout(3000)
                            
                            # 스크린샷
                            screenshot_path = self.data_dir / f"menu_{menu_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                            await page.screenshot(path=str(screenshot_path))
                            print(f"      스크린샷: {screenshot_path}")
                            
                            # 서브메뉴 찾기
                            sub_menus = await page.query_selector_all('a, li, div')
                            sub_menu_texts = []
                            for sub in sub_menus[:20]:
                                try:
                                    sub_text = await sub.inner_text()
                                    if sub_text and sub_text.strip() and len(sub_text.strip()) < 30:
                                        sub_menu_texts.append(sub_text.strip())
                                except:
                                    continue
                            
                            if sub_menu_texts:
                                self.menu_data['sub_menus'][menu_name] = sub_menu_texts[:10]
                                print(f"      서브메뉴 {len(sub_menu_texts)}개 발견")
                            
                            # 메인으로 돌아가기
                            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
                            await page.wait_for_timeout(2000)
                            
                        except Exception as e:
                            print(f"      클릭 실패: {e}")
                
                # 결과 저장
                print("\n[5] 탐색 결과 저장...")
                result_file = self.data_dir / f"menu_exploration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(self.menu_data, f, ensure_ascii=False, indent=2)
                print(f"   저장 완료: {result_file}")
                
                # 요약 출력
                print("\n" + "="*70)
                print("탐색 결과 요약")
                print("="*70)
                print(f"메인 메뉴: {len(self.menu_data['main_menus'])}개")
                print(f"서브 메뉴: {len(self.menu_data['sub_menus'])}개 카테고리")
                print(f"스크린샷: {len(self.menu_data['screenshots'])}개")
                
                if self.menu_data['main_menus']:
                    print("\n[발견된 메인 메뉴]")
                    for menu in self.menu_data['main_menus'][:10]:
                        print(f"   - {menu['text']}")
                
                if self.menu_data['sub_menus']:
                    print("\n[서브 메뉴 구조]")
                    for main, subs in self.menu_data['sub_menus'].items():
                        print(f"   {main}: {len(subs)}개 서브메뉴")
                
                # 추가 질문
                print("\n" + "="*70)
                print("추가 정보가 필요합니다:")
                print("="*70)
                print("1. 특정 메뉴를 클릭했을 때 팝업이 뜨나요, 새 페이지로 이동하나요?")
                print("2. 메뉴가 프레임 안에 있나요? (좌측, 상단 등)")
                print("3. 권한이 필요한 메뉴가 있나요?")
                print("4. 어떤 데이터를 주로 추출하실 건가요? (리스트, 상세정보 등)")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] {e}")
                import traceback
                traceback.print_exc()
                return False
            
            finally:
                print("\n브라우저를 20초 후 닫습니다... (메뉴 구조 확인 시간)")
                await page.wait_for_timeout(20000)
                await browser.close()


async def main():
    """메인 실행"""
    explorer = MekicsMenuExplorer()
    await explorer.explore_menus()


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 메인 화면 상세 분석
바탕화면의 아이콘/버튼 및 HTML 구조 완전 분석
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


class MekicsMainAnalyzer:
    """MEK-ICS 메인 화면 분석기"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    async def analyze_main_screen(self):
        """메인 화면 상세 분석"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone'],
                viewport={'width': 1920, 'height': 1080}  # 큰 화면으로 설정
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
                print("MEK-ICS ERP 메인 화면 상세 분석")
                print("="*80)
                
                # 메인 페이지 접속
                print("\n[1] 메인 페이지 접속...")
                await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
                await page.wait_for_timeout(7000)  # 충분한 로딩 시간
                
                # 전체 화면 스크린샷
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = self.data_dir / f"main_screen_full_{timestamp}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                print(f"   전체 화면 캡처: {screenshot_path}")
                
                # 뷰포트 스크린샷 (보이는 부분만)
                viewport_path = self.data_dir / f"main_screen_viewport_{timestamp}.png"
                await page.screenshot(path=str(viewport_path))
                print(f"   뷰포트 캡처: {viewport_path}")
                
                print("\n[2] HTML 구조 추출 및 저장...")
                
                # 전체 HTML 저장
                html_content = await page.content()
                html_file = self.data_dir / f"main_page_html_{timestamp}.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"   HTML 저장: {html_file}")
                
                # DOM 구조 분석
                print("\n[3] DOM 구조 분석...")
                
                # 모든 버튼/아이콘 찾기
                icon_selectors = [
                    'button',
                    'a',
                    'div[onclick]',
                    'img[onclick]',
                    '[class*="icon"]',
                    '[class*="btn"]',
                    '[class*="menu"]',
                    '[class*="link"]',
                    '.shortcut',
                    '.desktop-icon',
                    '.menu-item',
                    '.app-icon'
                ]
                
                all_elements = []
                for selector in icon_selectors:
                    elements = await page.query_selector_all(selector)
                    for elem in elements:
                        try:
                            text = await elem.inner_text() or ''
                            # 이미지인 경우 alt 텍스트 가져오기
                            if not text:
                                text = await elem.get_attribute('alt') or ''
                            if not text:
                                text = await elem.get_attribute('title') or ''
                            
                            # 속성 가져오기
                            elem_info = {
                                'text': text.strip(),
                                'tag': await elem.evaluate('el => el.tagName'),
                                'id': await elem.get_attribute('id') or '',
                                'class': await elem.get_attribute('class') or '',
                                'href': await elem.get_attribute('href') or '',
                                'onclick': await elem.get_attribute('onclick') or '',
                                'src': await elem.get_attribute('src') or '',
                                'style': await elem.get_attribute('style') or '',
                                'selector': selector
                            }
                            
                            # 위치 정보
                            try:
                                box = await elem.bounding_box()
                                if box:
                                    elem_info['position'] = {
                                        'x': box['x'],
                                        'y': box['y'],
                                        'width': box['width'],
                                        'height': box['height']
                                    }
                            except:
                                pass
                            
                            # 비어있지 않은 요소만 저장
                            if any([elem_info['text'], elem_info['onclick'], elem_info['href'], elem_info['src']]):
                                all_elements.append(elem_info)
                        except:
                            continue
                
                print(f"   총 {len(all_elements)}개 요소 발견")
                
                # 주요 메뉴 아이콘 필터링
                main_menu_keywords = ['영업', '생산', '구매', '품질', '재고', '회계', '인사', '자재', '출하', '입고', '재무', '경영']
                main_icons = []
                
                for elem in all_elements:
                    if any(keyword in str(elem.get('text', '')) for keyword in main_menu_keywords):
                        main_icons.append(elem)
                        print(f"   [메인 메뉴] {elem['text'][:50]}")
                
                # 이미지 요소 분석
                print("\n[4] 이미지 기반 아이콘 분석...")
                img_elements = await page.query_selector_all('img')
                print(f"   총 이미지: {len(img_elements)}개")
                
                img_data = []
                for img in img_elements[:30]:  # 처음 30개만
                    try:
                        img_info = {
                            'src': await img.get_attribute('src') or '',
                            'alt': await img.get_attribute('alt') or '',
                            'title': await img.get_attribute('title') or '',
                            'onclick': await img.get_attribute('onclick') or '',
                            'parent_onclick': await img.evaluate('el => el.parentElement ? el.parentElement.onclick : ""') or ''
                        }
                        if img_info['src']:
                            img_data.append(img_info)
                            if img_info['alt'] or img_info['title']:
                                print(f"   - {img_info['alt'] or img_info['title']}")
                    except:
                        continue
                
                # 클릭 가능한 영역 찾기
                print("\n[5] 클릭 가능한 영역 매핑...")
                clickable = await page.query_selector_all('[onclick], a[href], button')
                print(f"   클릭 가능 요소: {len(clickable)}개")
                
                clickable_data = []
                for elem in clickable[:50]:  # 처음 50개
                    try:
                        text = await elem.inner_text() or ''
                        onclick = await elem.get_attribute('onclick') or ''
                        href = await elem.get_attribute('href') or ''
                        
                        if text or onclick or href:
                            clickable_data.append({
                                'text': text.strip()[:100],
                                'onclick': onclick[:200],
                                'href': href[:200]
                            })
                            
                            # 주요 메뉴인 경우 출력
                            if any(k in text for k in main_menu_keywords):
                                print(f"   [클릭가능] {text[:50]}")
                    except:
                        continue
                
                # 프레임 내부 분석
                print("\n[6] 프레임/iframe 내부 분석...")
                frames = page.frames
                frame_data = []
                
                for i, frame in enumerate(frames):
                    if i == 0:
                        continue  # 메인 프레임 제외
                    
                    print(f"\n   프레임 {i}: {frame.url}")
                    
                    # 프레임 내부의 요소들
                    frame_elements = await frame.query_selector_all('a, button, div[onclick], img')
                    print(f"   프레임 내 요소: {len(frame_elements)}개")
                    
                    frame_items = []
                    for elem in frame_elements[:20]:
                        try:
                            text = await elem.inner_text() or ''
                            if text and any(k in text for k in main_menu_keywords):
                                frame_items.append(text.strip())
                                print(f"      - {text[:50]}")
                        except:
                            continue
                    
                    if frame_items:
                        frame_data.append({
                            'frame_index': i,
                            'url': frame.url,
                            'items': frame_items
                        })
                
                # 결과 종합
                analysis_result = {
                    'timestamp': timestamp,
                    'total_elements': len(all_elements),
                    'main_icons': main_icons,
                    'images': img_data,
                    'clickable': clickable_data,
                    'frames': frame_data,
                    'screenshots': [str(screenshot_path), str(viewport_path)],
                    'html_file': str(html_file)
                }
                
                # JSON으로 저장
                result_file = self.data_dir / f"main_analysis_{timestamp}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                print(f"\n[7] 분석 결과 저장: {result_file}")
                
                # 요약 출력
                print("\n" + "="*80)
                print("분석 결과 요약")
                print("="*80)
                print(f"1. HTML 파일: {html_file}")
                print(f"2. 스크린샷: {screenshot_path}")
                print(f"3. 발견된 요소: {len(all_elements)}개")
                print(f"4. 주요 메뉴: {len(main_icons)}개")
                print(f"5. 이미지: {len(img_data)}개")
                print(f"6. 클릭가능: {len(clickable_data)}개")
                
                if main_icons:
                    print("\n[발견된 주요 메뉴]")
                    for icon in main_icons[:15]:
                        print(f"   - {icon['text']}")
                
                print("\n분석 완료! HTML과 스크린샷을 확인하세요.")
                
                # 메뉴 클릭 테스트
                if main_icons:
                    print("\n[8] 첫 번째 메뉴 클릭 테스트...")
                    first_menu = main_icons[0]
                    print(f"   테스트 메뉴: {first_menu['text']}")
                    
                    # 선택자로 요소 찾기
                    if first_menu['id']:
                        test_elem = await page.query_selector(f"#{first_menu['id']}")
                    elif first_menu['class']:
                        classes = first_menu['class'].split()[0]
                        test_elem = await page.query_selector(f".{classes}")
                    else:
                        test_elem = None
                    
                    if test_elem:
                        await test_elem.click()
                        await page.wait_for_timeout(3000)
                        
                        # 클릭 후 스크린샷
                        after_click = self.data_dir / f"after_click_{timestamp}.png"
                        await page.screenshot(path=str(after_click))
                        print(f"   클릭 후 화면: {after_click}")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] {e}")
                import traceback
                traceback.print_exc()
                return False
            
            finally:
                print("\n브라우저를 30초 후 닫습니다... (결과 확인 시간)")
                await page.wait_for_timeout(30000)
                await browser.close()


async def main():
    """메인 실행"""
    analyzer = MekicsMainAnalyzer()
    await analyzer.analyze_main_screen()


if __name__ == "__main__":
    asyncio.run(main())
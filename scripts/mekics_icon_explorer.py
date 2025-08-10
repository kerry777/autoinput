#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 아이콘 실시간 탐색 - 검색 아이콘부터 시작
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def explore_icons():
    """아이콘 탐색 및 문서화"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    doc_path = data_dir / "ICON_DOCUMENTATION.md"
    
    # 문서 초기화
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write("# MEK-ICS 상단 아이콘 기능 문서\n")
        f.write(f"작성일: {datetime.now()}\n\n")
        f.write("## 우측 상단 아이콘 분석\n\n")
    
    async with async_playwright() as p:
        # 기존 브라우저에 연결하거나 새로 시작
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 메인 페이지 접속
        print("\n[1] MEK-ICS 메인 페이지 접속...")
        await page.goto("https://it.mek-ics.com/mekics/main/main.do")
        await page.wait_for_timeout(5000)
        
        print("\n[2] 검색 아이콘 찾기...")
        
        # 검색 아이콘 선택자들
        search_selectors = [
            '[class*="search"]',  # search 클래스
            '[class*="Search"]',  # Search 클래스
            '[title*="검색"]',    # 검색 타이틀
            '[title*="Search"]',  # Search 타이틀
            '[data-qtip*="검색"]',  # ExtJS 툴팁
            'button[aria-label*="search"]',  # ARIA 레이블
            '.x-btn-icon-el.x-search',  # ExtJS 검색 아이콘
            'span.x-btn-icon-el[style*="search"]',  # 스타일에 search
        ]
        
        found_search = None
        for selector in search_selectors:
            exists = await page.evaluate(f"""
                () => {{
                    const elem = document.querySelector('{selector}');
                    return elem ? {{
                        exists: true,
                        text: elem.textContent || elem.title || elem.getAttribute('data-qtip') || 'Search Icon',
                        selector: '{selector}'
                    }} : null;
                }}
            """)
            
            if exists:
                found_search = exists
                print(f"   검색 아이콘 발견: {selector}")
                break
        
        if found_search:
            print(f"\n[3] 검색 아이콘 클릭: {found_search['text']}")
            
            # 클릭 전 스크린샷
            await page.screenshot(path=str(data_dir / "before_search_click.png"))
            
            try:
                # 검색 아이콘 클릭
                await page.click(found_search['selector'])
                await page.wait_for_timeout(2000)
                
                # 결과 확인
                print("   클릭 완료! 변화 감지 중...")
                
                # 검색창이 열렸는지 확인
                search_result = await page.evaluate("""
                    () => {
                        // 검색 입력창 찾기
                        const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="검색"], input[name*="search"], .x-form-text[name*="search"]');
                        if (searchInputs.length > 0) {
                            return {
                                type: 'search_input',
                                count: searchInputs.length,
                                placeholder: searchInputs[0].placeholder || 'No placeholder'
                            };
                        }
                        
                        // 검색 팝업/모달 찾기
                        const searchModal = document.querySelector('.x-window[title*="검색"], .search-modal, .search-popup');
                        if (searchModal) {
                            return {
                                type: 'search_modal',
                                title: searchModal.title || searchModal.textContent.substring(0, 50)
                            };
                        }
                        
                        // 검색 패널 찾기
                        const searchPanel = document.querySelector('.search-panel, [class*="search-container"]');
                        if (searchPanel) {
                            return {
                                type: 'search_panel',
                                visible: searchPanel.style.display !== 'none'
                            };
                        }
                        
                        return null;
                    }
                """)
                
                # 클릭 후 스크린샷
                await page.screenshot(path=str(data_dir / "after_search_click.png"))
                
                # 문서화
                with open(doc_path, 'a', encoding='utf-8') as f:
                    f.write(f"### 1. 검색 아이콘\n")
                    f.write(f"- **위치**: 우측 상단\n")
                    f.write(f"- **선택자**: `{found_search['selector']}`\n")
                    
                    if search_result:
                        if search_result['type'] == 'search_input':
                            f.write(f"- **기능**: 검색 입력창 표시\n")
                            f.write(f"- **상세**: {search_result['count']}개의 검색 입력 필드 활성화\n")
                            f.write(f"- **Placeholder**: {search_result.get('placeholder', 'N/A')}\n")
                            print(f"   -> 검색 입력창 {search_result['count']}개 활성화됨")
                            
                        elif search_result['type'] == 'search_modal':
                            f.write(f"- **기능**: 검색 모달/팝업 열기\n")
                            f.write(f"- **제목**: {search_result.get('title', 'N/A')}\n")
                            print(f"   -> 검색 모달 열림")
                            
                        elif search_result['type'] == 'search_panel':
                            f.write(f"- **기능**: 검색 패널 토글\n")
                            f.write(f"- **상태**: {'표시' if search_result['visible'] else '숨김'}\n")
                            print(f"   -> 검색 패널 토글됨")
                    else:
                        f.write(f"- **기능**: 확인 필요 (명확한 변화 감지 안됨)\n")
                        print("   -> 명확한 변화를 감지하지 못함")
                    
                    f.write(f"- **테스트 시간**: {datetime.now()}\n\n")
                
                # ESC 키로 원래 상태로
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"   오류: {e}")
                with open(doc_path, 'a', encoding='utf-8') as f:
                    f.write(f"- **오류**: 클릭 실패 - {str(e)}\n\n")
        
        else:
            print("   검색 아이콘을 찾을 수 없음")
            
            # 모든 상단 버튼 찾기
            print("\n[4] 대신 모든 상단 아이콘 나열...")
            all_icons = await page.evaluate("""
                () => {
                    const icons = [];
                    
                    // ExtJS 툴바 버튼
                    const toolbar = Ext.ComponentQuery.query('toolbar[dock="top"]')[0];
                    if (toolbar) {
                        toolbar.items.items.forEach(item => {
                            if (item.xtype === 'button') {
                                icons.push({
                                    type: 'ExtJS Button',
                                    text: item.text || item.tooltip || item.iconCls || 'Unknown',
                                    id: item.id
                                });
                            }
                        });
                    }
                    
                    // 일반 HTML 아이콘
                    document.querySelectorAll('header button, .top-bar button, .toolbar button').forEach(btn => {
                        icons.push({
                            type: 'HTML Button',
                            text: btn.title || btn.textContent.trim() || 'Unknown',
                            class: btn.className
                        });
                    });
                    
                    return icons;
                }
            """)
            
            if all_icons:
                print(f"\n   발견된 상단 아이콘 {len(all_icons)}개:")
                with open(doc_path, 'a', encoding='utf-8') as f:
                    f.write("### 발견된 모든 상단 아이콘\n\n")
                    for i, icon in enumerate(all_icons, 1):
                        print(f"   {i}. {icon['text']} ({icon['type']})")
                        f.write(f"{i}. **{icon['text']}**\n")
                        f.write(f"   - Type: {icon['type']}\n")
                        if 'id' in icon:
                            f.write(f"   - ID: {icon['id']}\n")
                        if 'class' in icon:
                            f.write(f"   - Class: {icon['class']}\n")
                        f.write("\n")
        
        print(f"\n문서 저장 완료: {doc_path}")
        print("\n브라우저를 2분간 열어둡니다. 직접 클릭해보세요!")
        await page.wait_for_timeout(120000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_icons())
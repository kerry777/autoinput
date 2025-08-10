#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 인터랙티브 탐색기 - 실시간 아이콘 기능 파악
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


class MekicsExplorer:
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.doc_path = self.data_dir / "MEKICS_UI_DOCUMENTATION.md"
        self.page = None
        self.discoveries = []
        
    async def document_discovery(self, element_type, element_id, description, functionality):
        """발견한 기능 문서화"""
        discovery = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": element_type,
            "id": element_id,
            "description": description,
            "functionality": functionality
        }
        self.discoveries.append(discovery)
        
        # 파일에 추가
        with open(self.doc_path, 'a', encoding='utf-8') as f:
            f.write(f"\n## {element_type}: {description}\n")
            f.write(f"- **ID/Selector**: `{element_id}`\n")
            f.write(f"- **기능**: {functionality}\n")
            f.write(f"- **발견 시간**: {discovery['timestamp']}\n")
            f.write("\n---\n")
        
        print(f"\n[DOCUMENTED] {description}")
        
    async def click_and_analyze(self, selector, description):
        """요소 클릭 후 결과 분석"""
        print(f"\n[CLICKING] {description}...")
        
        # 클릭 전 상태 저장
        before_state = await self.page.evaluate("() => document.body.innerHTML.length")
        
        try:
            # 클릭 시도
            await self.page.click(selector, timeout=5000)
            await self.page.wait_for_timeout(2000)
            
            # 변화 감지
            after_state = await self.page.evaluate("() => document.body.innerHTML.length")
            
            # 팝업/모달 확인
            modal_check = await self.page.evaluate("""
                () => {
                    // ExtJS 모달 확인
                    const windows = Ext.WindowManager.getActive();
                    if (windows) {
                        return {
                            type: 'ExtJS Window',
                            title: windows.title || 'No title',
                            visible: true
                        };
                    }
                    
                    // 일반 모달 확인
                    const modals = document.querySelectorAll('.modal, .popup, [role="dialog"]');
                    if (modals.length > 0) {
                        return {
                            type: 'HTML Modal',
                            count: modals.length
                        };
                    }
                    
                    return null;
                }
            """)
            
            # 새 탭 확인
            if len(self.page.context.pages) > 1:
                print(f"  -> New tab opened!")
                return "Opens new tab/window"
            
            # 모달/팝업 확인
            if modal_check:
                print(f"  -> {modal_check['type']} opened: {modal_check.get('title', '')}")
                # 모달 닫기
                await self.page.keyboard.press('Escape')
                return f"Opens {modal_check['type']}"
            
            # 페이지 변화 확인
            if abs(after_state - before_state) > 1000:
                print(f"  -> Page content changed significantly")
                return "Changes page content"
            
            print(f"  -> No visible change detected")
            return "Function unclear (may require specific conditions)"
            
        except Exception as e:
            print(f"  -> Click failed: {str(e)[:50]}")
            return f"Not clickable or requires conditions"
    
    async def explore_top_icons(self):
        """상단 아이콘들 탐색"""
        print("\n" + "="*60)
        print("EXPLORING TOP NAVIGATION ICONS")
        print("="*60)
        
        # 상단 영역의 모든 버튼/아이콘 찾기
        icons = await self.page.evaluate("""
            () => {
                const results = [];
                
                // ExtJS 툴바 버튼
                const toolbar = Ext.ComponentQuery.query('toolbar[dock="top"]')[0];
                if (toolbar) {
                    toolbar.items.items.forEach((item, index) => {
                        if (item.xtype === 'button') {
                            results.push({
                                type: 'ExtJS Button',
                                selector: `#${item.id}`,
                                text: item.text || item.tooltip || `Button ${index}`,
                                index: index
                            });
                        }
                    });
                }
                
                // HTML 아이콘들
                const htmlIcons = document.querySelectorAll('header button, header a[class*="icon"], .top-bar button');
                htmlIcons.forEach((icon, index) => {
                    results.push({
                        type: 'HTML Icon',
                        selector: `header button:nth-of-type(${index+1})`,
                        text: icon.title || icon.textContent.trim() || `Icon ${index}`,
                        index: index
                    });
                });
                
                return results;
            }
        """)
        
        print(f"\nFound {len(icons)} icons/buttons in top area")
        
        # 각 아이콘 클릭 및 분석
        for i, icon in enumerate(icons[:10]):  # 상위 10개만
            print(f"\n[{i+1}/{len(icons)}] Testing: {icon['text']}")
            
            functionality = await self.click_and_analyze(
                icon['selector'], 
                icon['text']
            )
            
            await self.document_discovery(
                icon['type'],
                icon['selector'],
                icon['text'],
                functionality
            )
            
            # 원래 상태로 복귀
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(1000)
    
    async def interactive_mode(self):
        """대화형 모드"""
        print("\n" + "="*60)
        print("INTERACTIVE MODE ACTIVE")
        print("="*60)
        print("\nNow I can see the page. Tell me which icon to click!")
        print("Examples:")
        print("  - 'Click the first icon'")
        print("  - 'Click the settings button'")
        print("  - 'Try the menu icon'")
        print("\nWaiting for your instructions...")
        
        # 여기서 사용자 입력을 기다림
        await self.page.wait_for_timeout(300000)  # 5분 대기
    
    async def run(self):
        """메인 실행"""
        
        # 문서 파일 초기화
        with open(self.doc_path, 'w', encoding='utf-8') as f:
            f.write("# MEK-ICS UI Documentation\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n---\n")
        
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            
            context = await browser.new_context(
                locale='ko-KR',
                timezone_id='Asia/Seoul',
                viewport={'width': 1920, 'height': 1080}
            )
            
            # 쿠키 로드
            cookie_file = self.data_dir / "cookies.json"
            if cookie_file.exists():
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("Cookies loaded successfully")
            
            self.page = await context.new_page()
            
            # 메인 페이지 접속
            print("\n[1] Accessing MEK-ICS main page...")
            await self.page.goto("https://it.mek-ics.com/mekics/main/main.do")
            await self.page.wait_for_timeout(5000)
            
            # ExtJS 로드 대기
            await self.page.wait_for_function("() => typeof Ext !== 'undefined' && Ext.isReady")
            print("ExtJS loaded successfully")
            
            # 스크린샷
            screenshot = self.data_dir / f"main_screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=str(screenshot))
            print(f"Screenshot saved: {screenshot}")
            
            # 자동 탐색 모드
            await self.explore_top_icons()
            
            # 대화형 모드
            await self.interactive_mode()
            
            # 결과 요약
            print("\n" + "="*60)
            print("EXPLORATION SUMMARY")
            print("="*60)
            print(f"Total discoveries: {len(self.discoveries)}")
            print(f"Documentation saved to: {self.doc_path}")
            
            await browser.close()


if __name__ == "__main__":
    explorer = MekicsExplorer()
    asyncio.run(explorer.run())
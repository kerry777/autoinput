#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 실시간 탐색 - 로그인 후 아이콘 기능 파악
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def realtime_explore():
    """실시간 ERP 탐색"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    doc_path = data_dir / "ICON_FUNCTIONS.md"
    
    # 문서 초기화
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write("# MEK-ICS Icon Functions Documentation\n")
        f.write(f"Generated: {datetime.now()}\n\n")
    
    config_path = site_dir / "config" / "settings.json"
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
        
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("MEK-ICS REALTIME EXPLORATION")
        print("="*60)
        
        # 1. 로그인 페이지 접속
        print("\n[1] Going to login page...")
        await page.goto("https://it.mek-ics.com/mekics/login/login.do")
        await page.wait_for_timeout(3000)
        
        # 2. 로그인 시도
        print("\n[2] Attempting login...")
        print(f"   Username: {config['credentials']['username']}")
        
        # ID 입력
        await page.fill('input[name="userId"]', config['credentials']['username'])
        await page.wait_for_timeout(500)
        
        # 비밀번호 입력  
        await page.fill('input[name="passwd"]', config['credentials']['password'])
        await page.wait_for_timeout(500)
        
        # 로그인 버튼 클릭
        await page.click('button[type="submit"], input[type="submit"], #loginBtn')
        print("   Login button clicked")
        
        # 2FA 또는 메인 페이지 대기
        print("\n[3] Waiting for 2FA or main page...")
        print("   If 2FA appears, please complete it manually!")
        
        # 30초 대기 (2FA 처리 시간)
        await page.wait_for_timeout(30000)
        
        # 현재 URL 확인
        current_url = page.url
        print(f"\n[4] Current URL: {current_url}")
        
        if "main" in current_url:
            print("   Successfully logged in!")
            
            # ExtJS 로드 대기
            try:
                await page.wait_for_function(
                    "() => typeof Ext !== 'undefined' && Ext.isReady",
                    timeout=10000
                )
                print("   ExtJS loaded")
            except:
                print("   ExtJS not detected, continuing anyway...")
            
            # 스크린샷
            screenshot = data_dir / f"main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n[5] Screenshot saved: {screenshot}")
            
            # 상단 아이콘 찾기
            print("\n[6] Looking for top icons...")
            
            # 다양한 선택자로 아이콘 찾기
            icon_selectors = [
                '.x-btn-icon',  # ExtJS 아이콘 버튼
                '.toolbar-icon',  # 툴바 아이콘
                'header button',  # 헤더의 버튼
                '[class*="icon-"]',  # icon- 클래스
                '.menu-icon',  # 메뉴 아이콘
                '.user-icon',  # 사용자 아이콘
                '.logout-icon',  # 로그아웃 아이콘
                'button[data-qtip]',  # 툴팁이 있는 버튼
            ]
            
            found_icons = []
            for selector in icon_selectors:
                count = await page.evaluate(f"""
                    () => document.querySelectorAll('{selector}').length
                """)
                if count > 0:
                    found_icons.append((selector, count))
                    print(f"   Found {count} elements with selector: {selector}")
            
            # 아이콘 클릭 테스트
            print("\n[7] Testing icon clicks...")
            print("   I will click icons one by one and document their functions")
            
            # 첫 번째 아이콘 클릭 시도
            if found_icons:
                selector, count = found_icons[0]
                print(f"\n   Clicking first {selector}...")
                
                try:
                    await page.click(f"{selector}:first-of-type", timeout=3000)
                    await page.wait_for_timeout(2000)
                    
                    # 변화 감지
                    print("   Observing changes...")
                    
                    # 팝업 확인
                    popup = await page.evaluate("""
                        () => {
                            const windows = document.querySelectorAll('.x-window');
                            if (windows.length > 0) {
                                return windows[0].textContent.substring(0, 100);
                            }
                            return null;
                        }
                    """)
                    
                    if popup:
                        print(f"   -> Popup opened: {popup[:50]}...")
                        
                        # 문서화
                        with open(doc_path, 'a', encoding='utf-8') as f:
                            f.write(f"\n## Icon: {selector}:first-of-type\n")
                            f.write(f"- Function: Opens popup/modal\n")
                            f.write(f"- Content: {popup[:100]}\n")
                            f.write(f"- Time: {datetime.now()}\n\n")
                        
                        # 팝업 닫기
                        await page.keyboard.press('Escape')
                    else:
                        print("   -> No visible change detected")
                        
                except Exception as e:
                    print(f"   -> Click failed: {e}")
            
            print("\n" + "="*60)
            print("READY FOR INTERACTIVE EXPLORATION")
            print("="*60)
            print("\nThe browser is now open with MEK-ICS loaded.")
            print("You can see the page and tell me which icons to explore!")
            print("\nWaiting for 3 minutes for manual exploration...")
            
            # 3분 대기 (수동 탐색 시간)
            await page.wait_for_timeout(180000)
            
        else:
            print("   Not on main page. Please complete login manually.")
            print("   Waiting 2 minutes...")
            await page.wait_for_timeout(120000)
        
        # 쿠키 저장
        cookies = await context.cookies()
        with open(data_dir / "cookies.json", 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("\nCookies saved for next session")
        
        print("\n" + "="*60)
        print("Session complete!")
        print(f"Documentation saved to: {doc_path}")
        print("="*60)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(realtime_explore())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 실시간 세션 - 사용자와 함께 화면 공유
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright


async def live_session():
    """실시간 ERP 세션"""
    
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        # 브라우저 시작 (화면 표시)
        browser = await p.chromium.launch(
            headless=False,  # 화면 표시
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 쿠키 로드 (로그인 우회)
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("Cookie loaded successfully")
        
        page = await context.new_page()
        
        print("\n" + "="*60)
        print("MEK-ICS ERP 실시간 세션 시작")
        print("="*60)
        
        # 메인 페이지 접속
        print("\n[1] MEK-ICS 메인 페이지 접속 중...")
        await page.goto("https://it.mek-ics.com/mekics/main/main.do")
        await page.wait_for_timeout(5000)
        
        # ExtJS 로드 대기
        await page.wait_for_function("() => typeof Ext !== 'undefined' && Ext.isReady")
        print("ExtJS loaded successfully")
        
        # 우측 상단 아이콘 분석
        print("\n[2] 우측 상단 아이콘 분석 중...")
        
        # 상단 툴바 정보 추출
        toolbar_info = await page.evaluate("""
            () => {
                const result = {
                    icons: [],
                    buttons: [],
                    user_info: null
                };
                
                // 상단 툴바 찾기
                const toolbar = Ext.ComponentQuery.query('toolbar[dock="top"]')[0];
                if (toolbar) {
                    toolbar.items.items.forEach(item => {
                        if (item.xtype === 'button' || item.xtype === 'splitbutton') {
                            result.buttons.push({
                                text: item.text || '',
                                tooltip: item.tooltip || '',
                                iconCls: item.iconCls || '',
                                id: item.id || ''
                            });
                        }
                    });
                }
                
                // 우측 상단 영역 탐색
                const header = document.querySelector('.x-header') || 
                              document.querySelector('.main-header') ||
                              document.querySelector('#header');
                
                if (header) {
                    // 아이콘 버튼들 찾기
                    const iconButtons = header.querySelectorAll('[class*="icon"], [class*="btn"], button');
                    iconButtons.forEach(btn => {
                        result.icons.push({
                            className: btn.className,
                            title: btn.title || btn.getAttribute('data-qtip') || '',
                            text: btn.textContent.trim()
                        });
                    });
                }
                
                // 사용자 정보 찾기
                const userDisplay = document.querySelector('[class*="user"], [id*="user"]');
                if (userDisplay) {
                    result.user_info = userDisplay.textContent.trim();
                }
                
                return result;
            }
        """)
        
        print("\n발견된 요소들:")
        if toolbar_info['buttons']:
            print("\n툴바 버튼:")
            for btn in toolbar_info['buttons']:
                print(f"  - {btn['text']} ({btn['tooltip']})")
        
        if toolbar_info['icons']:
            print("\n아이콘:")
            for icon in toolbar_info['icons']:
                print(f"  - {icon['text']} ({icon['title']})")
        
        if toolbar_info['user_info']:
            print(f"\n사용자 정보: {toolbar_info['user_info']}")
        
        # 스크린샷 저장
        screenshot_path = data_dir / f"main_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print(f"\n스크린샷 저장: {screenshot_path}")
        
        # DOM 구조 분석
        print("\n[3] 상단 영역 DOM 구조 분석...")
        dom_structure = await page.evaluate("""
            () => {
                const headerArea = document.querySelector('body').children[0];
                const structure = {
                    tagName: headerArea.tagName,
                    id: headerArea.id,
                    className: headerArea.className,
                    children: []
                };
                
                // 첫 번째 레벨 자식들만
                for (let child of headerArea.children) {
                    if (child.offsetHeight > 0) {  // 보이는 요소만
                        structure.children.push({
                            tagName: child.tagName,
                            id: child.id,
                            className: child.className,
                            text: child.textContent.substring(0, 50)
                        });
                    }
                }
                
                return structure;
            }
        """)
        
        print(f"\n최상위 요소: {dom_structure['tagName']} (id: {dom_structure['id']})")
        for child in dom_structure['children'][:10]:  # 상위 10개만
            print(f"  └─ {child['tagName']} #{child['id']} .{child['className'][:30]}")
        
        # 대기
        print("\n" + "="*60)
        print("실시간 세션 활성화 중...")
        print("브라우저 창을 확인하세요!")
        print("우측 상단 아이콘들을 함께 볼 수 있습니다.")
        print("="*60)
        
        # 사용자가 확인할 시간
        print("\n브라우저를 닫지 마세요. 2분 동안 대기합니다...")
        await page.wait_for_timeout(120000)  # 2분 대기
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(live_session())
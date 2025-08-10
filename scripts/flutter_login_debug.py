#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter MSM 로그인 - 디버깅 버전
각 단계마다 상세 정보 출력
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_debug():
    """Flutter 로그인 디버깅"""
    
    print("\n[DEBUG MODE] Flutter MSM Login")
    print("="*50)
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500  # 느리게 실행
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드
            print("\n[1] Loading page...")
            await page.goto("http://it.mek-ics.com/msm")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 2. 페이지 분석
            print("\n[2] Analyzing page structure...")
            
            # 모든 input 요소 확인
            inputs = await page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input');
                    return inputs.length;
                }
            """)
            print(f"   - Found {inputs} input elements")
            
            # Flutter 요소 확인
            flutter_elements = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('[class*="flt-"]');
                    return elements.length;
                }
            """)
            print(f"   - Found {flutter_elements} Flutter elements")
            
            # 3. Tab 네비게이션 시작
            print("\n[3] Starting Tab navigation...")
            
            # 페이지 포커스
            await page.click('body')
            print("   - Page focused")
            await page.wait_for_timeout(500)
            
            # Tab으로 이동하면서 각 단계 확인
            for i in range(5):
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(300)
                
                # 현재 포커스 요소 정보
                focused = await page.evaluate("""
                    () => {
                        const elem = document.activeElement;
                        return {
                            tag: elem?.tagName,
                            type: elem?.type,
                            placeholder: elem?.placeholder,
                            className: elem?.className,
                            id: elem?.id,
                            name: elem?.name
                        };
                    }
                """)
                
                print(f"\n   Tab {i+1}: {focused['tag']}")
                print(f"   - type: {focused.get('type', 'none')}")
                print(f"   - placeholder: {focused.get('placeholder', 'none')}")
                
                # ID 필드 (보통 2번째 Tab)
                if i == 1:
                    print("   [ACTION] Entering ID...")
                    await page.keyboard.press('Control+A')
                    await page.keyboard.type('mdmtest')
                    await page.screenshot(path=f"logs/screenshots/flutter/debug_id_{timestamp}.png")
                
                # Password 필드 (보통 3번째 Tab)
                elif i == 2:
                    print("   [ACTION] Entering Password...")
                    await page.keyboard.press('Control+A')
                    await page.keyboard.type('0001')
                    await page.screenshot(path=f"logs/screenshots/flutter/debug_pw_{timestamp}.png")
                    
                # 로그인 버튼 찾기 (4번째 Tab)
                elif i == 3:
                    print("   [ACTION] Found submit button, clicking...")
                    await page.keyboard.press('Enter')  # 또는 Space
                    break
            
            # 4. 로그인 결과 대기
            print("\n[5] Waiting for login response...")
            await page.wait_for_timeout(5000)
            
            # 5. 결과 분석
            print("\n[6] Analyzing result...")
            
            current_url = page.url
            print(f"   - Current URL: {current_url}")
            
            # 페이지 제목 확인
            title = await page.title()
            print(f"   - Page title: {title}")
            
            # 페이지 텍스트 일부 확인
            try:
                body_text = await page.inner_text('body')
                if len(body_text) > 200:
                    body_text = body_text[:200] + "..."
                print(f"   - Body text preview: {body_text}")
            except:
                print("   - Could not get body text")
            
            # URL 변경 확인
            if current_url != "http://it.mek-ics.com/msm/":
                print("\n[SUCCESS] URL changed - Login successful!")
            else:
                print("\n[INFO] URL unchanged - checking other indicators...")
                
                # 로그인 후 요소 찾기
                success_indicators = [
                    'dashboard',
                    'welcome',
                    'logout',
                    'mdmtest',
                    '메인',
                    '대시보드'
                ]
                
                for indicator in success_indicators:
                    try:
                        element = await page.query_selector(f'text="{indicator}"')
                        if element:
                            print(f"   [FOUND] Success indicator: {indicator}")
                            break
                    except:
                        continue
            
            # 최종 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/debug_final_{timestamp}.png")
            print(f"\n[SAVED] Screenshots in logs/screenshots/flutter/")
            
            print("\n[7] Keeping browser open for manual inspection...")
            print("    Check if login was successful manually.")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Debug session ended")

if __name__ == "__main__":
    print("""
    =====================================
    Flutter MSM Login - Debug Mode
    =====================================
    Site: http://it.mek-ics.com/msm
    Credentials: mdmtest / 0001
    =====================================
    """)
    
    asyncio.run(flutter_login_debug())
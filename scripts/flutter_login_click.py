#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 로그인 - 로그인 버튼 클릭 방식
Password 입력 후 로그인 버튼을 좌표로 클릭
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def flutter_login_with_button_click():
    """Flutter 로그인 - 버튼 클릭"""
    
    print("\n[FLUTTER LOGIN - BUTTON CLICK METHOD]")
    print("="*50)
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500
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
            
            # 2. ID 필드 입력 (Tab 네비게이션)
            print("\n[2] Entering ID field...")
            await page.click('body')
            await page.wait_for_timeout(500)
            
            # Tab 2번으로 ID 필드
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            
            # ID 입력
            print("   - Typing: mdmtest")
            await page.keyboard.type('mdmtest')
            await page.wait_for_timeout(500)
            
            # 3. Password 필드 입력
            print("\n[3] Entering Password field...")
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(300)
            
            # Password 입력
            print("   - Typing: 0001")
            await page.keyboard.type('0001')
            await page.wait_for_timeout(500)
            
            # 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/click_filled_{timestamp}.png")
            
            # 4. 로그인 버튼 좌표 클릭 시도
            print("\n[4] Trying to click login button...")
            
            # 화면 중앙 기준으로 버튼 위치 추정
            viewport = page.viewport_size
            center_x = viewport['width'] // 2
            center_y = viewport['height'] // 2
            
            # 일반적인 로그인 버튼 위치들
            button_positions = [
                (center_x, center_y + 100),      # 중앙 아래
                (center_x, center_y + 150),      # 더 아래
                (center_x + 100, center_y + 100), # 오른쪽
                (center_x - 100, center_y + 100), # 왼쪽
            ]
            
            # 각 위치 클릭 시도
            for i, (x, y) in enumerate(button_positions):
                print(f"\n   Attempt {i+1}: Clicking at ({x}, {y})")
                await page.mouse.click(x, y)
                await page.wait_for_timeout(3000)
                
                # URL 변경 확인
                current_url = page.url
                if current_url != "http://it.mek-ics.com/msm/":
                    print(f"   [SUCCESS] URL changed to: {current_url}")
                    break
                else:
                    print(f"   [NO CHANGE] Still at: {current_url}")
            
            # 5. Tab + Space/Enter 시도
            if page.url == "http://it.mek-ics.com/msm/":
                print("\n[5] Trying Tab navigation to button...")
                
                # Password 필드에서 Tab으로 버튼으로 이동
                for i in range(3):
                    await page.keyboard.press('Tab')
                    await page.wait_for_timeout(300)
                    
                    # Space 또는 Enter로 버튼 클릭
                    print(f"   Tab {i+1}: Pressing Space")
                    await page.keyboard.press('Space')
                    await page.wait_for_timeout(2000)
                    
                    if page.url != "http://it.mek-ics.com/msm/":
                        print(f"   [SUCCESS] Login successful!")
                        break
            
            # 6. JavaScript로 버튼 찾기 시도
            if page.url == "http://it.mek-ics.com/msm/":
                print("\n[6] Searching for clickable elements...")
                
                clickable = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('*');
                        const clickables = [];
                        
                        elements.forEach(elem => {
                            const style = window.getComputedStyle(elem);
                            const rect = elem.getBoundingClientRect();
                            
                            // 클릭 가능한 요소 찾기
                            if ((style.cursor === 'pointer' || 
                                 elem.onclick || 
                                 elem.tagName === 'BUTTON' ||
                                 elem.tagName === 'INPUT') &&
                                rect.width > 0 && rect.height > 0) {
                                
                                clickables.push({
                                    tag: elem.tagName,
                                    x: rect.x + rect.width / 2,
                                    y: rect.y + rect.height / 2,
                                    width: rect.width,
                                    height: rect.height,
                                    text: elem.textContent?.trim()
                                });
                            }
                        });
                        
                        return clickables;
                    }
                """)
                
                print(f"   Found {len(clickable)} clickable elements")
                
                # Password 필드 아래쪽 요소들 클릭
                for elem in clickable:
                    if elem['y'] > center_y + 50:  # Password 필드보다 아래
                        print(f"   Clicking element at ({elem['x']}, {elem['y']})")
                        await page.mouse.click(elem['x'], elem['y'])
                        await page.wait_for_timeout(2000)
                        
                        if page.url != "http://it.mek-ics.com/msm/":
                            print(f"   [SUCCESS] Login successful!")
                            break
            
            # 7. 최종 결과
            print("\n[7] Final result...")
            final_url = page.url
            print(f"   Final URL: {final_url}")
            
            await page.screenshot(path=f"logs/screenshots/flutter/click_final_{timestamp}.png")
            
            if final_url != "http://it.mek-ics.com/msm/":
                print("\n[SUCCESS] LOGIN SUCCESSFUL!")
            else:
                print("\n[FAILED] Login failed - button not found")
                print("\nTry manual coordinates:")
                print("1. Take a screenshot")
                print("2. Find the exact login button position")
                print("3. Use page.mouse.click(x, y) with exact coordinates")
            
            print("\n[8] Browser will stay open for inspection...")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    =====================================
    Flutter Login - Button Click Method
    =====================================
    Site: http://it.mek-ics.com/msm
    Strategy: Find and click login button
    =====================================
    """)
    
    asyncio.run(flutter_login_with_button_click())
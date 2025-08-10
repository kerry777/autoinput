#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter Web App 로그인 테스트
Flutter는 Canvas 기반이라 일반 셀렉터로 접근 불가
좌표 기반 클릭과 키보드 입력 사용
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_flutter_login():
    """Flutter 웹앱 로그인 - 좌표 기반 접근"""
    
    print("\n" + "="*50)
    print("[FLUTTER APP LOGIN TEST]")
    print("="*50)
    print("\nFlutter apps use Canvas rendering")
    print("Using coordinate-based interaction")
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000  # 천천히 동작
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드
            print("\n[STEP 1] Loading Flutter app...")
            await page.goto("http://it.mek-ics.com/msm")
            
            # Flutter 앱 로딩 대기 (Canvas 렌더링 시간)
            print("[WAIT] Waiting for Flutter to render...")
            await page.wait_for_timeout(5000)  # 5초 대기
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/flutter/initial_{timestamp}.png")
            
            # 2. Canvas 요소 찾기
            print("\n[STEP 2] Looking for Flutter canvas...")
            canvas = await page.query_selector('flt-glass-pane')
            if not canvas:
                canvas = await page.query_selector('canvas')
            
            if canvas:
                print("[OK] Flutter rendering element found")
                
                # Canvas 위치와 크기 확인
                box = await canvas.bounding_box()
                if box:
                    print(f"[CANVAS] Position: x={box['x']}, y={box['y']}")
                    print(f"[CANVAS] Size: {box['width']}x{box['height']}")
            
            # 3. 화면 중앙 근처에서 로그인 필드 추정
            print("\n[STEP 3] Estimating login field positions...")
            
            # 화면 크기 가져오기
            viewport = page.viewport_size
            center_x = viewport['width'] // 2
            center_y = viewport['height'] // 2
            
            # 일반적인 로그인 폼 위치 (화면 중앙)
            # Flutter 앱은 보통 중앙 정렬
            username_y = center_y - 50  # ID 필드는 보통 위쪽
            password_y = center_y + 20  # PW 필드는 아래쪽
            button_y = center_y + 100   # 버튼은 더 아래
            
            print(f"[ESTIMATE] Username field: ({center_x}, {username_y})")
            print(f"[ESTIMATE] Password field: ({center_x}, {password_y})")
            print(f"[ESTIMATE] Login button: ({center_x}, {button_y})")
            
            # 4. 첫 번째 필드 클릭 (Username)
            print("\n[STEP 4] Clicking username field...")
            await page.mouse.click(center_x, username_y)
            await page.wait_for_timeout(500)
            
            # 기존 텍스트 전체 선택 후 입력
            await page.keyboard.press('Control+A')
            await page.keyboard.type('mdmtest')
            print("[INPUT] Typed: mdmtest")
            
            # 5. Tab 키로 다음 필드로 이동
            print("\n[STEP 5] Moving to password field...")
            await page.keyboard.press('Tab')
            await page.wait_for_timeout(500)
            
            # Password 입력
            await page.keyboard.type('0001')
            print("[INPUT] Typed: ****")
            
            # 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/filled_{timestamp}.png")
            print("[SCREENSHOT] After input")
            
            # 6. Enter 키로 로그인 시도
            print("\n[STEP 6] Attempting login...")
            await page.keyboard.press('Enter')
            
            # 또는 로그인 버튼 클릭 시도
            # await page.mouse.click(center_x, button_y)
            
            print("[WAIT] Waiting for response...")
            await page.wait_for_timeout(3000)
            
            # 7. 결과 확인
            new_url = page.url
            print(f"\n[RESULT] Current URL: {new_url}")
            
            if new_url != "http://it.mek-ics.com/msm/":
                print("[SUCCESS] URL changed - Login might be successful!")
            
            # 최종 스크린샷
            await page.screenshot(path=f"logs/screenshots/flutter/result_{timestamp}.png")
            
            # 8. 대체 방법: 직접 좌표 클릭
            print("\n[ALTERNATIVE] You can also try manual coordinates:")
            print("1. Take a screenshot")
            print("2. Find exact coordinates of fields")
            print("3. Use page.mouse.click(x, y) with exact coordinates")
            
            # Visual helper - 클릭 가능한 영역 표시
            print("\n[VISUAL] Clicking some test points...")
            test_points = [
                (center_x - 100, center_y),
                (center_x, center_y),
                (center_x + 100, center_y),
            ]
            
            for x, y in test_points:
                await page.mouse.move(x, y)
                await page.wait_for_timeout(200)
            
            print("\n[INFO] Browser will stay open for manual testing...")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

async def find_exact_coordinates():
    """스크린샷을 찍고 정확한 좌표 찾기 도우미"""
    
    print("\n[HELPER] Taking screenshot for coordinate mapping...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("http://it.mek-ics.com/msm")
        await page.wait_for_timeout(5000)
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"logs/screenshots/flutter/coordinate_helper_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        
        print(f"[SAVED] {screenshot_path}")
        print("\nOpen this image and find the exact coordinates of:")
        print("1. Username field")
        print("2. Password field")
        print("3. Login button")
        print("\nThen update the coordinates in the test script")
        
        await browser.close()

if __name__ == "__main__":
    print("""
    ============================================
         Flutter Web App Login Test
    ============================================
    Site: http://it.mek-ics.com/msm
    Method: Coordinate-based interaction
    ============================================
    """)
    
    # 먼저 좌표 찾기 도우미 실행 (선택사항)
    # asyncio.run(find_exact_coordinates())
    
    # 메인 테스트 실행
    asyncio.run(test_flutter_login())
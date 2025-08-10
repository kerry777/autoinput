#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 웹앱 로그인 테스트 - Placeholder 텍스트 활용
Flutter Canvas에서도 접근성을 위해 aria-label이나 placeholder가 존재할 수 있음
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_flutter_placeholder_login():
    """Flutter 웹앱 로그인 - Placeholder 텍스트로 필드 찾기"""
    
    print("\n" + "="*50)
    print("[FLUTTER PLACEHOLDER LOGIN TEST]")
    print("="*50)
    print("\nTrying to find input fields by placeholder text")
    print("Looking for 'id' and 'password' placeholders")
    
    os.makedirs("logs/screenshots/flutter", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500  # 동작 확인용
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # 1. 페이지 로드
            print("\n[STEP 1] Loading Flutter app...")
            await page.goto("http://it.mek-ics.com/msm")
            
            # Flutter 앱 로딩 대기
            print("[WAIT] Waiting for Flutter to render...")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/flutter/placeholder_initial_{timestamp}.png")
            
            # 2. HTML 구조 분석
            print("\n[STEP 2] Analyzing page structure...")
            
            # 모든 input 요소 찾기
            inputs = await page.query_selector_all('input')
            print(f"[FOUND] {len(inputs)} input elements")
            
            # 각 input의 속성 확인
            for i, input_elem in enumerate(inputs):
                placeholder = await input_elem.get_attribute('placeholder')
                aria_label = await input_elem.get_attribute('aria-label')
                input_type = await input_elem.get_attribute('type')
                name = await input_elem.get_attribute('name')
                id_attr = await input_elem.get_attribute('id')
                
                print(f"\n[INPUT {i+1}]")
                if placeholder:
                    print(f"  - placeholder: {placeholder}")
                if aria_label:
                    print(f"  - aria-label: {aria_label}")
                if input_type:
                    print(f"  - type: {input_type}")
                if name:
                    print(f"  - name: {name}")
                if id_attr:
                    print(f"  - id: {id_attr}")
            
            # 3. Placeholder로 필드 찾기 시도
            print("\n[STEP 3] Trying to find fields by placeholder...")
            
            # 다양한 placeholder 패턴 시도
            id_patterns = [
                'input[placeholder*="id" i]',
                'input[placeholder*="ID" i]',
                'input[placeholder*="아이디" i]',
                'input[placeholder*="username" i]',
                'input[placeholder*="사용자" i]',
                'input[type="text"]',
                'input:not([type="password"])'
            ]
            
            password_patterns = [
                'input[placeholder*="password" i]',
                'input[placeholder*="pw" i]',
                'input[placeholder*="비밀번호" i]',
                'input[placeholder*="패스워드" i]',
                'input[type="password"]'
            ]
            
            id_field = None
            password_field = None
            
            # ID 필드 찾기
            for pattern in id_patterns:
                try:
                    elem = await page.query_selector(pattern)
                    if elem and await elem.is_visible():
                        id_field = elem
                        print(f"[OK] ID field found with: {pattern}")
                        break
                except:
                    continue
            
            # Password 필드 찾기
            for pattern in password_patterns:
                try:
                    elem = await page.query_selector(pattern)
                    if elem and await elem.is_visible():
                        password_field = elem
                        print(f"[OK] Password field found with: {pattern}")
                        break
                except:
                    continue
            
            # 4. 필드에 입력
            if id_field and password_field:
                print("\n[STEP 4] Filling login form...")
                
                # ID 입력
                await id_field.click()
                await id_field.fill('mdmtest')
                print("[INPUT] ID: mdmtest")
                
                # Password 입력
                await password_field.click()
                await password_field.fill('0001')
                print("[INPUT] Password: ****")
                
                await page.screenshot(path=f"logs/screenshots/flutter/placeholder_filled_{timestamp}.png")
                
                # 5. 로그인 시도
                print("\n[STEP 5] Attempting login...")
                
                # Enter 키로 제출
                await password_field.press('Enter')
                
                # 또는 로그인 버튼 찾기
                login_button_patterns = [
                    'button:has-text("로그인")',
                    'button:has-text("Login")',
                    'button:has-text("Sign in")',
                    'button[type="submit"]',
                    'input[type="submit"]'
                ]
                
                for pattern in login_button_patterns:
                    try:
                        button = await page.query_selector(pattern)
                        if button and await button.is_visible():
                            await button.click()
                            print(f"[CLICK] Login button found: {pattern}")
                            break
                    except:
                        continue
                
                await page.wait_for_timeout(3000)
                
                # 6. 결과 확인
                new_url = page.url
                print(f"\n[RESULT] Current URL: {new_url}")
                
                await page.screenshot(path=f"logs/screenshots/flutter/placeholder_result_{timestamp}.png")
                
            else:
                print("\n[FAILED] Could not find login fields by placeholder")
                print("[INFO] Falling back to coordinate-based approach might be needed")
                
                # 대체 방법: aria-label로 시도
                print("\n[ALTERNATIVE] Trying aria-label...")
                
                id_by_aria = await page.query_selector('[aria-label*="id" i], [aria-label*="username" i]')
                pw_by_aria = await page.query_selector('[aria-label*="password" i], [aria-label*="pw" i]')
                
                if id_by_aria and pw_by_aria:
                    print("[OK] Found fields by aria-label")
                    await id_by_aria.fill('mdmtest')
                    await pw_by_aria.fill('0001')
                    await pw_by_aria.press('Enter')
                else:
                    print("[INFO] aria-label approach also failed")
            
            # 7. DOM 구조 덤프 (디버깅용)
            print("\n[DEBUG] Checking page accessibility tree...")
            
            # 접근성 트리 확인
            accessibility_tree = await page.accessibility.snapshot()
            if accessibility_tree:
                print("[INFO] Accessibility tree available")
                # 입력 필드 관련 노드 찾기
                def find_inputs(node, depth=0):
                    if node.get('role') in ['textbox', 'searchbox', 'combobox']:
                        print(f"{'  ' * depth}[{node.get('role')}] {node.get('name', 'unnamed')}")
                    for child in node.get('children', []):
                        find_inputs(child, depth + 1)
                
                find_inputs(accessibility_tree)
            
            print("\n[INFO] Keeping browser open for manual inspection...")
            await page.wait_for_timeout(15000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

async def analyze_flutter_dom():
    """Flutter DOM 구조 상세 분석"""
    
    print("\n[ANALYZER] Deep DOM structure analysis...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto("http://it.mek-ics.com/msm")
        await page.wait_for_timeout(5000)
        
        # 전체 HTML 덤프
        html_content = await page.content()
        
        # 로그 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"logs/flutter_dom_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"[SAVED] DOM structure to logs/flutter_dom_{timestamp}.html")
        
        # JavaScript로 모든 input 찾기
        inputs_info = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, textarea, [contenteditable="true"]');
                return Array.from(inputs).map(input => ({
                    tagName: input.tagName,
                    type: input.type,
                    placeholder: input.placeholder,
                    ariaLabel: input.getAttribute('aria-label'),
                    name: input.name,
                    id: input.id,
                    className: input.className,
                    visible: input.offsetParent !== null,
                    position: {
                        x: input.getBoundingClientRect().x,
                        y: input.getBoundingClientRect().y
                    }
                }));
            }
        """)
        
        print(f"\n[FOUND] {len(inputs_info)} input-like elements:")
        for i, info in enumerate(inputs_info):
            print(f"\nElement {i+1}:")
            for key, value in info.items():
                if value:
                    print(f"  {key}: {value}")
        
        await browser.close()

if __name__ == "__main__":
    print("""
    ============================================
      Flutter Login - Placeholder Method
    ============================================
    Target: http://it.mek-ics.com/msm
    Strategy: Find fields by placeholder text
    ============================================
    """)
    
    # DOM 분석 먼저 실행 (선택사항)
    # asyncio.run(analyze_flutter_dom())
    
    # 메인 테스트 실행
    asyncio.run(test_flutter_placeholder_login())
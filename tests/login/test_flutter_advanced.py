#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flutter 고급 로그인 테스트 - 여러 방법 시도
1. Semantic 요소 찾기
2. Flutter 특수 요소 찾기  
3. OCR 기반 접근 (텍스트 인식)
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_flutter_advanced():
    """Flutter 고급 접근 방법"""
    
    print("\n" + "="*50)
    print("[FLUTTER ADVANCED LOGIN TEST]")
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
            print("\n[STEP 1] Loading Flutter app...")
            await page.goto("http://it.mek-ics.com/msm")
            await page.wait_for_timeout(5000)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 2. Flutter semantics 요소 찾기
            print("\n[STEP 2] Looking for Flutter semantic elements...")
            
            # Flutter는 접근성을 위해 flt-semantics 요소 사용
            semantics = await page.query_selector_all('flt-semantics, [role="textbox"], [role="button"]')
            print(f"[FOUND] {len(semantics)} semantic elements")
            
            for i, elem in enumerate(semantics):
                role = await elem.get_attribute('role')
                aria_label = await elem.get_attribute('aria-label')
                if role or aria_label:
                    print(f"  Element {i+1}: role={role}, aria-label={aria_label}")
            
            # 3. Flutter 특수 클래스 찾기
            print("\n[STEP 3] Checking Flutter-specific elements...")
            
            flutter_elements = await page.evaluate("""
                () => {
                    // Flutter 관련 요소들
                    const elements = document.querySelectorAll('[class*="flt-"], flt-glass-pane, flt-scene, flt-semantics-placeholder');
                    const result = [];
                    
                    elements.forEach(elem => {
                        // 클릭 가능한 요소인지 확인
                        const isClickable = elem.style.cursor === 'pointer' || 
                                          elem.style.pointerEvents !== 'none';
                        
                        result.push({
                            tag: elem.tagName,
                            className: elem.className,
                            clickable: isClickable,
                            hasText: elem.textContent?.trim().length > 0,
                            position: {
                                x: elem.getBoundingClientRect().x,
                                y: elem.getBoundingClientRect().y,
                                width: elem.getBoundingClientRect().width,
                                height: elem.getBoundingClientRect().height
                            }
                        });
                    });
                    
                    return result;
                }
            """)
            
            print(f"[FOUND] {len(flutter_elements)} Flutter elements")
            clickable_elements = [e for e in flutter_elements if e.get('clickable')]
            print(f"[CLICKABLE] {len(clickable_elements)} clickable elements")
            
            # 4. 텍스트 기반 요소 찾기
            print("\n[STEP 4] Looking for text-containing elements...")
            
            # ID나 Password 텍스트를 포함하는 요소 찾기
            text_elements = await page.evaluate("""
                () => {
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    const texts = [];
                    let node;
                    
                    while(node = walker.nextNode()) {
                        const text = node.textContent.trim().toLowerCase();
                        if (text && (text.includes('id') || text.includes('password') || 
                                    text.includes('아이디') || text.includes('비밀번호'))) {
                            const parent = node.parentElement;
                            const rect = parent.getBoundingClientRect();
                            texts.push({
                                text: text,
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            });
                        }
                    }
                    
                    return texts;
                }
            """)
            
            if text_elements:
                print(f"[FOUND] Text elements containing login keywords:")
                for elem in text_elements:
                    print(f"  - '{elem['text']}' at ({elem['x']}, {elem['y']})")
                
                # 텍스트 근처 클릭 시도
                if len(text_elements) >= 1:
                    # ID 필드 근처 클릭 (텍스트 오른쪽)
                    id_elem = text_elements[0]
                    await page.mouse.click(id_elem['x'] + 100, id_elem['y'])
                    await page.keyboard.type('mdmtest')
                    print("[INPUT] Typed ID near text label")
                    
                    if len(text_elements) >= 2:
                        # Password 필드 근처 클릭
                        pw_elem = text_elements[1]
                        await page.mouse.click(pw_elem['x'] + 100, pw_elem['y'])
                        await page.keyboard.type('0001')
                        print("[INPUT] Typed password near text label")
            
            # 5. 키보드 네비게이션 시도
            print("\n[STEP 5] Trying keyboard navigation...")
            
            # Tab 키로 포커스 이동 시도
            for i in range(10):
                await page.keyboard.press('Tab')
                await page.wait_for_timeout(200)
                
                # 현재 포커스된 요소 확인
                focused = await page.evaluate("() => document.activeElement?.tagName")
                if focused:
                    print(f"  Tab {i+1}: Focused on {focused}")
                    
                    # input 같은 요소면 입력 시도
                    if i == 0:  # 첫 번째 필드
                        await page.keyboard.type('mdmtest')
                    elif i == 1:  # 두 번째 필드
                        await page.keyboard.type('0001')
            
            # 6. Flutter 디버그 정보 수집
            print("\n[STEP 6] Collecting Flutter debug info...")
            
            flutter_info = await page.evaluate("""
                () => {
                    // Flutter 전역 객체 확인
                    return {
                        hasFlutter: typeof window.flutter !== 'undefined',
                        flutterVersion: window.flutter?.version,
                        hasFlutterEngine: typeof window.flutterEngine !== 'undefined',
                        hasDartSdk: typeof window.dart !== 'undefined'
                    };
                }
            """)
            
            print("[FLUTTER INFO]")
            for key, value in flutter_info.items():
                print(f"  {key}: {value}")
            
            # 7. 스크린샷과 함께 좌표 매핑
            print("\n[STEP 7] Taking screenshot with coordinate grid...")
            
            # 그리드 오버레이 추가 (디버깅용)
            await page.evaluate("""
                () => {
                    const canvas = document.createElement('canvas');
                    canvas.style.position = 'fixed';
                    canvas.style.top = '0';
                    canvas.style.left = '0';
                    canvas.style.width = '100%';
                    canvas.style.height = '100%';
                    canvas.style.pointerEvents = 'none';
                    canvas.style.zIndex = '9999';
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;
                    
                    const ctx = canvas.getContext('2d');
                    ctx.strokeStyle = 'red';
                    ctx.lineWidth = 1;
                    
                    // 100px 간격 그리드
                    for(let x = 0; x < canvas.width; x += 100) {
                        ctx.beginPath();
                        ctx.moveTo(x, 0);
                        ctx.lineTo(x, canvas.height);
                        ctx.stroke();
                        
                        ctx.fillStyle = 'red';
                        ctx.fillText(x.toString(), x + 5, 20);
                    }
                    
                    for(let y = 0; y < canvas.height; y += 100) {
                        ctx.beginPath();
                        ctx.moveTo(0, y);
                        ctx.lineTo(canvas.width, y);
                        ctx.stroke();
                        
                        ctx.fillStyle = 'red';
                        ctx.fillText(y.toString(), 5, y + 15);
                    }
                    
                    document.body.appendChild(canvas);
                }
            """)
            
            await page.screenshot(path=f"logs/screenshots/flutter/grid_{timestamp}.png")
            print(f"[SAVED] Grid screenshot for coordinate mapping")
            
            # 그리드 제거
            await page.evaluate("() => document.querySelector('canvas')?.remove()")
            
            print("\n[INFO] Browser will stay open for manual testing...")
            print("[TIP] Use the grid screenshot to find exact coordinates")
            await page.wait_for_timeout(20000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    ============================================
      Flutter Advanced Login Analysis
    ============================================
    Multiple strategies:
    1. Semantic elements detection
    2. Flutter-specific elements
    3. Text-based positioning
    4. Keyboard navigation
    5. Coordinate grid mapping
    ============================================
    """)
    
    asyncio.run(test_flutter_advanced())
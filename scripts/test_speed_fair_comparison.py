#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Headless vs Browser 공정한 속도 비교
동일한 slow_mo 설정으로 순수한 렌더링 차이만 측정
"""

import asyncio
from playwright.async_api import async_playwright
import time
import os

async def test_simple_operations(headless=True):
    """간단한 작업들로 속도 차이 측정"""
    
    mode = "Headless" if headless else "Browser"
    print(f"\n{'='*50}")
    print(f"  {mode} 모드 - 간단한 작업 테스트")
    print(f"{'='*50}")
    
    operations_time = []
    
    async with async_playwright() as p:
        # 동일한 slow_mo 설정
        browser = await p.chromium.launch(
            headless=headless,
            slow_mo=100  # 동일하게 설정
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        try:
            # 1. 여러 페이지 빠르게 방문
            sites = [
                "https://www.google.com",
                "https://www.naver.com",
                "https://www.daum.net"
            ]
            
            navigation_start = time.time()
            for site in sites:
                await page.goto(site, wait_until='domcontentloaded', timeout=30000)
                await page.wait_for_timeout(500)
            navigation_time = time.time() - navigation_start
            operations_time.append(("페이지 네비게이션 (3개)", navigation_time))
            
            # 2. DOM 조작
            dom_start = time.time()
            await page.goto("https://www.google.com", wait_until='domcontentloaded')
            
            # 여러 번 DOM 요소 찾기
            for i in range(10):
                await page.query_selector('input[type="text"]')
                await page.query_selector_all('a')
                await page.query_selector_all('button')
            dom_time = time.time() - dom_start
            operations_time.append(("DOM 조작 (30회)", dom_time))
            
            # 3. 스크린샷
            screenshot_start = time.time()
            for i in range(3):
                await page.screenshot()
            screenshot_time = time.time() - screenshot_start
            operations_time.append(("스크린샷 (3장)", screenshot_time))
            
            # 4. JavaScript 실행
            js_start = time.time()
            for i in range(20):
                await page.evaluate('() => document.querySelectorAll("*").length')
                await page.evaluate('() => window.innerWidth')
                await page.evaluate('() => document.title')
            js_time = time.time() - js_start
            operations_time.append(("JavaScript 실행 (60회)", js_time))
            
        except Exception as e:
            print(f"에러: {str(e)}")
            
        finally:
            await browser.close()
    
    return operations_time

async def main():
    """공정한 속도 비교"""
    print("""
    ============================================
       Headless vs Browser 공정한 속도 비교
    ============================================
    동일한 slow_mo 설정으로 순수한 렌더링 
    성능 차이를 측정합니다.
    ============================================
    """)
    
    # Browser 모드 테스트
    print("\n[1/2] Browser 모드 테스트...")
    browser_start = time.time()
    browser_results = await test_simple_operations(headless=False)
    browser_total = time.time() - browser_start
    
    print("\n잠시 대기...")
    await asyncio.sleep(3)
    
    # Headless 모드 테스트
    print("\n[2/2] Headless 모드 테스트...")
    headless_start = time.time()
    headless_results = await test_simple_operations(headless=True)
    headless_total = time.time() - headless_start
    
    # 결과 분석
    print("\n" + "="*60)
    print("   상세 비교 결과")
    print("="*60)
    
    print("\n작업별 소요 시간:")
    print("-" * 50)
    print(f"{'작업':<25} {'Browser':>10} {'Headless':>10} {'차이':>10}")
    print("-" * 50)
    
    for i, (task_name, browser_time) in enumerate(browser_results):
        if i < len(headless_results):
            headless_time = headless_results[i][1]
            diff = browser_time - headless_time
            diff_percent = (diff / browser_time * 100) if browser_time > 0 else 0
            print(f"{task_name:<25} {browser_time:>8.2f}초 {headless_time:>8.2f}초 {diff_percent:>8.1f}%")
    
    print("-" * 50)
    print(f"{'전체 시간':<25} {browser_total:>8.2f}초 {headless_total:>8.2f}초")
    
    # 총 분석
    print("\n" + "="*60)
    print("   총 분석 결과")
    print("="*60)
    
    time_saved = browser_total - headless_total
    speedup_percent = (time_saved / browser_total * 100) if browser_total > 0 else 0
    
    print(f"Browser 모드 총 시간:  {browser_total:.2f}초")
    print(f"Headless 모드 총 시간: {headless_total:.2f}초")
    print(f"\n절약된 시간: {time_saved:.2f}초")
    print(f"속도 향상: {speedup_percent:.1f}%")
    
    if headless_total < browser_total:
        speedup_ratio = browser_total / headless_total
        print(f"Headless가 {speedup_ratio:.2f}배 빠름")
    
    print("\n" + "="*60)
    print("결론:")
    print("- UI 렌더링이 많은 작업일수록 Headless가 유리")
    print("- 네트워크 대기가 긴 작업은 차이가 적음")
    print("- 스크린샷, DOM 조작 등에서 차이 발생")
    print("- 실제 장기요양보험 사이트는 네트워크 대기가 길어 차이 적음")

if __name__ == "__main__":
    asyncio.run(main())
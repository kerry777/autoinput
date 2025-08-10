#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPT5 솔루션 자동 테스트
"""

import asyncio
import os
from playwright.async_api import async_playwright

async def test_gpt5_solution():
    """GPT5 솔루션 자동 테스트"""
    
    print("\n[GPT5 솔루션 자동 테스트]")
    print("="*60)
    print("분석 결과:")
    print("1. 스텔스 스크립트가 오히려 탐지 신호가 됨")
    print("2. 영구 프로필로 세션 유지가 핵심")
    print("3. 최소 설정이 최선의 전략")
    print("="*60)
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\gpt5_minimal"
    os.makedirs(profile_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # GPT5 핵심: 아무 플래그 없이 영구 프로필만 사용
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 탐지 확인
        print("\n[브라우저 속성]")
        check = await page.evaluate("""
            () => ({
                webdriver: navigator.webdriver,
                automation: navigator.automation,
                chrome: !!window.chrome,
                plugins: navigator.plugins.length
            })
        """)
        
        for key, value in check.items():
            print(f"- {key}: {value}")
        
        # 로그인
        print("\n[로그인 시도]")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(2000)
        
        if await page.locator("#username").count() > 0:
            await page.fill("#username", "kilmoon@mek-ics.com")
            await page.fill("#password", "moon7410!@")
            await page.click("#btnSubmit")
            await page.wait_for_timeout(5000)
            
            url = page.url
            print(f"\n결과 URL: {url}")
            
            if "secondStep" in url:
                print("\n[예상대로 2FA 트리거]")
                print("GPT5 설명: 첫 실행시 2FA는 정상")
                print("프로필에 세션 저장 후 재사용시 감소")
            else:
                print("\n[2FA 없이 통과!]")
        
        print(f"\n프로필 저장 위치: {profile_dir}")
        print("브라우저는 20초 후 종료...")
        await page.wait_for_timeout(20000)
        await context.close()

if __name__ == "__main__":
    asyncio.run(test_gpt5_solution())
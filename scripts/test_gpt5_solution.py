#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPT5 솔루션 테스트 - 영구 프로필 방식
"""

import asyncio
import os
from playwright.async_api import async_playwright
import time

async def test_gpt5_approach():
    """GPT5가 제안한 방식 테스트"""
    
    print("\n[GPT5 솔루션 테스트]")
    print("="*60)
    print("핵심: 스텔스 제거 + 영구 프로필 사용")
    print("="*60)
    
    # 영구 프로필 디렉토리
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\gpt5_test"
    os.makedirs(profile_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # GPT5 권장: 최소 설정으로 영구 프로필 사용
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
            # 스텔스 플래그 없음 - GPT5 핵심 포인트
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 탐지 상태 확인
        print("\n[1] 브라우저 속성 확인")
        detection = await page.evaluate("""
            () => {
                return {
                    webdriver: navigator.webdriver,
                    chrome: !!window.chrome,
                    plugins: navigator.plugins.length,
                    automation: window.navigator.automation
                };
            }
        """)
        print(f"- webdriver: {detection['webdriver']}")
        print(f"- chrome: {detection['chrome']}")
        print(f"- plugins: {detection['plugins']}")
        print(f"- automation: {detection['automation']}")
        
        # 로그인 페이지
        print("\n[2] 로그인 페이지 이동")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        # 로그인 시도
        print("\n[3] 로그인 시도")
        if await page.locator("#username").count() > 0:
            await page.fill("#username", "kilmoon@mek-ics.com")
            await page.fill("#password", "moon7410!@")
            await page.click("#btnSubmit")
            
            print("로그인 제출 완료, 결과 대기...")
            await page.wait_for_timeout(5000)
            
            # 결과 확인
            current_url = page.url
            print(f"\n[4] 결과 URL: {current_url}")
            
            if "secondStep" in current_url:
                print("\n❌ 2차 인증 트리거됨")
                print("GPT5 솔루션도 첫 실행시 2FA 발생")
                print("\n[참고] GPT5 설명:")
                print("- 첫 실행시 2FA는 정상임")
                print("- 2FA 완료 후 프로필에 세션 저장됨")
                print("- 다음 실행부터는 2FA 빈도 감소")
                
                # 2FA 입력 대기
                print("\n수동으로 2FA를 완료하세요...")
                print("완료 후 Enter를 누르세요...")
                input()
                
            elif "loginForm" not in current_url:
                print("\n✅ 로그인 성공! (2FA 없음)")
                print("프로필이 신뢰받는 상태")
            else:
                print("\n⚠️ 로그인 실패 또는 재시도 필요")
        else:
            print("이미 로그인된 상태입니다")
            print(f"현재 URL: {page.url}")
        
        # 쿠키 확인
        cookies = await context.cookies()
        print(f"\n[5] 저장된 쿠키 수: {len(cookies)}")
        
        # 프로필 정보
        print(f"\n[6] 프로필 경로: {profile_dir}")
        print("다음 실행시 이 프로필이 재사용됩니다")
        
        print("\n브라우저는 30초 후 종료됩니다...")
        await page.wait_for_timeout(30000)
        
        await context.close()

async def test_second_run():
    """두 번째 실행 테스트 (프로필 재사용)"""
    
    print("\n[두 번째 실행 - 프로필 재사용]")
    print("="*60)
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\gpt5_test"
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 직접 서비스 페이지로
        print("서비스 페이지로 직접 이동...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        current_url = page.url
        print(f"현재 URL: {current_url}")
        
        if "loginForm" not in current_url:
            print("\n✅ 세션 유지됨! 자동 로그인 성공")
        else:
            print("\n세션 만료, 재로그인 필요")
        
        await page.wait_for_timeout(10000)
        await context.close()

async def main():
    print("\n무엇을 테스트하시겠습니까?")
    print("1. 첫 번째 실행 (새 프로필)")
    print("2. 두 번째 실행 (프로필 재사용)")
    
    choice = input("\n선택 (1/2): ")
    
    if choice == "1":
        await test_gpt5_approach()
    elif choice == "2":
        await test_second_run()
    else:
        print("잘못된 선택")

if __name__ == "__main__":
    asyncio.run(main())
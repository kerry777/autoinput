#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSRF & CAPTCHA 처리 자동 테스트
"""

import asyncio
import os
import json
import random
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

async def test_csrf_handling():
    """CSRF 토큰 처리 테스트"""
    
    print("\n[CSRF & CAPTCHA 처리 테스트]")
    print("="*60)
    
    profile_dir = "C:\\projects\\autoinput\\browser_profiles\\csrf_test"
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs("logs/csrf", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        # 로그인 페이지
        print("\n[1] 로그인 페이지 접속")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(2000)
        
        # 숨겨진 필드 추출
        print("\n[2] 보안 필드 분석")
        hidden_fields = await page.evaluate("""
            () => {
                const result = {};
                document.querySelectorAll('input[type="hidden"]').forEach(input => {
                    if (input.name) {
                        result[input.name] = input.value;
                    }
                });
                return result;
            }
        """)
        
        print("발견된 숨겨진 필드:")
        for name, value in hidden_fields.items():
            if 'CSRF' in name:
                print(f"  - {name}: {value[:30]}...")
            elif 'BDC' in name:
                print(f"  - {name}: {value}")
            else:
                print(f"  - {name}: [값 존재]")
        
        # CAPTCHA 확인
        print("\n[3] CAPTCHA 확인")
        captcha_info = await page.evaluate("""
            () => {
                const captchaImg = document.querySelector('img[src*="botdetectcaptcha"]');
                const vcidInput = document.querySelector('input[name*="BDC_VCID"]');
                const backInput = document.querySelector('input[name*="BDC_BackWorkaround"]');
                
                return {
                    hasImage: !!captchaImg,
                    imageUrl: captchaImg ? captchaImg.src : null,
                    vcid: vcidInput ? vcidInput.value : null,
                    backWorkaround: backInput ? backInput.value : null,
                    captchaElements: document.querySelectorAll('[id*="botCaptcha"], [class*="botdetect"]').length
                };
            }
        """)
        
        print(f"CAPTCHA 이미지: {'있음' if captcha_info['hasImage'] else '없음'}")
        print(f"CAPTCHA 요소 수: {captcha_info['captchaElements']}")
        if captcha_info['vcid']:
            print(f"VCID: {captcha_info['vcid']}")
        
        # 인간같은 타이핑 시뮬레이션
        print("\n[4] 인간같은 입력 패턴 적용")
        
        # Username 입력
        username_field = await page.query_selector('#username')
        if username_field:
            await username_field.click()
            await page.wait_for_timeout(random.randint(200, 400))
            
            # 한 글자씩 타이핑
            for char in 'kilmoon@mek-ics.com':
                await page.keyboard.type(char)
                if char == '@':
                    await page.wait_for_timeout(random.randint(150, 250))
                else:
                    await page.wait_for_timeout(random.randint(50, 100))
        
        # Password 입력
        await page.wait_for_timeout(random.randint(300, 600))
        password_field = await page.query_selector('#password')
        if password_field:
            await password_field.click()
            await page.wait_for_timeout(random.randint(200, 400))
            
            for char in 'moon7410!@':
                await page.keyboard.type(char)
                await page.wait_for_timeout(random.randint(50, 100))
        
        # 제출 전 최종 확인
        print("\n[5] 제출 전 최종 상태")
        final_fields = await page.evaluate("""
            () => {
                const csrf = document.querySelector('input[name="OWASP_CSRFTOKEN"]');
                return {
                    csrfToken: csrf ? csrf.value : null,
                    formAction: document.querySelector('form') ? document.querySelector('form').action : null
                };
            }
        """)
        
        if final_fields['csrfToken']:
            print(f"CSRF 토큰 준비: {final_fields['csrfToken'][:20]}...")
        
        # 로그인 제출
        print("\n[6] 로그인 제출")
        await page.wait_for_timeout(random.randint(500, 800))
        await page.click('#btnSubmit')
        
        # 결과 대기
        await page.wait_for_timeout(5000)
        
        # 결과 분석
        final_url = page.url
        print(f"\n[7] 결과")
        print(f"최종 URL: {final_url}")
        
        if 'secondStep' in final_url:
            print("→ 2차 인증 페이지 (예상된 결과)")
            
            # 2차 인증 페이지 분석
            second_captcha = await page.evaluate("""
                () => {
                    return {
                        captchaElements: document.querySelectorAll('[id*="botCaptcha"], [class*="botdetect"]').length,
                        hasOtpField: !!document.querySelector('input[type="text"][name*="otp"], input[type="text"][id*="otp"]')
                    };
                }
            """)
            
            print(f"2차 인증 CAPTCHA 요소: {second_captcha['captchaElements']}")
            print(f"OTP 필드: {'있음' if second_captcha['hasOtpField'] else '없음'}")
            
        elif 'main.do' in final_url:
            print("→ 로그인 성공! (세션 재사용)")
        else:
            print(f"→ 예상치 못한 페이지: {final_url}")
        
        # 로그 저장
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "hidden_fields": list(hidden_fields.keys()),
            "captcha_detected": captcha_info['hasImage'],
            "final_url": final_url
        }
        
        log_file = Path("logs/csrf") / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.write_text(
            json.dumps(log_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print(f"\n로그 저장: {log_file}")
        print("\n브라우저는 20초 후 종료됩니다...")
        await page.wait_for_timeout(20000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_csrf_handling())
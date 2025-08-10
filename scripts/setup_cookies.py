#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 쿠키 설정 스크립트
수동 로그인 후 쿠키 저장
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def setup_cookies():
    """수동 로그인 후 쿠키 저장"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()
        
        try:
            print("="*60)
            print("Bizmeka 수동 로그인 및 쿠키 저장")
            print("="*60)
            print("1. 브라우저가 열리면 수동으로 로그인하세요")
            print("2. 2차 인증까지 완료하세요") 
            print("3. 메인 페이지에 도착하면 'y'를 입력하세요")
            print("-"*60)
            
            # 로그인 페이지로 이동
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            await page.wait_for_timeout(2000)
            
            print("\n로그인 진행 중... 완료되면 아래에 입력하세요")
            
            while True:
                try:
                    user_input = input("로그인 완료했나요? (y/n): ").strip().lower()
                    
                    if user_input == 'y':
                        # 쿠키 저장
                        cookies = await context.cookies()
                        
                        # 저장 경로 생성
                        cookie_dir = Path("sites/bizmeka/data")
                        cookie_dir.mkdir(parents=True, exist_ok=True)
                        
                        cookie_file = cookie_dir / "cookies.json"
                        with open(cookie_file, 'w', encoding='utf-8') as f:
                            json.dump(cookies, f, indent=2)
                        
                        print(f"✅ 쿠키 저장 완료: {len(cookies)}개")
                        print(f"   파일: {cookie_file}")
                        break
                    
                    elif user_input == 'n':
                        print("❌ 로그인이 취소되었습니다")
                        break
                    
                    else:
                        print("y 또는 n을 입력해주세요")
                        continue
                        
                except KeyboardInterrupt:
                    print("\n❌ 사용자에 의해 중단됨")
                    break
                except Exception as e:
                    print(f"❌ 입력 처리 오류: {e}")
                    break
        
        except Exception as e:
            print(f"오류: {e}")
        
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(setup_cookies())
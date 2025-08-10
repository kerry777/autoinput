#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
수동 로그인 모듈
- 브라우저 실행
- 수동 로그인 대기
- 쿠키 수집 및 저장
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import setup_logging, print_banner


async def manual_login():
    """수동 로그인 프로세스"""
    
    # 배너 출력
    print_banner("MANUAL LOGIN")
    
    # 설정 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 로깅 설정
    logger = setup_logging('manual_login')
    
    # 쿠키 매니저
    cookie_manager = CookieManager()
    
    print("\n[안내]")
    print("1. 브라우저가 열립니다")
    print("2. 수동으로 로그인하세요")
    print(f"   ID: {config['credentials']['username']}")
    print(f"   PW: {config['credentials']['password']}")
    print("3. 2차 인증을 완료하세요")
    print("4. 메인 페이지가 보이면 Enter를 누르세요")
    print("\n준비되면 Enter를 누르세요...")
    input()
    
    async with async_playwright() as p:
        # 영구 프로필로 브라우저 실행
        logger.info("브라우저 실행")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=config['paths']['profile'],
            headless=config['settings']['headless'],
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone']
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        
        # 로그인 페이지로 이동
        logger.info(f"로그인 페이지 이동: {config['urls']['login']}")
        await page.goto(config['urls']['login'])
        
        print("\n" + "="*60)
        print("브라우저에서 로그인을 완료하세요")
        print("="*60)
        print("[CHECK] '로그인 상태 유지' 체크박스를 확인하세요!")
        print("[CHECK] 2차 인증까지 완료하세요!")
        print("\n완료 후 Enter를 누르세요...")
        input()
        
        # 메인 페이지로 이동하여 세션 확인
        logger.info("세션 확인")
        await page.goto(config['urls']['main'])
        await page.wait_for_timeout(config['settings']['wait_time'])
        
        current_url = page.url
        
        # 로그인 성공 확인
        if 'loginForm' not in current_url and 'secondStep' not in current_url:
            print("\n[OK] 로그인 성공!")
            
            # 쿠키 수집
            logger.info("쿠키 수집")
            cookies = await browser.cookies()
            
            # 쿠키 저장
            if cookie_manager.save_cookies(cookies):
                logger.info(f"쿠키 {len(cookies)}개 저장 완료")
                
                # 세션 ID 확인
                session_id = cookie_manager.get_session_id()
                if session_id:
                    print(f"세션 ID: {session_id[:30]}...")
                
                print("\n" + "="*60)
                print("[OK] 설정 완료!")
                print("이제 auto_access.py를 실행하면 자동 로그인됩니다.")
                print("="*60)
            else:
                logger.error("쿠키 저장 실패")
                print("\n[ERROR] 쿠키 저장 실패")
        else:
            logger.warning(f"로그인 미완료: {current_url}")
            print("\n[ERROR] 로그인이 완료되지 않았습니다")
            print("다시 시도해주세요")
        
        # 브라우저 종료
        await page.wait_for_timeout(5000)
        await browser.close()


def main():
    """메인 함수"""
    try:
        asyncio.run(manual_login())
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
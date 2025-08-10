#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 접속 모듈
- 저장된 쿠키로 자동 로그인
- 2FA 없이 바로 접속
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


async def auto_access():
    """자동 접속 프로세스"""
    
    # 배너 출력
    print_banner("AUTO ACCESS")
    
    # 설정 로드
    config = load_config()
    
    # 로깅 설정
    logger = setup_logging('auto_access')
    
    # 쿠키 매니저
    cookie_manager = CookieManager()
    
    # 쿠키 확인
    if not Path(cookie_manager.cookie_path).exists():
        print_status('error', '쿠키 파일이 없습니다')
        print("\n먼저 manual_login.py를 실행하여 로그인하세요:")
        print("  python manual_login.py")
        return False
    
    # 쿠키 로드
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print_status('error', '쿠키 로드 실패')
        return False
    
    print_status('success', f'쿠키 {len(cookies)}개 로드됨')
    
    # 쿠키 유효성 간단 체크
    print_status('info', '쿠키 로드 완료')
    
    # 세션 ID 확인
    session_id = cookie_manager.get_session_id()
    if session_id:
        print_status('info', f'세션 ID: {session_id[:30]}...')
    
    async with async_playwright() as p:
        # 브라우저 실행
        logger.info("브라우저 실행")
        print_status('info', '브라우저 실행 중...')
        
        browser = await p.chromium.launch(
            headless=config['settings']['headless']
        )
        
        # 컨텍스트 생성
        context = await browser.new_context(
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone']
        )
        
        # 쿠키 설정
        logger.info("쿠키 설정")
        await context.add_cookies(cookies)
        
        # 페이지 생성
        page = await context.new_page()
        
        # 메인 페이지로 이동
        logger.info(f"메인 페이지 접속: {config['urls']['main']}")
        print_status('info', '메인 페이지 접속 중...')
        
        try:
            await page.goto(config['urls']['main'])
            await page.wait_for_timeout(config['settings']['wait_time'])
            
            current_url = page.url
            logger.info(f"현재 URL: {current_url}")
            
            # 로그인 확인
            if 'loginForm' in current_url or 'secondStep' in current_url:
                logger.warning("로그인 필요")
                print_status('error', '세션이 만료되었습니다')
                print("\nmanual_login.py를 다시 실행하세요:")
                print("  python manual_login.py")
                
                await browser.close()
                return False
            
            # 성공
            logger.info("자동 접속 성공")
            print_status('success', '자동 접속 성공!')
            print(f"\n현재 페이지: {page.title()}")
            
            # 자동 갱신 옵션
            if config['settings'].get('auto_refresh', False):
                print_status('info', '세션 자동 갱신 활성화')
                
                # 주기적으로 페이지 새로고침 (세션 유지)
                refresh_interval = 60 * 10  # 10분
                print(f"\n{refresh_interval//60}분마다 세션 갱신")
                print("종료하려면 Ctrl+C를 누르세요...")
                
                try:
                    while True:
                        await page.wait_for_timeout(refresh_interval * 1000)
                        logger.info("세션 갱신")
                        await page.reload()
                        print_status('info', f'세션 갱신됨 - {page.title()}')
                except KeyboardInterrupt:
                    print("\n\n세션 유지 중단")
            else:
                # 대기
                print("\n브라우저를 사용하세요")
                print("종료하려면 Enter를 누르세요...")
                input()
            
            # 브라우저 종료
            await browser.close()
            return True
            
        except Exception as e:
            logger.error(f"접속 실패: {e}")
            print_status('error', f'접속 실패: {e}')
            await browser.close()
            return False


def main():
    """메인 함수"""
    try:
        success = asyncio.run(auto_access())
        
        if success:
            print("\n" + "="*60)
            print("[OK] 자동 접속 완료")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("[ERROR] 자동 접속 실패")
            print("="*60)
            
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
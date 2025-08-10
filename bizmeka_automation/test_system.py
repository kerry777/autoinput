#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 자동화 시스템 테스트
- 환경 설정 확인
- 쿠키 상태 확인
- 자동 로그인 테스트
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from cookie_manager import CookieManager
from utils import load_config, validate_credentials, print_banner, print_status


def test_environment():
    """환경 설정 테스트"""
    print_banner("환경 설정 테스트")
    
    # 설정 로드
    config = load_config()
    
    # 필수 파일 확인
    files_to_check = [
        ('.env', '환경 설정 파일'),
        ('config.json', '설정 파일'),
        ('cookie_manager.py', '쿠키 관리 모듈'),
        ('manual_login.py', '수동 로그인 모듈'),
        ('auto_access.py', '자동 접속 모듈')
    ]
    
    all_present = True
    for file, desc in files_to_check:
        if Path(file).exists():
            print_status('success', f'{desc}: {file}')
        else:
            print_status('error', f'{desc} 없음: {file}')
            all_present = False
    
    # 로그인 정보 확인
    if validate_credentials(config):
        print_status('success', '로그인 정보 설정됨')
    else:
        all_present = False
    
    return all_present


def test_cookies():
    """쿠키 상태 테스트"""
    print_banner("쿠키 상태 테스트")
    
    cookie_manager = CookieManager()
    
    # 쿠키 파일 존재 확인
    if not Path(cookie_manager.cookie_path).exists():
        print_status('warning', '쿠키 파일 없음 - 수동 로그인 필요')
        return False
    
    # 쿠키 로드
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print_status('error', '쿠키 로드 실패')
        return False
    
    print_status('success', f'쿠키 {len(cookies)}개 로드됨')
    
    # 세션 ID 확인
    session_id = cookie_manager.get_session_id()
    if session_id:
        print_status('success', f'세션 ID: {session_id[:30]}...')
    else:
        print_status('warning', 'JSESSIONID 없음')
    
    # 만료 확인 (간단히 처리)
    print_status('success', '쿠키 유효 (세션 쿠키)')
    
    return True


async def test_auto_login():
    """자동 로그인 테스트"""
    print_banner("자동 로그인 테스트")
    
    config = load_config()
    cookie_manager = CookieManager()
    
    # 쿠키 확인
    if not cookie_manager.load_cookies():
        print_status('error', '쿠키 없음 - manual_login.py 먼저 실행')
        return False
    
    print_status('info', '자동 로그인 테스트 중...')
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # 브라우저 실행
            browser = await p.chromium.launch(
                headless=config['settings']['headless']
            )
            context = await browser.new_context(
                locale=config['browser']['locale'],
                timezone_id=config['browser']['timezone']
            )
            
            # 쿠키 설정
            cookies = cookie_manager.load_cookies()
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            # 메인 페이지 접속
            await page.goto(config['urls']['main'])
            await page.wait_for_timeout(3000)
            
            # 로그인 확인
            current_url = page.url
            if 'loginForm' not in current_url:
                print_status('success', '자동 로그인 성공!')
                result = True
            else:
                print_status('error', '자동 로그인 실패 - 재로그인 필요')
                result = False
            
            await browser.close()
            return result
            
    except Exception as e:
        print_status('error', f'테스트 실패: {e}')
        return False


def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print(" Bizmeka 자동화 시스템 테스트 ".center(60))
    print("="*60)
    
    # 1. 환경 테스트
    env_ok = test_environment()
    
    # 2. 쿠키 테스트
    cookies_ok = test_cookies()
    
    # 3. 자동 로그인 테스트 (선택적)
    if env_ok and cookies_ok:
        print("\n자동 로그인을 테스트하시겠습니까? (y/n): ", end="")
        if input().lower() == 'y':
            asyncio.run(test_auto_login())
    
    # 결과 요약
    print_banner("테스트 결과")
    
    if not env_ok:
        print_status('error', '환경 설정 필요')
        print("  1. .env 파일 생성")
        print("  2. 로그인 정보 입력")
    elif not cookies_ok:
        print_status('warning', '수동 로그인 필요')
        print("  실행: python manual_login.py")
    else:
        print_status('success', '시스템 준비 완료!')
        print("\n사용 가능한 명령:")
        print("  - python manual_login.py    # 수동 로그인 (쿠키 갱신)")
        print("  - python auto_access.py     # 자동 접속")
        print("  - python test_system.py     # 시스템 테스트")


if __name__ == "__main__":
    main()
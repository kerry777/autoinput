#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS ERP 로그인 자동화
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


class MekicsLogin:
    """MEK-ICS ERP 로그인 클래스"""
    
    def __init__(self):
        self.site_dir = Path("sites/mekics")
        self.data_dir = self.site_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    async def login(self):
        """로그인 실행"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config['browser']['headless']
            )
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone']
            )
            page = await context.new_page()
            
            try:
                print("="*60)
                print("MEK-ICS ERP 자동 로그인")
                print("="*60)
                print(f"URL: {self.config['site_info']['login_url']}")
                print(f"사용자: {self.config['credentials']['username']}")
                print("-"*60)
                
                # 로그인 페이지 접속
                print("[1] 로그인 페이지 접속...")
                await page.goto(self.config['site_info']['login_url'])
                await page.wait_for_timeout(self.config['timeouts']['default'])
                
                # 스크린샷 저장
                screenshot_path = self.data_dir / f"login_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                print(f"   스크린샷 저장: {screenshot_path}")
                
                # 로그인 폼 찾기
                print("[2] 로그인 폼 분석...")
                
                # 가능한 사용자명 필드 선택자들
                username_selectors = [
                    'input[name="username"]',
                    'input[name="userid"]',
                    'input[name="user_id"]',
                    'input[name="id"]',
                    'input[name="loginId"]',
                    'input[name="userId"]',
                    'input[type="text"]',
                    '#username',
                    '#userid',
                    '#user_id',
                    '#id'
                ]
                
                # 가능한 비밀번호 필드 선택자들
                password_selectors = [
                    'input[name="password"]',
                    'input[name="passwd"]',
                    'input[name="pwd"]',
                    'input[name="userPw"]',
                    'input[name="userPassword"]',
                    'input[type="password"]',
                    '#password',
                    '#passwd',
                    '#pwd'
                ]
                
                # 사용자명 필드 찾기
                username_field = None
                for selector in username_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            username_field = selector
                            print(f"   사용자명 필드 발견: {selector}")
                            break
                    except:
                        continue
                
                # 비밀번호 필드 찾기
                password_field = None
                for selector in password_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            password_field = selector
                            print(f"   비밀번호 필드 발견: {selector}")
                            break
                    except:
                        continue
                
                if not username_field or not password_field:
                    print("[ERROR] 로그인 폼을 찾을 수 없습니다")
                    print("페이지 HTML 분석 중...")
                    
                    # 모든 input 필드 출력
                    inputs = await page.query_selector_all('input')
                    print(f"\n발견된 input 필드: {len(inputs)}개")
                    for i, input_elem in enumerate(inputs[:10]):  # 처음 10개만
                        input_type = await input_elem.get_attribute('type') or 'text'
                        input_name = await input_elem.get_attribute('name') or ''
                        input_id = await input_elem.get_attribute('id') or ''
                        print(f"   {i+1}. type={input_type}, name={input_name}, id={input_id}")
                    
                    return False
                
                # 로그인 정보 입력
                print("[3] 로그인 정보 입력...")
                await page.fill(username_field, self.config['credentials']['username'])
                await page.wait_for_timeout(500)
                
                await page.fill(password_field, self.config['credentials']['password'])
                await page.wait_for_timeout(500)
                
                # 로그인 버튼 찾기
                print("[4] 로그인 버튼 찾기...")
                login_button_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("로그인")',
                    'button:has-text("Login")',
                    'input[value="로그인"]',
                    'input[value="Login"]',
                    '#loginBtn',
                    '#login',
                    '.login-btn',
                    '.btn-login'
                ]
                
                login_button = None
                for selector in login_button_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            login_button = selector
                            print(f"   로그인 버튼 발견: {selector}")
                            break
                    except:
                        continue
                
                if login_button:
                    print("[5] 로그인 시도...")
                    await page.click(login_button)
                else:
                    # Enter 키로 시도
                    print("[5] Enter 키로 로그인 시도...")
                    await page.keyboard.press('Enter')
                
                # 로그인 결과 대기
                await page.wait_for_timeout(self.config['timeouts']['login'])
                
                # 결과 확인
                current_url = page.url
                print(f"\n[6] 로그인 결과:")
                print(f"   현재 URL: {current_url}")
                
                # 로그인 성공 여부 판단
                if 'login' not in current_url.lower():
                    print("[SUCCESS] 로그인 성공!")
                    
                    # 쿠키 저장
                    cookies = await context.cookies()
                    cookie_file = self.data_dir / "cookies.json"
                    with open(cookie_file, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, indent=2)
                    print(f"   쿠키 저장: {len(cookies)}개")
                    
                    # 로그인 후 스크린샷
                    screenshot_path = self.data_dir / f"after_login_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=str(screenshot_path))
                    print(f"   스크린샷: {screenshot_path}")
                    
                    # 메뉴 탐색
                    print("\n[7] 메뉴 구조 분석...")
                    await self.explore_menus(page)
                    
                    return True
                else:
                    print("[FAIL] 로그인 실패")
                    
                    # 오류 메시지 찾기
                    error_selectors = [
                        '.error-message',
                        '.alert',
                        '.warning',
                        '[class*="error"]',
                        '[class*="alert"]'
                    ]
                    
                    for selector in error_selectors:
                        error_elem = await page.query_selector(selector)
                        if error_elem:
                            error_text = await error_elem.inner_text()
                            print(f"   오류 메시지: {error_text}")
                            break
                    
                    return False
                
            except Exception as e:
                print(f"[ERROR] {e}")
                import traceback
                traceback.print_exc()
                return False
            
            finally:
                print("\n브라우저를 10초 후 닫습니다...")
                await page.wait_for_timeout(10000)
                await browser.close()
    
    async def explore_menus(self, page):
        """메뉴 구조 탐색"""
        try:
            # 메뉴 찾기
            menu_selectors = [
                'nav a',
                '.menu a',
                '.nav-menu a',
                '[class*="menu"] a',
                'ul li a',
                '.gnb a',
                '.lnb a'
            ]
            
            menus = []
            for selector in menu_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"   {selector}에서 {len(elements)}개 메뉴 발견")
                    for elem in elements[:5]:  # 처음 5개만
                        text = await elem.inner_text()
                        href = await elem.get_attribute('href') or ''
                        if text.strip():
                            menus.append({
                                'text': text.strip(),
                                'href': href
                            })
                    break
            
            if menus:
                print(f"\n   주요 메뉴:")
                for i, menu in enumerate(menus[:10], 1):
                    print(f"   {i}. {menu['text']}")
                
                # 메뉴 정보 저장
                menu_file = self.data_dir / "menu_structure.json"
                with open(menu_file, 'w', encoding='utf-8') as f:
                    json.dump(menus, f, ensure_ascii=False, indent=2)
                print(f"\n   메뉴 구조 저장: {menu_file}")
            
        except Exception as e:
            print(f"   메뉴 탐색 오류: {e}")


async def main():
    """메인 실행 함수"""
    login = MekicsLogin()
    result = await login.login()
    
    if result:
        print("\n" + "="*60)
        print("로그인 성공! 쿠키가 저장되었습니다.")
        print("다음 접속 시 쿠키를 사용하여 자동 로그인됩니다.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("로그인 실패. 로그를 확인하세요.")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
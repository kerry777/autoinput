#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BizmekaAuth - 비즈메카 인증 처리 클래스
쿠키 기반 2FA 우회 로직
"""

import json
import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import BrowserContext, Page

# from core.base.scraper import BaseScraper  # 불필요한 import 제거


class BizmekaAuth:
    """비즈메카 인증 처리"""
    
    def __init__(self):
        self.site_dir = Path("sites/bizmeka")
        self.data_dir = self.site_dir / "data"
        self.cookie_file = self.data_dir / "cookies.json"
        
        # 설정 로드
        config_path = self.site_dir / "config" / "settings.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {}
        
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def setup_browser(self, context: BrowserContext, page: Page):
        """브라우저 설정"""
        self.context = context
        self.page = page
    
    def load_cookies(self) -> list:
        """쿠키 로드"""
        if self.cookie_file.exists():
            try:
                with open(self.cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                print(f"✅ 쿠키 로드: {len(cookies)}개")
                return cookies
            except Exception as e:
                print(f"❌ 쿠키 로드 실패: {e}")
        return []
    
    def save_cookies(self, cookies: list):
        """쿠키 저장"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            print(f"✅ 쿠키 저장: {len(cookies)}개")
        except Exception as e:
            print(f"❌ 쿠키 저장 실패: {e}")
    
    async def ensure_login(self) -> bool:
        """로그인 확인 및 처리"""
        if not self.context or not self.page:
            print("❌ 브라우저가 설정되지 않음")
            return False
        
        # 쿠키 로드 및 적용
        cookies = self.load_cookies()
        if cookies:
            try:
                await self.context.add_cookies(cookies)
                print("🍪 기존 쿠키 적용 완료")
                
                # 메인 페이지 접속하여 로그인 상태 확인
                main_url = self.config.get('site_info', {}).get('main_url', 'https://bizmeka.com')
                await self.page.goto(main_url)
                await self.page.wait_for_timeout(3000)
                
                # 로그인 상태 확인
                if await self._check_login_status():
                    print("✅ 기존 쿠키로 로그인 성공")
                    return True
                else:
                    print("⚠️ 쿠키 만료됨 - 수동 로그인 필요")
                    return await self._manual_login_required()
            except Exception as e:
                print(f"❌ 쿠키 적용 실패: {e}")
        
        # 쿠키가 없거나 실패한 경우
        print("🔑 수동 로그인이 필요합니다")
        return await self._manual_login_required()
    
    async def _check_login_status(self) -> bool:
        """로그인 상태 확인"""
        try:
            # 로그아웃 링크나 사용자 정보가 있는지 확인
            logout_indicators = [
                'a:has-text("로그아웃")',
                'a:has-text("logout")',
                '.user-info',
                '.user-name',
                '#user_name'
            ]
            
            for indicator in logout_indicators:
                element = await self.page.query_selector(indicator)
                if element:
                    return True
            
            # 로그인 폼이 있으면 로그아웃 상태
            login_form = await self.page.query_selector('form[action*="login"], input[name="username"], input[name="password"]')
            if login_form:
                return False
            
            # URL 기반 확인
            current_url = self.page.url
            if 'login' in current_url.lower():
                return False
            
            # 기본적으로 로그인 상태로 가정
            return True
            
        except Exception as e:
            print(f"⚠️ 로그인 상태 확인 실패: {e}")
            return False
    
    async def _manual_login_required(self) -> bool:
        """수동 로그인 안내"""
        print("\n" + "="*50)
        print("🔐 수동 로그인이 필요합니다!")
        print("="*50)
        print("1. 현재 브라우저에서 수동으로 로그인하세요")
        print("2. 2차 인증(2FA)까지 완료하세요") 
        print("3. 로그인이 완료되면 'y'를 입력하세요")
        print("4. 쿠키가 자동으로 저장됩니다")
        print("-"*50)
        
        while True:
            try:
                user_input = input("로그인 완료했나요? (y/n): ").strip().lower()
                
                if user_input == 'y':
                    # 로그인 상태 재확인
                    if await self._check_login_status():
                        # 쿠키 저장
                        cookies = await self.context.cookies()
                        self.save_cookies(cookies)
                        print("✅ 로그인 완료 및 쿠키 저장!")
                        return True
                    else:
                        print("❌ 아직 로그인되지 않았습니다. 다시 확인해주세요.")
                        continue
                
                elif user_input == 'n':
                    print("❌ 로그인이 취소되었습니다")
                    return False
                
                else:
                    print("y 또는 n을 입력해주세요")
                    continue
                    
            except KeyboardInterrupt:
                print("\n❌ 사용자에 의해 중단됨")
                return False
            except Exception as e:
                print(f"❌ 입력 처리 오류: {e}")
                return False
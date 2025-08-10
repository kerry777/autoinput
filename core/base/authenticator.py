#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BaseAuth - 인증 처리 기본 클래스
"""

from abc import ABC, abstractmethod
from playwright.async_api import BrowserContext, Page


class BaseAuth(ABC):
    """인증 처리 기본 클래스"""
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.context = None
        self.page = None
    
    async def setup_browser(self, context: BrowserContext, page: Page):
        """브라우저 설정"""
        self.context = context
        self.page = page
    
    @abstractmethod
    async def login(self) -> bool:
        """로그인 - 하위 클래스에서 구현"""
        pass
    
    @abstractmethod
    async def check_login_status(self) -> bool:
        """로그인 상태 확인 - 하위 클래스에서 구현"""
        pass
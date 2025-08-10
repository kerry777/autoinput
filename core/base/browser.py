#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BrowserManager - 브라우저 관리 클래스
"""

from playwright.async_api import Browser, BrowserContext, Page


class BrowserManager:
    """브라우저 관리 클래스"""
    
    def __init__(self):
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
    
    async def setup(self, browser: Browser, **context_options):
        """브라우저 설정"""
        self.browser = browser
        self.context = await browser.new_context(**context_options)
        self.page = await self.context.new_page()
        
        return self.context, self.page
    
    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Navigator - 페이지 네비게이션 유틸리티
"""

from typing import List
from playwright.async_api import Page


class Navigator:
    """페이지 네비게이션 처리 클래스"""
    
    def __init__(self):
        self.page_selectors = [
            'a:has-text("{page_num}")',
            'button:has-text("{page_num}")',
            '[onclick*="page={page_num}"]',
            '.pagination a:has-text("{page_num}")'
        ]
        
        self.next_selectors = [
            'a:has-text("다음")',
            'a:has-text("Next")',
            'a[title="다음"]',
            '.pagination .next',
            'button:has-text(">")'
        ]
    
    async def go_to_page(self, page: Page, page_num: int) -> bool:
        """특정 페이지로 이동"""
        try:
            for selector_template in self.page_selectors:
                selector = selector_template.format(page_num=page_num)
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        await page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            return False
            
        except Exception:
            return False
    
    async def go_to_next_page(self, page: Page) -> bool:
        """다음 페이지로 이동"""
        try:
            for selector in self.next_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        await page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            return False
            
        except Exception:
            return False
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PopupHandler - 팝업 처리 유틸리티
여러 사이트에서 공통으로 사용되는 팝업 처리 로직
"""

from typing import List
from playwright.async_api import Page


class PopupHandler:
    """팝업 처리 전문 클래스"""
    
    def __init__(self):
        # 공통 팝업 닫기 선택자들
        self.close_selectors = [
            'button[aria-label="Close"]',
            'button[aria-label="닫기"]', 
            'button.ui-dialog-titlebar-close',
            'span.ui-icon-closethick',
            'button[title="닫기"]',
            'button[title="Close"]',
            '.ui-dialog-titlebar-close',
            'button:has-text("X")',
            'button:has-text("×")',
            'button:has-text("확인")',
            'button:has-text("OK")',
            '.modal-close',
            '.close-button'
        ]
    
    async def close_all(self, page: Page, max_attempts: int = 5) -> bool:
        """모든 팝업 닫기"""
        closed_count = 0
        
        for attempt in range(max_attempts):
            try:
                # 1. ESC 키 시도 (가장 효과적)
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(300)
                
                # 2. X 버튼 클릭 시도
                for selector in self.close_selectors:
                    try:
                        close_btn = await page.wait_for_selector(selector, timeout=1000)
                        if close_btn:
                            await close_btn.click()
                            closed_count += 1
                            await page.wait_for_timeout(300)
                            break
                    except:
                        continue
                
                # 3. 오버레이 확인 후 ESC
                overlay = await page.query_selector('div.ui-widget-overlay, .modal-overlay, .popup-overlay')
                if overlay:
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    
                    # 오버레이가 사라졌는지 확인
                    overlay_check = await page.query_selector('div.ui-widget-overlay, .modal-overlay, .popup-overlay')
                    if not overlay_check:
                        closed_count += 1
                else:
                    # 더 이상 팝업이 없으면 종료
                    break
                    
            except Exception:
                # 팝업이 없으면 종료
                break
        
        return closed_count > 0
    
    async def handle_alert(self, page: Page, action: str = "accept") -> bool:
        """JavaScript alert 처리"""
        try:
            if action == "accept":
                page.on("dialog", lambda dialog: dialog.accept())
            elif action == "dismiss":
                page.on("dialog", lambda dialog: dialog.dismiss())
            return True
        except:
            return False
    
    async def close_specific_popup(self, page: Page, popup_text: str) -> bool:
        """특정 텍스트를 포함한 팝업 닫기"""
        try:
            # 텍스트를 포함한 팝업 찾기
            popup = await page.query_selector(f'*:has-text("{popup_text}")')
            if popup:
                # 해당 팝업의 닫기 버튼 찾기
                for selector in self.close_selectors:
                    close_btn = await popup.query_selector(selector)
                    if close_btn:
                        await close_btn.click()
                        return True
            return False
        except:
            return False
    
    async def wait_for_popup_gone(self, page: Page, timeout: int = 5000) -> bool:
        """팝업이 사라질 때까지 대기"""
        try:
            # 오버레이나 모달이 사라질 때까지 대기
            await page.wait_for_selector(
                'div.ui-widget-overlay, .modal-overlay, .popup-overlay', 
                state='detached', 
                timeout=timeout
            )
            return True
        except:
            return False
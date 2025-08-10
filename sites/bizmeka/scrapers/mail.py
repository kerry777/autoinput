#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BizmekaMailScraper - 비즈메카 메일 스크래퍼
기존의 여러 버전들을 통합한 최종 완성 버전
"""

from typing import List, Dict, Any
from datetime import datetime
from playwright.async_api import Page

from core.base.scraper import BaseScraper


class BizmekaMailScraper(BaseScraper):
    """비즈메카 메일 스크래퍼"""
    
    def __init__(self):
        super().__init__('bizmeka')
        self.selectors = self._load_selectors()
    
    async def scrape(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """메일 스크래핑 메인 로직"""
        if not self.page:
            raise ValueError("Page not initialized. Call setup_browser first.")
        
        self.log("메일 스크래핑 시작")
        all_mails = []
        
        # 메일 시스템 접속
        await self._navigate_to_mail_system()
        
        # 받은메일함 접속
        await self._navigate_to_inbox()
        
        # 페이지별 메일 수집
        for page_num in range(1, max_pages + 1):
            self.log(f"페이지 {page_num} 처리 중...")
            
            # 팝업 처리
            await self.close_popups()
            
            # 메일 데이터 추출
            page_mails = await self._extract_mails_from_page(page_num)
            all_mails.extend(page_mails)
            
            self.log(f"페이지 {page_num}: {len(page_mails)}개 메일 수집")
            
            # 다음 페이지로 이동
            if page_num < max_pages:
                success = await self._navigate_to_next_page(page_num + 1)
                if not success:
                    self.log(f"페이지 {page_num}까지만 수집 가능")
                    break
        
        self.log(f"총 {len(all_mails)}개 메일 수집 완료")
        return all_mails
    
    async def _navigate_to_mail_system(self):
        """메일 시스템 접속"""
        mail_link = await self.page.query_selector('a[href*="mail"]')
        if mail_link:
            await mail_link.click()
            await self.page.wait_for_timeout(3000)
            
            # 새 탭으로 전환
            if len(self.context.pages) > 1:
                self.page = self.context.pages[-1]
                self.log("새 탭으로 전환")
    
    async def _navigate_to_inbox(self):
        """받은메일함 접속"""
        await self.close_popups()
        
        # 동적 선택자로 받은메일함 찾기
        inbox_selectors = [
            '[id^="mnu_Inbox_"]',  # 가장 정확한 선택자
            'a[onclick*="Inbox"]',
            'a:has-text("받은메일함")',
            '.mbutton:has-text("받은메일함")'
        ]
        
        for selector in inbox_selectors:
            try:
                inbox = await self.page.query_selector(selector)
                if inbox:
                    await inbox.click()
                    self.log("받은메일함 접속 완료")
                    await self.page.wait_for_timeout(3000)
                    break
            except:
                continue
        
        # 팝업 다시 처리
        await self.close_popups()
    
    async def _extract_mails_from_page(self, page_num: int) -> List[Dict[str, Any]]:
        """페이지에서 메일 추출"""
        page_mails = []
        
        try:
            # 프레임 확인
            target_page = self.page
            for frame in self.page.frames:
                if 'mail' in frame.url.lower():
                    target_page = frame
                    break
            
            # li.m_data 요소들 찾기
            mail_items = await target_page.query_selector_all('li.m_data')
            
            for i, item in enumerate(mail_items):
                try:
                    # 속성에서 기본 정보 추출
                    from_name = await item.get_attribute('data-fromname') or ''
                    from_addr = await item.get_attribute('data-fromaddr') or ''
                    mail_id = await item.get_attribute('data-key') or ''
                    
                    # 제목 추출
                    subject = ''
                    subject_elem = await item.query_selector('p.m_subject')
                    if subject_elem:
                        subject_text = await subject_elem.inner_text()
                        # 불필요한 문자 제거
                        subject = self._clean_subject(subject_text)
                    
                    # 날짜와 크기 추출
                    date = ''
                    size = ''
                    date_elem = await item.query_selector('span.m_date')
                    size_elem = await item.query_selector('span.m_size')
                    
                    if date_elem:
                        date = await date_elem.inner_text()
                    if size_elem:
                        size = await size_elem.inner_text()
                    
                    # 읽음 상태
                    item_class = await item.get_attribute('class') or ''
                    is_unread = 'unread' in item_class
                    
                    # 데이터 구성
                    mail_data = {
                        '페이지': page_num,
                        '순번': i + 1,
                        '메일ID': mail_id,
                        '보낸사람': from_name.strip(),
                        '이메일주소': from_addr.strip(),
                        '제목': subject.strip(),
                        '날짜': date.strip(),
                        '크기': size.strip(),
                        '읽음상태': '안읽음' if is_unread else '읽음',
                        '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    if mail_data['보낸사람'] or mail_data['제목']:
                        page_mails.append(mail_data)
                
                except Exception as e:
                    self.log(f"메일 항목 {i} 처리 오류: {e}", "WARNING")
                    continue
        
        except Exception as e:
            self.log(f"메일 추출 오류: {e}", "ERROR")
        
        return page_mails
    
    def _clean_subject(self, subject_text: str) -> str:
        """제목 텍스트 정리"""
        # 이모지와 불필요한 문자 제거
        subject = subject_text.strip()
        subject = subject.replace('🌅', '').replace('&nbsp;', ' ')
        subject = subject.replace('\n', ' ').replace('\t', ' ')
        
        # 여러 공백을 하나로
        while '  ' in subject:
            subject = subject.replace('  ', ' ')
        
        return subject.strip()
    
    async def _navigate_to_next_page(self, page_num: int) -> bool:
        """다음 페이지로 이동"""
        try:
            await self.close_popups()
            
            # 페이지 번호 링크 찾기
            page_selectors = [
                f'a:has-text("{page_num}")',
                f'[onclick*="page={page_num}"]',
                f'.pagination a:has-text("{page_num}")'
            ]
            
            for selector in page_selectors:
                try:
                    page_link = await self.page.query_selector(selector)
                    if page_link:
                        await page_link.click()
                        self.log(f"{page_num}페이지로 이동")
                        await self.page.wait_for_timeout(3000)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.log(f"페이지 이동 오류: {e}", "ERROR")
            return False
    
    async def scrape_and_save(self, max_pages: int = 3, filename: str = None) -> str:
        """스크래핑 후 Excel로 저장"""
        mails = await self.scrape(max_pages)
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"bizmeka_mails_{timestamp}.xlsx"
        
        filepath = self.save_data_to_excel(mails, filename)
        self.log(f"Excel 저장 완료: {filepath}")
        
        return filepath
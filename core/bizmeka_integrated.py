#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 통합 모듈 - 37개 파일에서 실제 작동하는 코드만 추출
"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page


class BizmekaIntegrated:
    """Bizmeka 통합 자동화 - 검증된 코드만 포함"""
    
    def __init__(self):
        self.data_dir = Path("C:\\projects\\autoinput\\data")
        self.cookie_file = self.data_dir / "bizmeka_cookies.json"
        self.profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_production"
        self.mail_data = []
        
    # ============ Step 1: 수동 로그인 (bizmeka_step1_manual_login.py에서 추출) ============
    async def manual_login_and_save_cookies(self):
        """
        수동 로그인으로 쿠키 저장 - 2FA 우회의 핵심
        From: bizmeka_step1_manual_login.py (작동 확인됨)
        """
        print("\n" + "="*60)
        print("Bizmeka 수동 로그인 - 쿠키 저장")
        print("="*60)
        print("\n아이디: kilmoon@mek-ics.com")
        print("비밀번호: moon7410!@")
        print("\n준비되면 Enter를 누르세요...")
        input()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                locale="ko-KR",
                timezone_id="Asia/Seoul"
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 로그인 페이지
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            
            print("\n브라우저에서 로그인을 완료하세요!")
            print("2FA까지 완료 후 Enter를 누르세요")
            input("\n로그인 완료 후 Enter: ")
            
            # 쿠키 저장
            cookies = await browser.cookies()
            with open(self.cookie_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"\n쿠키 {len(cookies)}개 저장됨")
            await browser.close()
            return True
    
    # ============ Step 2: 쿠키로 자동 로그인 (bizmeka_step2_auto_access.py에서 추출) ============
    async def auto_login_with_cookies(self):
        """
        저장된 쿠키로 자동 로그인
        From: bizmeka_step2_auto_access.py (작동 확인됨)
        """
        if not self.cookie_file.exists():
            print("[ERROR] 쿠키 파일이 없습니다!")
            print("먼저 manual_login_and_save_cookies()를 실행하세요.")
            return None
        
        # 쿠키 로드
        with open(self.cookie_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print(f"쿠키 {len(cookies)}개 로드됨")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale="ko-KR",
                timezone_id="Asia/Seoul"
            )
            
            # 쿠키 주입
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            # 메인 페이지 접속
            await page.goto("https://www.bizmeka.com/app/main.do")
            await page.wait_for_timeout(3000)
            
            # 실제 로그인 확인
            current_url = page.url
            if 'loginForm' in current_url:
                print("[FAIL] 세션 만료 - 쿠키 재생성 필요")
                await browser.close()
                return None
            elif 'secondStep' in current_url:
                print("[WARN] 2FA 필요 - 수동 로그인 필요")
                await browser.close()
                return None
            else:
                title = await page.title()
                print(f"[SUCCESS] 로그인 성공: {title}")
                return browser, context, page
    
    # ============ Step 3: 메일 스크래핑 (mail_scraper_final.py에서 추출) ============
    async def close_popups(self, page: Page):
        """
        팝업 자동 닫기
        From: mail_scraper_final.py
        """
        closed = 0
        for _ in range(5):
            try:
                # X 버튼 클릭
                close_selectors = [
                    'button.ui-dialog-titlebar-close',
                    'span.ui-icon-closethick',
                    '.ui-dialog-titlebar-close'
                ]
                
                for selector in close_selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=1000)
                        if btn:
                            await btn.click()
                            closed += 1
                            await page.wait_for_timeout(500)
                            break
                    except:
                        continue
                
                # ESC 키로 닫기
                if closed == 0:
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    
            except:
                break
        
        return closed
    
    async def extract_mail_list(self, page: Page):
        """
        메일 리스트 추출
        From: mail_scraper_final.py (DOM 구조 기반)
        """
        try:
            # JavaScript로 데이터 추출
            mail_data = await page.evaluate('''() => {
                const mails = [];
                
                // li.m_data 구조 (SITE_DB_BIZMEKA.md에 문서화된 구조)
                const items = document.querySelectorAll('li.m_data');
                
                for (let item of items) {
                    const checkbox = item.querySelector('input.mailcb');
                    const sender = item.querySelector('.m_sender');
                    const subject = item.querySelector('.m_subject');
                    const date = item.querySelector('.m_date');
                    const size = item.querySelector('.m_size');
                    
                    if (checkbox && sender && subject) {
                        mails.push({
                            id: checkbox.value || '',
                            sender: sender.textContent.trim(),
                            subject: subject.textContent.trim(),
                            date: date ? date.textContent.trim() : '',
                            size: size ? size.textContent.trim() : '',
                            read: !item.classList.contains('unread')
                        });
                    }
                }
                
                return mails;
            }''')
            
            print(f"추출된 메일: {len(mail_data)}개")
            self.mail_data.extend(mail_data)
            return mail_data
            
        except Exception as e:
            print(f"추출 오류: {e}")
            return []
    
    async def scrape_mails(self, max_pages=3):
        """
        메일 스크래핑 메인 함수
        """
        result = await self.auto_login_with_cookies()
        if not result:
            return False
        
        browser, context, page = result
        
        try:
            # 메일 페이지로 이동 - JavaScript로 새 창 열기
            await page.evaluate('''() => {
                window.open('https://ezwebmail.bizmeka.com/mail/list.do', '_blank');
            }''')
            await page.wait_for_timeout(5000)
            
            # 새 탭 처리
            if len(context.pages) > 1:
                page = context.pages[-1]
                await page.wait_for_timeout(2000)
            
            # 팝업 닫기
            await self.close_popups(page)
            
            # 받은메일함 클릭
            try:
                inbox = await page.wait_for_selector('a:has-text("받은메일함")', timeout=2000)
                if inbox:
                    await inbox.click()
                    await page.wait_for_timeout(2000)
            except:
                pass
            
            # 팝업 다시 닫기
            await self.close_popups(page)
            
            # 페이지별 스크래핑
            for page_num in range(1, max_pages + 1):
                print(f"\n{page_num}페이지 스크래핑...")
                
                # 팝업 닫기
                await self.close_popups(page)
                
                # 데이터 추출
                await self.extract_mail_list(page)
                
                # 다음 페이지
                if page_num < max_pages:
                    try:
                        next_btn = await page.wait_for_selector(f'a:has-text("{page_num + 1}")', timeout=2000)
                        if next_btn:
                            await next_btn.click()
                            await page.wait_for_timeout(2000)
                    except:
                        break
            
            # Excel 저장
            if self.mail_data:
                self.save_to_excel()
            
            await browser.close()
            return True
            
        except Exception as e:
            print(f"스크래핑 실패: {e}")
            await browser.close()
            return False
    
    def save_to_excel(self):
        """Excel 파일로 저장"""
        if not self.mail_data:
            print("저장할 데이터 없음")
            return
        
        df = pd.DataFrame(self.mail_data)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.data_dir / f"bizmeka_mails_{timestamp}.xlsx"
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\nExcel 저장: {filename}")
        print(f"총 {len(df)}개 메일 저장됨")
        
        return filename


# ============ 사용 예시 ============
async def main():
    biz = BizmekaIntegrated()
    
    # 옵션 1: 수동 로그인 (쿠키가 없거나 만료된 경우)
    # await biz.manual_login_and_save_cookies()
    
    # 옵션 2: 자동 로그인 후 메일 스크래핑
    await biz.scrape_mails(max_pages=3)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Bizmeka 통합 모듈")
    print("37개 파일에서 실제 작동하는 코드만 추출")
    print("="*60)
    
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - DevTools 기반 버전
스크린샷의 실제 구조 활용
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, Page
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


class MailScraperDevTools:
    """DevTools 기반 메일 스크래퍼"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging('mail_scraper_devtools')
        self.cookie_manager = CookieManager()
        self.mail_data = []
    
    async def close_popup_esc(self, page: Page):
        """ESC로 팝업 닫기"""
        for _ in range(3):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
    
    async def extract_mail_from_table(self, page: Page, page_num: int):
        """테이블에서 메일 추출"""
        print(f"\n페이지 {page_num} 추출 중...")
        
        try:
            # 팝업 먼저 닫기
            await self.close_popup_esc(page)
            
            # JavaScript로 직접 추출 - DevTools에서 확인한 구조
            mails = await page.evaluate('''() => {
                const results = [];
                
                // 메일 테이블의 모든 행 찾기
                const rows = document.querySelectorAll('tr');
                
                for (let row of rows) {
                    const cells = row.querySelectorAll('td');
                    
                    // 체크박스가 있는 행 확인
                    const checkbox = row.querySelector('input[type="checkbox"]');
                    if (!checkbox || checkbox.id === 'checkAll') continue;
                    
                    // 충분한 셀이 있는지 확인
                    if (cells.length >= 6) {
                        // 텍스트 추출
                        const sender = cells[3] ? cells[3].innerText.trim() : '';
                        const subject = cells[4] ? cells[4].innerText.trim() : '';
                        const date = cells[5] ? cells[5].innerText.trim() : '';
                        const size = cells[6] ? cells[6].innerText.trim() : '';
                        
                        // 유효한 데이터만 추가
                        if ((sender || subject) && date.includes('202')) {
                            results.push({
                                sender: sender,
                                subject: subject,
                                date: date,
                                size: size
                            });
                        }
                    }
                }
                
                // 백업 방법: class name으로 찾기
                if (results.length === 0) {
                    const mailRows = document.querySelectorAll('.mail_list tr, .list_table tr, tbody tr');
                    
                    for (let row of mailRows) {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 5) {
                            const texts = Array.from(cells).map(cell => cell.innerText.trim());
                            
                            // 날짜 찾기
                            const dateIndex = texts.findIndex(t => /202\d-\d{2}-\d{2}/.test(t));
                            
                            if (dateIndex >= 0) {
                                results.push({
                                    sender: texts[dateIndex - 2] || texts[3] || '',
                                    subject: texts[dateIndex - 1] || texts[4] || '',
                                    date: texts[dateIndex] || '',
                                    size: texts[dateIndex + 1] || ''
                                });
                            }
                        }
                    }
                }
                
                return results;
            }''')
            
            # 데이터 저장
            for mail in mails:
                if mail['sender'] or mail['subject']:
                    self.mail_data.append({
                        '페이지': page_num,
                        '보낸사람': mail['sender'],
                        '제목': mail['subject'],
                        '날짜': mail['date'],
                        '크기': mail['size'],
                        '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            print(f"  → {len(mails)}개 메일 수집")
            
            # 샘플 출력
            for i, mail in enumerate(mails[:3], 1):
                sender = mail['sender'][:20] if mail['sender'] else 'Unknown'
                subject = mail['subject'][:30] if mail['subject'] else 'No subject'
                print(f"    {i}. {sender}: {subject}...")
            
            return len(mails)
            
        except Exception as e:
            print(f"  추출 오류: {e}")
            return 0
    
    async def go_to_page(self, page: Page, page_num: int):
        """페이지 이동"""
        try:
            await self.close_popup_esc(page)
            
            # 페이지 번호 링크 클릭
            page_link = await page.query_selector(f'a:has-text("{page_num}")')
            if page_link:
                await page_link.click()
                await page.wait_for_timeout(2000)
                return True
                
        except:
            pass
        
        return False
    
    async def run(self, max_pages: int = 3):
        """메인 실행"""
        print("\n" + "="*60)
        print("Bizmeka 메일 스크래퍼 - DevTools 버전")
        print("="*60)
        
        # 쿠키 로드
        cookies = self.cookie_manager.load_cookies()
        if not cookies:
            print("\n[ERROR] 쿠키 없음 - manual_login.py 먼저 실행")
            return False
        
        print("[OK] 쿠키 로드 완료")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone']
            )
            
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            try:
                # 메인 페이지 접속
                print("\n1. 메인 페이지 접속...")
                await page.goto(self.config['urls']['main'])
                await page.wait_for_timeout(3000)
                
                # 메일 버튼 찾기 및 클릭
                print("2. 메일 시스템 접속...")
                mail_link = await page.wait_for_selector('a[href*="mail"]', timeout=5000)
                if mail_link:
                    await mail_link.click()
                    await page.wait_for_timeout(3000)
                
                # 새 탭 처리
                if len(context.pages) > 1:
                    page = context.pages[-1]
                    print("   → 새 탭 전환")
                
                # 팝업 닫기
                await self.close_popup_esc(page)
                
                # 받은메일함 확인
                try:
                    inbox = await page.wait_for_selector('a:has-text("받은메일함")', timeout=2000)
                    if inbox:
                        await inbox.click()
                        print("3. 받은메일함 접속")
                        await page.wait_for_timeout(2000)
                except:
                    print("3. 이미 받은메일함")
                
                # 페이지별 수집
                print(f"\n4. 메일 수집 시작 (최대 {max_pages}페이지)")
                print("-" * 40)
                
                for page_num in range(1, max_pages + 1):
                    count = await self.extract_mail_from_table(page, page_num)
                    
                    if page_num < max_pages and count > 0:
                        if not await self.go_to_page(page, page_num + 1):
                            print(f"\n페이지 {page_num}까지만 수집 가능")
                            break
                
                # 결과 저장
                print("\n" + "="*60)
                if self.mail_data:
                    self.save_to_excel()
                    print(f"[SUCCESS] 총 {len(self.mail_data)}개 메일 수집 완료!")
                else:
                    print("[WARNING] 수집된 메일이 없습니다")
                    
                    # 디버깅용 스크린샷
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    screenshot_path = f'data/debug_{timestamp}.png'
                    await page.screenshot(path=screenshot_path)
                    print(f"[DEBUG] 스크린샷 저장: {screenshot_path}")
                
                await browser.close()
                return True
                
            except Exception as e:
                print(f"\n[ERROR] 실행 오류: {e}")
                await browser.close()
                return False
    
    def save_to_excel(self):
        """Excel 저장"""
        try:
            df = pd.DataFrame(self.mail_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            
            # Excel 저장
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='메일목록')
                
                # 열 너비 자동 조정
                worksheet = writer.sheets['메일목록']
                for column in df:
                    column_width = max(df[column].astype(str).str.len().max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
            
            print(f"\n[EXCEL] 파일 저장 완료")
            print(f"  • 파일명: {filename}")
            print(f"  • 메일 수: {len(self.mail_data)}개")
            
            # 요약 통계
            if '보낸사람' in df.columns:
                top_senders = df['보낸사람'].value_counts().head(3)
                print("\n[주요 발신자]")
                for sender, count in top_senders.items():
                    print(f"  • {sender}: {count}개")
            
        except Exception as e:
            print(f"[ERROR] Excel 저장 실패: {e}")


if __name__ == "__main__":
    scraper = MailScraperDevTools()
    asyncio.run(scraper.run(max_pages=3))
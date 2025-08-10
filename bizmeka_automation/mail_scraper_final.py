#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 최종 버전
팝업 자동 닫기 및 데이터 추출
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, Page
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


class MailScraperFinal:
    """최종 메일 스크래퍼"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging('mail_scraper_final')
        self.cookie_manager = CookieManager()
        self.mail_data = []
    
    async def close_all_popups(self, page: Page):
        """모든 팝업 닫기"""
        closed_count = 0
        
        # 최대 5번 시도 (여러 팝업이 있을 수 있음)
        for _ in range(5):
            try:
                # X 버튼 찾기 (스크린샷에서 확인한 선택자)
                close_selectors = [
                    'button[aria-label="Close"]',
                    'button.ui-dialog-titlebar-close',
                    'span.ui-icon-closethick',
                    'button[title="닫기"]',
                    'button[title="Close"]',
                    '.ui-dialog-titlebar-close',
                    'button:has-text("X")',
                    'button:has-text("×")'
                ]
                
                close_btn = None
                for selector in close_selectors:
                    try:
                        close_btn = await page.wait_for_selector(selector, timeout=1000)
                        if close_btn:
                            await close_btn.click()
                            print_status('success', f'팝업 닫기 #{closed_count + 1}')
                            closed_count += 1
                            await page.wait_for_timeout(500)
                            break
                    except:
                        continue
                
                # 버튼을 못 찾았으면 ESC 키 시도
                if not close_btn:
                    # 오버레이가 있는지 확인
                    overlay = await page.query_selector('div.ui-widget-overlay')
                    if overlay:
                        await page.keyboard.press('Escape')
                        await page.wait_for_timeout(500)
                        
                        # 오버레이가 사라졌는지 확인
                        overlay_check = await page.query_selector('div.ui-widget-overlay')
                        if not overlay_check:
                            print_status('success', 'ESC로 팝업 닫기')
                            closed_count += 1
                    else:
                        # 더 이상 팝업이 없음
                        break
                        
            except Exception as e:
                # 팝업이 없으면 종료
                break
        
        if closed_count > 0:
            print_status('info', f'총 {closed_count}개 팝업 닫음')
        
        return closed_count > 0
    
    async def extract_mail_data(self, page: Page, page_num: int):
        """메일 데이터 추출"""
        print_status('info', f'{page_num}페이지 데이터 추출 중...')
        
        scraped_count = 0
        
        try:
            # JavaScript로 직접 데이터 추출 - 테이블 구조 기반
            mail_data = await page.evaluate('''() => {
                const mails = [];
                
                // 메일 테이블 행 찾기 (체크박스가 있는 행)
                const rows = document.querySelectorAll('tr');
                
                for (let row of rows) {
                    // 체크박스가 있는 행만 처리
                    const checkbox = row.querySelector('input[type="checkbox"]');
                    if (!checkbox || checkbox.id === 'checkAll') continue;
                    
                    const cells = row.querySelectorAll('td');
                    if (cells.length < 7) continue;
                    
                    // 메일 데이터 추출
                    const mailInfo = {
                        checkbox: cells[0]?.innerText?.trim() || '',
                        star: cells[1]?.innerText?.trim() || '',
                        attachment: cells[2]?.innerText?.trim() || '',
                        sender: cells[3]?.innerText?.trim() || '',
                        subject: cells[4]?.innerText?.trim() || '',
                        date: cells[5]?.innerText?.trim() || '',
                        size: cells[6]?.innerText?.trim() || ''
                    };
                    
                    // 보낸사람과 제목이 있는 경우만 추가
                    if (mailInfo.sender || mailInfo.subject) {
                        mails.push(mailInfo);
                    }
                }
                
                return mails;
            }''')
            
            # 데이터 파싱 - None 체크
            if not mail_data:
                mail_data = []
            
            for mail_info in mail_data:
                try:
                    # 직접 매핑된 데이터 사용
                    sender = mail_info.get('sender', '')
                    subject = mail_info.get('subject', '')
                    date = mail_info.get('date', '')
                    size = mail_info.get('size', '')
                    
                    # 데이터 저장
                    if subject or sender:
                        self.mail_data.append({
                            '페이지': page_num,
                            '보낸사람': sender,
                            '제목': subject,
                            '날짜': date,
                            '크기': size,
                            '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        scraped_count += 1
                        
                        if scraped_count <= 3:
                            print_status('info', f'수집: {sender[:30]} - {subject[:40]}')
                
                except Exception as e:
                    self.logger.error(f"데이터 파싱 오류: {e}")
                    continue
            
            print_status('success', f'{page_num}페이지: {scraped_count}개 메일 수집')
            
        except Exception as e:
            self.logger.error(f"추출 실패: {e}")
            print_status('error', f'추출 실패: {e}')
        
        return scraped_count
    
    async def navigate_to_next_page(self, page: Page, target_page: int):
        """다음 페이지로 이동"""
        try:
            # 먼저 팝업 닫기
            await self.close_all_popups(page)
            
            # 페이지 번호 클릭
            selectors = [
                f'a:has-text("{target_page}")',
                f'button:has-text("{target_page}")',
                f'span:has-text("{target_page}")',
            ]
            
            for selector in selectors:
                try:
                    page_btn = await page.wait_for_selector(selector, timeout=2000)
                    if page_btn:
                        await page_btn.click()
                        print_status('info', f'{target_page}페이지로 이동')
                        await page.wait_for_timeout(2000)
                        return True
                except:
                    continue
            
            # 페이지 번호를 못 찾으면 >> 버튼 시도
            next_btn = await page.query_selector('a:has-text(">>"), button:has-text(">>")')
            if next_btn:
                await next_btn.click()
                print_status('info', '다음 페이지 그룹으로 이동')
                await page.wait_for_timeout(2000)
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"페이지 이동 실패: {e}")
            return False
    
    async def run(self, max_pages: int = 3):
        """메일 스크래핑 실행"""
        print_banner("MAIL SCRAPER FINAL")
        
        # 쿠키 로드
        cookies = self.cookie_manager.load_cookies()
        if not cookies:
            print_status('error', '쿠키 없음 - manual_login.py 실행 필요')
            return False
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config['settings']['headless']
            )
            
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone']
            )
            
            await context.add_cookies(cookies)
            page = await context.new_page()
            
            try:
                # 메인 페이지 접속
                print_status('info', '메인 페이지 접속 중...')
                await page.goto(self.config['urls']['main'])
                await page.wait_for_timeout(3000)
                
                # 메일 버튼 클릭
                print_status('info', '메일 버튼 찾는 중...')
                mail_btn = await page.wait_for_selector('a[href*="mail"], button:has-text("메일")', timeout=5000)
                if mail_btn:
                    await mail_btn.click()
                    print_status('success', '메일 버튼 클릭')
                    await page.wait_for_timeout(3000)
                
                # 새 탭 처리
                if len(context.pages) > 1:
                    page = context.pages[-1]
                    print_status('info', '새 탭으로 전환')
                    await page.wait_for_timeout(2000)
                
                # 첫 팝업 닫기
                await self.close_all_popups(page)
                
                # 받은메일함 클릭 (선택적)
                try:
                    inbox = await page.wait_for_selector('a:has-text("받은메일함")', timeout=2000)
                    if inbox:
                        await inbox.click()
                        print_status('success', '받은메일함 클릭')
                        await page.wait_for_timeout(2000)
                except:
                    print_status('info', '이미 받은메일함')
                
                # 팝업 다시 닫기
                await self.close_all_popups(page)
                
                # 페이지별 스크래핑
                for page_num in range(1, max_pages + 1):
                    # 팝업 닫기
                    await self.close_all_popups(page)
                    
                    # 데이터 추출
                    count = await self.extract_mail_data(page, page_num)
                    
                    # 다음 페이지로 이동
                    if page_num < max_pages:
                        if not await self.navigate_to_next_page(page, page_num + 1):
                            print_status('info', f'{page_num}페이지까지만 수집')
                            break
                
                # Excel 저장
                if self.mail_data:
                    self.save_to_excel()
                else:
                    print_status('warning', '수집된 데이터 없음')
                
                
                await browser.close()
                return True
                
            except Exception as e:
                self.logger.error(f"실행 실패: {e}")
                print_status('error', f'실행 실패: {e}')
                await browser.close()
                return False
    
    def save_to_excel(self):
        """Excel 파일로 저장"""
        try:
            df = pd.DataFrame(self.mail_data)
            
            # 원본 컬럼 제거 (디버그용)
            if '원본' in df.columns:
                df = df.drop('원본', axis=1)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print_status('success', f'Excel 저장: {filename}')
            print(f"\n수집 결과:")
            print(f"  총 {len(self.mail_data)}개 메일")
            print(f"  파일: {filename}")
            
            # 샘플 출력
            print("\n[샘플 데이터]")
            for i, mail in enumerate(self.mail_data[:5], 1):
                print(f"  {i}. {mail['보낸사람'][:20]}: {mail['제목'][:40]}...")
            
        except Exception as e:
            print_status('error', f'Excel 저장 실패: {e}')


if __name__ == "__main__":
    try:
        scraper = MailScraperFinal()
        asyncio.run(scraper.run(max_pages=3))
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
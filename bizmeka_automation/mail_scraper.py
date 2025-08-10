#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼
- 자동 로그인
- 메일 버튼 클릭
- 받은 메일함 접속
- 페이지네이션하며 메일 데이터 수집
- Excel 파일로 저장
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, Page
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


class MailScraper:
    """메일 스크래퍼 클래스"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging('mail_scraper')
        self.cookie_manager = CookieManager()
        self.mail_data = []
        
    async def login_and_navigate(self, page: Page) -> bool:
        """로그인 후 메일함으로 이동"""
        try:
            # 쿠키 로드
            cookies = self.cookie_manager.load_cookies()
            if not cookies:
                print_status('error', '쿠키 없음 - manual_login.py 실행 필요')
                return False
            
            # 쿠키 설정
            await page.context.add_cookies(cookies)
            
            # 메인 페이지 접속
            print_status('info', '메인 페이지 접속 중...')
            await page.goto(self.config['urls']['main'])
            await page.wait_for_timeout(3000)
            
            # 로그인 확인
            if 'loginForm' in page.url:
                print_status('error', '로그인 실패 - 세션 만료')
                return False
            
            print_status('success', '로그인 성공')
            
            # 메일 버튼 찾기 및 클릭
            print_status('info', '메일 버튼 찾는 중...')
            
            # 여러 가능한 선택자 시도
            mail_selectors = [
                'a[href*="mail"]',
                'button:has-text("메일")',
                'a:has-text("메일")',
                'span:has-text("메일")',
                'div:has-text("메일")',
                '[class*="mail"]',
                '[id*="mail"]'
            ]
            
            mail_button = None
            for selector in mail_selectors:
                try:
                    mail_button = await page.wait_for_selector(selector, timeout=2000)
                    if mail_button:
                        self.logger.info(f"메일 버튼 찾음: {selector}")
                        break
                except:
                    continue
            
            if not mail_button:
                print_status('error', '메일 버튼을 찾을 수 없습니다')
                # 스크린샷 저장
                await page.screenshot(path='data/mail_button_not_found.png')
                return False
            
            # 메일 버튼 클릭
            await mail_button.click()
            print_status('success', '메일 버튼 클릭')
            await page.wait_for_timeout(2000)
            
            # 메일 용량 초과 팝업 처리
            try:
                # 팝업 확인 버튼 찾기
                popup_confirm = await page.wait_for_selector('button:has-text("확인")', timeout=2000)
                if popup_confirm:
                    print_status('info', '메일 용량 초과 팝업 감지 - 확인 클릭')
                    await popup_confirm.click()
                    await page.wait_for_timeout(1000)
            except:
                # 팝업이 없으면 계속 진행
                pass
            
            await page.wait_for_timeout(2000)
            
            # 새 창/탭 처리
            if len(page.context.pages) > 1:
                # 새 탭이 열렸다면 그 탭으로 전환
                page = page.context.pages[-1]
                await page.wait_for_load_state('networkidle')
            
            # 추가 팝업 처리 (메일 페이지 로드 후)
            try:
                popup_confirm2 = await page.wait_for_selector('button:has-text("확인")', timeout=1000)
                if popup_confirm2:
                    print_status('info', '추가 팝업 감지 - 확인 클릭')
                    await popup_confirm2.click()
                    await page.wait_for_timeout(1000)
            except:
                pass
            
            # 받은 메일함 클릭
            print_status('info', '받은 메일함 찾는 중...')
            
            inbox_selectors = [
                'a:has-text("받은메일함")',
                'a:has-text("받은 메일함")',
                'span:has-text("받은메일함")',
                'span:has-text("받은 메일함")',
                '[class*="inbox"]',
                'a[href*="inbox"]',
                'a[href*="receiveBox"]'
            ]
            
            inbox = None
            for selector in inbox_selectors:
                try:
                    inbox = await page.wait_for_selector(selector, timeout=2000)
                    if inbox:
                        self.logger.info(f"받은 메일함 찾음: {selector}")
                        break
                except:
                    continue
            
            if inbox:
                # 오버레이 제거 시도
                try:
                    overlay = await page.query_selector('div.ui-widget-overlay')
                    if overlay:
                        await page.evaluate('document.querySelector("div.ui-widget-overlay").remove()')
                        await page.wait_for_timeout(500)
                except:
                    pass
                
                # 클릭 시도
                try:
                    await inbox.click()
                    print_status('success', '받은 메일함 접속')
                except:
                    # 클릭 실패시 JavaScript로 직접 클릭
                    await page.evaluate('el => el.click()', inbox)
                    print_status('success', '받은 메일함 접속 (JS)')
                
                await page.wait_for_timeout(3000)
            else:
                print_status('warning', '받은 메일함 버튼 없음 - 이미 받은 메일함일 수 있음')
            
            return True
            
        except Exception as e:
            self.logger.error(f"네비게이션 실패: {e}")
            print_status('error', f'네비게이션 실패: {e}')
            return False
    
    async def scrape_mail_page(self, page: Page, page_num: int):
        """현재 페이지의 메일 데이터 스크래핑"""
        print_status('info', f'{page_num}페이지 스크래핑 중...')
        
        # 디버그용 스크린샷 저장
        await page.screenshot(path=f'data/mail_page_{page_num}.png')
        
        try:
            # iframe/frame 확인
            frames = page.frames
            print_status('info', f'총 {len(frames)}개 프레임')
            
            # 메일 목록이 있는 프레임 찾기
            target_frame = None
            for frame in frames:
                try:
                    # 프레임 내에서 메일 관련 요소 찾기
                    mail_element = await frame.query_selector('table, div[class*="mail"], #mailList')
                    if mail_element:
                        target_frame = frame
                        print_status('info', '메일 목록 프레임 발견')
                        break
                except:
                    continue
            
            if target_frame:
                page = target_frame
            
            # 메일 목록 테이블 찾기 - 다양한 선택자 시도
            selectors = [
                'tr[class*="mail"]',
                'tr[class*="list"]',
                'tbody tr',
                'table tr',
                'div[class*="mail-item"]',
                'div[class*="list-item"]',
                '.mail-list tr',
                '#mailList tr'
            ]
            
            mail_rows = []
            for selector in selectors:
                mail_rows = await page.query_selector_all(selector)
                if mail_rows and len(mail_rows) > 1:
                    print_status('info', f'선택자 {selector}로 {len(mail_rows)}개 행 발견')
                    break
            
            # HTML 저장 (디버그용)
            if page_num == 1:
                html_content = await page.content()
                with open(f'data/mail_page_{page_num}.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print_status('info', f'mail_page_{page_num}.html 저장')
            
            scraped_count = 0
            
            # 첫 번째 행은 헤더일 가능성이 높으므로 건너뛰기
            start_index = 1 if len(mail_rows) > 1 else 0
            
            for row in mail_rows[start_index:]:
                try:
                    # 모든 셀 가져오기
                    cells = await row.query_selector_all('td')
                    if not cells or len(cells) < 2:
                        continue
                    
                    # 셀 내용 추출 - 빈 셀도 포함
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip() if text else '')
                    
                    # 디버그: 첫 번째 행의 셀 내용 출력
                    if scraped_count == 0 and cell_texts:
                        print_status('info', f'첫 행 데이터: {cell_texts[:5]}')
                    
                    # 발신자 찾기 (일반적으로 2번째 또는 3번째 컬럼)
                    sender = None
                    sender_selectors = [
                        'td[class*="from"]',
                        'td[class*="sender"]',
                        'td:nth-child(2)',  # 보통 두 번째 컬럼
                        'td:nth-child(3)',  # 또는 세 번째
                        'td:nth-child(4)'   # 또는 네 번째
                    ]
                    
                    for selector in sender_selectors:
                        element = await row.query_selector(selector)
                        if element:
                            sender = await element.inner_text()
                            if sender and sender.strip():
                                break
                    
                    # 제목 찾기
                    subject = None
                    subject_selectors = [
                        'td[class*="subject"]',
                        'td[class*="title"]',
                        'a[class*="subject"]',
                        'td:nth-child(3)',  # 보통 세 번째 컬럼
                        'td:nth-child(4)',  # 또는 네 번째
                        'td:nth-child(5)'   # 또는 다섯 번째
                    ]
                    
                    for selector in subject_selectors:
                        element = await row.query_selector(selector)
                        if element:
                            subject = await element.inner_text()
                            if subject and subject.strip():
                                break
                    
                    # 날짜 찾기 (선택적)
                    date = None
                    date_selectors = [
                        'td[class*="date"]',
                        'td[class*="time"]',
                        'td:last-child',  # 보통 마지막 컬럼
                        'td:nth-last-child(2)'  # 또는 뒤에서 두 번째
                    ]
                    
                    for selector in date_selectors:
                        element = await row.query_selector(selector)
                        if element:
                            date = await element.inner_text()
                            if date and date.strip():
                                break
                    
                    # 데이터 저장 - 이미지 분석 기반 컬럼 위치
                    # 컬럼: [체크박스, 별표, 첨부, 보낸사람, 제목, 날짜, 크기]
                    if cell_texts and len(cell_texts) >= 7:
                        # 정확한 컬럼 위치 사용
                        sender_text = cell_texts[3] if len(cell_texts) > 3 else ''
                        subject_text = cell_texts[4] if len(cell_texts) > 4 else ''
                        date_text = cell_texts[5] if len(cell_texts) > 5 else ''
                        
                        # 빈 데이터는 건너뛰기
                        if sender_text or subject_text:
                            self.mail_data.append({
                                '페이지': page_num,
                                '보낸사람': sender_text,
                                '제목': subject_text,
                                '날짜': date_text,
                                '크기': cell_texts[6] if len(cell_texts) > 6 else '',
                                '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            scraped_count += 1
                            
                            # 처음 몇 개 데이터 출력
                            if scraped_count <= 3:
                                print_status('info', f'수집: {sender_text[:20]} - {subject_text[:30]}')
                    elif sender and subject:
                        # 기존 방식으로도 저장
                        self.mail_data.append({
                            '페이지': page_num,
                            '보낸사람': sender.strip(),
                            '제목': subject.strip(),
                            '날짜': date.strip() if date else '',
                            '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        scraped_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"행 파싱 실패: {e}")
                    continue
            
            print_status('success', f'{page_num}페이지: {scraped_count}개 메일 수집')
            
        except Exception as e:
            self.logger.error(f"페이지 스크래핑 실패: {e}")
            print_status('error', f'페이지 스크래핑 실패: {e}')
            # 디버그용 스크린샷
            await page.screenshot(path=f'data/page_{page_num}_error.png')
    
    async def navigate_pages(self, page: Page, max_pages: int = 3):
        """페이지 네비게이션 및 스크래핑"""
        
        for page_num in range(1, max_pages + 1):
            # 현재 페이지 스크래핑
            await self.scrape_mail_page(page, page_num)
            
            # 다음 페이지로 이동 (마지막 페이지 제외)
            if page_num < max_pages:
                print_status('info', f'{page_num + 1}페이지로 이동 중...')
                
                # 페이지네이션 버튼 찾기
                next_selectors = [
                    'a:has-text("다음")',
                    'button:has-text("다음")',
                    'a[class*="next"]',
                    'button[class*="next"]',
                    f'a:has-text("{page_num + 1}")',
                    f'button:has-text("{page_num + 1}")',
                    'a[title*="다음"]',
                    'img[alt*="다음"]'
                ]
                
                moved = False
                for selector in next_selectors:
                    try:
                        next_button = await page.wait_for_selector(selector, timeout=2000)
                        if next_button:
                            await next_button.click()
                            await page.wait_for_timeout(2000)
                            moved = True
                            break
                    except:
                        continue
                
                if not moved:
                    print_status('warning', '다음 페이지 버튼을 찾을 수 없습니다')
                    # 페이지 번호 직접 클릭 시도
                    try:
                        page_link = await page.wait_for_selector(f'a:has-text("{page_num + 1}")', timeout=2000)
                        await page_link.click()
                        await page.wait_for_timeout(2000)
                    except:
                        print_status('info', f'{page_num}페이지까지만 수집')
                        break
    
    def save_to_excel(self):
        """수집한 데이터를 Excel 파일로 저장"""
        if not self.mail_data:
            print_status('warning', '저장할 데이터가 없습니다')
            return False
        
        try:
            # DataFrame 생성
            df = pd.DataFrame(self.mail_data)
            
            # 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            
            # Excel 저장
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print_status('success', f'Excel 파일 저장: {filename}')
            print(f"\n수집 결과:")
            print(f"  - 총 메일 수: {len(self.mail_data)}개")
            print(f"  - 파일 위치: {filename}")
            
            # 샘플 데이터 출력
            print("\n[샘플 데이터]")
            for i, mail in enumerate(self.mail_data[:5], 1):
                print(f"  {i}. {mail['보낸사람']}: {mail['제목'][:30]}...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Excel 저장 실패: {e}")
            print_status('error', f'Excel 저장 실패: {e}')
            return False
    
    async def run(self, max_pages: int = 3):
        """메일 스크래핑 실행"""
        print_banner("MAIL SCRAPER")
        
        # 쿠키 확인
        if not self.cookie_manager.load_cookies():
            print_status('error', '쿠키 없음 - manual_login.py 실행 필요')
            return False
        
        async with async_playwright() as p:
            # 브라우저 실행
            browser = await p.chromium.launch(
                headless=self.config['settings']['headless']
            )
            
            context = await browser.new_context(
                locale=self.config['browser']['locale'],
                timezone_id=self.config['browser']['timezone']
            )
            
            page = await context.new_page()
            
            try:
                # 로그인 및 메일함 이동
                if not await self.login_and_navigate(page):
                    await browser.close()
                    return False
                
                # 페이지 네비게이션 및 스크래핑
                await self.navigate_pages(page, max_pages)
                
                # Excel 저장
                self.save_to_excel()
                
                await browser.close()
                return True
                
            except Exception as e:
                self.logger.error(f"스크래핑 실패: {e}")
                print_status('error', f'스크래핑 실패: {e}')
                await browser.close()
                return False


async def main():
    """메인 함수"""
    scraper = MailScraper()
    
    # 페이지 수 입력
    print("\n수집할 페이지 수를 입력하세요 (기본: 3): ", end="")
    user_input = input().strip()
    max_pages = 3
    
    if user_input.isdigit():
        max_pages = int(user_input)
    
    print(f"\n{max_pages}페이지 수집을 시작합니다...")
    
    success = await scraper.run(max_pages)
    
    if success:
        print("\n" + "="*60)
        print("[OK] 메일 스크래핑 완료")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("[ERROR] 메일 스크래핑 실패")
        print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
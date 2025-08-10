#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 수정 버전
스크린샷 분석 기반 정확한 데이터 추출
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, Page
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


class MailScraperFixed:
    """수정된 메일 스크래퍼"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging('mail_scraper_fixed')
        self.cookie_manager = CookieManager()
        self.mail_data = []
    
    async def close_popup(self, page: Page):
        """팝업 닫기"""
        try:
            # 팝업 오버레이 확인
            overlay = await page.query_selector('div.ui-widget-overlay')
            if overlay:
                print_status('info', '팝업 오버레이 감지')
                
                # X 버튼 또는 확인 버튼 찾기
                close_btn = await page.query_selector('button.ui-dialog-titlebar-close, .ui-icon-closethick')
                if close_btn:
                    await close_btn.click()
                    print_status('success', '팝업 닫기 성공')
                    await page.wait_for_timeout(1000)
                    return True
                
                # 확인 버튼
                confirm_btn = await page.query_selector('button:has-text("확인")')
                if confirm_btn:
                    await confirm_btn.click()
                    print_status('success', '팝업 확인 클릭')
                    await page.wait_for_timeout(1000)
                    return True
                
                # ESC 키로 닫기 시도
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
                
                # 오버레이가 사라졌는지 확인
                overlay_gone = await page.query_selector('div.ui-widget-overlay')
                if not overlay_gone:
                    print_status('success', '팝업 닫기 성공 (ESC)')
                    return True
        except:
            pass
        
        return False
    
    async def scrape_mail_data(self, page: Page, page_num: int):
        """메일 데이터 추출"""
        print_status('info', f'{page_num}페이지 스크래핑 중...')
        
        # 팝업 닫기
        await self.close_popup(page)
        
        scraped_count = 0
        
        try:
            # 모든 프레임에서 메일 데이터 찾기
            frames = page.frames
            
            for frame in frames:
                try:
                    # 테이블 행 찾기
                    rows = await frame.query_selector_all('tr')
                    
                    if not rows:
                        continue
                    
                    for row in rows:
                        try:
                            # 모든 td 셀 가져오기
                            cells = await row.query_selector_all('td')
                            
                            if not cells or len(cells) < 5:
                                continue
                            
                            # 셀 텍스트 추출
                            cell_texts = []
                            for cell in cells:
                                text = await cell.inner_text()
                                cell_texts.append(text.strip() if text else '')
                            
                            # 메일 데이터인지 확인 (날짜 형식으로 판단)
                            has_date = False
                            for text in cell_texts:
                                if '2025-' in text or '2024-' in text:
                                    has_date = True
                                    break
                            
                            if not has_date:
                                continue
                            
                            # 데이터 파싱
                            # 일반적인 컬럼 위치: [체크, 별, 첨부, 보낸사람, 제목, 날짜, 크기]
                            sender = ''
                            subject = ''
                            date = ''
                            size = ''
                            
                            # 컬럼 수에 따라 동적으로 처리
                            if len(cell_texts) >= 7:
                                # 표준 7개 컬럼
                                sender = cell_texts[3]
                                subject = cell_texts[4]
                                date = cell_texts[5]
                                size = cell_texts[6]
                            elif len(cell_texts) >= 5:
                                # 컬럼이 적을 경우 
                                # 날짜가 포함된 셀 찾기
                                date_idx = -1
                                for i, text in enumerate(cell_texts):
                                    if '2025-' in text or '2024-' in text:
                                        date_idx = i
                                        date = text
                                        break
                                
                                if date_idx > 0:
                                    # 날짜 앞의 2개 셀을 보낸사람과 제목으로 추정
                                    if date_idx >= 2:
                                        sender = cell_texts[date_idx - 2]
                                        subject = cell_texts[date_idx - 1]
                                    elif date_idx >= 1:
                                        subject = cell_texts[date_idx - 1]
                                    
                                    # 날짜 뒤 셀이 크기
                                    if date_idx < len(cell_texts) - 1:
                                        size = cell_texts[date_idx + 1]
                            
                            # 데이터 저장
                            if subject or sender:  # 제목이나 보낸사람이 있으면 저장
                                self.mail_data.append({
                                    '페이지': page_num,
                                    '보낸사람': sender,
                                    '제목': subject,
                                    '날짜': date,
                                    '크기': size,
                                    '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
                                scraped_count += 1
                                
                                # 처음 3개 출력
                                if scraped_count <= 3:
                                    print_status('info', f'수집: {sender[:20]} - {subject[:30]}')
                        
                        except Exception as e:
                            continue
                
                except Exception as e:
                    continue
            
            print_status('success', f'{page_num}페이지: {scraped_count}개 메일 수집')
            
        except Exception as e:
            self.logger.error(f"스크래핑 실패: {e}")
            print_status('error', f'스크래핑 실패: {e}')
    
    async def run(self, max_pages: int = 3):
        """메일 스크래핑 실행"""
        print_banner("MAIL SCRAPER FIXED")
        
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
            
            # 쿠키 설정
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            try:
                # 메인 페이지 접속
                print_status('info', '메인 페이지 접속 중...')
                await page.goto(self.config['urls']['main'])
                await page.wait_for_timeout(3000)
                
                # 메일 버튼 클릭
                print_status('info', '메일 버튼 찾는 중...')
                mail_button = await page.wait_for_selector('a[href*="mail"], button:has-text("메일")', timeout=5000)
                if mail_button:
                    await mail_button.click()
                    print_status('success', '메일 버튼 클릭')
                    await page.wait_for_timeout(3000)
                
                # 새 탭 처리
                if len(context.pages) > 1:
                    page = context.pages[-1]
                    print_status('info', '새 탭으로 전환')
                
                # 받은메일함 클릭 (선택적)
                try:
                    inbox = await page.wait_for_selector('a:has-text("받은메일함")', timeout=3000)
                    if inbox:
                        await inbox.click()
                        print_status('success', '받은메일함 클릭')
                        await page.wait_for_timeout(2000)
                except:
                    print_status('info', '이미 받은메일함')
                
                # 페이지별 스크래핑
                for page_num in range(1, max_pages + 1):
                    await self.scrape_mail_data(page, page_num)
                    
                    # 다음 페이지로 이동
                    if page_num < max_pages:
                        try:
                            # 페이지 번호 클릭
                            next_page = await page.query_selector(f'a:has-text("{page_num + 1}")')
                            if not next_page:
                                # >> 버튼 시도
                                next_page = await page.query_selector('a:has-text(">>")')
                            
                            if next_page:
                                await next_page.click()
                                print_status('info', f'{page_num + 1}페이지로 이동')
                                await page.wait_for_timeout(2000)
                            else:
                                print_status('info', f'{page_num}페이지까지만 존재')
                                break
                        except:
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
                print(f"  {i}. {mail['보낸사람']}: {mail['제목'][:30]}...")
            
        except Exception as e:
            print_status('error', f'Excel 저장 실패: {e}')


async def main():
    """메인 함수"""
    scraper = MailScraperFixed()
    success = await scraper.run(max_pages=3)
    
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
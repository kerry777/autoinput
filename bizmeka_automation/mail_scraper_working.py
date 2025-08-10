#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 실제 작동 버전
스크린샷 기반 정확한 선택자 사용
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright, Page
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


class MailScraperWorking:
    """작동하는 메일 스크래퍼"""
    
    def __init__(self):
        self.config = load_config()
        self.logger = setup_logging('mail_scraper_working')
        self.cookie_manager = CookieManager()
        self.mail_data = []
    
    async def close_popup_forcefully(self, page: Page):
        """팝업 강제 닫기"""
        print("팝업 닫기 시도 중...")
        
        # 1. ESC 키 여러 번 누르기
        for i in range(5):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(300)
        
        # 2. 확인 버튼 클릭 시도
        try:
            confirm_btn = await page.wait_for_selector('button:has-text("확인")', timeout=1000)
            if confirm_btn:
                await confirm_btn.click()
                print("확인 버튼 클릭됨")
        except:
            pass
        
        # 3. X 버튼 클릭 시도
        try:
            close_btn = await page.wait_for_selector('.ui-dialog-titlebar-close', timeout=1000)
            if close_btn:
                await close_btn.click()
                print("X 버튼 클릭됨")
        except:
            pass
        
        await page.wait_for_timeout(1000)
    
    async def extract_mail_data_direct(self, page: Page, page_num: int):
        """직접적인 메일 데이터 추출"""
        print(f"\n{page_num}페이지 데이터 추출 중...")
        
        try:
            # 먼저 팝업 닫기
            await self.close_popup_forcefully(page)
            
            # 모든 프레임에서 시도
            extracted_mails = []
            
            for frame in page.frames:
                try:
                    # 각 프레임에서 메일 추출 시도
                    frame_mails = await frame.evaluate('''() => {
                        const mails = [];
                        
                        // 여러 방법으로 테이블 찾기
                        const tables = document.querySelectorAll('table');
                        
                        for (let table of tables) {
                            const rows = table.querySelectorAll('tbody tr, tr');
                            
                            for (let row of rows) {
                                const cells = row.querySelectorAll('td');
                                
                                // 충분한 셀이 있고 날짜 패턴이 있는 경우
                                if (cells.length >= 5) {
                                    const rowTexts = [];
                                    for (let cell of cells) {
                                        const text = (cell.innerText || cell.textContent || '').trim();
                                        rowTexts.push(text);
                                    }
                                    
                                    // 날짜 패턴 확인 (2025-08-08 형식)
                                    const datePattern = /20\d{2}-\d{2}-\d{2}/;
                                    const hasDate = rowTexts.some(text => datePattern.test(text));
                                    
                                    if (hasDate) {
                                        // 날짜 인덱스 찾기
                                        const dateIdx = rowTexts.findIndex(text => datePattern.test(text));
                                        
                                        // 메일 구조 추정
                                        let mail = {
                                            sender: '',
                                            subject: '',
                                            date: '',
                                            size: ''
                                        };
                                        
                                        // bizmeka 관리자 패턴
                                        if (rowTexts.some(t => t.includes('bizmeka') || t.includes('@'))) {
                                            // 이메일 주소나 bizmeka가 포함된 텍스트 찾기
                                            const senderIdx = rowTexts.findIndex(t => 
                                                t.includes('bizmeka') || t.includes('@') || t.includes('관리자')
                                            );
                                            
                                            if (senderIdx !== -1) {
                                                mail.sender = rowTexts[senderIdx];
                                            }
                                            
                                            // 제목은 보통 보낸사람 다음
                                            if (senderIdx !== -1 && senderIdx < rowTexts.length - 1) {
                                                // [받은메일함] 같은 태그 찾기
                                                for (let i = senderIdx + 1; i < dateIdx; i++) {
                                                    if (rowTexts[i] && rowTexts[i].length > 5) {
                                                        mail.subject = rowTexts[i];
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                        
                                        // 날짜와 크기
                                        mail.date = rowTexts[dateIdx] || '';
                                        if (dateIdx < rowTexts.length - 1) {
                                            // KB/MB 패턴
                                            const sizeIdx = rowTexts.findIndex(t => 
                                                t.includes('KB') || t.includes('MB') || t.includes('GB')
                                            );
                                            if (sizeIdx !== -1) {
                                                mail.size = rowTexts[sizeIdx];
                                            }
                                        }
                                        
                                        // 유효한 메일만 추가
                                        if (mail.sender || mail.subject) {
                                            mails.push(mail);
                                        }
                                    }
                                }
                            }
                        }
                        
                        return mails;
                    }''')
                    
                    if frame_mails and len(frame_mails) > 0:
                        extracted_mails.extend(frame_mails)
                        print(f"  프레임에서 {len(frame_mails)}개 메일 발견")
                
                except Exception as e:
                    continue
            
            # 메인 페이지에서도 시도
            main_mails = await page.evaluate('''() => {
                const mails = [];
                
                // 스크린샷에서 본 구조로 직접 찾기
                const rows = document.querySelectorAll('tr');
                
                for (let row of rows) {
                    const cells = row.querySelectorAll('td');
                    
                    if (cells.length >= 7) {
                        const texts = [];
                        for (let i = 0; i < cells.length; i++) {
                            texts.push((cells[i].innerText || '').trim());
                        }
                        
                        // 날짜 패턴 체크
                        const datePattern = /20\d{2}-\d{2}-\d{2}/;
                        
                        // 일반적인 메일 테이블 구조
                        // 0: checkbox, 1: star, 2: attachment, 3: sender, 4: subject, 5: date, 6: size
                        if (datePattern.test(texts[5]) || datePattern.test(texts[6])) {
                            mails.push({
                                sender: texts[3] || '',
                                subject: texts[4] || '',
                                date: texts[5] || texts[6] || '',
                                size: texts[6] || texts[7] || ''
                            });
                        }
                        // 다른 가능한 구조
                        else if (texts.some(t => datePattern.test(t))) {
                            const dateIdx = texts.findIndex(t => datePattern.test(t));
                            if (dateIdx >= 2) {
                                mails.push({
                                    sender: texts[dateIdx - 2] || '',
                                    subject: texts[dateIdx - 1] || '',
                                    date: texts[dateIdx] || '',
                                    size: texts[dateIdx + 1] || ''
                                });
                            }
                        }
                    }
                }
                
                return mails;
            }''')
            
            if main_mails and len(main_mails) > 0:
                extracted_mails.extend(main_mails)
                print(f"  메인 페이지에서 {len(main_mails)}개 메일 발견")
            
            # 중복 제거 및 저장
            seen = set()
            for mail in extracted_mails:
                key = f"{mail['sender']}_{mail['subject']}_{mail['date']}"
                if key not in seen:
                    seen.add(key)
                    self.mail_data.append({
                        '페이지': page_num,
                        '보낸사람': mail['sender'],
                        '제목': mail['subject'],
                        '날짜': mail['date'],
                        '크기': mail['size'],
                        '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            unique_count = len(seen)
            print(f"  {page_num}페이지: {unique_count}개 고유 메일 수집됨")
            
            # 샘플 출력
            if unique_count > 0:
                for mail in self.mail_data[-3:]:  # 최근 3개
                    print(f"    - {mail['보낸사람']}: {mail['제목'][:30]}...")
            
            return unique_count
            
        except Exception as e:
            print(f"  추출 오류: {e}")
            return 0
    
    async def navigate_page(self, page: Page, target_page: int):
        """페이지 이동"""
        try:
            # 팝업 먼저 닫기
            await self.close_popup_forcefully(page)
            
            # 페이지 번호 클릭
            page_link = await page.query_selector(f'a:has-text("{target_page}")')
            if page_link:
                await page_link.click()
                print(f"{target_page}페이지로 이동")
                await page.wait_for_timeout(2000)
                return True
            
            # 다음 버튼 시도
            next_btn = await page.query_selector('a[title="다음"]')
            if next_btn:
                await next_btn.click()
                print("다음 페이지로 이동")
                await page.wait_for_timeout(2000)
                return True
                
        except Exception as e:
            print(f"페이지 이동 실패: {e}")
        
        return False
    
    async def run(self, max_pages: int = 3):
        """메일 스크래핑 실행"""
        print("\n" + "="*60)
        print("Bizmeka 메일 스크래퍼 - 작동 버전")
        print("="*60)
        
        # 쿠키 확인
        cookies = self.cookie_manager.load_cookies()
        if not cookies:
            print("[ERROR] 쿠키 없음 - manual_login.py 먼저 실행하세요")
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
                # 메인 페이지
                print("\n메인 페이지 접속 중...")
                await page.goto(self.config['urls']['main'])
                await page.wait_for_timeout(3000)
                
                # 메일 버튼 클릭
                print("메일 버튼 클릭...")
                mail_btn = await page.wait_for_selector('a[href*="mail"]', timeout=5000)
                if mail_btn:
                    await mail_btn.click()
                    await page.wait_for_timeout(3000)
                
                # 새 탭 처리
                if len(context.pages) > 1:
                    page = context.pages[-1]
                    print("새 탭으로 전환")
                
                # 초기 팝업 닫기
                await self.close_popup_forcefully(page)
                
                # 받은메일함 확인
                try:
                    inbox = await page.wait_for_selector('a:has-text("받은메일함")', timeout=2000)
                    if inbox:
                        await inbox.click()
                        print("받은메일함 클릭")
                        await page.wait_for_timeout(2000)
                except:
                    print("이미 받은메일함에 있음")
                
                # 페이지별 수집
                total_collected = 0
                for page_num in range(1, max_pages + 1):
                    count = await self.extract_mail_data_direct(page, page_num)
                    total_collected += count
                    
                    if page_num < max_pages:
                        if not await self.navigate_page(page, page_num + 1):
                            break
                
                # 결과 저장
                if self.mail_data:
                    self.save_to_excel()
                    print(f"\n[OK] 총 {len(self.mail_data)}개 메일 수집 완료")
                else:
                    print("\n[WARN] 수집된 메일이 없습니다")
                
                await browser.close()
                return True
                
            except Exception as e:
                print(f"\n[ERROR] 오류 발생: {e}")
                await browser.close()
                return False
    
    def save_to_excel(self):
        """Excel 저장"""
        try:
            df = pd.DataFrame(self.mail_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\n[EXCEL] Excel 파일 저장: {filename}")
            
            # 요약 출력
            print("\n[수집 요약]")
            print(f"  - 총 메일 수: {len(self.mail_data)}개")
            print(f"  - 파일 위치: {filename}")
            
            # 샘플 데이터
            print("\n[샘플 데이터 - 처음 5개]")
            for i, mail in enumerate(self.mail_data[:5], 1):
                sender = mail['보낸사람'][:20] if mail['보낸사람'] else 'Unknown'
                subject = mail['제목'][:40] if mail['제목'] else 'No subject'
                print(f"  {i}. {sender}: {subject}...")
                
        except Exception as e:
            print(f"[ERROR] Excel 저장 실패: {e}")


if __name__ == "__main__":
    scraper = MailScraperWorking()
    asyncio.run(scraper.run(max_pages=3))
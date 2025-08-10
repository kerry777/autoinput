#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 리스트를 Excel로 저장
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright


async def mail_to_excel():
    print("\n" + "="*60)
    print("Bizmeka Mail to Excel")
    print("="*60)
    
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
    data_dir = Path("C:\\projects\\autoinput\\data")
    
    # 쿠키 로드
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"\n[1] Loaded {len(cookies)} cookies")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        # 쿠키 주입
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 메인 페이지 접속 (중요: 이 순서대로 해야 함)
        print("[2] Going to main page...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        # 로그인 확인
        if 'loginForm' in page.url:
            print("[ERROR] Not logged in!")
            await browser.close()
            return
        
        print("[3] Login successful")
        
        # 메일 버튼 찾기
        print("[4] Looking for mail button...")
        
        # 여러 선택자 시도
        mail_selectors = [
            'a[onclick*="webmail"]',
            'a[onclick*="mail"]',
            'button:has-text("메일")',
            'a:has-text("웹메일")',
            '[class*="mail"]',
            'a[href*="mail"]'
        ]
        
        mail_clicked = False
        for selector in mail_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=2000)
                if btn:
                    await btn.click()
                    print(f"   Clicked: {selector}")
                    mail_clicked = True
                    break
            except:
                continue
        
        if not mail_clicked:
            print("   Mail button not found, trying direct URL...")
            # JavaScript로 새 창 열기
            await page.evaluate('''() => {
                window.open('https://ezwebmail.bizmeka.com/mail/list.do', '_blank');
            }''')
        
        await page.wait_for_timeout(3000)
        
        # 새 탭 처리
        if len(context.pages) > 1:
            mail_page = context.pages[-1]
            print("[5] Switched to mail tab")
        else:
            mail_page = page
        
        await mail_page.wait_for_timeout(3000)
        
        # 팝업 닫기
        print("[6] Closing popups...")
        for _ in range(5):
            await mail_page.keyboard.press('Escape')
            await mail_page.wait_for_timeout(300)
        
        # 메일 데이터 추출
        print("[7] Extracting mail data...")
        
        all_mails = []
        
        # 여러 페이지 스크래핑 (최대 3페이지)
        for page_num in range(1, 4):
            print(f"\n   Page {page_num}:")
            
            # 팝업 다시 닫기
            await mail_page.keyboard.press('Escape')
            await mail_page.wait_for_timeout(500)
            
            # 데이터 추출
            mail_data = await mail_page.evaluate('''() => {
                const mails = [];
                
                // li.m_data 구조 우선 시도
                let items = document.querySelectorAll('li.m_data');
                
                if (items.length > 0) {
                    // Bizmeka 메일 구조
                    for (let item of items) {
                        const checkbox = item.querySelector('input.mailcb');
                        const sender = item.querySelector('.m_sender');
                        const subject = item.querySelector('.m_subject');
                        const date = item.querySelector('.m_date');
                        const size = item.querySelector('.m_size');
                        
                        if (sender && subject) {
                            mails.push({
                                id: checkbox ? checkbox.value : '',
                                sender: sender.textContent.trim(),
                                subject: subject.textContent.trim(),
                                date: date ? date.textContent.trim() : '',
                                size: size ? size.textContent.trim() : '',
                                unread: item.classList.contains('unread')
                            });
                        }
                    }
                } else {
                    // 테이블 구조 시도
                    const rows = document.querySelectorAll('tr');
                    for (let row of rows) {
                        const checkbox = row.querySelector('input[type="checkbox"]');
                        if (checkbox) {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 4) {
                                mails.push({
                                    sender: cells[2]?.textContent?.trim() || '',
                                    subject: cells[3]?.textContent?.trim() || '',
                                    date: cells[4]?.textContent?.trim() || '',
                                    size: cells[5]?.textContent?.trim() || ''
                                });
                            }
                        }
                    }
                }
                
                return mails;
            }''')
            
            print(f"   Found {len(mail_data)} mails")
            
            if mail_data:
                all_mails.extend(mail_data)
                
                # 샘플 출력
                if page_num == 1 and len(mail_data) > 0:
                    print("   Sample:")
                    for mail in mail_data[:3]:
                        print(f"     - {mail['sender'][:20]}: {mail['subject'][:30]}")
            
            # 다음 페이지로 이동
            if page_num < 3:
                try:
                    next_btn = await mail_page.wait_for_selector(f'a:has-text("{page_num + 1}")', timeout=2000)
                    if next_btn:
                        await next_btn.click()
                        await mail_page.wait_for_timeout(2000)
                except:
                    print(f"   No page {page_num + 1}")
                    break
        
        # Excel 저장
        if all_mails:
            print(f"\n[8] Saving {len(all_mails)} mails to Excel...")
            
            df = pd.DataFrame(all_mails)
            
            # 컬럼 순서 정리
            columns = ['sender', 'subject', 'date', 'size']
            if 'id' in df.columns:
                columns = ['id'] + columns
            if 'unread' in df.columns:
                columns = columns + ['unread']
            
            df = df[columns]
            
            # 파일 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = data_dir / f"bizmeka_mails_{timestamp}.xlsx"
            
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"\n" + "="*60)
            print(f"SUCCESS! Saved to:")
            print(f"{filename}")
            print(f"Total: {len(df)} mails")
            print("="*60)
        else:
            print("\n[ERROR] No mail data found")
        
        print("\nBrowser will close in 10 seconds...")
        await mail_page.wait_for_timeout(10000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(mail_to_excel())
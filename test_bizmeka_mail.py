#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 직접 테스트
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright


async def test_mail():
    data_dir = Path("C:\\projects\\autoinput\\data")
    cookie_file = data_dir / "bizmeka_cookies.json"
    
    # 쿠키 로드
    with open(cookie_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"Cookies loaded: {len(cookies)}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        # 쿠키 주입
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 직접 메일 페이지로
        print("Going to mail page...")
        await page.goto("https://ezwebmail.bizmeka.com/mail/list.do")
        await page.wait_for_timeout(5000)
        
        # URL 확인
        print(f"Current URL: {page.url}")
        
        # 팝업 닫기 (ESC)
        for _ in range(3):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 메일 리스트 추출
        print("\nExtracting mail data...")
        mail_data = await page.evaluate('''() => {
            const mails = [];
            
            // 방법 1: li.m_data 구조
            let items = document.querySelectorAll('li.m_data');
            
            // 방법 2: 테이블 구조
            if (items.length === 0) {
                const rows = document.querySelectorAll('tr');
                for (let row of rows) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length > 3) {
                        mails.push({
                            sender: cells[1]?.textContent?.trim() || '',
                            subject: cells[2]?.textContent?.trim() || '',
                            date: cells[3]?.textContent?.trim() || ''
                        });
                    }
                }
            } else {
                // li.m_data 처리
                for (let item of items) {
                    const sender = item.querySelector('.m_sender');
                    const subject = item.querySelector('.m_subject');
                    const date = item.querySelector('.m_date');
                    
                    if (sender && subject) {
                        mails.push({
                            sender: sender.textContent.trim(),
                            subject: subject.textContent.trim(),
                            date: date ? date.textContent.trim() : ''
                        });
                    }
                }
            }
            
            return mails;
        }''')
        
        print(f"Found {len(mail_data)} mails")
        
        if mail_data:
            # 처음 5개만 출력
            for i, mail in enumerate(mail_data[:5], 1):
                print(f"{i}. {mail['sender'][:30]} - {mail['subject'][:40]}")
            
            # Excel 저장
            df = pd.DataFrame(mail_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = data_dir / f"bizmeka_mails_{timestamp}.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\nSaved to: {filename}")
            print(f"Total: {len(df)} mails")
        else:
            print("No mail data found")
            
            # 페이지 구조 확인
            structure = await page.evaluate('''() => {
                return {
                    li_count: document.querySelectorAll('li').length,
                    tr_count: document.querySelectorAll('tr').length,
                    div_count: document.querySelectorAll('div').length,
                    url: window.location.href,
                    title: document.title
                };
            }''')
            print(f"\nPage structure: {structure}")
        
        print("\nKeeping browser open for 30 seconds...")
        await page.wait_for_timeout(30000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_mail())
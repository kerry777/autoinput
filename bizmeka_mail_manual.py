#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 - 수동 확인 후 추출
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright


async def manual_mail():
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
    data_dir = Path("C:\\projects\\autoinput\\data")
    
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR", 
            timezone_id="Asia/Seoul"
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 메인 페이지
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        print("\n" + "="*60)
        print("MANUAL STEPS REQUIRED:")
        print("="*60)
        print("1. Click on Mail/Webmail button in the browser")
        print("2. Close any popups with ESC or X button")
        print("3. Make sure you can see the mail list")
        print("4. Then press Enter here")
        print("="*60)
        
        input("\nPress Enter when mail list is visible: ")
        
        # 현재 활성 페이지 가져오기
        pages = context.pages
        mail_page = pages[-1]  # 마지막 탭이 메일 페이지일 것
        
        print("\nExtracting mail data...")
        
        # 데이터 추출
        mail_data = await mail_page.evaluate('''() => {
            const mails = [];
            
            // 모든 가능한 메일 요소 찾기
            const selectors = [
                'li.m_data',  // Bizmeka 구조
                'tr:has(input[type="checkbox"])',  // 테이블 구조
                'div.mail-item',  // 다른 가능한 구조
                'tr.mail-row'
            ];
            
            for (let selector of selectors) {
                const items = document.querySelectorAll(selector);
                if (items.length > 0) {
                    console.log(`Found ${items.length} items with selector: ${selector}`);
                    
                    for (let item of items) {
                        // 텍스트 내용 전체 가져오기
                        const text = item.textContent;
                        if (text && text.length > 10) {
                            mails.push({
                                raw: text.replace(/\\s+/g, ' ').trim(),
                                html: item.innerHTML.substring(0, 200)
                            });
                        }
                    }
                    break;
                }
            }
            
            // 아무것도 못찾으면 모든 텍스트 요소 확인
            if (mails.length === 0) {
                const allElements = document.querySelectorAll('*');
                for (let elem of allElements) {
                    const text = elem.textContent;
                    if (text && text.includes('@') && text.length > 20 && text.length < 500) {
                        mails.push({
                            raw: text.replace(/\\s+/g, ' ').trim()
                        });
                    }
                }
            }
            
            return mails;
        }''')
        
        print(f"Found {len(mail_data)} potential mail items")
        
        if mail_data:
            # 파싱
            parsed_mails = []
            for item in mail_data:
                text = item['raw']
                
                # 이메일 주소 찾기
                import re
                email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
                
                parsed_mails.append({
                    'content': text[:200],
                    'email': email_match.group(0) if email_match else '',
                    'length': len(text)
                })
            
            # Excel 저장
            df = pd.DataFrame(parsed_mails)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = data_dir / f"bizmeka_mails_raw_{timestamp}.xlsx"
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"\nSaved to: {filename}")
            print(f"Total items: {len(df)}")
            
            # 샘플 출력
            for i, mail in enumerate(parsed_mails[:5], 1):
                print(f"\n{i}. {mail['content'][:100]}...")
        else:
            print("No data found")
        
        print("\nKeeping browser open for manual inspection...")
        print("Press Ctrl+C to close")
        
        try:
            await asyncio.sleep(300)  # 5분 대기
        except KeyboardInterrupt:
            pass
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(manual_mail())
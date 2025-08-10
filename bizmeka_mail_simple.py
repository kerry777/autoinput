#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 직접 추출 - 간단 버전
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright


async def extract_mail():
    print("\n" + "="*60)
    print("Bizmeka 메일 추출 - 간단 버전")
    print("="*60)
    
    cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
    data_dir = Path("C:\\projects\\autoinput\\data")
    
    # 쿠키 로드
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    
    print(f"\n[1] 쿠키 {len(cookies)}개 로드")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale="ko-KR",
            timezone_id="Asia/Seoul"
        )
        
        # 쿠키 주입
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        print("[2] 메인 페이지 접속...")
        await page.goto("https://www.bizmeka.com/app/main.do")
        await page.wait_for_timeout(3000)
        
        # 로그인 확인
        current_url = page.url
        if 'loginForm' in current_url:
            print("[ERROR] 로그인 실패")
            await browser.close()
            return
        
        print("[3] 로그인 성공")
        
        # JavaScript로 메일 페이지 열기
        print("[4] 메일 페이지 열기...")
        await page.evaluate('''() => {
            window.open('https://ezwebmail.bizmeka.com/mail/list.do', 'mail');
        }''')
        
        await page.wait_for_timeout(5000)
        
        # 새 탭으로 전환
        all_pages = context.pages
        print(f"[5] 열린 탭 수: {len(all_pages)}")
        
        if len(all_pages) > 1:
            mail_page = all_pages[-1]
            print(f"    메일 탭 URL: {mail_page.url}")
        else:
            mail_page = page
        
        # 팝업 닫기
        print("[6] 팝업 닫기...")
        for _ in range(5):
            await mail_page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 메일 데이터 추출
        print("[7] 메일 데이터 추출...")
        
        mail_data = await mail_page.evaluate('''() => {
            const mails = [];
            
            // 모든 li 요소 확인
            const items = document.querySelectorAll('li.m_data');
            console.log('Found li.m_data:', items.length);
            
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
            
            // li.m_data가 없으면 테이블 구조 시도
            if (mails.length === 0) {
                const rows = document.querySelectorAll('tr');
                console.log('Found tr:', rows.length);
                
                for (let row of rows) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 4) {
                        const text = row.textContent;
                        if (text.includes('@')) {
                            mails.push({
                                sender: cells[2]?.textContent?.trim() || '',
                                subject: cells[3]?.textContent?.trim() || '',
                                date: cells[4]?.textContent?.trim() || ''
                            });
                        }
                    }
                }
            }
            
            return mails;
        }''')
        
        print(f"[8] 추출된 메일: {len(mail_data)}개")
        
        if mail_data:
            # 첫 5개 출력
            print("\n샘플 메일:")
            for i, mail in enumerate(mail_data[:5], 1):
                print(f"  {i}. {mail['sender'][:30]} - {mail['subject'][:40]}")
            
            # Excel 저장
            df = pd.DataFrame(mail_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = data_dir / f"bizmeka_mails_{timestamp}.xlsx"
            
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print("\n" + "="*60)
            print(f"성공! Excel 파일 저장:")
            print(f"{filename}")
            print(f"총 {len(df)}개 메일 저장")
            print("="*60)
        else:
            print("\n메일 데이터를 찾을 수 없습니다.")
            print("브라우저에서 직접 확인하세요.")
        
        print("\n브라우저는 30초 후 자동으로 닫힙니다.")
        await page.wait_for_timeout(30000)
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(extract_mail())
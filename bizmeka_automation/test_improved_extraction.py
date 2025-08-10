#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
개선된 메일 데이터 추출 테스트
실제 테이블 구조 기반 추출
"""

import asyncio
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config, print_status
from datetime import datetime


async def test_improved_extraction():
    """개선된 데이터 추출 테스트"""
    
    config = load_config()
    cookie_manager = CookieManager()
    
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print_status('error', '쿠키 없음')
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone']
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 메인 페이지
        await page.goto(config['urls']['main'])
        await page.wait_for_timeout(3000)
        
        # 메일 클릭
        mail_btn = await page.wait_for_selector('a[href*="mail"]', timeout=5000)
        if mail_btn:
            await mail_btn.click()
            await page.wait_for_timeout(3000)
        
        # 새 탭 처리
        if len(context.pages) > 1:
            page = context.pages[-1]
        
        # 팝업 닫기 (ESC)
        for _ in range(3):
            try:
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
            except:
                pass
        
        print("\n" + "="*60)
        print("개선된 메일 추출 테스트")
        print("="*60)
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f'data/test_extraction_{timestamp}.png'
        await page.screenshot(path=screenshot_path)
        print(f"스크린샷 저장: {screenshot_path}")
        
        # 개선된 추출 로직
        mail_data = await page.evaluate('''() => {
            const mails = [];
            
            // 메일 테이블 행 찾기 - 더 구체적인 선택자 사용
            const rows = document.querySelectorAll('table tbody tr');
            console.log('Total rows found:', rows.length);
            
            for (let row of rows) {
                // 체크박스가 있는 행만 처리
                const checkbox = row.querySelector('input[type="checkbox"]');
                if (!checkbox || checkbox.id === 'checkAll') continue;
                
                const cells = row.querySelectorAll('td');
                console.log('Row cells:', cells.length);
                
                if (cells.length >= 7) {
                    // 각 셀에서 텍스트 추출
                    const mailInfo = {
                        checkbox: cells[0]?.innerText?.trim() || '',
                        star: cells[1]?.innerText?.trim() || '',
                        attachment: cells[2]?.innerText?.trim() || '',
                        sender: cells[3]?.innerText?.trim() || '',
                        subject: cells[4]?.innerText?.trim() || '',
                        date: cells[5]?.innerText?.trim() || '',
                        size: cells[6]?.innerText?.trim() || ''
                    };
                    
                    console.log('Extracted mail:', mailInfo);
                    
                    // 보낸사람과 제목이 있는 경우만 추가
                    if (mailInfo.sender || mailInfo.subject) {
                        mails.push(mailInfo);
                    }
                }
            }
            
            // 다른 방법: class나 id로 찾기
            if (mails.length === 0) {
                // 메일 리스트 테이블을 더 구체적으로 찾기
                const mailTable = document.querySelector('table[id*="mail"], table[class*="mail"], table[class*="list"]');
                if (mailTable) {
                    const tableRows = mailTable.querySelectorAll('tbody tr');
                    console.log('Mail table rows:', tableRows.length);
                    
                    for (let row of tableRows) {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 5) {
                            const rowData = [];
                            for (let cell of cells) {
                                rowData.push(cell.innerText?.trim() || '');
                            }
                            
                            // 날짜 패턴 확인
                            const hasDate = rowData.some(text => 
                                text.includes('2025-') || text.includes('2024-')
                            );
                            
                            if (hasDate) {
                                // 날짜 위치 찾기
                                const dateIndex = rowData.findIndex(text => 
                                    text.includes('2025-') || text.includes('2024-')
                                );
                                
                                if (dateIndex >= 2) {
                                    mails.push({
                                        sender: rowData[dateIndex - 2] || '',
                                        subject: rowData[dateIndex - 1] || '',
                                        date: rowData[dateIndex] || '',
                                        size: rowData[dateIndex + 1] || ''
                                    });
                                }
                            }
                        }
                    }
                }
            }
            
            return {
                mailCount: mails.length,
                mails: mails,
                debug: {
                    totalTables: document.querySelectorAll('table').length,
                    totalRows: document.querySelectorAll('tr').length,
                    totalCheckboxes: document.querySelectorAll('input[type="checkbox"]').length
                }
            };
        }''')
        
        print(f"\n디버그 정보:")
        print(f"  총 테이블 수: {mail_data['debug']['totalTables']}")
        print(f"  총 행 수: {mail_data['debug']['totalRows']}")
        print(f"  총 체크박스 수: {mail_data['debug']['totalCheckboxes']}")
        
        print(f"\n추출된 메일: {mail_data['mailCount']}개")
        
        if mail_data['mails']:
            for i, mail in enumerate(mail_data['mails'][:5], 1):
                print(f"\n메일 {i}:")
                print(f"  보낸사람: {mail.get('sender', 'N/A')}")
                print(f"  제목: {mail.get('subject', 'N/A')}")
                print(f"  날짜: {mail.get('date', 'N/A')}")
                print(f"  크기: {mail.get('size', 'N/A')}")
        else:
            print("\n메일을 찾지 못했습니다.")
            print("페이지 구조를 다시 분석합니다...")
            
            # iframe 확인
            frames = page.frames
            print(f"\n프레임 수: {len(frames)}")
            
            for i, frame in enumerate(frames):
                try:
                    frame_url = frame.url
                    if 'mail' in frame_url.lower():
                        print(f"\n메일 프레임 발견: {frame_url[:50]}...")
                        
                        # 프레임 내에서 추출
                        frame_data = await frame.evaluate('''() => {
                            const rows = document.querySelectorAll('tr');
                            const mails = [];
                            
                            for (let row of rows) {
                                const cells = row.querySelectorAll('td');
                                if (cells.length >= 5) {
                                    const rowText = [];
                                    for (let cell of cells) {
                                        rowText.push(cell.innerText?.trim() || '');
                                    }
                                    
                                    // 날짜가 있는 행만
                                    if (rowText.some(t => t.includes('2025-') || t.includes('2024-'))) {
                                        mails.push(rowText);
                                    }
                                }
                            }
                            
                            return mails;
                        }''')
                        
                        if frame_data:
                            print(f"프레임에서 {len(frame_data)}개 메일 발견")
                            for j, mail_row in enumerate(frame_data[:3], 1):
                                print(f"  메일 {j}: {' | '.join(mail_row[:5])}")
                except:
                    continue
        
        print("\n테스트 완료. 브라우저를 닫으려면 Enter...")
        input()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_improved_extraction())
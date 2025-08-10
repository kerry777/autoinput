#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
메일 데이터 추출 테스트
프레임 구조 확인 및 데이터 추출
"""

import asyncio
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config, print_status


async def test_extraction():
    """데이터 추출 테스트"""
    
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
        
        # 팝업 닫기
        try:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
        except:
            pass
        
        # 받은메일함
        try:
            inbox = await page.wait_for_selector('a:has-text("받은메일함")', timeout=2000)
            if inbox:
                await inbox.click()
                await page.wait_for_timeout(2000)
        except:
            pass
        
        # 팝업 다시 닫기
        try:
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
        except:
            pass
        
        print("\n" + "="*60)
        print("프레임 분석")
        print("="*60)
        
        # 모든 프레임 확인
        frames = page.frames
        print(f"프레임 수: {len(frames)}")
        
        mail_found = False
        
        for i, frame in enumerate(frames):
            try:
                url = frame.url
                print(f"\n프레임 {i}: {url[:50]}...")
                
                # 각 프레임에서 데이터 추출 시도
                data = await frame.evaluate('''() => {
                    const result = {
                        tables: document.querySelectorAll('table').length,
                        rows: document.querySelectorAll('tr').length,
                        cells: document.querySelectorAll('td').length,
                        mails: []
                    };
                    
                    // 모든 행 검사
                    const rows = document.querySelectorAll('tr');
                    for (let row of rows) {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 5) {
                            const cellTexts = [];
                            for (let cell of cells) {
                                const text = cell.innerText || cell.textContent || '';
                                cellTexts.push(text.trim().substring(0, 50));
                            }
                            
                            // 날짜 패턴 확인
                            const hasDate = cellTexts.some(t => 
                                t.includes('2025-') || t.includes('2024-')
                            );
                            
                            if (hasDate) {
                                result.mails.push(cellTexts);
                            }
                        }
                    }
                    
                    return result;
                }''')
                
                print(f"  테이블: {data['tables']}, 행: {data['rows']}, 셀: {data['cells']}")
                
                if data['mails'] and len(data['mails']) > 0:
                    print(f"  [메일 데이터 발견!] {len(data['mails'])}개")
                    mail_found = True
                    
                    for j, mail in enumerate(data['mails'][:3]):
                        print(f"    메일 {j+1}:")
                        for k, cell in enumerate(mail[:7]):
                            if cell:
                                print(f"      컬럼 {k}: {cell}")
                
            except Exception as e:
                print(f"  프레임 {i} 오류: {e}")
        
        if not mail_found:
            print("\n메일 데이터를 찾지 못했습니다.")
            print("페이지 소스를 확인합니다...")
            
            # 현재 페이지 HTML 저장
            html = await page.content()
            with open('data/test_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("data/test_page.html 저장됨")
        
        print("\n테스트 완료. 브라우저를 닫으려면 Enter...")
        input()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_extraction())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 단순화 버전
가장 기본적인 방법으로 추출
"""

import asyncio
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config


async def scrape_mails():
    """메일 스크래핑 메인 함수"""
    
    config = load_config()
    cookie_manager = CookieManager()
    
    # 쿠키 로드
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print("[ERROR] 쿠키 없음")
        return
    
    print("\n" + "="*60)
    print("Bizmeka 메일 스크래퍼 - 단순화 버전")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 메인 페이지
        print("\n1. 메인 페이지 접속...")
        await page.goto(config['urls']['main'])
        await page.wait_for_timeout(3000)
        
        # 메일 버튼 클릭
        print("2. 메일 접속...")
        mail_link = await page.query_selector('a[href*="mail"]')
        if mail_link:
            await mail_link.click()
            await page.wait_for_timeout(3000)
        
        # 새 탭 처리
        if len(context.pages) > 1:
            page = context.pages[-1]
        
        # ESC로 팝업 닫기
        print("3. 팝업 처리...")
        for _ in range(3):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 메일 데이터 수집
        print("4. 메일 데이터 수집...")
        all_mails = []
        
        for page_num in range(1, 4):  # 3페이지
            print(f"\n   페이지 {page_num} 처리 중...")
            
            # ESC로 팝업 닫기
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            
            # 테이블 행 찾기 - 단순한 선택자 사용
            rows = await page.query_selector_all('tr')
            print(f"   → {len(rows)}개 행 발견")
            
            page_mails = []
            for row in rows:
                try:
                    # 체크박스 확인
                    checkbox = await row.query_selector('input[type="checkbox"]')
                    if not checkbox:
                        continue
                    
                    # checkbox id가 'checkAll'이면 헤더
                    checkbox_id = await checkbox.get_attribute('id')
                    if checkbox_id == 'checkAll':
                        continue
                    
                    # 셀 추출
                    cells = await row.query_selector_all('td')
                    if len(cells) < 6:
                        continue
                    
                    # 텍스트 추출
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip() if text else '')
                    
                    # 날짜 패턴 확인 (2025-08-08 형식)
                    has_date = any('202' in text and '-' in text for text in cell_texts)
                    
                    if has_date:
                        # 데이터 매핑 (일반적인 구조)
                        mail_data = {
                            '페이지': page_num,
                            '보낸사람': cell_texts[3] if len(cell_texts) > 3 else '',
                            '제목': cell_texts[4] if len(cell_texts) > 4 else '',
                            '날짜': cell_texts[5] if len(cell_texts) > 5 else '',
                            '크기': cell_texts[6] if len(cell_texts) > 6 else '',
                            '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        # 유효한 데이터만 추가
                        if mail_data['보낸사람'] or mail_data['제목']:
                            page_mails.append(mail_data)
                            
                            # 처음 몇 개만 출력
                            if len(page_mails) <= 3:
                                sender = mail_data['보낸사람'][:20] if mail_data['보낸사람'] else 'Unknown'
                                subject = mail_data['제목'][:30] if mail_data['제목'] else 'No subject'
                                print(f"      • {sender}: {subject}...")
                
                except Exception as e:
                    continue
            
            print(f"   → {len(page_mails)}개 메일 수집")
            all_mails.extend(page_mails)
            
            # 다음 페이지로 이동
            if page_num < 3:
                try:
                    # 페이지 번호 클릭
                    next_page = page_num + 1
                    page_link = await page.query_selector(f'a:has-text("{next_page}")')
                    if page_link:
                        await page_link.click()
                        print(f"   → {next_page}페이지로 이동")
                        await page.wait_for_timeout(2000)
                except:
                    print(f"   → 페이지 이동 실패")
                    break
        
        # 결과 저장
        print("\n" + "="*60)
        if all_mails:
            # DataFrame 생성
            df = pd.DataFrame(all_mails)
            
            # Excel 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"[SUCCESS] 메일 수집 완료!")
            print(f"  • 총 메일 수: {len(all_mails)}개")
            print(f"  • 저장 파일: {filename}")
            
            # 요약
            print(f"\n[수집 요약]")
            for i, mail in enumerate(all_mails[:5], 1):
                sender = mail['보낸사람'][:20] if mail['보낸사람'] else 'Unknown'
                subject = mail['제목'][:40] if mail['제목'] else 'No subject'
                print(f"  {i}. {sender}: {subject}...")
        else:
            print("[WARNING] 수집된 메일이 없습니다")
            
            # 디버깅 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            await page.screenshot(path=f'data/debug_{timestamp}.png')
            print(f"[DEBUG] 스크린샷 저장됨")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_mails())
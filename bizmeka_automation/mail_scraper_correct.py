#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 올바른 선택자 버전
실제 HTML 구조 기반
"""

import asyncio
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config


async def scrape_bizmeka_mails():
    """메일 스크래핑"""
    
    config = load_config()
    cookie_manager = CookieManager()
    
    # 쿠키 로드
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print("[ERROR] 쿠키 없음 - manual_login.py 먼저 실행")
        return
    
    print("\n" + "="*60)
    print("Bizmeka 메일 스크래퍼 - 최종 버전")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 1. 메인 페이지
        print("\n1. 메인 페이지 접속...")
        await page.goto(config['urls']['main'])
        await page.wait_for_timeout(3000)
        
        # 2. 메일 버튼 클릭
        print("2. 메일 시스템 접속...")
        mail_link = await page.query_selector('a[href*="mail"]')
        if mail_link:
            await mail_link.click()
            await page.wait_for_timeout(3000)
        
        # 새 탭 처리
        if len(context.pages) > 1:
            page = context.pages[-1]
            print("   → 새 탭 전환")
        
        # 3. 팝업 닫기
        print("3. 팝업 처리...")
        for _ in range(3):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 4. 받은메일함 클릭 - 올바른 선택자 사용
        print("4. 받은메일함 접속...")
        try:
            # ID로 직접 찾기
            inbox = await page.query_selector('#mnu_Inbox_kilmoon')
            if not inbox:
                # 텍스트로 찾기
                inbox = await page.query_selector('a:has-text("받은메일함")')
            
            if inbox:
                await inbox.click()
                print("   → 받은메일함 클릭 완료")
                await page.wait_for_timeout(3000)
            else:
                print("   → 받은메일함 링크를 찾을 수 없음")
        except Exception as e:
            print(f"   → 받은메일함 접속 오류: {e}")
        
        # 팝업 다시 닫기
        for _ in range(2):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 5. 메일 데이터 수집
        print("\n5. 메일 데이터 수집 시작...")
        print("-" * 40)
        
        all_mails = []
        
        for page_num in range(1, 4):  # 3페이지
            print(f"\n페이지 {page_num} 수집 중...")
            
            # 팝업 닫기
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            
            # iframe 확인
            frames = page.frames
            target_frame = page  # 기본값
            
            # mail 관련 iframe 찾기
            for frame in frames:
                if 'mail' in frame.url.lower():
                    target_frame = frame
                    print(f"   → 메일 프레임 발견")
                    break
            
            # 메일 데이터 추출
            try:
                # JavaScript로 직접 추출
                mails = await target_frame.evaluate('''() => {
                    const results = [];
                    const rows = document.querySelectorAll('tr');
                    
                    for (let row of rows) {
                        const cells = row.querySelectorAll('td');
                        
                        // 체크박스 확인
                        const checkbox = row.querySelector('input[type="checkbox"]');
                        if (!checkbox || checkbox.id === 'checkAll') continue;
                        
                        if (cells.length >= 6) {
                            const cellTexts = [];
                            for (let i = 0; i < cells.length; i++) {
                                const text = cells[i].innerText || cells[i].textContent || '';
                                cellTexts.push(text.trim());
                            }
                            
                            // 날짜 패턴 확인
                            const hasDate = cellTexts.some(t => t.includes('2025-') || t.includes('2024-'));
                            
                            if (hasDate) {
                                // 일반적인 테이블 구조
                                // 0: checkbox, 1: star, 2: attach, 3: sender, 4: subject, 5: date, 6: size
                                results.push({
                                    sender: cellTexts[3] || '',
                                    subject: cellTexts[4] || '',
                                    date: cellTexts[5] || '',
                                    size: cellTexts[6] || ''
                                });
                            }
                        }
                    }
                    
                    return results;
                }''')
                
                if mails:
                    print(f"   → {len(mails)}개 메일 발견")
                    
                    for mail in mails:
                        mail_data = {
                            '페이지': page_num,
                            '보낸사람': mail['sender'],
                            '제목': mail['subject'],
                            '날짜': mail['date'],
                            '크기': mail['size'],
                            '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        all_mails.append(mail_data)
                        
                        # 샘플 출력
                        if len(all_mails) <= 5:
                            sender = mail['sender'][:20] if mail['sender'] else 'Unknown'
                            subject = mail['subject'][:30] if mail['subject'] else 'No subject'
                            print(f"      • {sender}: {subject}...")
                else:
                    print(f"   → 메일을 찾을 수 없음")
                    
                    # 백업 방법: 수동으로 행 확인
                    rows = await target_frame.query_selector_all('tr')
                    print(f"   → {len(rows)}개 행 확인 중...")
                    
                    for row in rows[:10]:  # 처음 10개만
                        try:
                            cells = await row.query_selector_all('td')
                            if len(cells) >= 6:
                                cell_texts = []
                                for cell in cells:
                                    text = await cell.inner_text()
                                    cell_texts.append(text.strip() if text else '')
                                
                                # 날짜 확인
                                if any('202' in t and '-' in t for t in cell_texts):
                                    print(f"      데이터 행: {' | '.join(cell_texts[:7])}")
                        except:
                            continue
                    
            except Exception as e:
                print(f"   → 추출 오류: {e}")
            
            # 다음 페이지로 이동
            if page_num < 3:
                try:
                    next_page = page_num + 1
                    # 페이지 링크 찾기
                    page_link = await target_frame.query_selector(f'a:has-text("{next_page}")')
                    if not page_link:
                        # 페이지네이션 영역에서 찾기
                        page_link = await target_frame.query_selector(f'[class*="pag"] a:has-text("{next_page}")')
                    
                    if page_link:
                        await page_link.click()
                        print(f"   → {next_page}페이지로 이동")
                        await page.wait_for_timeout(2000)
                    else:
                        print(f"   → 페이지 링크를 찾을 수 없음")
                except Exception as e:
                    print(f"   → 페이지 이동 실패: {e}")
        
        # 6. 결과 저장
        print("\n" + "="*60)
        if all_mails:
            # DataFrame 생성
            df = pd.DataFrame(all_mails)
            
            # Excel 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            
            # 열 너비 조정된 Excel 저장
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='메일목록')
                
                # 열 너비 자동 조정
                worksheet = writer.sheets['메일목록']
                for column in df:
                    column_width = max(df[column].astype(str).str.len().max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    if col_idx < 26:  # Excel 열 제한
                        worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 50)
            
            print(f"[SUCCESS] 메일 수집 완료!")
            print(f"\n[수집 결과]")
            print(f"  • 총 메일 수: {len(all_mails)}개")
            print(f"  • 저장 파일: {filename}")
            
            # 요약
            print(f"\n[메일 샘플]")
            for i, mail in enumerate(all_mails[:5], 1):
                sender = mail['보낸사람'][:20] if mail['보낸사람'] else 'Unknown'
                subject = mail['제목'][:40] if mail['제목'] else 'No subject'
                date = mail['날짜'][:10] if mail['날짜'] else 'No date'
                print(f"  {i}. [{date}] {sender}: {subject}...")
            
            # 발신자 통계
            if '보낸사람' in df.columns:
                top_senders = df['보낸사람'].value_counts().head(3)
                if not top_senders.empty:
                    print(f"\n[주요 발신자]")
                    for sender, count in top_senders.items():
                        print(f"  • {sender}: {count}개")
        else:
            print("[WARNING] 수집된 메일이 없습니다")
            
            # 디버깅 정보
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f'data/debug_{timestamp}.png'
            await page.screenshot(path=screenshot_path)
            print(f"\n[DEBUG] 스크린샷 저장: {screenshot_path}")
            
            # HTML 저장
            html_path = f'data/debug_{timestamp}.html'
            html = await page.content()
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[DEBUG] HTML 저장: {html_path}")
        
        await browser.close()
        print("\n프로그램 종료")


if __name__ == "__main__":
    asyncio.run(scrape_bizmeka_mails())
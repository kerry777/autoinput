#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 동적 선택자 버전
로그인 아이디에 따른 동적 태그 처리
"""

import asyncio
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config


async def scrape_with_dynamic_selectors():
    """동적 선택자를 사용한 메일 스크래핑"""
    
    config = load_config()
    cookie_manager = CookieManager()
    
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print("[ERROR] 쿠키 없음")
        return
    
    print("\n" + "="*60)
    print("Bizmeka 메일 스크래퍼 - 동적 선택자 버전")
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
        
        # 2. 메일 접속
        print("2. 메일 시스템 접속...")
        mail_link = await page.query_selector('a[href*="mail"]')
        if mail_link:
            await mail_link.click()
            await page.wait_for_timeout(3000)
        
        if len(context.pages) > 1:
            page = context.pages[-1]
        
        # 3. 팝업 처리
        for _ in range(3):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 4. 동적 받은메일함 선택자 찾기
        print("3. 받은메일함 접속...")
        
        try:
            # 여러 방법으로 받은메일함 링크 찾기
            inbox_selectors = [
                '[id^="mnu_Inbox_"]',  # mnu_Inbox_로 시작하는 ID
                'a[onclick*="Inbox"]',  # onclick에 Inbox가 포함된 링크
                'a:has-text("받은메일함")',  # 텍스트 기반
                '.mbutton:has-text("받은메일함")'  # class 기반
            ]
            
            inbox_clicked = False
            for selector in inbox_selectors:
                try:
                    inbox = await page.query_selector(selector)
                    if inbox:
                        print(f"   → 받은메일함 발견: {selector}")
                        await inbox.click()
                        await page.wait_for_timeout(2000)
                        inbox_clicked = True
                        break
                except:
                    continue
            
            if not inbox_clicked:
                print("   → 받은메일함 링크를 찾을 수 없음")
                
                # 페이지의 모든 링크 확인
                links = await page.query_selector_all('a')
                print(f"   → 페이지 내 총 {len(links)}개 링크 확인 중...")
                
                for i, link in enumerate(links[:20]):  # 처음 20개만
                    try:
                        text = await link.inner_text()
                        onclick = await link.get_attribute('onclick')
                        id_attr = await link.get_attribute('id')
                        
                        if ('받은메일함' in text or 
                            (onclick and 'Inbox' in onclick) or 
                            (id_attr and 'Inbox' in id_attr)):
                            print(f"   → 링크 {i}: {text} (ID: {id_attr}, onclick: {onclick})")
                    except:
                        continue
        
        except Exception as e:
            print(f"   → 받은메일함 접속 오류: {e}")
        
        # 팝업 다시 처리
        for _ in range(2):
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
        
        # 5. 메일 데이터 수집
        print("\n4. 메일 데이터 추출...")
        print("-" * 40)
        
        all_mails = []
        
        for page_num in range(1, 4):
            print(f"\n페이지 {page_num} 처리 중...")
            
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            
            # 프레임 확인
            frames = page.frames
            main_frame = page
            
            for frame in frames:
                if 'mail' in frame.url.lower() or 'list' in frame.url.lower():
                    main_frame = frame
                    print(f"   → 메일 프레임 사용")
                    break
            
            try:
                # 더 간단한 접근 - 모든 테이블 행 검사
                mails_found = await main_frame.evaluate('''() => {
                    const results = [];
                    
                    // 모든 테이블 행 찾기
                    const allRows = document.querySelectorAll('tr');
                    
                    for (let row of allRows) {
                        const cells = row.querySelectorAll('td');
                        
                        // 최소 5개 셀이 있어야 함
                        if (cells.length < 5) continue;
                        
                        // 체크박스가 있는지 확인
                        const hasCheckbox = row.querySelector('input[type="checkbox"]');
                        if (!hasCheckbox) continue;
                        
                        // checkAll은 헤더이므로 제외
                        const checkboxId = hasCheckbox.id || '';
                        if (checkboxId === 'checkAll') continue;
                        
                        // 셀 텍스트 추출
                        const cellData = [];
                        for (let i = 0; i < Math.min(cells.length, 8); i++) {
                            const text = cells[i].innerText || cells[i].textContent || '';
                            cellData.push(text.trim());
                        }
                        
                        // 날짜 패턴 찾기 (202X-XX-XX)
                        const datePattern = /202\d-\d{2}-\d{2}/;
                        const hasValidDate = cellData.some(text => datePattern.test(text));
                        
                        if (hasValidDate) {
                            // 날짜 위치 찾기
                            const dateIndex = cellData.findIndex(text => datePattern.test(text));
                            
                            // 메일 데이터 구조 추정
                            let sender = '';
                            let subject = '';
                            let date = cellData[dateIndex] || '';
                            let size = '';
                            
                            // 일반적인 메일 테이블 구조
                            if (dateIndex >= 2) {
                                sender = cellData[dateIndex - 2] || '';
                                subject = cellData[dateIndex - 1] || '';
                            }
                            
                            // 크기는 보통 날짜 뒤에
                            if (dateIndex < cellData.length - 1) {
                                const nextText = cellData[dateIndex + 1] || '';
                                if (nextText.includes('KB') || nextText.includes('MB')) {
                                    size = nextText;
                                }
                            }
                            
                            // 보낸사람이 비어있으면 다른 셀에서 찾기
                            if (!sender) {
                                for (let i = 0; i < dateIndex; i++) {
                                    const text = cellData[i] || '';
                                    if (text && text.length > 2 && !text.includes('★')) {
                                        sender = text;
                                        break;
                                    }
                                }
                            }
                            
                            // 제목이 비어있으면 다른 셀에서 찾기
                            if (!subject) {
                                for (let i = 0; i < dateIndex; i++) {
                                    const text = cellData[i] || '';
                                    if (text && text.length > 5 && text !== sender) {
                                        subject = text;
                                        break;
                                    }
                                }
                            }
                            
                            // 유효한 데이터만 추가
                            if (sender || subject) {
                                results.push({
                                    sender: sender,
                                    subject: subject,
                                    date: date,
                                    size: size,
                                    rawData: cellData.join(' | ')  // 디버깅용
                                });
                            }
                        }
                    }
                    
                    return results;
                }''')
                
                if mails_found and len(mails_found) > 0:
                    print(f"   → {len(mails_found)}개 메일 발견")
                    
                    for mail in mails_found:
                        mail_data = {
                            '페이지': page_num,
                            '보낸사람': mail['sender'],
                            '제목': mail['subject'],
                            '날짜': mail['date'],
                            '크기': mail['size'],
                            '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        all_mails.append(mail_data)
                        
                        # 처음 3개만 출력
                        if len(all_mails) <= 3:
                            sender = mail['sender'][:25] if mail['sender'] else 'Unknown'
                            subject = mail['subject'][:35] if mail['subject'] else 'No subject'
                            print(f"      • {sender}: {subject}...")
                else:
                    print(f"   → 메일을 찾지 못함")
                    print(f"   → 디버그 정보:")
                    
                    # 기본 정보 수집
                    debug_info = await main_frame.evaluate('''() => {
                        return {
                            totalRows: document.querySelectorAll('tr').length,
                            totalTables: document.querySelectorAll('table').length,
                            totalCheckboxes: document.querySelectorAll('input[type="checkbox"]').length,
                            url: window.location.href
                        };
                    }''')
                    
                    print(f"        - 총 행 수: {debug_info.get('totalRows', 0)}")
                    print(f"        - 총 테이블 수: {debug_info.get('totalTables', 0)}")
                    print(f"        - 총 체크박스 수: {debug_info.get('totalCheckboxes', 0)}")
                    print(f"        - 현재 URL: {debug_info.get('url', 'Unknown')}")
            
            except Exception as e:
                print(f"   → 추출 오류: {e}")
            
            # 다음 페이지로 이동
            if page_num < 3:
                try:
                    next_page = page_num + 1
                    page_selectors = [
                        f'a:has-text("{next_page}")',
                        f'[onclick*="page={next_page}"]',
                        f'.pagination a:has-text("{next_page}")'
                    ]
                    
                    moved = False
                    for selector in page_selectors:
                        try:
                            next_link = await main_frame.query_selector(selector)
                            if next_link:
                                await next_link.click()
                                print(f"   → {next_page}페이지로 이동 ({selector})")
                                await page.wait_for_timeout(2000)
                                moved = True
                                break
                        except:
                            continue
                    
                    if not moved:
                        print(f"   → {next_page}페이지 링크를 찾을 수 없음")
                        break
                        
                except Exception as e:
                    print(f"   → 페이지 이동 오류: {e}")
                    break
        
        # 6. 결과 처리
        print("\n" + "="*60)
        if all_mails:
            # DataFrame 생성
            df = pd.DataFrame(all_mails)
            
            # Excel 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/bizmeka_mails_{timestamp}.xlsx'
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"[SUCCESS] 메일 수집 성공!")
            print(f"\n[수집 결과]")
            print(f"  • 총 메일: {len(all_mails)}개")
            print(f"  • 저장 파일: {filename}")
            
            # 통계
            pages = df['페이지'].value_counts().sort_index()
            print(f"\n[페이지별 수집량]")
            for page, count in pages.items():
                print(f"  • 페이지 {page}: {count}개")
            
            print(f"\n[메일 샘플]")
            for i, mail in enumerate(all_mails[:5], 1):
                sender = mail['보낸사람'][:20] if mail['보낸사람'] else 'Unknown'
                subject = mail['제목'][:30] if mail['제목'] else 'No subject'
                date = mail['날짜'][:16] if mail['날짜'] else ''
                print(f"  {i}. [{date}] {sender}: {subject}...")
        
        else:
            print("[WARNING] 수집된 메일이 없습니다")
            
            # 디버깅 자료 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            await page.screenshot(path=f'data/debug_final_{timestamp}.png')
            print(f"[DEBUG] 최종 스크린샷: data/debug_final_{timestamp}.png")
            
            html = await page.content()
            with open(f'data/debug_final_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[DEBUG] 최종 HTML: data/debug_final_{timestamp}.html")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(scrape_with_dynamic_selectors())
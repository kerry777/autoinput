#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 대화형 버전
사용자가 브라우저를 조작하면서 실시간 데이터 추출
"""

import asyncio
from datetime import datetime
import pandas as pd
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config


async def interactive_mail_scraper():
    """대화형 메일 스크래퍼"""
    
    config = load_config()
    cookie_manager = CookieManager()
    
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print("[ERROR] 쿠키 없음")
        return
    
    print("\n" + "="*60)
    print("Bizmeka 메일 스크래퍼 - 대화형 버전")
    print("="*60)
    print("\n사용법:")
    print("1. 브라우저가 열리면 수동으로 메일함 페이지로 이동하세요")
    print("2. Enter를 누르면 현재 페이지의 메일을 추출합니다")
    print("3. 'q'를 입력하면 종료합니다")
    print("\n시작하려면 Enter를 누르세요...")
    input()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 메인 페이지로 이동
        await page.goto(config['urls']['main'])
        await page.wait_for_timeout(2000)
        
        # 메일 링크 클릭
        mail_link = await page.query_selector('a[href*="mail"]')
        if mail_link:
            await mail_link.click()
            await page.wait_for_timeout(3000)
        
        # 새 탭으로 전환
        if len(context.pages) > 1:
            page = context.pages[-1]
        
        all_mails = []
        page_num = 1
        
        print(f"\n브라우저가 열렸습니다. 메일함으로 이동해주세요.")
        print(f"준비가 되면 Enter를 누르거나 'q'를 입력해 종료하세요.")
        
        while True:
            user_input = input(f"\n[페이지 {page_num}] Enter=추출, q=종료: ").strip().lower()
            
            if user_input == 'q':
                break
            
            print(f"\n페이지 {page_num} 메일 추출 중...")
            
            try:
                # 현재 페이지의 모든 테이블 행 확인
                rows = await page.query_selector_all('tr')
                print(f"   → 총 {len(rows)}개 행 발견")
                
                page_mails = []
                
                for i, row in enumerate(rows):
                    try:
                        # 체크박스 확인
                        checkbox = await row.query_selector('input[type="checkbox"]')
                        if not checkbox:
                            continue
                        
                        checkbox_id = await checkbox.get_attribute('id')
                        if checkbox_id == 'checkAll':
                            continue
                        
                        # 셀 추출
                        cells = await row.query_selector_all('td')
                        if len(cells) < 6:
                            continue
                        
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip() if text else '')
                        
                        # 날짜 패턴 확인
                        has_date = any('202' in text and '-' in text for text in cell_texts)
                        
                        if has_date:
                            # 날짜 위치 찾기
                            date_idx = -1
                            for idx, text in enumerate(cell_texts):
                                if '202' in text and '-' in text and len(text) >= 10:
                                    date_idx = idx
                                    break
                            
                            if date_idx >= 0:
                                mail_info = {
                                    '페이지': page_num,
                                    '보낸사람': cell_texts[date_idx-2] if date_idx >= 2 else cell_texts[3] if len(cell_texts) > 3 else '',
                                    '제목': cell_texts[date_idx-1] if date_idx >= 1 else cell_texts[4] if len(cell_texts) > 4 else '',
                                    '날짜': cell_texts[date_idx],
                                    '크기': cell_texts[date_idx+1] if date_idx < len(cell_texts)-1 else cell_texts[6] if len(cell_texts) > 6 else '',
                                    '수집시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    '원본데이터': ' | '.join(cell_texts[:8])  # 디버깅용
                                }\n                                \n                                if mail_info['보낸사람'] or mail_info['제목']:\n                                    page_mails.append(mail_info)\n                                    print(f\"      메일 {len(page_mails)}: {mail_info['보낸사람'][:15]} - {mail_info['제목'][:25]}...\")\n                    \n                    except Exception as e:\n                        continue\n                \n                print(f\"   → {len(page_mails)}개 메일 추출됨\")\n                all_mails.extend(page_mails)\n                \n                if len(page_mails) == 0:\n                    print(\"\\n디버깅 정보:\")\n                    \n                    # 첫 10개 행의 셀 내용 출력\n                    for i, row in enumerate(rows[:10]):\n                        try:\n                            cells = await row.query_selector_all('td')\n                            if len(cells) >= 3:\n                                cell_texts = []\n                                for cell in cells:\n                                    text = await cell.inner_text()\n                                    cell_texts.append(text.strip()[:20] if text else '')\n                                print(f\"   행 {i}: {' | '.join(cell_texts[:6])}\")\n                        except:\n                            continue\n                    \n                    # 스크린샷 저장\n                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n                    screenshot_path = f'data/debug_interactive_{timestamp}.png'\n                    await page.screenshot(path=screenshot_path)\n                    print(f\"   디버그 스크린샷: {screenshot_path}\")\n                \n                page_num += 1\n                \n            except Exception as e:\n                print(f\"   → 오류: {e}\")\n        \n        # 결과 저장\n        print(\"\\n\" + \"=\"*60)\n        if all_mails:\n            df = pd.DataFrame(all_mails)\n            \n            # 원본데이터 컬럼 제거\n            if '원본데이터' in df.columns:\n                debug_df = df.copy()  # 디버깅용 백업\n                df = df.drop('원본데이터', axis=1)\n            \n            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')\n            filename = f'data/bizmeka_mails_interactive_{timestamp}.xlsx'\n            \n            # 메인 결과 저장\n            df.to_excel(filename, index=False, engine='openpyxl')\n            \n            # 디버깅용 저장 (원본 데이터 포함)\n            if '원본데이터' in debug_df.columns:\n                debug_filename = f'data/debug_mails_{timestamp}.xlsx'\n                debug_df.to_excel(debug_filename, index=False, engine='openpyxl')\n            \n            print(f\"[SUCCESS] 대화형 메일 수집 완료!\")\n            print(f\"\\n[수집 결과]\")\n            print(f\"  • 총 메일: {len(all_mails)}개\")\n            print(f\"  • 메인 파일: {filename}\")\n            if '원본데이터' in debug_df.columns:\n                print(f\"  • 디버그 파일: {debug_filename}\")\n            \n            # 통계\n            if len(all_mails) > 0:\n                print(f\"\\n[메일 샘플 - 처음 10개]\")\n                for i, mail in enumerate(all_mails[:10], 1):\n                    sender = mail['보낸사람'][:20] if mail['보낸사람'] else 'Unknown'\n                    subject = mail['제목'][:30] if mail['제목'] else 'No subject'\n                    date = mail['날짜'][:16] if mail['날짜'] else ''\n                    print(f\"  {i:2d}. [{date}] {sender}: {subject}...\")\n                \n                # 발신자 통계\n                sender_counts = df['보낸사람'].value_counts()\n                if len(sender_counts) > 0:\n                    print(f\"\\n[발신자 통계]\")\n                    for sender, count in sender_counts.head(5).items():\n                        if sender:\n                            print(f\"  • {sender}: {count}개\")\n        else:\n            print(\"[INFO] 수집된 메일이 없습니다\")\n        \n        await browser.close()\n        return len(all_mails) if all_mails else 0\n\n\nif __name__ == \"__main__\":\n    try:\n        result = asyncio.run(interactive_mail_scraper())\n        print(f\"\\n프로그램 종료 - 총 {result}개 메일 수집\")\n    except KeyboardInterrupt:\n        print(\"\\n사용자에 의해 중단됨\")\n    except Exception as e:\n        print(f\"\\n오류 발생: {e}\")
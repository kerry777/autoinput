#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 디버그 버전
- 페이지 구조 분석
- 선택자 찾기
- 스크린샷 저장
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, Page
from cookie_manager import CookieManager
from utils import load_config, setup_logging, print_banner, print_status


async def debug_mail_scraper():
    """디버그 모드로 메일 스크래퍼 실행"""
    
    print_banner("MAIL SCRAPER DEBUG")
    
    config = load_config()
    logger = setup_logging('mail_scraper_debug')
    cookie_manager = CookieManager()
    
    # 디버그 디렉토리 생성
    debug_dir = Path('data/debug')
    debug_dir.mkdir(exist_ok=True, parents=True)
    
    # 쿠키 확인
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print_status('error', '쿠키 없음 - manual_login.py 실행 필요')
        return
    
    async with async_playwright() as p:
        # 브라우저 실행 (디버그는 항상 headless=False)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone']
        )
        
        # 쿠키 설정
        await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        try:
            # 1. 메인 페이지 접속
            print_status('info', '메인 페이지 접속...')
            await page.goto(config['urls']['main'])
            await page.wait_for_timeout(3000)
            
            # 스크린샷 저장
            await page.screenshot(path=debug_dir / 'step1_main.png')
            print_status('success', 'step1_main.png 저장')
            
            # 페이지 분석
            print("\n[메인 페이지 분석]")
            
            # 메일 관련 요소 찾기
            mail_elements = await page.query_selector_all('a, button, span, div')
            mail_found = []
            
            for element in mail_elements:
                try:
                    text = await element.inner_text()
                    if '메일' in text.lower() or 'mail' in text.lower():
                        tag = await element.evaluate('el => el.tagName')
                        classes = await element.evaluate('el => el.className')
                        href = await element.evaluate('el => el.href || ""')
                        onclick = await element.evaluate('el => el.onclick ? el.onclick.toString() : ""')
                        
                        mail_found.append({
                            'text': text.strip()[:50],
                            'tag': tag,
                            'class': classes,
                            'href': href,
                            'onclick': onclick[:100] if onclick else ''
                        })
                except:
                    continue
            
            print(f"메일 관련 요소 {len(mail_found)}개 발견:")
            for i, item in enumerate(mail_found[:10], 1):
                print(f"  {i}. [{item['tag']}] {item['text']}")
                if item['href']:
                    print(f"     href: {item['href'][:50]}...")
                if item['class']:
                    print(f"     class: {item['class']}")
            
            # 사용자 선택
            print("\n메일 버튼을 직접 클릭하세요.")
            print("클릭 후 Enter를 누르세요...")
            input()
            
            # 2. 메일 페이지 분석
            await page.wait_for_timeout(2000)
            
            # 새 탭 처리
            if len(context.pages) > 1:
                page = context.pages[-1]
                print_status('info', '새 탭 감지')
            
            await page.screenshot(path=debug_dir / 'step2_mail.png')
            print_status('success', 'step2_mail.png 저장')
            
            print("\n[메일 페이지 분석]")
            print(f"현재 URL: {page.url}")
            
            # 받은메일함 요소 찾기
            inbox_elements = await page.query_selector_all('a, span, li, div')
            inbox_found = []
            
            for element in inbox_elements:
                try:
                    text = await element.inner_text()
                    if '받은' in text or 'inbox' in text.lower() or '수신' in text:
                        tag = await element.evaluate('el => el.tagName')
                        classes = await element.evaluate('el => el.className')
                        href = await element.evaluate('el => el.href || ""')
                        
                        inbox_found.append({
                            'text': text.strip()[:50],
                            'tag': tag,
                            'class': classes,
                            'href': href
                        })
                except:
                    continue
            
            print(f"받은메일함 관련 요소 {len(inbox_found)}개 발견:")
            for i, item in enumerate(inbox_found[:10], 1):
                print(f"  {i}. [{item['tag']}] {item['text']}")
                if item['href']:
                    print(f"     href: {item['href'][:50]}...")
            
            print("\n받은메일함을 직접 클릭하세요.")
            print("클릭 후 Enter를 누르세요...")
            input()
            
            # 3. 메일 목록 분석
            await page.wait_for_timeout(2000)
            await page.screenshot(path=debug_dir / 'step3_inbox.png')
            print_status('success', 'step3_inbox.png 저장')
            
            print("\n[메일 목록 분석]")
            
            # 테이블 구조 분석
            tables = await page.query_selector_all('table')
            print(f"테이블 {len(tables)}개 발견")
            
            for i, table in enumerate(tables, 1):
                rows = await table.query_selector_all('tr')
                if len(rows) > 2:  # 헤더 + 데이터 행이 있는 테이블
                    print(f"\n테이블 {i}: {len(rows)}개 행")
                    
                    # 첫 번째 데이터 행 분석
                    if len(rows) > 1:
                        first_row = rows[1]
                        cells = await first_row.query_selector_all('td, th')
                        print(f"  컬럼 수: {len(cells)}")
                        
                        for j, cell in enumerate(cells, 1):
                            try:
                                text = await cell.inner_text()
                                print(f"    컬럼 {j}: {text.strip()[:30]}...")
                            except:
                                print(f"    컬럼 {j}: [읽기 실패]")
            
            # 페이지네이션 분석
            print("\n[페이지네이션 분석]")
            
            pagination = await page.query_selector_all('a, button')
            page_found = []
            
            for element in pagination:
                try:
                    text = await element.inner_text()
                    # 숫자, 다음, 이전 등
                    if text.strip().isdigit() or '다음' in text or '이전' in text or 'next' in text.lower() or 'prev' in text.lower():
                        tag = await element.evaluate('el => el.tagName')
                        classes = await element.evaluate('el => el.className')
                        
                        page_found.append({
                            'text': text.strip(),
                            'tag': tag,
                            'class': classes
                        })
                except:
                    continue
            
            print(f"페이지네이션 요소 {len(page_found)}개 발견:")
            for item in page_found[:20]:
                print(f"  [{item['tag']}] {item['text']} (class: {item['class']})")
            
            # HTML 저장 (구조 분석용)
            html_content = await page.content()
            with open(debug_dir / 'inbox_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print_status('success', 'inbox_page.html 저장')
            
            print("\n[디버그 완료]")
            print("저장된 파일:")
            print(f"  - {debug_dir}/step1_main.png")
            print(f"  - {debug_dir}/step2_mail.png")
            print(f"  - {debug_dir}/step3_inbox.png")
            print(f"  - {debug_dir}/inbox_page.html")
            
            print("\n브라우저를 닫으려면 Enter를 누르세요...")
            input()
            
        except Exception as e:
            logger.error(f"디버그 실패: {e}")
            print_status('error', f'디버그 실패: {e}')
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(debug_mail_scraper())
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
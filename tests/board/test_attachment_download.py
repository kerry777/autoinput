#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
첨부파일 다운로드 테스트 - 직접 접근 방식
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_download():
    """첨부파일 다운로드 테스트"""
    
    print("""
    ==============================================================
                첨부파일 다운로드 기능 테스트
    ==============================================================
    
    1. 메인 페이지에서 시작
    2. 알림·자료실 메뉴 클릭
    3. 공지사항 클릭
    4. 게시물 목록 확인
    5. 첨부파일이 있는 게시물 찾기
    6. 첨부파일 다운로드 시도
    
    ==============================================================
    """)
    
    download_dir = "data/downloads/test_attachments"
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs("logs/screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000,
            downloads_path=download_dir
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        try:
            # 1. 메인 페이지 접속
            print("\n[1단계] 메인 페이지 접속")
            await page.goto("https://longtermcare.or.kr", wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # 2. 알림·자료실 메뉴 찾기
            print("[2단계] 알림·자료실 메뉴 찾기")
            
            # 메뉴 클릭 시도 - 여러 가능한 셀렉터
            menu_selectors = [
                'a:has-text("알림·자료실")',
                'a:has-text("알림")',
                '#gnb a:has-text("알림")',
                '.menu a:has-text("알림")',
                'nav a:has-text("알림")'
            ]
            
            menu_found = False
            for selector in menu_selectors:
                menu = await page.query_selector(selector)
                if menu:
                    print(f"  ✓ 메뉴 발견: {selector}")
                    await menu.hover()  # 마우스 오버
                    await page.wait_for_timeout(1000)
                    menu_found = True
                    break
            
            if not menu_found:
                print("  ✗ 알림·자료실 메뉴를 찾을 수 없음")
            
            # 3. 공지사항 서브메뉴 클릭
            print("[3단계] 공지사항 클릭")
            
            notice_selectors = [
                'a:has-text("공지사항")',
                'a[href*="공지사항"]',
                'a[href*="notice"]',
                'a[href*="board"]'
            ]
            
            for selector in notice_selectors:
                notice = await page.query_selector(selector)
                if notice:
                    print(f"  ✓ 공지사항 링크 발견")
                    await notice.click()
                    await page.wait_for_timeout(3000)
                    break
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f'logs/screenshots/notice_page_{timestamp}.png')
            print(f"[스크린샷] logs/screenshots/notice_page_{timestamp}.png")
            
            # 4. 게시물 목록 확인
            print("\n[4단계] 게시물 목록 확인")
            
            # 테이블 찾기
            tables = await page.query_selector_all('table')
            print(f"  테이블 개수: {len(tables)}개")
            
            # 게시물 행 찾기
            rows = await page.query_selector_all('tbody tr, table tr')
            print(f"  전체 행 개수: {len(rows)}개")
            
            # 5. 첫 번째 게시물 클릭
            print("\n[5단계] 게시물 상세 보기")
            
            # 게시물 링크 찾기
            post_links = await page.query_selector_all('td a[onclick*="View"], td a[onclick*="Detail"], td a[onclick*="fn"]')
            
            if post_links:
                print(f"  게시물 링크 {len(post_links)}개 발견")
                
                # 첫 번째 게시물 클릭
                first_link = post_links[0]
                post_title = await first_link.text_content()
                print(f"  첫 번째 게시물: {post_title[:50] if post_title else 'Unknown'}")
                
                await first_link.click()
                await page.wait_for_timeout(3000)
                
                # 상세 페이지 스크린샷
                await page.screenshot(path=f'logs/screenshots/post_detail_{timestamp}.png')
                print(f"[스크린샷] logs/screenshots/post_detail_{timestamp}.png")
                
                # 6. 첨부파일 찾기
                print("\n[6단계] 첨부파일 찾기")
                
                # 첨부파일 영역 찾기
                file_selectors = [
                    'a[onclick*="download"]',
                    'a[onclick*="fileDown"]',
                    'a[onclick*="fnFile"]',
                    'a[href*="download"]',
                    '.file-list a',
                    '.attach a',
                    'td:has-text("첨부") ~ td a',
                    'th:has-text("첨부") ~ td a'
                ]
                
                files_found = []
                for selector in file_selectors:
                    files = await page.query_selector_all(selector)
                    if files:
                        files_found = files
                        print(f"  ✓ 첨부파일 {len(files)}개 발견 (셀렉터: {selector})")
                        break
                
                if files_found:
                    # 7. 첨부파일 다운로드
                    print("\n[7단계] 첨부파일 다운로드")
                    
                    for idx, file_link in enumerate(files_found[:2], 1):  # 최대 2개만
                        try:
                            file_name = await file_link.text_content()
                            print(f"  파일 {idx}: {file_name[:50] if file_name else 'Unknown'}")
                            
                            # onclick 속성 확인
                            onclick = await file_link.get_attribute('onclick')
                            href = await file_link.get_attribute('href')
                            
                            print(f"    onclick: {onclick[:100] if onclick else 'None'}")
                            print(f"    href: {href[:100] if href else 'None'}")
                            
                            # 다운로드 시도
                            try:
                                async with page.expect_download(timeout=30000) as download_info:
                                    if onclick:
                                        # JavaScript 함수 실행
                                        await page.evaluate(onclick)
                                    else:
                                        # 직접 클릭
                                        await file_link.click()
                                
                                download = await download_info.value
                                
                                # 파일 저장
                                suggested_name = download.suggested_filename
                                file_path = os.path.join(download_dir, suggested_name)
                                await download.save_as(file_path)
                                
                                print(f"    ✓ 다운로드 성공: {suggested_name}")
                                print(f"    저장 위치: {file_path}")
                                
                            except Exception as e:
                                print(f"    ✗ 다운로드 실패: {str(e)[:100]}")
                            
                        except Exception as e:
                            print(f"  파일 {idx} 처리 실패: {str(e)[:100]}")
                else:
                    print("  ✗ 첨부파일을 찾을 수 없음")
                    
                    # 페이지 내용 분석
                    print("\n[페이지 분석]")
                    page_text = await page.text_content('body')
                    if '첨부' in page_text:
                        print("  '첨부' 텍스트는 페이지에 있음")
                    
                    # 모든 링크 출력
                    all_links = await page.query_selector_all('a')
                    print(f"  전체 링크 수: {len(all_links)}개")
                    
                    for idx, link in enumerate(all_links[:10], 1):
                        text = await link.text_content()
                        if text and len(text.strip()) > 0:
                            print(f"    {idx}. {text[:50]}")
            else:
                print("  ✗ 게시물 링크를 찾을 수 없음")
            
            print("\n[테스트 완료] 10초 후 브라우저가 닫힙니다...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    print("\n첨부파일 다운로드 테스트를 시작합니다...\n")
    asyncio.run(test_download())
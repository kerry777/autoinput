#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서식자료실 직접 클릭 방식 다운로더
게시물을 직접 클릭하여 첨부파일 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def download_forms():
    """서식자료실 첨부파일 다운로드"""
    
    print("""
    ==============================================================
              서식자료실 첨부파일 다운로드 (직접 클릭)
    ==============================================================
    """)
    
    download_dir = "data/downloads/forms_direct"
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs("logs/screenshots", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000  # 천천히 진행
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        try:
            # 1. 서식자료실 페이지로 이동
            print("\n[1단계] 서식자료실 페이지 이동")
            url = "https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(5000)
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f'logs/screenshots/forms_list_{timestamp}.png')
            print(f"  ✓ 페이지 로드 완료")
            
            # 2. 첫 번째 게시물 찾기 (번호 순서대로)
            print("\n[2단계] 게시물 목록 확인")
            
            # 화면에 보이는 게시물 찾기 - 번호 601로 시작하는 첫 번째 행
            # 스크린샷에서 보이는 구조: 번호 | 구분 | 제목 | 작성자 | 등록일 | 첨부 | 조회
            
            # 첫 번째 게시물 제목 클릭 시도
            post_titles = [
                "2025년 장기요양기관 운영 관련 서식 모음집",  # 최신 게시물
                "동거서류미비안심시",  # 60125 게시물
                "슬라이드보드사용법보기"  # 60124 게시물
            ]
            
            download_count = 0
            max_downloads = 3
            
            for idx, title_part in enumerate(post_titles[:max_downloads], 1):
                try:
                    print(f"\n[게시물 {idx}] 제목 검색: {title_part}...")
                    
                    # 제목 링크 찾기 - 여러 방법 시도
                    title_link = None
                    
                    # 방법 1: boardId가 포함된 링크 찾기
                    if idx == 1:  # 첫 번째 게시물
                        # 가장 최근 게시물 링크 찾기
                        board_links = await page.query_selector_all('a[href*="boardId="]')
                        if board_links and len(board_links) > 0:
                            # 첫 번째 게시물 링크 선택
                            title_link = board_links[0]
                    
                    # 방법 2: span 태그 내 텍스트로 찾기
                    if not title_link:
                        spans = await page.query_selector_all('span[style*="font-weight:bold"]')
                        for span in spans:
                            text = await span.text_content()
                            if text and title_part in text:
                                # span의 부모 a 태그 찾기
                                parent = await span.evaluate_handle('el => el.parentElement')
                                tag_name = await parent.evaluate('el => el.tagName')
                                if tag_name == 'A':
                                    title_link = parent
                                    break
                    
                    # 방법 3: 텍스트 포함 링크 찾기
                    if not title_link:
                        all_links = await page.query_selector_all('a')
                        for link in all_links:
                            text = await link.text_content()
                            if text and title_part in text.replace(' ', ''):
                                href = await link.get_attribute('href')
                                if href and 'boardId' in href:
                                    title_link = link
                                    break
                    
                    if title_link:
                        title_text = await title_link.text_content()
                        print(f"  ✓ 게시물 발견: {title_text[:50]}")
                        
                        # 3. 게시물 클릭
                        await title_link.click()
                        await page.wait_for_timeout(3000)
                        
                        # 상세 페이지 스크린샷
                        await page.screenshot(path=f'logs/screenshots/detail_{idx}_{timestamp}.png')
                        print(f"  ✓ 상세 페이지 진입")
                        
                        # 4. 첨부파일 찾기
                        print(f"  [첨부파일 찾기]")
                        
                        # 첨부파일 링크 패턴들
                        file_selectors = [
                            'a[onclick*="fnFileDown"]',
                            'a[onclick*="fn_file_down"]',
                            'a[onclick*="download"]',
                            'a:has-text(".hwp")',
                            'a:has-text(".pdf")',
                            'a:has-text(".doc")',
                            'a:has-text(".xls")',
                            'a:has-text(".zip")',
                            'td:has-text("첨부") ~ td a',
                            'th:has-text("첨부") ~ td a',
                            'td a[href*="download"]',
                            'td a[href$=".hwp"]',
                            'td a[href$=".pdf"]'
                        ]
                        
                        file_links = []
                        for selector in file_selectors:
                            links = await page.query_selector_all(selector)
                            if links:
                                file_links.extend(links)
                                print(f"    ✓ 셀렉터 '{selector[:30]}...'로 {len(links)}개 발견")
                                break
                        
                        # 중복 제거
                        unique_links = []
                        seen_texts = set()
                        for link in file_links:
                            text = await link.text_content()
                            if text and text not in seen_texts:
                                seen_texts.add(text)
                                unique_links.append(link)
                        
                        if unique_links:
                            print(f"    총 {len(unique_links)}개 고유 파일")
                            
                            # 5. 첨부파일 다운로드
                            post_folder = os.path.join(download_dir, f"post_{idx}")
                            os.makedirs(post_folder, exist_ok=True)
                            
                            for file_idx, file_link in enumerate(unique_links[:2], 1):  # 최대 2개
                                try:
                                    file_text = await file_link.text_content()
                                    print(f"    파일 {file_idx}: {file_text[:50]}")
                                    
                                    # 다운로드 시도
                                    async with page.expect_download(timeout=30000) as download_info:
                                        # onclick 확인
                                        onclick = await file_link.get_attribute('onclick')
                                        if onclick:
                                            # JavaScript 함수 실행
                                            await page.evaluate(onclick)
                                        else:
                                            # 직접 클릭
                                            await file_link.click()
                                    
                                    download = await download_info.value
                                    suggested_name = download.suggested_filename
                                    file_path = os.path.join(post_folder, suggested_name)
                                    await download.save_as(file_path)
                                    
                                    print(f"      ✓ 다운로드 성공: {suggested_name}")
                                    print(f"      저장 위치: {file_path}")
                                    download_count += 1
                                    
                                except Exception as e:
                                    print(f"      ✗ 다운로드 실패: {str(e)[:50]}")
                        else:
                            print(f"    ✗ 첨부파일을 찾을 수 없음")
                        
                        # 6. 목록으로 돌아가기
                        print(f"  [목록으로 복귀]")
                        
                        # 목록 버튼 찾기
                        list_btn = await page.query_selector('a:has-text("목록"), button:has-text("목록")')
                        if list_btn:
                            await list_btn.click()
                        else:
                            await page.go_back()
                        
                        await page.wait_for_timeout(2000)
                        print(f"  ✓ 목록 페이지로 복귀")
                        
                    else:
                        print(f"  ✗ 게시물을 찾을 수 없음: {title_part}")
                        
                except Exception as e:
                    print(f"  [ERROR] 게시물 {idx} 처리 실패: {str(e)[:100]}")
                    # 목록으로 돌아가기 시도
                    try:
                        await page.go_back()
                        await page.wait_for_timeout(2000)
                    except:
                        pass
            
            # 최종 결과
            print(f"""
            ==============================================================
                                    완료!
            ==============================================================
            
              총 {download_count}개 파일 다운로드 성공
              저장 위치: {download_dir}/post_[번호]/
            
            ==============================================================
            """)
            
            print("\n[INFO] 10초 후 브라우저가 닫힙니다...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    print("\n서식자료실 직접 다운로드 시작\n")
    asyncio.run(download_forms())
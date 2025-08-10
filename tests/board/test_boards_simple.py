#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단한 자료실 테스트 - 직접 게시물 ID 지정
"""

import asyncio
from playwright.async_api import async_playwright
import os
import sys
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_boards():
    """자료실 테스트"""
    
    print("""
    ==============================================================
           서식, 법령, 질문, 통계 자료실 테스트
    ==============================================================
    """)
    
    # 테스트할 게시물들 (실제 게시물 ID 사용)
    test_posts = [
        {
            'board': '서식자료실',
            'communityKey': 'B0017',
            'boardId': '60123',  # 월별 서류 작성법
            'title': '월별 서류 작성법'
        },
        {
            'board': '법령자료실', 
            'communityKey': 'B0018',
            'boardId': '60115',  # 실제 법령자료실 게시물
            'title': '법령 관련 자료'
        },
        {
            'board': '통계자료실',
            'communityKey': 'B0020',  # B0020으로 수정
            'boardId': '60076',  # 실제 통계자료실 게시물
            'title': '통계 자료'
        },
        {
            'board': '자주하는질문',
            'communityKey': 'B0019',  # B0019로 수정
            'boardId': '60184',  # 실제 자주하는질문 게시물
            'title': '자주하는 질문'
        }
    ]
    
    download_dir = "data/downloads/boards_test"
    os.makedirs(download_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        page = await context.new_page()
        
        results = []
        
        for post in test_posts:
            print(f"\n{'='*50}")
            print(f"  {post['board']} 테스트")
            print(f"{'='*50}")
            
            try:
                # 상세 페이지 직접 접근
                url = f"https://longtermcare.or.kr/npbs/cms/board/board/Board.jsp?searchType=ALL&searchWord=&list_start_date=&list_end_date=&pageSize=&branch_id=&branch_child_id=&pageNum=1&list_show_answer=N&communityKey={post['communityKey']}&boardId={post['boardId']}&act=VIEW"
                
                print(f"  게시물 ID: {post['boardId']}")
                print(f"  URL 접속 중...")
                
                response = await page.goto(url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 페이지 상태 확인
                if response and response.status == 200:
                    print(f"  ✅ 페이지 로드 성공")
                else:
                    print(f"  ❌ 페이지 로드 실패 (상태: {response.status if response else 'None'})")
                
                # 제목 확인
                title_selectors = ['h3', 'h4', '.board-title', '.view-title', 'td.subject', 'td.title']
                title_found = False
                
                for selector in title_selectors:
                    title_element = await page.query_selector(selector)
                    if title_element:
                        actual_title = await title_element.text_content()
                        if actual_title and actual_title.strip():
                            print(f"  제목: {actual_title[:50]}")
                            title_found = True
                            break
                
                if not title_found:
                    # 페이지 내용 확인
                    page_text = await page.text_content('body')
                    if '존재하지 않는' in page_text or '삭제' in page_text or '없습니다' in page_text:
                        print(f"  ⚠️ 게시물이 없거나 삭제됨")
                    else:
                        print(f"  ⚠️ 제목을 찾을 수 없음")
                
                # 첨부파일 찾기
                print(f"  [첨부파일 검색]")
                
                # 다양한 첨부파일 패턴
                file_selectors = [
                    'a[href*="/Download.jsp"]',
                    'a[href*="download"]',
                    'a[onclick*="download"]',
                    'a[onclick*="fnFileDown"]',
                    'a[href$=".hwp"]',
                    'a[href$=".pdf"]',
                    'a[href$=".doc"]',
                    'a[href$=".xls"]',
                    'a[href$=".zip"]'
                ]
                
                file_links = []
                for selector in file_selectors:
                    links = await page.query_selector_all(selector)
                    if links:
                        file_links.extend(links)
                        print(f"    셀렉터 '{selector[:30]}...'로 {len(links)}개 발견")
                        break
                
                # 중복 제거
                unique_files = []
                seen_texts = set()
                
                for link in file_links:
                    try:
                        text = await link.text_content()
                        if text and text.strip() and text not in seen_texts:
                            seen_texts.add(text)
                            unique_files.append(link)
                    except:
                        pass
                
                download_count = 0
                
                if unique_files:
                    print(f"    총 {len(unique_files)}개 파일")
                    
                    # 다운로드 폴더
                    board_folder = os.path.join(download_dir, post['board'].replace('/', '_'))
                    os.makedirs(board_folder, exist_ok=True)
                    
                    # 파일 다운로드 (최대 2개)
                    for idx, file_link in enumerate(unique_files[:2], 1):
                        try:
                            file_text = await file_link.text_content()
                            print(f"    파일 {idx}: {file_text[:40]}")
                            
                            # 다운로드
                            async with page.expect_download(timeout=30000) as download_info:
                                await file_link.click()
                            
                            download = await download_info.value
                            suggested_name = download.suggested_filename
                            safe_name = re.sub(r'[<>:"/\\|?*]', '_', suggested_name)[:100]
                            file_path = os.path.join(board_folder, safe_name)
                            
                            await download.save_as(file_path)
                            print(f"      ✅ 다운로드 성공: {safe_name}")
                            download_count += 1
                            
                        except Exception as e:
                            print(f"      ❌ 다운로드 실패: {str(e)[:50]}")
                else:
                    print(f"    첨부파일 없음")
                
                results.append({
                    'board': post['board'],
                    'boardId': post['boardId'],
                    'files': download_count
                })
                
            except Exception as e:
                print(f"  [ERROR] {str(e)[:100]}")
                results.append({
                    'board': post['board'],
                    'boardId': post['boardId'],
                    'files': 0,
                    'error': str(e)[:100]
                })
        
        # 결과 요약
        print(f"""
        ==============================================================
                            테스트 결과 요약
        ==============================================================
        """)
        
        total_files = 0
        for result in results:
            status = f"{result['files']}개 파일" if result['files'] > 0 else "파일 없음/실패"
            print(f"  {result['board']}: {status}")
            total_files += result['files']
        
        print(f"""
        ──────────────────────────────────
        총 다운로드: {total_files}개 파일
        저장 위치: {download_dir}/
        ==============================================================
        """)
        
        print("\n[INFO] 10초 후 종료...")
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    print("\n자료실 테스트 시작\n")
    asyncio.run(test_boards())
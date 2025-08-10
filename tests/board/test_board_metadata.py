#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
게시판 메타데이터 수집 테스트 - 간단한 버전
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
import sys
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def test_board_metadata():
    """게시판 메타데이터 수집 테스트"""
    
    print("""
    ==============================================================
              게시판 메타데이터 수집 테스트
    ==============================================================
    """)
    
    # 서식자료실 테스트
    test_url = 'https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        page = await context.new_page()
        
        print(f"[INFO] 서식자료실 접속 중...")
        await page.goto(test_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 페이지 구조 확인
        print(f"[INFO] 페이지 구조 분석 중...")
        
        # iframe 확인
        iframes = await page.query_selector_all('iframe')
        print(f"  iframe 수: {len(iframes)}개")
        
        # iframe이 있으면 전환
        if iframes:
            frame = await iframes[0].content_frame()
            if frame:
                page = frame
                print(f"  iframe으로 전환")
                await page.wait_for_timeout(2000)
        
        # 테이블 찾기
        tables = await page.query_selector_all('table')
        print(f"  테이블 수: {len(tables)}개")
        
        # 각 테이블 확인
        for idx, table in enumerate(tables, 1):
            rows = await table.query_selector_all('tr')
            print(f"  테이블 {idx}: {len(rows)}개 행")
            
            if len(rows) > 1:  # 헤더 포함 2개 이상
                # 첫 번째 데이터 행 샘플
                if len(rows) > 1:
                    sample_row = rows[1]
                    cells = await sample_row.query_selector_all('td')
                    print(f"    첫 번째 행의 셀 수: {len(cells)}개")
                    
                    # 각 셀 내용 확인
                    for cell_idx, cell in enumerate(cells[:5], 1):
                        text = await cell.text_content()
                        print(f"    셀 {cell_idx}: {text[:30] if text else 'N/A'}")
        
        # 게시물 데이터 수집
        posts_data = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 가장 가능성 높은 테이블 선택 (보통 가장 큰 테이블)
        main_table = None
        max_rows = 0
        
        for table in tables:
            rows = await table.query_selector_all('tr')
            if len(rows) > max_rows:
                max_rows = len(rows)
                main_table = table
        
        if main_table and max_rows > 1:
            print(f"\n[INFO] 메인 테이블에서 데이터 수집 시작 ({max_rows}개 행)")
            
            rows = await main_table.query_selector_all('tr')
            
            # 헤더 제외하고 처리 (최대 5개)
            for row_idx, row in enumerate(rows[1:6], 1):
                try:
                    cells = await row.query_selector_all('td')
                    
                    if len(cells) >= 4:  # 최소 4개 셀 (번호, 제목, 작성자, 날짜)
                        post_data = {
                            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '순번': row_idx
                        }
                        
                        # 번호
                        if len(cells) > 0:
                            num_text = await cells[0].text_content()
                            post_data['번호'] = num_text.strip() if num_text else ''
                        
                        # 구분
                        if len(cells) > 1:
                            category_text = await cells[1].text_content()
                            post_data['구분'] = category_text.strip() if category_text else ''
                        
                        # 제목 및 링크
                        if len(cells) > 2:
                            title_cell = cells[2]
                            title_link = await title_cell.query_selector('a')
                            
                            if title_link:
                                title_text = await title_link.text_content()
                                post_data['제목'] = title_text.strip() if title_text else ''
                                
                                # href에서 boardId 추출
                                href = await title_link.get_attribute('href')
                                if href and 'boardId=' in href:
                                    board_id_match = re.search(r'boardId=(\d+)', href)
                                    if board_id_match:
                                        post_data['boardId'] = board_id_match.group(1)
                                        
                                        # 상세 페이지 URL 생성
                                        detail_url = f"https://longtermcare.or.kr/npbs/cms/board/board/Board.jsp?"
                                        detail_url += f"communityKey=B0017&boardId={post_data['boardId']}&act=VIEW"
                                        post_data['상세URL'] = detail_url
                            else:
                                title_text = await title_cell.text_content()
                                post_data['제목'] = title_text.strip() if title_text else ''
                        
                        # 작성자
                        if len(cells) > 3:
                            author_text = await cells[3].text_content()
                            post_data['작성자'] = author_text.strip() if author_text else ''
                        
                        # 작성일
                        if len(cells) > 4:
                            date_text = await cells[4].text_content()
                            post_data['작성일'] = date_text.strip() if date_text else ''
                        
                        # 조회수
                        if len(cells) > 5:
                            view_text = await cells[5].text_content()
                            post_data['조회수'] = view_text.strip() if view_text else ''
                        
                        posts_data.append(post_data)
                        print(f"  [{row_idx}] {post_data.get('제목', 'N/A')[:40]}...")
                        
                        # 상세 페이지에서 첨부파일 정보 수집
                        if 'boardId' in post_data:
                            new_page = await context.new_page()
                            try:
                                await new_page.goto(post_data['상세URL'], wait_until='networkidle')
                                await new_page.wait_for_timeout(2000)
                                
                                # 첨부파일 확인
                                file_links = await new_page.query_selector_all('a[href*="/Download.jsp"]')
                                post_data['첨부파일수'] = len(file_links)
                                
                                if file_links:
                                    file_names = []
                                    download_dir = f"data/downloads/metadata_test/{timestamp}"
                                    os.makedirs(download_dir, exist_ok=True)
                                    
                                    for file_idx, file_link in enumerate(file_links[:2], 1):
                                        try:
                                            file_text = await file_link.text_content()
                                            file_names.append(file_text.strip()[:50])
                                            
                                            # 파일 다운로드
                                            async with new_page.expect_download(timeout=30000) as download_info:
                                                await file_link.click()
                                            
                                            download = await download_info.value
                                            safe_name = re.sub(r'[<>:"/\\|?*]', '_', download.suggested_filename)[:100]
                                            file_path = os.path.join(download_dir, f"{row_idx:03d}_{safe_name}")
                                            
                                            await download.save_as(file_path)
                                            post_data[f'첨부파일{file_idx}'] = safe_name
                                            print(f"    ✅ 첨부파일 다운로드: {safe_name[:30]}...")
                                            
                                        except Exception as e:
                                            print(f"    ❌ 첨부파일 다운로드 실패: {str(e)[:30]}")
                                    
                                    post_data['첨부파일목록'] = ' | '.join(file_names)
                                
                            except Exception as e:
                                print(f"    상세 페이지 오류: {str(e)[:50]}")
                            finally:
                                await new_page.close()
                        
                except Exception as e:
                    print(f"  [ERROR] 행 {row_idx} 처리 실패: {str(e)[:50]}")
        
        # Excel 저장
        if posts_data:
            df = pd.DataFrame(posts_data)
            excel_file = f"data/board_metadata_test_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name='서식자료실')
            
            print(f"""
            ==============================================================
                                    수집 완료
            ==============================================================
            수집 게시물: {len(posts_data)}개
            Excel 파일: {excel_file}
            첨부파일: data/downloads/metadata_test/{timestamp}/
            ==============================================================
            """)
            
            # 데이터 샘플 출력
            print("\n[수집된 데이터 샘플]")
            for col in df.columns[:8]:
                print(f"  {col}: {df[col].iloc[0] if not df.empty else 'N/A'}")
        else:
            print("\n[WARNING] 수집된 데이터가 없습니다.")
        
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    print("\n게시판 메타데이터 수집 테스트\n")
    asyncio.run(test_board_metadata())
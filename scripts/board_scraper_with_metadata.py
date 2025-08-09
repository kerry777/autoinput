#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
게시판 스크래핑 - 게시물 메타데이터 + 첨부파일 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
import sys
import re
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class BoardScraper:
    """게시판 스크래퍼 - 메타데이터 수집 및 첨부파일 다운로드"""
    
    def __init__(self):
        self.boards = {
            '서식자료실': {'communityKey': 'B0017', 'list_url': 'https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017'},
            '법령자료실': {'communityKey': 'B0018', 'list_url': 'https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000950&bKey=B0018'},
            '통계자료실': {'communityKey': 'B0020', 'list_url': 'https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000001000&bKey=B0020'},
            '자주하는질문': {'communityKey': 'B0019', 'list_url': 'https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000980&bKey=B0019'}
        }
        self.all_posts_data = []
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    async def scrape_board_list(self, page, board_name, max_posts=10):
        """게시판 목록에서 게시물 정보 수집"""
        board_info = self.boards[board_name]
        posts_data = []
        
        print(f"\n{'='*60}")
        print(f"  {board_name} 스크래핑 시작")
        print(f"{'='*60}")
        
        # 게시판 목록 페이지 접속
        await page.goto(board_info['list_url'], wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 게시물 목록 수집 - 다양한 셀렉터 시도
        posts = await page.query_selector_all('tr.notice_off')
        
        if not posts:
            posts = await page.query_selector_all('tbody tr[class*="notice"]')
        
        if not posts:
            posts = await page.query_selector_all('table tbody tr')
            # 헤더 행 제외
            if posts and len(posts) > 1:
                posts = posts[1:]  # 첫 번째 행(헤더) 제외
        
        if not posts:
            # 스크린샷 저장하여 디버깅
            screenshot_path = f"logs/debug_{board_name}_{self.timestamp}.png"
            await page.screenshot(path=screenshot_path)
            print(f"  [DEBUG] 스크린샷 저장: {screenshot_path}")
        
        print(f"  발견된 게시물: {len(posts)}개")
        
        # 각 게시물 정보 수집 (최대 max_posts개)
        for idx, post in enumerate(posts[:max_posts], 1):
            try:
                post_data = {
                    '게시판': board_name,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '순번': idx
                }
                
                # 게시물 번호
                num_elem = await post.query_selector('td:first-child')
                if num_elem:
                    post_data['번호'] = await num_elem.text_content()
                
                # 제목 및 링크
                title_link = await post.query_selector('a')
                if title_link:
                    post_data['제목'] = (await title_link.text_content()).strip()
                    
                    # boardId 추출
                    href = await title_link.get_attribute('href')
                    if href and 'boardId=' in href:
                        board_id = re.search(r'boardId=(\d+)', href)
                        if board_id:
                            post_data['boardId'] = board_id.group(1)
                
                # 작성자
                author_elem = await post.query_selector('td:nth-child(3)')
                if author_elem:
                    post_data['작성자'] = await author_elem.text_content()
                
                # 작성일
                date_elem = await post.query_selector('td:nth-child(4)')
                if date_elem:
                    post_data['작성일'] = await date_elem.text_content()
                
                # 조회수
                view_elem = await post.query_selector('td:nth-child(5)')
                if view_elem:
                    post_data['조회수'] = await view_elem.text_content()
                
                # 상세 페이지에서 추가 정보 수집
                if 'boardId' in post_data:
                    detail_data = await self.scrape_post_detail(
                        page, board_name, post_data['boardId'], idx
                    )
                    post_data.update(detail_data)
                
                posts_data.append(post_data)
                print(f"  [{idx}/{min(len(posts), max_posts)}] {post_data.get('제목', 'N/A')[:30]}...")
                
            except Exception as e:
                print(f"  [ERROR] 게시물 {idx} 처리 실패: {str(e)[:50]}")
        
        return posts_data
    
    async def scrape_post_detail(self, page, board_name, board_id, post_num):
        """게시물 상세 페이지에서 추가 정보 및 첨부파일 수집"""
        detail_data = {}
        board_info = self.boards[board_name]
        
        # 새 페이지에서 상세 정보 수집
        new_page = await page.context.new_page()
        
        try:
            # 상세 페이지 URL
            detail_url = f"https://longtermcare.or.kr/npbs/cms/board/board/Board.jsp?"
            detail_url += f"searchType=ALL&searchWord=&list_start_date=&list_end_date="
            detail_url += f"&pageSize=&branch_id=&branch_child_id=&pageNum=1"
            detail_url += f"&list_show_answer=N&communityKey={board_info['communityKey']}"
            detail_url += f"&boardId={board_id}&act=VIEW"
            
            await new_page.goto(detail_url, wait_until='networkidle')
            await new_page.wait_for_timeout(2000)
            
            # 내용 수집 (첫 200자)
            content_selectors = ['.board-content', '.view-content', 'td.content', 'div.content']
            for selector in content_selectors:
                content_elem = await new_page.query_selector(selector)
                if content_elem:
                    content = await content_elem.text_content()
                    detail_data['내용'] = content[:200].strip() if content else ''
                    break
            
            # 첨부파일 처리
            file_links = await new_page.query_selector_all('a[href*="/Download.jsp"]')
            
            if file_links:
                detail_data['첨부파일수'] = len(file_links)
                file_names = []
                download_dir = f"data/downloads/{board_name.replace('/', '_')}/{self.timestamp}"
                os.makedirs(download_dir, exist_ok=True)
                
                for idx, file_link in enumerate(file_links[:3], 1):  # 최대 3개만
                    try:
                        file_text = await file_link.text_content()
                        file_names.append(file_text.strip())
                        
                        # 파일 다운로드
                        async with new_page.expect_download(timeout=30000) as download_info:
                            await file_link.click()
                        
                        download = await download_info.value
                        suggested_name = download.suggested_filename
                        safe_name = re.sub(r'[<>:"/\\|?*]', '_', suggested_name)[:100]
                        
                        # 파일명에 게시물 번호 포함
                        final_name = f"{post_num:03d}_{safe_name}"
                        file_path = os.path.join(download_dir, final_name)
                        
                        await download.save_as(file_path)
                        detail_data[f'첨부파일{idx}'] = safe_name
                        detail_data[f'파일경로{idx}'] = file_path
                        
                    except Exception as e:
                        print(f"      첨부파일 {idx} 다운로드 실패: {str(e)[:30]}")
                
                detail_data['첨부파일목록'] = ' | '.join(file_names[:3])
            else:
                detail_data['첨부파일수'] = 0
                detail_data['첨부파일목록'] = ''
            
        except Exception as e:
            print(f"    상세 페이지 처리 실패: {str(e)[:50]}")
        
        finally:
            await new_page.close()
        
        return detail_data
    
    async def scrape_all_boards(self, max_posts_per_board=5):
        """모든 게시판 스크래핑"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=300)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            page = await context.new_page()
            
            for board_name in self.boards.keys():
                posts_data = await self.scrape_board_list(page, board_name, max_posts_per_board)
                self.all_posts_data.extend(posts_data)
                
                # 중간 저장
                await self.save_to_excel(board_name)
            
            # 전체 데이터 저장
            await self.save_all_data()
            
            await browser.close()
    
    async def save_to_excel(self, board_name):
        """개별 게시판 데이터를 Excel로 저장"""
        if not self.all_posts_data:
            return
        
        # 해당 게시판 데이터만 필터링
        board_data = [p for p in self.all_posts_data if p['게시판'] == board_name]
        
        if board_data:
            df = pd.DataFrame(board_data)
            
            # 컬럼 순서 정리
            columns_order = ['게시판', '수집일시', '순번', '번호', 'boardId', '제목', 
                           '작성자', '작성일', '조회수', '내용', '첨부파일수', '첨부파일목록']
            
            # 첨부파일 관련 컬럼 추가
            for col in df.columns:
                if col.startswith('첨부파일') or col.startswith('파일경로'):
                    if col not in columns_order:
                        columns_order.append(col)
            
            # 존재하는 컬럼만 선택
            columns_order = [col for col in columns_order if col in df.columns]
            df = df[columns_order]
            
            # Excel 저장
            safe_board_name = board_name.replace('/', '_')
            excel_file = f"data/boards_{safe_board_name}_{self.timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name=board_name)
            print(f"\n  ✅ {board_name} 데이터 저장: {excel_file}")
    
    async def save_all_data(self):
        """전체 데이터를 통합 Excel로 저장"""
        if not self.all_posts_data:
            return
        
        # 전체 데이터 DataFrame
        df_all = pd.DataFrame(self.all_posts_data)
        
        # 통합 Excel 파일
        excel_file = f"data/all_boards_metadata_{self.timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 전체 데이터 시트
            df_all.to_excel(writer, sheet_name='전체_데이터', index=False)
            
            # 게시판별 시트
            for board_name in self.boards.keys():
                board_data = [p for p in self.all_posts_data if p['게시판'] == board_name]
                if board_data:
                    df_board = pd.DataFrame(board_data)
                    safe_name = board_name.replace('/', '_')[:31]  # Excel 시트명 제한
                    df_board.to_excel(writer, sheet_name=safe_name, index=False)
        
        print(f"""
        {'='*60}
                        스크래핑 완료 요약
        {'='*60}
        총 수집 게시물: {len(self.all_posts_data)}개
        통합 Excel 파일: {excel_file}
        첨부파일 저장: data/downloads/[게시판명]/{self.timestamp}/
        {'='*60}
        """)
        
        # JSON 백업
        json_file = f"data/all_boards_metadata_{self.timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_posts_data, f, ensure_ascii=False, indent=2)
        print(f"  JSON 백업: {json_file}")

async def main():
    """메인 실행 함수"""
    scraper = BoardScraper()
    
    # 각 게시판에서 5개씩 수집 (테스트용)
    await scraper.scrape_all_boards(max_posts_per_board=5)

if __name__ == "__main__":
    print("""
    ================================================
       게시판 메타데이터 수집 + 첨부파일 다운로드
    ================================================
    """)
    asyncio.run(main())
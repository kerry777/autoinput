#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자료실 게시판 스크래퍼 - 첨부파일 다운로드 기능 포함
서식, 법령, 질문, 통계 자료실에서 각 3개 게시물과 첨부파일 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd
import sys

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class BoardScraper:
    """게시판 스크래퍼 - 첨부파일 다운로드 포함"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.boards = {
            '서식': '/npbs/d/m/000/moveBoardView?menuId=npe0000002207&prevPath=/npbs/indexMain.web',
            '법령': '/npbs/d/m/000/moveBoardView?menuId=npe0000002208&prevPath=/npbs/indexMain.web',
            '질문': '/npbs/d/m/000/moveBoardView?menuId=npe0000002209&prevPath=/npbs/indexMain.web',
            '통계': '/npbs/d/m/000/moveBoardView?menuId=npe0000002210&prevPath=/npbs/indexMain.web'
        }
        self.download_dir = "data/downloads/board_attachments"
        self.data_dir = "data/scraped"
        self.all_posts = []
        self.download_stats = {
            '총_게시물': 0,
            '첨부파일_있음': 0,
            '다운로드_성공': 0,
            '다운로드_실패': 0
        }
        
    async def initialize(self):
        """초기화"""
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 각 게시판별 다운로드 폴더 생성
        for board_name in self.boards.keys():
            board_dir = os.path.join(self.download_dir, board_name)
            os.makedirs(board_dir, exist_ok=True)
        
        print(f"[INIT] 다운로드 디렉토리: {self.download_dir}")
        print(f"[INIT] 데이터 디렉토리: {self.data_dir}")
    
    async def scrape_board_list(self, page, board_name, board_url, max_posts=3):
        """게시판 목록에서 게시물 정보 수집"""
        print(f"\n{'='*60}")
        print(f"  {board_name} 자료실 스크래핑")
        print(f"{'='*60}")
        
        # 게시판 페이지로 이동
        full_url = self.base_url + board_url
        print(f"[이동] {full_url}")
        await page.goto(full_url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        posts_data = []
        
        # 게시물 목록 찾기 (테이블 구조 가정)
        rows = await page.query_selector_all('table tbody tr, .board-list tr, .list-table tr')
        
        if not rows:
            # 다른 셀렉터 시도
            rows = await page.query_selector_all('tr')
            rows = rows[1:] if rows else []  # 헤더 제외
        
        print(f"[확인] {len(rows)}개 게시물 발견")
        
        # 최대 max_posts개만 처리
        for idx, row in enumerate(rows[:max_posts], 1):
            try:
                post_info = {
                    '게시판': board_name,
                    '순번': idx,
                    '제목': '',
                    '작성자': '',
                    '작성일': '',
                    '조회수': '',
                    '첨부파일': '없음',
                    '다운로드_경로': '',
                    '게시물_URL': ''
                }
                
                # 제목 추출 (링크 포함)
                title_link = await row.query_selector('a')
                if title_link:
                    post_info['제목'] = await title_link.text_content()
                    post_info['제목'] = post_info['제목'].strip()
                    
                    # 게시물 상세 페이지 URL
                    href = await title_link.get_attribute('href')
                    onclick = await title_link.get_attribute('onclick')
                    
                    if onclick and 'fnViewDetail' in onclick:
                        # JavaScript 함수에서 게시물 번호 추출
                        post_info['게시물_URL'] = onclick
                
                # 다른 정보 추출
                cells = await row.query_selector_all('td')
                if len(cells) >= 4:
                    # 일반적인 게시판 구조: 번호, 제목, 작성자, 작성일, 조회수
                    if len(cells) > 2:
                        post_info['작성자'] = await cells[2].text_content() if len(cells) > 2 else ''
                    if len(cells) > 3:
                        post_info['작성일'] = await cells[3].text_content() if len(cells) > 3 else ''
                    if len(cells) > 4:
                        post_info['조회수'] = await cells[4].text_content() if len(cells) > 4 else ''
                
                # 첨부파일 아이콘 확인
                file_icon = await row.query_selector('img[alt*="첨부"], img[src*="file"], img[src*="attach"], .file-icon, .ico-file')
                if file_icon:
                    post_info['첨부파일'] = '있음'
                
                posts_data.append(post_info)
                print(f"  [{idx}] {post_info['제목'][:30]}... {'[첨부]' if post_info['첨부파일'] == '있음' else ''}")
                
            except Exception as e:
                print(f"  [ERROR] 게시물 {idx} 처리 실패: {str(e)}")
                continue
        
        # 각 게시물 상세 페이지 방문하여 첨부파일 다운로드
        for post in posts_data:
            if post['게시물_URL']:
                await self.download_attachments(page, post, board_name)
                await page.wait_for_timeout(1000)  # 서버 부하 방지
        
        return posts_data
    
    async def download_attachments(self, page, post_info, board_name):
        """게시물 상세 페이지에서 첨부파일 다운로드"""
        try:
            print(f"\n  [상세] {post_info['제목'][:30]}...")
            
            # onclick 함수 실행하여 상세 페이지로 이동
            if 'fnViewDetail' in post_info['게시물_URL']:
                await page.evaluate(post_info['게시물_URL'])
                await page.wait_for_timeout(2000)
            else:
                print(f"    [SKIP] 상세 페이지 URL 없음")
                return
            
            # 첨부파일 영역 찾기
            file_areas = [
                '.file-list',
                '.attach-file',
                '.board-file',
                '#fileList',
                '.file_list',
                'div:has-text("첨부파일")',
                'td:has-text("첨부파일")'
            ]
            
            file_links = []
            for selector in file_areas:
                links = await page.query_selector_all(f'{selector} a')
                if links:
                    file_links.extend(links)
                    break
            
            # 일반적인 파일 링크도 찾기
            if not file_links:
                file_links = await page.query_selector_all('a[href*="download"], a[href*="file"], a[onclick*="download"]')
            
            if file_links:
                print(f"    [파일] {len(file_links)}개 첨부파일 발견")
                
                download_folder = os.path.join(self.download_dir, board_name, f"post_{post_info['순번']}")
                os.makedirs(download_folder, exist_ok=True)
                
                for idx, link in enumerate(file_links[:3], 1):  # 최대 3개 파일만
                    try:
                        file_name = await link.text_content()
                        file_name = file_name.strip() if file_name else f"file_{idx}"
                        
                        # 파일 다운로드
                        async with page.expect_download(timeout=30000) as download_info:
                            await link.click()
                        
                        download = await download_info.value
                        
                        # 파일 저장
                        file_path = os.path.join(download_folder, file_name)
                        await download.save_as(file_path)
                        
                        print(f"      ✓ {file_name} 다운로드 완료")
                        post_info['다운로드_경로'] = download_folder
                        self.download_stats['다운로드_성공'] += 1
                        
                    except Exception as e:
                        print(f"      ✗ 파일 {idx} 다운로드 실패: {str(e)[:50]}")
                        self.download_stats['다운로드_실패'] += 1
                
                post_info['첨부파일'] = f"{len(file_links)}개"
                self.download_stats['첨부파일_있음'] += 1
            else:
                print(f"    [파일] 첨부파일 없음")
            
            # 목록으로 돌아가기
            back_btn = await page.query_selector('a:has-text("목록"), button:has-text("목록"), .btn-list')
            if back_btn:
                await back_btn.click()
                await page.wait_for_timeout(1500)
            else:
                # 브라우저 뒤로가기
                await page.go_back()
                await page.wait_for_timeout(1500)
                
        except Exception as e:
            print(f"    [ERROR] 첨부파일 다운로드 실패: {str(e)[:100]}")
    
    async def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 엑셀 파일로 저장
        excel_file = os.path.join(self.data_dir, f"board_data_{timestamp}.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 전체 데이터
            if self.all_posts:
                df = pd.DataFrame(self.all_posts)
                df.to_excel(writer, sheet_name='전체_게시물', index=False)
            
            # 게시판별 시트
            for board_name in self.boards.keys():
                board_posts = [p for p in self.all_posts if p['게시판'] == board_name]
                if board_posts:
                    df_board = pd.DataFrame(board_posts)
                    df_board.to_excel(writer, sheet_name=f'{board_name}_자료실', index=False)
            
            # 통계 시트
            stats_df = pd.DataFrame([self.download_stats])
            stats_df.to_excel(writer, sheet_name='다운로드_통계', index=False)
        
        print(f"\n[저장] 엑셀 파일: {excel_file}")
        
        # JSON 백업
        json_file = os.path.join(self.data_dir, f"board_data_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'posts': self.all_posts,
                'stats': self.download_stats,
                'timestamp': timestamp
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[저장] JSON 백업: {json_file}")
        
        return excel_file
    
    async def run(self):
        """메인 실행"""
        await self.initialize()
        
        print("""
        ==============================================================
                    자료실 게시판 스크래핑 (첨부파일 포함)
        ==============================================================
        
          대상: 서식, 법령, 질문, 통계 자료실
          수집: 각 게시판별 3개 게시물
          기능: 첨부파일 자동 다운로드
        
        ==============================================================
        """)
        
        async with async_playwright() as p:
            # 다운로드를 위한 브라우저 설정
            browser = await p.chromium.launch(
                headless=False,  # 다운로드 확인을 위해 화면 표시
                slow_mo=500
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True  # 다운로드 허용
            )
            
            page = await context.new_page()
            
            try:
                # 각 게시판 순회
                for board_name, board_url in self.boards.items():
                    posts = await self.scrape_board_list(page, board_name, board_url, max_posts=3)
                    self.all_posts.extend(posts)
                    self.download_stats['총_게시물'] += len(posts)
                    
                    await page.wait_for_timeout(2000)  # 게시판 간 대기
                
                # 결과 저장
                excel_file = await self.save_results()
                
                # 통계 출력
                print(f"""
                ==============================================================
                                    스크래핑 완료
                ==============================================================
                
                  [수집 통계]
                  - 총 게시물: {self.download_stats['총_게시물']}개
                  - 첨부파일 있는 게시물: {self.download_stats['첨부파일_있음']}개
                  - 다운로드 성공: {self.download_stats['다운로드_성공']}개
                  - 다운로드 실패: {self.download_stats['다운로드_실패']}개
                  
                  [저장 위치]
                  - 게시물 정보: {excel_file}
                  - 첨부파일: {self.download_dir}/[게시판명]/post_[번호]/
                
                ==============================================================
                """)
                
                print("\n[INFO] 브라우저가 10초 후 닫힙니다...")
                await page.wait_for_timeout(10000)
                
            except Exception as e:
                print(f"\n[ERROR] 스크래핑 실패: {str(e)}")
                import traceback
                traceback.print_exc()
            
            finally:
                await browser.close()
                print("\n[COMPLETE] 작업 완료")

async def main():
    """메인 함수"""
    scraper = BoardScraper()
    await scraper.run()

if __name__ == "__main__":
    print("\n자료실 게시판 스크래핑을 시작합니다...\n")
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
법령, 질문, 통계 자료실 첨부파일 다운로드 테스트
모든 자료실 게시판 테스트
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import sys
import re
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class AllBoardsScraper:
    """모든 자료실 스크래퍼"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.download_dir = "data/downloads/all_boards"
        self.results = {
            '서식': {'posts': 0, 'files': 0},
            '법령': {'posts': 0, 'files': 0},
            '질문': {'posts': 0, 'files': 0},
            '통계': {'posts': 0, 'files': 0}
        }
        
        # 각 게시판의 URL과 communityKey
        self.boards = {
            '서식': {
                'url': '/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017',
                'communityKey': 'B0017',
                'name': '서식자료실'
            },
            '법령': {
                'url': '/npbs/d/m/000/moveBoardView?menuId=npe0000000930&bKey=B0018',
                'communityKey': 'B0018',
                'name': '법령자료실'
            },
            '질문': {
                'url': '/npbs/d/m/000/moveBoardView?menuId=npe0000000940&bKey=B0008',
                'communityKey': 'B0008',
                'name': '자주하는질문'
            },
            '통계': {
                'url': '/npbs/d/m/000/moveBoardView?menuId=npe0000000950&bKey=B0009',
                'communityKey': 'B0009',
                'name': '통계자료실'
            }
        }
    
    async def initialize(self):
        """초기화"""
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs("logs/screenshots", exist_ok=True)
        
        # 각 게시판별 다운로드 폴더 생성
        for board_name in self.boards.keys():
            board_dir = os.path.join(self.download_dir, board_name)
            os.makedirs(board_dir, exist_ok=True)
        
        print(f"[INIT] 다운로드 디렉토리: {self.download_dir}")
    
    async def get_board_posts(self, page, board_type):
        """게시판 목록에서 게시물 ID 추출"""
        board_info = self.boards[board_type]
        
        print(f"\n{'='*60}")
        print(f"  {board_info['name']} 스크래핑")
        print(f"{'='*60}")
        
        # 게시판 목록 페이지로 이동
        list_url = self.base_url + board_info['url']
        print(f"\n[1] 목록 페이지 이동")
        print(f"    URL: {list_url[:80]}...")
        
        await page.goto(list_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f'logs/screenshots/{board_type}_list_{timestamp}.png'
        await page.screenshot(path=screenshot_path)
        print(f"    [스크린샷] {screenshot_path}")
        
        # 게시물 ID 추출 - JavaScript로 링크 분석
        post_ids = await page.evaluate('''() => {
            const posts = [];
            const links = document.querySelectorAll('a[href*="boardId="]');
            
            for (let link of links) {
                const href = link.getAttribute('href');
                const match = href.match(/boardId=(\d+)/);
                if (match) {
                    const title = link.textContent.trim();
                    posts.push({
                        id: match[1],
                        title: title
                    });
                }
            }
            
            // 중복 제거
            const unique = [];
            const seen = new Set();
            for (let post of posts) {
                if (!seen.has(post.id)) {
                    seen.add(post.id);
                    unique.push(post);
                }
            }
            
            return unique.slice(0, 3); // 최대 3개
        }''')
        
        if not post_ids:
            # 백업 방법: onclick 속성에서 추출
            post_ids = await page.evaluate('''() => {
                const posts = [];
                const elements = document.querySelectorAll('[onclick*="fnViewDetail"], [onclick*="fnDetail"], [onclick*="view"]');
                
                for (let el of elements) {
                    const onclick = el.getAttribute('onclick');
                    const match = onclick.match(/['"](\d+)['"]/);
                    if (match) {
                        const title = el.textContent.trim();
                        posts.push({
                            id: match[1],
                            title: title
                        });
                    }
                }
                
                return posts.slice(0, 3);
            }''')
        
        print(f"    추출된 게시물: {len(post_ids)}개")
        for post in post_ids:
            print(f"      - ID: {post['id']}, 제목: {post['title'][:30]}...")
        
        return post_ids, board_info['communityKey']
    
    async def download_post_attachments(self, page, board_type, post_id, community_key):
        """게시물 상세 페이지에서 첨부파일 다운로드"""
        
        # 상세 페이지 URL 생성
        detail_url = f"https://longtermcare.or.kr/npbs/cms/board/board/Board.jsp?searchType=ALL&searchWord=&list_start_date=&list_end_date=&pageSize=&branch_id=&branch_child_id=&pageNum=1&list_show_answer=N&communityKey={community_key}&boardId={post_id}&act=VIEW"
        
        print(f"\n  [게시물 {post_id}]")
        print(f"    상세 페이지 이동...")
        
        await page.goto(detail_url, wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # 첨부파일 찾기
        file_links = await page.query_selector_all('a[href*="/Download.jsp"], a[href*="file"], a[onclick*="download"]')
        
        if not file_links:
            # 확장 검색
            all_links = await page.query_selector_all('a')
            file_links = []
            for link in all_links:
                try:
                    text = await link.text_content()
                    href = await link.get_attribute('href')
                    if text and any(ext in text.lower() for ext in ['.hwp', '.pdf', '.doc', '.xls', '.zip', '.ppt']):
                        file_links.append(link)
                    elif href and '/Download.jsp' in href:
                        file_links.append(link)
                except:
                    pass
        
        download_count = 0
        
        if file_links:
            print(f"    첨부파일 {len(file_links)}개 발견")
            
            # 다운로드 폴더 생성
            post_folder = os.path.join(self.download_dir, board_type, f"post_{post_id}")
            os.makedirs(post_folder, exist_ok=True)
            
            # 파일 다운로드
            for idx, file_link in enumerate(file_links[:2], 1):  # 최대 2개
                try:
                    file_text = await file_link.text_content()
                    file_name = file_text.strip() if file_text else f"file_{idx}"
                    
                    print(f"      파일 {idx}: {file_name[:40]}...")
                    
                    # 다운로드 시도
                    async with page.expect_download(timeout=30000) as download_info:
                        await file_link.click()
                    
                    download = await download_info.value
                    
                    # 파일 저장
                    suggested_name = download.suggested_filename
                    safe_name = re.sub(r'[<>:"/\\|?*]', '_', suggested_name)[:100]
                    file_path = os.path.join(post_folder, safe_name)
                    
                    await download.save_as(file_path)
                    
                    print(f"        ✅ 다운로드 성공: {safe_name}")
                    download_count += 1
                    
                except Exception as e:
                    print(f"        ❌ 다운로드 실패: {str(e)[:50]}")
        else:
            print(f"    첨부파일 없음")
        
        return download_count
    
    async def scrape_board(self, page, board_type):
        """게시판 스크래핑"""
        try:
            # 1. 게시물 목록 가져오기
            post_ids, community_key = await self.get_board_posts(page, board_type)
            
            if not post_ids:
                print(f"    ⚠️ 게시물을 찾을 수 없음")
                return
            
            # 2. 각 게시물에서 첨부파일 다운로드
            total_files = 0
            for post in post_ids[:3]:  # 최대 3개 게시물
                try:
                    files = await self.download_post_attachments(page, board_type, post['id'], community_key)
                    total_files += files
                    self.results[board_type]['posts'] += 1
                except Exception as e:
                    print(f"    [ERROR] 게시물 {post['id']} 처리 실패: {str(e)[:50]}")
            
            self.results[board_type]['files'] = total_files
            print(f"\n  [완료] {board_type}: {self.results[board_type]['posts']}개 게시물, {total_files}개 파일")
            
        except Exception as e:
            print(f"  [ERROR] {board_type} 게시판 처리 실패: {str(e)[:100]}")
    
    async def run(self):
        """메인 실행"""
        await self.initialize()
        
        print("""
        ==============================================================
                    모든 자료실 첨부파일 다운로드 테스트
        ==============================================================
        
          대상: 서식, 법령, 질문, 통계 자료실
          방식: 각 게시판에서 최대 3개 게시물의 첨부파일 다운로드
        
        ==============================================================
        """)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                slow_mo=500
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            
            page = await context.new_page()
            
            try:
                # 각 게시판 처리
                for board_type in ['서식', '법령', '질문', '통계']:
                    await self.scrape_board(page, board_type)
                    await page.wait_for_timeout(2000)  # 게시판 간 대기
                
                # 결과 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                result_file = os.path.join(self.download_dir, f"results_{timestamp}.json")
                
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, ensure_ascii=False, indent=2)
                
                # 최종 결과 출력
                print(f"""
                ==============================================================
                                    테스트 완료!
                ==============================================================
                
                📊 전체 결과:
                """)
                
                total_posts = 0
                total_files = 0
                
                for board_type, stats in self.results.items():
                    print(f"  {board_type}자료실: {stats['posts']}개 게시물, {stats['files']}개 파일")
                    total_posts += stats['posts']
                    total_files += stats['files']
                
                print(f"""
                  ──────────────────────────────────
                  총계: {total_posts}개 게시물, {total_files}개 파일
                
                📁 저장 위치: {self.download_dir}/[게시판]/post_[ID]/
                📄 결과 파일: {result_file}
                
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
                print("\n[COMPLETE] 작업 완료")

async def main():
    """메인 함수"""
    scraper = AllBoardsScraper()
    await scraper.run()

if __name__ == "__main__":
    print("\n🚀 모든 자료실 테스트 시작\n")
    asyncio.run(main())
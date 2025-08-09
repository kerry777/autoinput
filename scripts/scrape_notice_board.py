#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
공지사항 게시판 스크래퍼 - 첨부파일 다운로드 테스트
공지사항에서 최근 3개 게시물과 첨부파일 다운로드
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd
import sys
import re

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class NoticeBoardScraper:
    """공지사항 게시판 스크래퍼"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr"
        self.notice_url = "/npbs/d/m/000/moveBoardView?menuId=npe0000002450&prevPath=%2Fnpbs%2FindexMain.web"
        self.download_dir = "data/downloads/notice_attachments"
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
        os.makedirs('logs/screenshots', exist_ok=True)
        
        print(f"[INIT] 다운로드 디렉토리: {self.download_dir}")
        print(f"[INIT] 데이터 디렉토리: {self.data_dir}")
    
    async def scrape_notice_list(self, page, max_posts=3):
        """공지사항 목록에서 게시물 정보 수집"""
        print(f"\n{'='*60}")
        print(f"  공지사항 게시판 스크래핑")
        print(f"{'='*60}")
        
        # 공지사항 페이지로 이동
        full_url = self.base_url + self.notice_url
        print(f"\n[이동] 공지사항 페이지")
        print(f"URL: {full_url}")
        
        await page.goto(full_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f'logs/screenshots/notice_list_{timestamp}.png'
        await page.screenshot(path=screenshot_path)
        print(f"[스크린샷] {screenshot_path}")
        
        posts_data = []
        
        # 게시물 목록 찾기 - 여러 가능한 셀렉터 시도
        selectors = [
            'table.board-list tbody tr',
            'table.list-table tbody tr',
            'table.tbl-list tbody tr',
            '.board-list tbody tr',
            '.list-wrapper tbody tr',
            'table tbody tr[onclick]',
            'table tbody tr'
        ]
        
        rows = []
        for selector in selectors:
            rows = await page.query_selector_all(selector)
            if rows:
                print(f"[확인] 셀렉터 '{selector}'로 {len(rows)}개 게시물 발견")
                break
        
        if not rows:
            # tbody가 없는 경우 tr 직접 찾기
            all_trs = await page.query_selector_all('table tr')
            # 헤더 제외 (보통 첫 번째 tr)
            rows = all_trs[1:] if len(all_trs) > 1 else []
            print(f"[확인] 전체 tr에서 {len(rows)}개 행 발견")
        
        # 최대 max_posts개만 처리
        actual_posts = 0
        for idx, row in enumerate(rows, 1):
            if actual_posts >= max_posts:
                break
                
            try:
                # 공지/일반 구분
                cells = await row.query_selector_all('td')
                if not cells:
                    continue
                
                # 첫 번째 셀이 '공지'인 경우 건너뛰기 (선택사항)
                first_cell_text = await cells[0].text_content() if cells else ""
                
                post_info = {
                    '순번': actual_posts + 1,
                    '구분': '공지' if '공지' in first_cell_text else '일반',
                    '제목': '',
                    '작성자': '',
                    '작성일': '',
                    '조회수': '',
                    '첨부파일': '없음',
                    '다운로드_경로': '',
                    '게시물_번호': ''
                }
                
                # 제목 추출 (보통 두 번째 td에 있음)
                title_cell = cells[1] if len(cells) > 1 else None
                if title_cell:
                    title_link = await title_cell.query_selector('a')
                    if title_link:
                        post_info['제목'] = await title_link.text_content()
                        post_info['제목'] = post_info['제목'].strip()
                        
                        # onclick 속성에서 게시물 번호 추출
                        onclick = await title_link.get_attribute('onclick')
                        if onclick:
                            # fnViewDetail('123456') 형태에서 번호 추출
                            match = re.search(r"fnViewDetail\('(\d+)'\)", onclick)
                            if match:
                                post_info['게시물_번호'] = match.group(1)
                
                # 작성자, 작성일, 조회수 추출
                if len(cells) > 2:
                    post_info['작성자'] = (await cells[2].text_content()).strip() if len(cells) > 2 else ''
                if len(cells) > 3:
                    post_info['작성일'] = (await cells[3].text_content()).strip() if len(cells) > 3 else ''
                if len(cells) > 4:
                    post_info['조회수'] = (await cells[4].text_content()).strip() if len(cells) > 4 else ''
                
                # 첨부파일 아이콘 확인
                file_indicators = [
                    'img[alt*="첨부"]',
                    'img[src*="file"]',
                    'img[src*="attach"]',
                    'span.file',
                    'i.fa-paperclip',
                    '.attach'
                ]
                
                has_attachment = False
                for indicator in file_indicators:
                    file_icon = await row.query_selector(indicator)
                    if file_icon:
                        has_attachment = True
                        break
                
                if has_attachment:
                    post_info['첨부파일'] = '있음'
                
                posts_data.append(post_info)
                actual_posts += 1
                
                print(f"  [{actual_posts}] {post_info['제목'][:40]}... {'[첨부]' if post_info['첨부파일'] == '있음' else ''}")
                
            except Exception as e:
                print(f"  [ERROR] 게시물 {idx} 처리 실패: {str(e)}")
                continue
        
        # 각 게시물 상세 페이지 방문하여 첨부파일 다운로드
        for post in posts_data:
            if post['게시물_번호']:
                await self.view_and_download(page, post)
                await page.wait_for_timeout(2000)  # 서버 부하 방지
        
        return posts_data
    
    async def view_and_download(self, page, post_info):
        """게시물 상세 보기 및 첨부파일 다운로드"""
        try:
            print(f"\n  [상세] {post_info['제목'][:40]}...")
            
            # 게시물 번호로 상세 페이지 이동
            if post_info['게시물_번호']:
                # JavaScript 함수 실행
                await page.evaluate(f"fnViewDetail('{post_info['게시물_번호']}')")
                await page.wait_for_timeout(3000)
                
                # 스크린샷 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f'logs/screenshots/notice_detail_{post_info["순번"]}_{timestamp}.png'
                await page.screenshot(path=screenshot_path)
                print(f"    [스크린샷] {screenshot_path}")
                
                # 첨부파일 찾기
                file_selectors = [
                    'a[onclick*="fnFileDown"]',
                    'a[href*="download"]',
                    '.file-list a',
                    '.attach-file a',
                    'td:has-text("첨부파일") ~ td a',
                    'th:has-text("첨부파일") ~ td a'
                ]
                
                file_links = []
                for selector in file_selectors:
                    links = await page.query_selector_all(selector)
                    if links:
                        file_links = links
                        print(f"    [파일] 셀렉터 '{selector}'로 {len(links)}개 파일 발견")
                        break
                
                if file_links:
                    download_folder = os.path.join(self.download_dir, f"post_{post_info['순번']}_{post_info['게시물_번호']}")
                    os.makedirs(download_folder, exist_ok=True)
                    
                    for idx, link in enumerate(file_links[:3], 1):  # 최대 3개 파일
                        try:
                            file_name = await link.text_content()
                            file_name = file_name.strip() if file_name else f"file_{idx}"
                            
                            # 파일명 정리 (경로 구분자 제거)
                            file_name = file_name.replace('/', '_').replace('\\', '_')
                            
                            print(f"      다운로드 시도: {file_name}")
                            
                            # onclick 속성 확인
                            onclick = await link.get_attribute('onclick')
                            if onclick and 'fnFileDown' in onclick:
                                # fnFileDown 함수 실행으로 다운로드
                                async with page.expect_download(timeout=30000) as download_info:
                                    await page.evaluate(onclick)
                                
                                download = await download_info.value
                                file_path = os.path.join(download_folder, file_name)
                                await download.save_as(file_path)
                                
                                print(f"      ✓ {file_name} 다운로드 완료")
                                self.download_stats['다운로드_성공'] += 1
                            else:
                                # 일반 링크 클릭
                                async with page.expect_download(timeout=30000) as download_info:
                                    await link.click()
                                
                                download = await download_info.value
                                file_path = os.path.join(download_folder, file_name)
                                await download.save_as(file_path)
                                
                                print(f"      ✓ {file_name} 다운로드 완료")
                                self.download_stats['다운로드_성공'] += 1
                            
                            post_info['다운로드_경로'] = download_folder
                            
                        except Exception as e:
                            print(f"      ✗ 파일 {idx} 다운로드 실패: {str(e)[:50]}")
                            self.download_stats['다운로드_실패'] += 1
                    
                    post_info['첨부파일'] = f"{len(file_links)}개"
                    self.download_stats['첨부파일_있음'] += 1
                else:
                    print(f"    [파일] 첨부파일 없음")
                
                # 목록으로 돌아가기
                list_btn = await page.query_selector('a:has-text("목록"), button:has-text("목록")')
                if list_btn:
                    await list_btn.click()
                    await page.wait_for_timeout(2000)
                else:
                    # 브라우저 뒤로가기
                    await page.go_back()
                    await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"    [ERROR] 상세 페이지 처리 실패: {str(e)[:100]}")
    
    async def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 엑셀 파일로 저장
        excel_file = os.path.join(self.data_dir, f"notice_board_{timestamp}.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 전체 데이터
            if self.all_posts:
                df = pd.DataFrame(self.all_posts)
                df.to_excel(writer, sheet_name='공지사항', index=False)
            
            # 통계 시트
            stats_df = pd.DataFrame([self.download_stats])
            stats_df.to_excel(writer, sheet_name='다운로드_통계', index=False)
        
        print(f"\n[저장] 엑셀 파일: {excel_file}")
        
        # JSON 백업
        json_file = os.path.join(self.data_dir, f"notice_board_{timestamp}.json")
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
                공지사항 게시판 스크래핑 (첨부파일 다운로드 테스트)
        ==============================================================
        
          대상: 공지사항 게시판
          수집: 최근 3개 게시물
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
                # 공지사항 스크래핑
                posts = await self.scrape_notice_list(page, max_posts=3)
                self.all_posts.extend(posts)
                self.download_stats['총_게시물'] = len(posts)
                
                # 결과 저장
                excel_file = await self.save_results()
                
                # 통계 출력
                print(f"""
                ==============================================================
                                공지사항 스크래핑 완료
                ==============================================================
                
                  [수집 통계]
                  - 총 게시물: {self.download_stats['총_게시물']}개
                  - 첨부파일 있는 게시물: {self.download_stats['첨부파일_있음']}개
                  - 다운로드 성공: {self.download_stats['다운로드_성공']}개
                  - 다운로드 실패: {self.download_stats['다운로드_실패']}개
                  
                  [저장 위치]
                  - 게시물 정보: {excel_file}
                  - 첨부파일: {self.download_dir}/post_[번호]/
                
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
    scraper = NoticeBoardScraper()
    await scraper.run()

if __name__ == "__main__":
    print("\n공지사항 게시판 스크래핑을 시작합니다...\n")
    asyncio.run(main())
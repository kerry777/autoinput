#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서식자료실 게시판 스크래퍼 - 첨부파일 다운로드
https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017
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

class FormsBoardScraper:
    """서식자료실 게시판 스크래퍼"""
    
    def __init__(self):
        self.board_url = "https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017&prevPath=/npbs/d/m/000/moveBoardView"
        self.download_dir = "data/downloads/forms_attachments"
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
    
    async def scrape_forms_list(self, page, max_posts=3):
        """서식자료실 목록에서 게시물 정보 수집"""
        print(f"\n{'='*60}")
        print(f"  서식자료실 게시판 스크래핑")
        print(f"{'='*60}")
        
        # 서식자료실 페이지로 직접 이동
        print(f"\n[이동] 서식자료실 페이지")
        print(f"URL: {self.board_url}")
        
        await page.goto(self.board_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 스크린샷 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f'logs/screenshots/forms_list_{timestamp}.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[스크린샷] {screenshot_path}")
        
        posts_data = []
        
        # 게시물 목록 찾기
        print("\n[게시물 목록 찾기]")
        
        # 게시물 목록 테이블 찾기 - 클래스명으로 정확히 찾기
        selectors = [
            'table tbody tr',
            'div.board-list tbody tr',
            'div.list tbody tr',
            'div.board tbody tr',
            '.board-wrap tbody tr',
            '#content tbody tr'
        ]
        
        rows = []
        for selector in selectors:
            rows = await page.query_selector_all(selector)
            if rows:
                print(f"  셀렉터 '{selector}'로 게시물 발견")
                break
        
        # 백업 방법: 모든 tr 찾기
        if not rows:
            all_trs = await page.query_selector_all('tr')
            # 번호가 있는 행만 필터링 (첫 번째 td가 숫자인 경우)
            valid_rows = []
            for tr in all_trs:
                first_td = await tr.query_selector('td:first-child')
                if first_td:
                    text = await first_td.text_content()
                    if text and text.strip().isdigit():
                        valid_rows.append(tr)
            rows = valid_rows
        
        print(f"  게시물 행: {len(rows)}개 발견")
        
        # 최대 max_posts개만 처리
        for idx in range(min(max_posts, len(rows))):
            row = rows[idx]
            
            try:
                cells = await row.query_selector_all('td')
                if not cells:
                    continue
                
                post_info = {
                    '순번': idx + 1,
                    '번호': '',
                    '제목': '',
                    '작성자': '',
                    '작성일': '',
                    '조회수': '',
                    '첨부파일': '확인중',
                    '다운로드_경로': '',
                    '게시물_URL': ''
                }
                
                # 각 셀에서 정보 추출
                if len(cells) > 0:
                    post_info['번호'] = (await cells[0].text_content()).strip()
                
                # 제목 (보통 두 번째 셀)
                if len(cells) > 1:
                    title_cell = cells[1]
                    title_link = await title_cell.query_selector('a')
                    
                    if title_link:
                        post_info['제목'] = (await title_link.text_content()).strip()
                        
                        # 클릭 가능한 링크 정보 저장
                        onclick = await title_link.get_attribute('onclick')
                        href = await title_link.get_attribute('href')
                        
                        if onclick:
                            post_info['게시물_URL'] = onclick
                        elif href:
                            post_info['게시물_URL'] = href
                    
                    # 첨부파일 아이콘 확인
                    file_icon = await title_cell.query_selector('img[alt*="첨부"], img[src*="file"], img[src*="attach"], span.file, i.ico-file')
                    if file_icon:
                        post_info['첨부파일'] = '있음'
                
                # 작성자, 작성일, 조회수
                if len(cells) > 2:
                    post_info['작성자'] = (await cells[2].text_content()).strip()
                if len(cells) > 3:
                    post_info['작성일'] = (await cells[3].text_content()).strip()
                if len(cells) > 4:
                    post_info['조회수'] = (await cells[4].text_content()).strip()
                
                posts_data.append(post_info)
                print(f"  [{idx + 1}] {post_info['제목'][:40]}... {'[첨부]' if post_info['첨부파일'] == '있음' else ''}")
                
            except Exception as e:
                print(f"  [ERROR] 게시물 {idx + 1} 정보 추출 실패: {str(e)[:50]}")
                continue
        
        # 각 게시물 상세 페이지에서 첨부파일 다운로드
        print("\n[상세 페이지 및 첨부파일 다운로드]")
        
        for post in posts_data:
            try:
                # 제목 링크 다시 찾기
                links = await page.query_selector_all('td a')
                target_link = None
                
                for link in links:
                    text = await link.text_content()
                    if text and post['제목'] in text:
                        target_link = link
                        break
                
                if target_link:
                    print(f"\n  [{post['순번']}] {post['제목'][:30]}... 상세 보기")
                    
                    # 상세 페이지로 이동
                    await target_link.click()
                    await page.wait_for_timeout(3000)
                    
                    # 상세 페이지 스크린샷
                    detail_screenshot = f'logs/screenshots/forms_detail_{post["순번"]}_{timestamp}.png'
                    await page.screenshot(path=detail_screenshot)
                    print(f"    [스크린샷] {detail_screenshot}")
                    
                    # 첨부파일 찾기 및 다운로드
                    await self.download_attachments(page, post)
                    
                    # 목록으로 돌아가기
                    back_selectors = [
                        'a:has-text("목록")',
                        'button:has-text("목록")',
                        'a.btn-list',
                        'button.btn-list'
                    ]
                    
                    back_clicked = False
                    for selector in back_selectors:
                        back_btn = await page.query_selector(selector)
                        if back_btn:
                            await back_btn.click()
                            await page.wait_for_timeout(2000)
                            back_clicked = True
                            break
                    
                    if not back_clicked:
                        await page.go_back()
                        await page.wait_for_timeout(2000)
                    
            except Exception as e:
                print(f"  [ERROR] 게시물 {post['순번']} 상세 처리 실패: {str(e)[:50]}")
                continue
        
        return posts_data
    
    async def download_attachments(self, page, post_info):
        """첨부파일 다운로드"""
        try:
            print(f"    [첨부파일 찾기]")
            
            # 첨부파일 링크 찾기 - 다양한 셀렉터 시도
            file_selectors = [
                'a[onclick*="fnFileDown"]',
                'a[onclick*="fileDown"]',
                'a[onclick*="download"]',
                'a[href*="download"]',
                'a[href*="file"]',
                '.file-list a',
                '.attach-list a',
                '.board-file a',
                'td:has-text("첨부파일") a',
                'td:has-text("첨부파일") ~ td a',
                'th:has-text("첨부파일") ~ td a'
            ]
            
            file_links = []
            for selector in file_selectors:
                links = await page.query_selector_all(selector)
                if links:
                    file_links = links
                    print(f"      셀렉터 '{selector[:30]}...'로 {len(links)}개 파일 발견")
                    break
            
            if not file_links:
                # 모든 링크 확인
                all_links = await page.query_selector_all('a')
                for link in all_links:
                    text = await link.text_content()
                    onclick = await link.get_attribute('onclick')
                    href = await link.get_attribute('href')
                    
                    # 파일 다운로드 관련 링크 찾기
                    if onclick and ('download' in onclick.lower() or 'file' in onclick.lower()):
                        file_links.append(link)
                    elif href and ('.hwp' in href or '.pdf' in href or '.doc' in href or '.xls' in href or 'download' in href):
                        file_links.append(link)
                
                if file_links:
                    print(f"      확장 검색으로 {len(file_links)}개 파일 링크 발견")
            
            if file_links:
                # 다운로드 폴더 생성
                download_folder = os.path.join(self.download_dir, f"post_{post_info['순번']}")
                os.makedirs(download_folder, exist_ok=True)
                
                post_info['첨부파일'] = f"{len(file_links)}개"
                self.download_stats['첨부파일_있음'] += 1
                
                # 파일 다운로드
                for idx, link in enumerate(file_links[:3], 1):  # 최대 3개
                    try:
                        file_text = await link.text_content()
                        file_name = file_text.strip() if file_text else f"file_{idx}"
                        
                        # 파일명 정리
                        file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
                        
                        print(f"      파일 {idx}: {file_name[:30]}... 다운로드 시도")
                        
                        # 다운로드 시도
                        async with page.expect_download(timeout=30000) as download_info:
                            onclick = await link.get_attribute('onclick')
                            if onclick:
                                # JavaScript 함수 실행
                                await page.evaluate(onclick)
                            else:
                                # 직접 클릭
                                await link.click()
                        
                        download = await download_info.value
                        
                        # 파일 저장
                        suggested = download.suggested_filename
                        file_path = os.path.join(download_folder, suggested)
                        await download.save_as(file_path)
                        
                        print(f"        ✓ 다운로드 성공: {suggested}")
                        self.download_stats['다운로드_성공'] += 1
                        post_info['다운로드_경로'] = download_folder
                        
                    except Exception as e:
                        print(f"        ✗ 다운로드 실패: {str(e)[:50]}")
                        self.download_stats['다운로드_실패'] += 1
            else:
                print(f"      첨부파일 없음")
                post_info['첨부파일'] = '없음'
                
        except Exception as e:
            print(f"    [ERROR] 첨부파일 처리 실패: {str(e)[:100]}")
    
    async def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 엑셀 파일로 저장
        excel_file = os.path.join(self.data_dir, f"forms_board_{timestamp}.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 게시물 데이터
            if self.all_posts:
                df = pd.DataFrame(self.all_posts)
                df.to_excel(writer, sheet_name='서식자료실', index=False)
            
            # 다운로드 통계
            stats_df = pd.DataFrame([self.download_stats])
            stats_df.to_excel(writer, sheet_name='다운로드_통계', index=False)
        
        print(f"\n[저장] 엑셀 파일: {excel_file}")
        
        # JSON 백업
        json_file = os.path.join(self.data_dir, f"forms_board_{timestamp}.json")
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
                    서식자료실 게시판 스크래핑
        ==============================================================
        
          대상: 서식자료실 게시판
          수집: 최근 3개 게시물
          기능: 첨부파일 자동 다운로드
          URL: https://longtermcare.or.kr (서식자료실)
        
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
                # 서식자료실 스크래핑
                posts = await self.scrape_forms_list(page, max_posts=3)
                self.all_posts = posts
                self.download_stats['총_게시물'] = len(posts)
                
                # 결과 저장
                excel_file = await self.save_results()
                
                # 통계 출력
                print(f"""
                ==============================================================
                                서식자료실 스크래핑 완료
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
    scraper = FormsBoardScraper()
    await scraper.run()

if __name__ == "__main__":
    print("\n서식자료실 게시판 스크래핑을 시작합니다...\n")
    asyncio.run(main())
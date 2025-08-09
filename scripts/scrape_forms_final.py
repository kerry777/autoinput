#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서식자료실 최종 스크래퍼 - 정확한 테이블 구조 기반
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json
import pandas as pd
import sys
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class FormsFinalScraper:
    """서식자료실 최종 스크래퍼"""
    
    def __init__(self):
        self.board_url = "https://longtermcare.or.kr/npbs/d/m/000/moveBoardView?menuId=npe0000000920&bKey=B0017"
        self.download_dir = "data/downloads/forms_final"
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
    
    async def scrape_forms(self, page, max_posts=3):
        """서식자료실 스크래핑"""
        print(f"\n{'='*60}")
        print(f"  서식자료실 게시판 스크래핑")
        print(f"{'='*60}")
        
        # 페이지 이동
        print(f"\n[이동] 서식자료실")
        await page.goto(self.board_url, wait_until='networkidle')
        
        # 페이지 완전 로딩 대기
        print("[대기] 게시판 로딩 중...")
        await page.wait_for_timeout(5000)
        
        # 게시판 테이블이 로드될 때까지 대기
        try:
            await page.wait_for_selector('table', timeout=10000)
            print("  ✓ 테이블 로드 완료")
        except:
            print("  ✗ 테이블 로드 실패")
        
        # 스크린샷
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f'logs/screenshots/forms_final_{timestamp}.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[스크린샷] {screenshot_path}")
        
        posts_data = []
        
        # 게시물 찾기 - JavaScript 실행으로 직접 데이터 추출
        print("\n[게시물 데이터 추출]")
        
        # JavaScript로 테이블 데이터 직접 추출
        table_data = await page.evaluate('''() => {
            const rows = [];
            
            // 모든 테이블 행 찾기
            const allRows = document.querySelectorAll('tr');
            
            for (let row of allRows) {
                const cells = row.querySelectorAll('td');
                
                // td가 5개 이상인 행만 (번호, 구분, 제목, 작성자, 등록일, 첨부, 조회)
                if (cells.length >= 5) {
                    const rowData = {
                        번호: cells[0]?.textContent?.trim() || '',
                        구분: cells[1]?.textContent?.trim() || '',
                        제목: cells[2]?.textContent?.trim() || '',
                        작성자: cells[3]?.textContent?.trim() || '',
                        등록일: cells[4]?.textContent?.trim() || '',
                        첨부: cells[5]?.textContent?.trim() || '',
                        조회: cells[6]?.textContent?.trim() || '',
                        제목링크: null
                    };
                    
                    // 제목 셀에서 링크 정보 추출
                    const titleLink = cells[2]?.querySelector('a');
                    if (titleLink) {
                        rowData.제목링크 = {
                            onclick: titleLink.getAttribute('onclick'),
                            href: titleLink.getAttribute('href'),
                            text: titleLink.textContent?.trim()
                        };
                    }
                    
                    // 첨부파일 아이콘 확인
                    const fileIcon = cells[5]?.querySelector('img');
                    if (fileIcon) {
                        rowData.첨부파일있음 = true;
                    }
                    
                    // 번호가 숫자인 경우만 추가
                    if (rowData.번호 && !isNaN(rowData.번호)) {
                        rows.push(rowData);
                    }
                }
            }
            
            return rows;
        }''')
        
        print(f"  추출된 게시물: {len(table_data)}개")
        
        # 최대 max_posts개만 처리
        for idx, row_data in enumerate(table_data[:max_posts], 1):
            post_info = {
                '순번': idx,
                '번호': row_data.get('번호', ''),
                '구분': row_data.get('구분', ''),
                '제목': row_data.get('제목', ''),
                '작성자': row_data.get('작성자', ''),
                '등록일': row_data.get('등록일', ''),
                '첨부파일': '있음' if row_data.get('첨부파일있음') else '확인필요',
                '조회수': row_data.get('조회', ''),
                '다운로드_경로': ''
            }
            
            posts_data.append(post_info)
            print(f"  [{idx}] {post_info['제목'][:40]}... {'[첨부]' if post_info['첨부파일'] == '있음' else ''}")
            
            # 상세 페이지로 이동하여 첨부파일 다운로드
            if row_data.get('제목링크'):
                await self.download_from_detail(page, post_info, row_data['제목링크'])
                
                # 목록으로 돌아가기
                await page.go_back()
                await page.wait_for_timeout(2000)
        
        return posts_data
    
    async def download_from_detail(self, page, post_info, link_info):
        """상세 페이지에서 첨부파일 다운로드"""
        try:
            print(f"\n    [상세] {post_info['제목'][:30]}...")
            
            # onclick이 있으면 JavaScript 실행
            if link_info.get('onclick'):
                await page.evaluate(link_info['onclick'])
            else:
                # 제목으로 링크 찾아서 클릭
                link = await page.query_selector(f'a:has-text("{post_info["제목"][:20]}")')
                if link:
                    await link.click()
            
            await page.wait_for_timeout(3000)
            
            # 상세 페이지 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            detail_screenshot = f'logs/screenshots/detail_{post_info["순번"]}_{timestamp}.png'
            await page.screenshot(path=detail_screenshot)
            print(f"      [스크린샷] {detail_screenshot}")
            
            # 첨부파일 찾기
            print(f"      [첨부파일 찾기]")
            
            # JavaScript로 첨부파일 링크 찾기
            file_links = await page.evaluate('''() => {
                const links = [];
                
                // 다양한 패턴으로 파일 링크 찾기
                const patterns = [
                    'a[onclick*="fnFileDown"]',
                    'a[onclick*="download"]',
                    'a[href*="download"]',
                    'a[href$=".hwp"]',
                    'a[href$=".pdf"]',
                    'a[href$=".doc"]',
                    'a[href$=".xls"]',
                    'a[href$=".zip"]'
                ];
                
                for (let pattern of patterns) {
                    const elements = document.querySelectorAll(pattern);
                    for (let el of elements) {
                        links.push({
                            text: el.textContent?.trim(),
                            onclick: el.getAttribute('onclick'),
                            href: el.getAttribute('href')
                        });
                    }
                }
                
                // 중복 제거
                const unique = [];
                const seen = new Set();
                for (let link of links) {
                    const key = link.text + link.onclick + link.href;
                    if (!seen.has(key)) {
                        seen.add(key);
                        unique.push(link);
                    }
                }
                
                return unique;
            }''')
            
            if file_links:
                print(f"      ✓ {len(file_links)}개 첨부파일 발견")
                
                # 다운로드 폴더 생성
                download_folder = os.path.join(self.download_dir, f"post_{post_info['순번']}_{post_info['번호']}")
                os.makedirs(download_folder, exist_ok=True)
                
                post_info['첨부파일'] = f"{len(file_links)}개"
                self.download_stats['첨부파일_있음'] += 1
                
                # 파일 다운로드
                for idx, file_info in enumerate(file_links[:3], 1):  # 최대 3개
                    try:
                        file_name = file_info['text'] or f"file_{idx}"
                        file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)[:100]
                        
                        print(f"        파일 {idx}: {file_name[:30]}...")
                        
                        # 다운로드 시도
                        async with page.expect_download(timeout=30000) as download_info:
                            if file_info['onclick']:
                                await page.evaluate(file_info['onclick'])
                            elif file_info['href']:
                                link_element = await page.query_selector(f'a[href="{file_info["href"]}"]')
                                if link_element:
                                    await link_element.click()
                        
                        download = await download_info.value
                        suggested = download.suggested_filename
                        file_path = os.path.join(download_folder, suggested)
                        await download.save_as(file_path)
                        
                        print(f"          ✓ 다운로드 성공: {suggested}")
                        self.download_stats['다운로드_성공'] += 1
                        post_info['다운로드_경로'] = download_folder
                        
                    except Exception as e:
                        print(f"          ✗ 다운로드 실패: {str(e)[:50]}")
                        self.download_stats['다운로드_실패'] += 1
            else:
                print(f"      첨부파일 없음")
                post_info['첨부파일'] = '없음'
                
        except Exception as e:
            print(f"      [ERROR] 상세 페이지 처리 실패: {str(e)[:100]}")
    
    async def save_results(self):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 엑셀 파일로 저장
        excel_file = os.path.join(self.data_dir, f"forms_final_{timestamp}.xlsx")
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            if self.all_posts:
                df = pd.DataFrame(self.all_posts)
                df.to_excel(writer, sheet_name='서식자료실', index=False)
            
            stats_df = pd.DataFrame([self.download_stats])
            stats_df.to_excel(writer, sheet_name='다운로드_통계', index=False)
        
        print(f"\n[저장] 엑셀 파일: {excel_file}")
        
        # JSON 백업
        json_file = os.path.join(self.data_dir, f"forms_final_{timestamp}.json")
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
                    서식자료실 첨부파일 다운로드
        ==============================================================
        
          대상: 서식자료실 게시판
          수집: 최근 3개 게시물
          기능: 첨부파일 자동 다운로드
        
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
                posts = await self.scrape_forms(page, max_posts=3)
                self.all_posts = posts
                self.download_stats['총_게시물'] = len(posts)
                
                # 결과 저장
                excel_file = await self.save_results()
                
                # 통계 출력
                print(f"""
                ==============================================================
                                    완료!
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
                print(f"\n[ERROR] {str(e)}")
                import traceback
                traceback.print_exc()
            
            finally:
                await browser.close()
                print("\n[COMPLETE] 작업 완료")

async def main():
    scraper = FormsFinalScraper()
    await scraper.run()

if __name__ == "__main__":
    print("\n서식자료실 최종 스크래퍼 실행\n")
    asyncio.run(main())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 게시판 스크래핑
https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinList.web?menuId=npe0000002542
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

class ObjectionBoardScraper:
    """이의신청 게시판 스크래퍼"""
    
    def __init__(self):
        self.base_url = "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinList.web?menuId=npe0000002542"
        self.all_posts = []
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    async def scrape_board(self, max_pages=3):
        """게시판 스크래핑 메인 함수"""
        
        print("""
        ==============================================================
                        이의신청 게시판 스크래핑
        ==============================================================
        """)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=300)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                accept_downloads=True
            )
            page = await context.new_page()
            
            # 페이지 접속
            print(f"[INFO] 이의신청 게시판 접속...")
            await page.goto(self.base_url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 페이지 구조 분석
            print(f"[INFO] 페이지 구조 분석 중...")
            
            # 스크린샷 저장 (iframe 전환 전)
            screenshot_dir = "logs/screenshots/objection"
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = f"{screenshot_dir}/list_{self.timestamp}.png"
            await page.screenshot(path=screenshot_path)
            print(f"  스크린샷 저장: {screenshot_path}")
            
            # iframe 확인
            iframes = await page.query_selector_all('iframe')
            current_context = page  # frame 또는 page를 저장
            
            if iframes:
                print(f"  iframe {len(iframes)}개 발견")
                frame = await iframes[0].content_frame()
                if frame:
                    current_context = frame
                    print(f"  iframe으로 전환")
                    await current_context.wait_for_timeout(2000)
            
            # 테이블 찾기 (current_context 사용)
            tables = await current_context.query_selector_all('table')
            print(f"  테이블 수: {len(tables)}개")
            
            # 게시물 목록 찾기
            posts = []
            
            # 다양한 셀렉터 시도
            selectors = [
                'tr.notice_off',
                'tbody tr',
                'table tbody tr',
                '.board-list tbody tr',
                'table.list tbody tr'
            ]
            
            for selector in selectors:
                posts = await current_context.query_selector_all(selector)
                if posts:
                    print(f"  셀렉터 '{selector}'로 {len(posts)}개 게시물 발견")
                    break
            
            # 테이블에서 직접 찾기
            if not posts and tables:
                for table in tables:
                    rows = await table.query_selector_all('tr')
                    if len(rows) > 1:  # 헤더 포함 2개 이상
                        posts = rows[1:]  # 헤더 제외
                        print(f"  테이블에서 {len(posts)}개 행 발견")
                        break
            
            if not posts:
                print(f"[WARNING] 게시물을 찾을 수 없습니다.")
                # 페이지 내용 확인
                page_text = await current_context.text_content('body')
                if page_text:
                    print(f"  페이지 텍스트 샘플: {page_text[:200]}")
            
            # 각 페이지 처리
            current_page = 1
            
            while current_page <= max_pages:
                print(f"\n[페이지 {current_page}]")
                
                # 현재 페이지 게시물 수집
                page_posts = await self.scrape_current_page(current_context, current_page)
                self.all_posts.extend(page_posts)
                
                # 다음 페이지 확인
                if current_page < max_pages:
                    next_button = await self.find_next_button(current_context)
                    if next_button:
                        print(f"  다음 페이지로 이동...")
                        await next_button.click()
                        # Frame에서는 wait_for_load_state 대신 timeout 사용
                        await current_context.wait_for_timeout(3000)
                        current_page += 1
                    else:
                        print(f"  다음 페이지가 없습니다.")
                        break
                else:
                    break
            
            # Excel 저장
            await self.save_to_excel()
            
            # JSON 백업
            await self.save_to_json()
            
            print(f"""
            ==============================================================
                                스크래핑 완료
            ==============================================================
            총 수집 게시물: {len(self.all_posts)}개
            Excel 파일: data/objection_board_{self.timestamp}.xlsx
            JSON 파일: data/objection_board_{self.timestamp}.json
            ==============================================================
            """)
            
            await page.wait_for_timeout(5000)
            await browser.close()
    
    async def scrape_current_page(self, context, page_num):
        """현재 페이지의 게시물 수집"""
        posts_data = []
        
        # 게시물 찾기
        posts = await context.query_selector_all('tbody tr')
        
        if not posts:
            # 테이블에서 직접 찾기
            tables = await context.query_selector_all('table')
            for table in tables:
                rows = await table.query_selector_all('tr')
                if len(rows) > 1:
                    posts = rows[1:]
                    break
        
        print(f"  {len(posts)}개 게시물 발견")
        
        for idx, post in enumerate(posts[:10], 1):  # 페이지당 최대 10개
            try:
                cells = await post.query_selector_all('td')
                
                if len(cells) >= 4:  # 최소 4개 셀 필요
                    post_data = {
                        '페이지': page_num,
                        '순번': (page_num - 1) * 10 + idx,
                        '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 번호
                    if len(cells) > 0:
                        num_text = await cells[0].text_content()
                        post_data['번호'] = num_text.strip() if num_text else ''
                    
                    # 제목
                    if len(cells) > 1:
                        title_cell = cells[1]
                        title_link = await title_cell.query_selector('a')
                        
                        if title_link:
                            title_text = await title_link.text_content()
                            post_data['제목'] = title_text.strip() if title_text else ''
                            
                            # 링크 href 추출
                            href = await title_link.get_attribute('href')
                            if href:
                                post_data['링크'] = href
                        else:
                            title_text = await title_cell.text_content()
                            post_data['제목'] = title_text.strip() if title_text else ''
                    
                    # 작성자
                    if len(cells) > 2:
                        author_text = await cells[2].text_content()
                        post_data['작성자'] = author_text.strip() if author_text else ''
                    
                    # 작성일
                    if len(cells) > 3:
                        date_text = await cells[3].text_content()
                        post_data['작성일'] = date_text.strip() if date_text else ''
                    
                    # 조회수
                    if len(cells) > 4:
                        view_text = await cells[4].text_content()
                        post_data['조회수'] = view_text.strip() if view_text else ''
                    
                    # 상태
                    if len(cells) > 5:
                        status_text = await cells[5].text_content()
                        post_data['처리상태'] = status_text.strip() if status_text else ''
                    
                    posts_data.append(post_data)
                    print(f"    [{idx}] {post_data.get('제목', 'N/A')[:40]}...")
                    
            except Exception as e:
                print(f"    [ERROR] 게시물 {idx} 처리 실패: {str(e)[:50]}")
        
        return posts_data
    
    async def find_next_button(self, context):
        """다음 페이지 버튼 찾기"""
        # 다양한 다음 버튼 셀렉터
        next_selectors = [
            'a:has-text("다음")',
            'a.next',
            'a[title*="다음"]',
            '.paging a.next',
            '.pagination .next',
            'a[onclick*="next"]'
        ]
        
        for selector in next_selectors:
            next_btn = await context.query_selector(selector)
            if next_btn:
                # 버튼이 활성화되어 있는지 확인
                disabled = await next_btn.get_attribute('disabled')
                class_name = await next_btn.get_attribute('class')
                
                if not disabled and (not class_name or 'disabled' not in class_name):
                    return next_btn
        
        # 페이지 번호로 찾기 (현재 페이지 + 1)
        page_links = await context.query_selector_all('.paging a, .pagination a')
        for link in page_links:
            text = await link.text_content()
            if text and text.strip().isdigit():
                # 현재 페이지보다 큰 번호 찾기
                # 간단히 다음 번호 클릭
                return link
        
        return None
    
    async def save_to_excel(self):
        """Excel 파일로 저장"""
        if not self.all_posts:
            return
        
        df = pd.DataFrame(self.all_posts)
        
        # 컬럼 순서 정리
        columns_order = ['페이지', '순번', '수집일시', '번호', '제목', '작성자', 
                        '작성일', '조회수', '처리상태', '링크']
        
        # 존재하는 컬럼만 선택
        columns_order = [col for col in columns_order if col in df.columns]
        df = df[columns_order]
        
        # Excel 저장
        excel_file = f"data/objection_board_{self.timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # 전체 데이터
            df.to_excel(writer, sheet_name='전체_데이터', index=False)
            
            # 페이지별 시트
            for page_num in df['페이지'].unique():
                page_df = df[df['페이지'] == page_num]
                sheet_name = f'페이지_{page_num}'
                page_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"\n✅ Excel 파일 저장: {excel_file}")
    
    async def save_to_json(self):
        """JSON 파일로 저장"""
        if not self.all_posts:
            return
        
        json_file = f"data/objection_board_{self.timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_posts, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 파일 저장: {json_file}")

async def main():
    """메인 실행 함수"""
    scraper = ObjectionBoardScraper()
    await scraper.scrape_board(max_pages=3)  # 3페이지까지 수집

if __name__ == "__main__":
    print("\n이의신청 게시판 스크래핑 시작\n")
    asyncio.run(main())
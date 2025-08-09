#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 상세 페이지 직접 접근 및 스크래핑
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

async def scrape_objection_direct():
    """이의신청 상세 페이지 직접 접근"""
    
    # 사용자 제공 URL
    detail_url = "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId=EG000858892"
    list_url = "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinList.web?menuId=npe0000002542"
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("""
    ==============================================================
                    이의신청 게시판 직접 접근 스크래핑
    ==============================================================
    """)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # 1. 목록 페이지 먼저 접근
        print(f"[INFO] 목록 페이지 접근...")
        await page.goto(list_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        # 스크린샷
        screenshot_dir = "logs/screenshots/objection"
        os.makedirs(screenshot_dir, exist_ok=True)
        await page.screenshot(path=f"{screenshot_dir}/list_page_{timestamp}.png")
        
        # 페이지 소스 확인
        page_content = await page.content()
        
        # iframe 내부 확인
        iframes = await page.query_selector_all('iframe')
        if iframes:
            frame = await iframes[0].content_frame()
            if frame:
                print(f"[INFO] iframe 발견, 내부 확인...")
                frame_content = await frame.content()
                
                # Frame HTML이 실제로 로드되었는지 확인
                if len(frame_content) > 100:  # 의미있는 내용이 있다면
                    print(f"  iframe 내용 길이: {len(frame_content)}")
                    
                    # iframe 내부 테이블 확인
                    tables = await frame.query_selector_all('table')
                    print(f"  iframe 테이블 수: {len(tables)}")
                    
                    if tables:
                        # 테이블 내용 분석
                        for i, table in enumerate(tables):
                            rows = await table.query_selector_all('tr')
                            print(f"    테이블 {i+1}: {len(rows)}개 행")
                            
                            if len(rows) > 1:  # 헤더 + 데이터가 있다면
                                print(f"[INFO] 게시물 목록 발견!")
                                
                                posts_data = []
                                
                                # 각 행 처리 (첫 번째 행은 헤더로 간주)
                                for idx, row in enumerate(rows[1:6], 1):  # 최대 5개만
                                    try:
                                        cells = await row.query_selector_all('td')
                                        
                                        if len(cells) >= 3:
                                            post_data = {
                                                '순번': idx,
                                                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            }
                                            
                                            # 각 셀 내용 수집
                                            for cell_idx, cell in enumerate(cells):
                                                cell_text = await cell.text_content()
                                                post_data[f'컬럼{cell_idx+1}'] = cell_text.strip() if cell_text else ''
                                                
                                                # 링크 확인
                                                link = await cell.query_selector('a')
                                                if link:
                                                    href = await link.get_attribute('href')
                                                    if href:
                                                        post_data[f'링크{cell_idx+1}'] = href
                                            
                                            posts_data.append(post_data)
                                            print(f"    [{idx}] 게시물 수집 완료")
                                    
                                    except Exception as e:
                                        print(f"    [ERROR] 행 {idx} 처리 실패: {str(e)[:50]}")
                                
                                # 결과 저장
                                if posts_data:
                                    df = pd.DataFrame(posts_data)
                                    excel_file = f"data/objection_posts_{timestamp}.xlsx"
                                    df.to_excel(excel_file, index=False, sheet_name='이의신청_게시물')
                                    
                                    json_file = f"data/objection_posts_{timestamp}.json"
                                    with open(json_file, 'w', encoding='utf-8') as f:
                                        json.dump(posts_data, f, ensure_ascii=False, indent=2)
                                    
                                    print(f"""
                                    ========================================
                                    이의신청 게시물 수집 완료
                                    ========================================
                                    수집 게시물: {len(posts_data)}개
                                    Excel: {excel_file}
                                    JSON: {json_file}
                                    ========================================
                                    """)
                                    
                                    # 수집된 데이터 샘플 출력
                                    print(f"\n[데이터 샘플]")
                                    for key, value in posts_data[0].items():
                                        print(f"  {key}: {str(value)[:50]}")
                                
                                break
                else:
                    print(f"  iframe 내용이 비어있음")
        
        # 2. 상세 페이지 접근
        print(f"\n[INFO] 상세 페이지 접근...")
        await page.goto(detail_url, wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path=f"{screenshot_dir}/detail_page_{timestamp}.png")
        
        # 상세 페이지 내용 확인
        detail_content = await page.content()
        print(f"  상세 페이지 길이: {len(detail_content)}")
        
        # iframe이 있다면 확인
        detail_iframes = await page.query_selector_all('iframe')
        if detail_iframes:
            detail_frame = await detail_iframes[0].content_frame()
            if detail_frame:
                detail_frame_content = await detail_frame.content()
                print(f"  상세 iframe 길이: {len(detail_frame_content)}")
                
                # 상세 내용 추출
                detail_data = await extract_detail_content(detail_frame)
                
                if detail_data:
                    # 상세 데이터 저장
                    detail_df = pd.DataFrame([detail_data])
                    detail_excel = f"data/objection_detail_{timestamp}.xlsx"
                    detail_df.to_excel(detail_excel, index=False, sheet_name='상세내용')
                    
                    print(f"""
                    ========================================
                    상세 내용 수집 완료
                    ========================================
                    Excel: {detail_excel}
                    ========================================
                    """)
        
        print(f"\n[INFO] 10초 대기...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

async def extract_detail_content(frame):
    """상세 페이지 내용 추출"""
    try:
        detail_data = {
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 제목 찾기
        title_selectors = ['h1', 'h2', 'h3', '.title', '.subject', 'td.title']
        for selector in title_selectors:
            title_elem = await frame.query_selector(selector)
            if title_elem:
                title_text = await title_elem.text_content()
                if title_text and title_text.strip():
                    detail_data['제목'] = title_text.strip()
                    break
        
        # 내용 찾기
        content_selectors = ['.content', '.view', 'td.content', '.board-content']
        for selector in content_selectors:
            content_elem = await frame.query_selector(selector)
            if content_elem:
                content_text = await content_elem.text_content()
                if content_text and content_text.strip():
                    detail_data['내용'] = content_text.strip()[:500]  # 처음 500자만
                    break
        
        # 테이블 형태 데이터 추출
        tables = await frame.query_selector_all('table')
        for table in tables:
            rows = await table.query_selector_all('tr')
            for row in rows:
                cells = await row.query_selector_all('td, th')
                if len(cells) == 2:  # 레이블:값 형태
                    label_elem, value_elem = cells
                    label = await label_elem.text_content()
                    value = await value_elem.text_content()
                    
                    if label and value:
                        label = label.strip().replace(':', '').replace(' ', '_')
                        detail_data[label] = value.strip()
        
        return detail_data if len(detail_data) > 1 else None
        
    except Exception as e:
        print(f"  상세 내용 추출 실패: {str(e)[:50]}")
        return None

if __name__ == "__main__":
    print("이의신청 직접 접근 스크래핑 시작")
    asyncio.run(scrape_objection_direct())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 게시판 - API 기반 데이터 수집
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

async def scrape_objection_api():
    """네트워크 요청을 통한 이의신청 데이터 수집"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("""
    ==============================================================
                이의신청 게시판 - API 기반 수집
    ==============================================================
    """)
    
    # 테스트용 상세 URL들
    detail_urls = [
        "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId=EG000858892",
        "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId=EG000858889",
        "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId=EG000858888",
        "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId=EG000858887",
        "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId=EG000858886"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        collected_data = []
        
        # 각 상세 페이지 직접 접근
        for idx, url in enumerate(detail_urls, 1):
            print(f"\n[{idx}/{len(detail_urls)}] 상세 페이지 접근")
            print(f"URL: {url}")
            
            try:
                # 상세 페이지 접근
                await page.goto(url, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                # 페이지 내용 분석
                content = await page.content()
                
                # 기본 정보 수집
                post_data = {
                    '순번': idx,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'URL': url,
                    'artiId': extract_article_id(url)
                }
                
                # 페이지에서 텍스트 추출
                text_content = await page.text_content('body')
                if text_content:
                    post_data['페이지_텍스트_길이'] = len(text_content)
                    post_data['텍스트_샘플'] = text_content[:200].strip()
                
                # iframe 확인
                iframes = await page.query_selector_all('iframe')
                if iframes:
                    frame = await iframes[0].content_frame()
                    if frame:
                        frame_content = await frame.content()
                        frame_text = await frame.text_content('body')
                        
                        post_data['iframe_있음'] = True
                        post_data['iframe_내용_길이'] = len(frame_content) if frame_content else 0
                        post_data['iframe_텍스트_길이'] = len(frame_text) if frame_text else 0
                        
                        if frame_text and len(frame_text) > 50:
                            post_data['iframe_텍스트_샘플'] = frame_text[:200].strip()
                            
                            # iframe 내부에서 상세 정보 추출
                            detail_info = await extract_from_iframe(frame)
                            post_data.update(detail_info)
                else:
                    post_data['iframe_있음'] = False
                
                # 네트워크 요청 모니터링
                # (이미 페이지가 로드된 상태이므로 추가적인 요청은 적을 수 있음)
                
                collected_data.append(post_data)
                print(f"  ✅ 데이터 수집 완료")
                
                # 데이터 샘플 출력
                if 'iframe_텍스트_샘플' in post_data:
                    print(f"  텍스트: {post_data['iframe_텍스트_샘플'][:50]}...")
                
            except Exception as e:
                print(f"  ❌ 오류 발생: {str(e)[:100]}")
                post_data = {
                    '순번': idx,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'URL': url,
                    'artiId': extract_article_id(url),
                    '오류': str(e)[:200]
                }
                collected_data.append(post_data)
        
        # 결과 저장
        if collected_data:
            # Excel 저장
            df = pd.DataFrame(collected_data)
            excel_file = f"data/objection_api_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name='이의신청_API수집')
            
            # JSON 저장
            json_file = f"data/objection_api_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, ensure_ascii=False, indent=2)
            
            print(f"""
            ==============================================================
                            API 기반 수집 완료
            ==============================================================
            수집 데이터: {len(collected_data)}개
            Excel: {excel_file}
            JSON: {json_file}
            ==============================================================
            """)
            
            # 수집 결과 요약
            success_count = len([d for d in collected_data if '오류' not in d])
            error_count = len(collected_data) - success_count
            
            print(f"""
            [수집 결과 요약]
            성공: {success_count}개
            실패: {error_count}개
            iframe 있음: {len([d for d in collected_data if d.get('iframe_있음')])}개
            iframe 내용 있음: {len([d for d in collected_data if d.get('iframe_텍스트_길이', 0) > 50])}개
            """)
        
        await page.wait_for_timeout(5000)
        await browser.close()

def extract_article_id(url):
    """URL에서 article ID 추출"""
    match = re.search(r'artiId=([^&]+)', url)
    return match.group(1) if match else ''

async def extract_from_iframe(frame):
    """iframe에서 상세 정보 추출"""
    detail_info = {}
    
    try:
        # 제목 찾기
        title_selectors = [
            'h1', 'h2', 'h3', '.title', '.subject', 
            'td.title', 'th:contains("제목")', 'td:contains("제목")'
        ]
        
        for selector in title_selectors:
            elements = await frame.query_selector_all(selector)
            for elem in elements:
                text = await elem.text_content()
                if text and text.strip() and len(text.strip()) > 3:
                    detail_info['제목'] = text.strip()
                    break
            if '제목' in detail_info:
                break
        
        # 내용 찾기
        content_selectors = [
            '.content', '.view', '.board-content', 'textarea',
            'td.content', 'div.content'
        ]
        
        for selector in content_selectors:
            elements = await frame.query_selector_all(selector)
            for elem in elements:
                text = await elem.text_content()
                if text and text.strip() and len(text.strip()) > 10:
                    detail_info['내용'] = text.strip()[:300]  # 처음 300자
                    break
            if '내용' in detail_info:
                break
        
        # 테이블 데이터 추출
        tables = await frame.query_selector_all('table')
        for table_idx, table in enumerate(tables):
            rows = await table.query_selector_all('tr')
            for row in rows:
                cells = await row.query_selector_all('td, th')
                
                if len(cells) >= 2:
                    for i in range(0, len(cells) - 1, 2):
                        label_elem = cells[i]
                        value_elem = cells[i + 1]
                        
                        label = await label_elem.text_content()
                        value = await value_elem.text_content()
                        
                        if label and value and label.strip() and value.strip():
                            label_clean = label.strip().replace(':', '').replace(' ', '_')
                            if len(label_clean) > 0 and len(value.strip()) > 0:
                                detail_info[f'표{table_idx+1}_{label_clean}'] = value.strip()
        
        # 링크 정보 추출
        links = await frame.query_selector_all('a[href]')
        link_count = len(links)
        if link_count > 0:
            detail_info['링크수'] = link_count
            
            # 첫 번째 링크 정보
            if links:
                first_link = links[0]
                href = await first_link.get_attribute('href')
                text = await first_link.text_content()
                if href:
                    detail_info['첫번째_링크'] = href
                if text and text.strip():
                    detail_info['첫번째_링크_텍스트'] = text.strip()
        
    except Exception as e:
        detail_info['추출_오류'] = str(e)[:100]
    
    return detail_info

if __name__ == "__main__":
    print("이의신청 API 기반 수집 시작")
    asyncio.run(scrape_objection_api())
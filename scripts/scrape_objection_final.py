#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 게시판 최종 스크래핑 - 다양한 방식 시도
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

async def scrape_objection_final():
    """모든 방법을 시도하여 이의신청 데이터 수집"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("""
    ==============================================================
                이의신청 게시판 최종 스크래핑
    ==============================================================
    """)
    
    # 목록 페이지와 알려진 상세 페이지들
    list_url = "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinList.web?menuId=npe0000002542"
    
    # 더 많은 ID로 시도
    article_ids = [
        "EG000858892", "EG000858889", "EG000858888", "EG000858887", "EG000858886",
        "EG000858885", "EG000858884", "EG000858883", "EG000858882", "EG000858881"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 더 많은 대기 및 사용자 에이전트 설정
        await context.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        page = await context.new_page()
        collected_data = []
        
        # 방법 1: 목록 페이지에서 실제 목록 찾기
        print(f"\n[방법 1] 목록 페이지 분석")
        await page.goto(list_url, wait_until='networkidle')
        await page.wait_for_timeout(5000)  # 더 긴 대기
        
        # 자바스크립트 실행 대기
        await page.evaluate('() => window.scrollTo(0, 100)')
        await page.wait_for_timeout(2000)
        
        # 스크린샷
        screenshot_dir = "logs/screenshots/objection"
        os.makedirs(screenshot_dir, exist_ok=True)
        await page.screenshot(path=f"{screenshot_dir}/final_list_{timestamp}.png")
        
        # 메인 페이지에서 직접 찾기
        await try_main_page_extraction(page, collected_data)
        
        # iframe 다시 시도
        await try_iframe_extraction(page, collected_data)
        
        # 방법 2: 네트워크 요청 모니터링
        print(f"\n[방법 2] 네트워크 요청 모니터링")
        network_data = []
        
        def handle_response(response):
            if 'selectIndi' in response.url or 'Opinion' in response.url:
                network_data.append({
                    'url': response.url,
                    'status': response.status,
                    'headers': dict(response.headers)
                })
        
        page.on('response', handle_response)
        
        # 페이지 새로고침
        await page.reload(wait_until='networkidle')
        await page.wait_for_timeout(3000)
        
        print(f"  네트워크 요청 {len(network_data)}개 발견")
        
        # 방법 3: 직접 상세 페이지들 방문
        print(f"\n[방법 3] 상세 페이지 직접 방문")
        
        for idx, article_id in enumerate(article_ids, 1):
            detail_url = f"https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId={article_id}"
            
            try:
                print(f"  [{idx}/{len(article_ids)}] {article_id}")
                
                # 새 탭에서 열기
                detail_page = await context.new_page()
                
                await detail_page.goto(detail_url, wait_until='networkidle')
                await detail_page.wait_for_timeout(3000)
                
                # 상세 정보 수집
                post_data = await extract_detail_data(detail_page, article_id, idx)
                if post_data:
                    collected_data.append(post_data)
                    print(f"    ✅ 수집 완료")
                else:
                    print(f"    ❌ 내용 없음")
                
                await detail_page.close()
                
            except Exception as e:
                print(f"    ❌ 오류: {str(e)[:50]}")
        
        # 방법 4: 페이지 소스에서 숨겨진 데이터 찾기
        print(f"\n[방법 4] 페이지 소스 분석")
        page_source = await page.content()
        
        # 자바스크립트 변수나 JSON 데이터 찾기
        js_data = extract_js_data(page_source)
        if js_data:
            print(f"  자바스크립트 데이터 {len(js_data)}개 발견")
            for i, data in enumerate(js_data):
                collected_data.append({
                    '순번': len(collected_data) + 1,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '출처': 'JavaScript',
                    'JS데이터': str(data)[:200]
                })
        
        # 결과 저장
        if collected_data:
            # Excel 저장
            df = pd.DataFrame(collected_data)
            excel_file = f"data/objection_final_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name='이의신청_최종수집')
            
            # JSON 저장
            json_file = f"data/objection_final_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, ensure_ascii=False, indent=2)
            
            print(f"""
            ==============================================================
                            최종 수집 완료
            ==============================================================
            총 수집 데이터: {len(collected_data)}개
            Excel: {excel_file}
            JSON: {json_file}
            네트워크 요청: {len(network_data)}개
            ==============================================================
            """)
            
            # 데이터 타입별 요약
            sources = {}
            for data in collected_data:
                source = data.get('출처', '알수없음')
                sources[source] = sources.get(source, 0) + 1
            
            print(f"\n[수집 소스별 요약]")
            for source, count in sources.items():
                print(f"  {source}: {count}개")
        
        else:
            print(f"\n❌ 수집된 데이터가 없습니다.")
            
            # 디버그 정보 저장
            debug_info = {
                'timestamp': timestamp,
                'network_requests': network_data,
                'page_title': await page.title(),
                'page_url': page.url,
                'iframe_count': len(await page.query_selector_all('iframe'))
            }
            
            debug_file = f"logs/objection_debug_{timestamp}.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_info, f, ensure_ascii=False, indent=2)
            
            print(f"디버그 정보 저장: {debug_file}")
        
        await page.wait_for_timeout(3000)
        await browser.close()

async def try_main_page_extraction(page, collected_data):
    """메인 페이지에서 직접 데이터 추출 시도"""
    try:
        # 테이블 찾기
        tables = await page.query_selector_all('table')
        print(f"  메인 페이지 테이블 수: {len(tables)}")
        
        for table_idx, table in enumerate(tables):
            rows = await table.query_selector_all('tr')
            if len(rows) > 1:
                print(f"    테이블 {table_idx + 1}: {len(rows)}개 행")
                
                for row_idx, row in enumerate(rows[1:], 1):  # 헤더 제외
                    cells = await row.query_selector_all('td')
                    if len(cells) >= 3:
                        cell_texts = []
                        for cell in cells:
                            text = await cell.text_content()
                            cell_texts.append(text.strip() if text else '')
                        
                        if any(cell_texts):  # 빈 행이 아니라면
                            collected_data.append({
                                '순번': len(collected_data) + 1,
                                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                '출처': f'메인페이지_테이블{table_idx + 1}',
                                '행번호': row_idx,
                                '셀데이터': ' | '.join(cell_texts)
                            })
                            
                            if row_idx <= 3:  # 처음 3개만 로그
                                print(f"      행 {row_idx}: {' | '.join(cell_texts)[:50]}")
        
    except Exception as e:
        print(f"    메인 페이지 추출 오류: {str(e)[:50]}")

async def try_iframe_extraction(page, collected_data):
    """iframe에서 데이터 추출 시도"""
    try:
        iframes = await page.query_selector_all('iframe')
        print(f"  iframe 수: {len(iframes)}")
        
        for iframe_idx, iframe in enumerate(iframes):
            frame = await iframe.content_frame()
            if frame:
                # 더 긴 대기
                await frame.wait_for_timeout(5000)
                
                # 스크롤 시도
                try:
                    await frame.evaluate('() => window.scrollTo(0, 100)')
                    await frame.wait_for_timeout(1000)
                except:
                    pass
                
                content = await frame.content()
                text = await frame.text_content('body')
                
                print(f"    iframe {iframe_idx + 1}: 내용 {len(content)}, 텍스트 {len(text)}")
                
                if text and len(text) > 100:
                    tables = await frame.query_selector_all('table')
                    print(f"      테이블 수: {len(tables)}")
                    
                    for table in tables:
                        rows = await table.query_selector_all('tr')
                        if len(rows) > 1:
                            for row_idx, row in enumerate(rows[1:3], 1):  # 처음 2개만
                                cells = await row.query_selector_all('td')
                                cell_texts = []
                                for cell in cells:
                                    cell_text = await cell.text_content()
                                    cell_texts.append(cell_text.strip() if cell_text else '')
                                
                                if any(cell_texts):
                                    collected_data.append({
                                        '순번': len(collected_data) + 1,
                                        '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        '출처': f'iframe{iframe_idx + 1}_테이블',
                                        '행번호': row_idx,
                                        '셀데이터': ' | '.join(cell_texts)
                                    })
                                    print(f"        행 {row_idx}: {' | '.join(cell_texts)[:50]}")
        
    except Exception as e:
        print(f"    iframe 추출 오류: {str(e)[:50]}")

async def extract_detail_data(page, article_id, idx):
    """상세 페이지에서 데이터 추출"""
    try:
        # 페이지 제목
        title = await page.title()
        
        # 텍스트 내용
        text_content = await page.text_content('body')
        
        if not text_content or len(text_content) < 100:
            return None
        
        post_data = {
            '순번': idx,
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '출처': '상세페이지',
            'artiId': article_id,
            '페이지제목': title,
            '텍스트길이': len(text_content),
            '텍스트샘플': text_content[:300].strip()
        }
        
        # iframe 확인
        iframes = await page.query_selector_all('iframe')
        if iframes:
            frame = await iframes[0].content_frame()
            if frame:
                frame_text = await frame.text_content('body')
                if frame_text and len(frame_text) > 50:
                    post_data['iframe텍스트길이'] = len(frame_text)
                    post_data['iframe텍스트샘플'] = frame_text[:200].strip()
        
        return post_data
        
    except Exception as e:
        return None

def extract_js_data(html_content):
    """HTML에서 JavaScript 데이터 추출"""
    js_data = []
    
    try:
        # JSON 패턴 찾기
        json_patterns = [
            r'var\s+\w+\s*=\s*(\{[^;]+\});',
            r'data\s*:\s*(\{[^}]+\})',
            r'list\s*:\s*(\[[^\]]+\])'
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, html_content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                try:
                    data_str = match.group(1)
                    if len(data_str) > 20:  # 의미있는 길이
                        js_data.append(data_str[:100])
                except:
                    continue
    
    except Exception as e:
        pass
    
    return js_data

if __name__ == "__main__":
    print("이의신청 최종 스크래핑 시작")
    asyncio.run(scrape_objection_final())
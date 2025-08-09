#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 게시판 - 빠른 본문 내용 추출
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
import sys
import json

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def scrape_objection_content_quick():
    """빠른 본문 내용 추출"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    collected_data = []
    
    print("""
    ==============================================================
            이의신청 게시판 - 빠른 본문 내용 추출
    ==============================================================
    """)
    
    # 알려진 게시물 ID들
    post_ids = ["EG000858892", "EG000858889", "EG000858888"]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        for idx, post_id in enumerate(post_ids, 1):
            print(f"\n[{idx}/{len(post_ids)}] {post_id} 본문 추출")
            
            page = await context.new_page()
            
            try:
                detail_url = f"https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId={post_id}"
                
                await page.goto(detail_url, wait_until='networkidle')
                await page.wait_for_timeout(5000)  # 5초 대기
                
                post_data = {
                    '순번': idx,
                    'artiId': post_id,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 메인 페이지에서 텍스트 추출
                main_text = await page.text_content('body')
                if main_text:
                    post_data['메인_텍스트_길이'] = len(main_text)
                    post_data['메인_텍스트_샘플'] = main_text[:300].strip()
                
                # iframe에서 추출 시도
                iframes = await page.query_selector_all('iframe')
                if iframes:
                    print(f"  iframe {len(iframes)}개 발견")
                    
                    for i, iframe in enumerate(iframes):
                        try:
                            frame = await iframe.content_frame()
                            if frame:
                                # 더 긴 대기
                                await frame.wait_for_timeout(3000)
                                
                                # 프레임 내용 확인
                                frame_text = await frame.text_content('body')
                                frame_html = await frame.content()
                                
                                post_data[f'iframe{i+1}_텍스트_길이'] = len(frame_text) if frame_text else 0
                                post_data[f'iframe{i+1}_HTML_길이'] = len(frame_html) if frame_html else 0
                                
                                if frame_text and len(frame_text) > 50:
                                    post_data[f'iframe{i+1}_내용'] = frame_text[:200].strip()
                                    print(f"    iframe {i+1} 내용: {len(frame_text)}글자")
                                    
                                    # HTML 저장 (디버깅용)
                                    html_dir = "logs/iframe_html"
                                    os.makedirs(html_dir, exist_ok=True)
                                    html_file = f"{html_dir}/{post_id}_iframe{i+1}_{timestamp}.html"
                                    with open(html_file, 'w', encoding='utf-8') as f:
                                        f.write(frame_html)
                                    post_data[f'iframe{i+1}_HTML파일'] = html_file
                                
                                # 특정 요소들 찾기
                                elements = await frame.query_selector_all('*')
                                post_data[f'iframe{i+1}_요소수'] = len(elements)
                                
                                # 테이블 찾기
                                tables = await frame.query_selector_all('table')
                                if tables:
                                    post_data[f'iframe{i+1}_테이블수'] = len(tables)
                                    
                                    # 첫 번째 테이블 내용
                                    first_table = tables[0]
                                    rows = await first_table.query_selector_all('tr')
                                    if rows:
                                        table_text = []
                                        for row in rows[:3]:  # 처음 3행만
                                            cells = await row.query_selector_all('td, th')
                                            row_text = []
                                            for cell in cells:
                                                cell_text = await cell.text_content()
                                                if cell_text:
                                                    row_text.append(cell_text.strip())
                                            if row_text:
                                                table_text.append(' | '.join(row_text))
                                        
                                        if table_text:
                                            post_data[f'iframe{i+1}_테이블내용'] = '\n'.join(table_text)
                                
                        except Exception as e:
                            print(f"    iframe {i+1} 처리 오류: {str(e)[:50]}")
                
                collected_data.append(post_data)
                print(f"  ✅ 데이터 수집 완료")
                
            except Exception as e:
                print(f"  ❌ 오류: {str(e)[:100]}")
                collected_data.append({
                    '순번': idx,
                    'artiId': post_id,
                    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '오류': str(e)[:200]
                })
            finally:
                await page.close()
        
        # 결과 저장
        if collected_data:
            df = pd.DataFrame(collected_data)
            excel_file = f"data/objection_content_quick_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name='본문추출')
            
            json_file = f"data/objection_content_quick_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(collected_data, f, ensure_ascii=False, indent=2)
            
            print(f"""
            ==============================================================
                            빠른 본문 추출 완료
            ==============================================================
            수집 데이터: {len(collected_data)}개
            Excel: {excel_file}
            JSON: {json_file}
            ==============================================================
            """)
            
            # 결과 분석
            content_found = 0
            for data in collected_data:
                for key in data.keys():
                    if 'iframe' in key and '내용' in key:
                        content_found += 1
                        break
            
            print(f"""
            [추출 결과 분석]
            총 처리: {len(collected_data)}개
            내용 발견: {content_found}개
            """)
        
        await browser.close()

if __name__ == "__main__":
    print("이의신청 빠른 본문 추출 시작")
    asyncio.run(scrape_objection_content_quick())
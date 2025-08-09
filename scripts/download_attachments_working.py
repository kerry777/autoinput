#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
서식자료실 첨부파일 다운로드 - 작동 버전
직접 URL 접근 방식
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import sys
import re

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def download_attachments():
    """첨부파일 다운로드"""
    
    print("""
    ==============================================================
              서식자료실 첨부파일 다운로드 (최종)
    ==============================================================
    
    방식: 직접 URL 접근으로 게시물 상세 페이지 이동
    
    ==============================================================
    """)
    
    download_dir = "data/downloads/attachments_working"
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs("logs/screenshots", exist_ok=True)
    
    # 테스트할 게시물 ID들 (서식자료실 최근 게시물)
    board_posts = [
        {'id': '60125', 'title': '동거가족인정서류'},
        {'id': '60124', 'title': '슬라이드보드사용법'},
        {'id': '60123', 'title': '월별 서류 작성법'}
    ]
    
    # 추가로 최신 게시물 ID도 테스트 (2025년 자료)
    board_posts.insert(0, {'id': '60093', 'title': '2025년 장기요양기관 운영 관련 서식 모음집'})
    
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
        
        download_count = 0
        
        try:
            for idx, post in enumerate(board_posts[:3], 1):  # 최대 3개 게시물
                print(f"\n[게시물 {idx}] ID: {post['id']} - {post['title']}")
                
                try:
                    # 1. 상세 페이지 직접 접근
                    detail_url = f"https://longtermcare.or.kr/npbs/cms/board/board/Board.jsp?searchType=ALL&searchWord=&list_start_date=&list_end_date=&pageSize=&branch_id=&branch_child_id=&pageNum=1&list_show_answer=N&communityKey=B0017&boardId={post['id']}&act=VIEW"
                    
                    print(f"  URL: {detail_url[:100]}...")
                    await page.goto(detail_url, wait_until='networkidle')
                    await page.wait_for_timeout(3000)
                    
                    # 스크린샷
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = f'logs/screenshots/post_{post["id"]}_{timestamp}.png'
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"  [스크린샷] {screenshot_path}")
                    
                    # 2. 제목 확인 (옵션)
                    try:
                        title_element = await page.query_selector('h3, h4, .board-title, .view-title, td.title')
                        if title_element:
                            actual_title = await title_element.text_content()
                            print(f"  제목: {actual_title[:50] if actual_title else 'Unknown'}")
                    except:
                        pass
                    
                    # 3. 첨부파일 찾기
                    print(f"  [첨부파일 검색]")
                    
                    # 다양한 첨부파일 셀렉터
                    file_selectors = [
                        # 일반적인 패턴
                        'a[onclick*="fnFileDown"]',
                        'a[onclick*="fn_file_down"]',
                        'a[onclick*="fileDown"]',
                        'a[onclick*="download"]',
                        
                        # href 기반
                        'a[href*="/download"]',
                        'a[href*="file"]',
                        
                        # 파일 확장자
                        'a[href$=".hwp"]',
                        'a[href$=".pdf"]',
                        'a[href$=".doc"]',
                        'a[href$=".docx"]',
                        'a[href$=".xls"]',
                        'a[href$=".xlsx"]',
                        'a[href$=".zip"]',
                        
                        # 클래스/ID 기반
                        '.file-list a',
                        '.attach-list a',
                        '.board-file a',
                        '#fileList a',
                        
                        # 테이블 구조
                        'td:has-text("첨부파일") ~ td a',
                        'th:has-text("첨부파일") ~ td a',
                        'td:has-text("첨부") a',
                        
                        # 아이콘 근처
                        'img[alt*="첨부"] ~ a',
                        'img[src*="file"] ~ a',
                        'img[src*="attach"] ~ a'
                    ]
                    
                    file_links = []
                    for selector in file_selectors:
                        links = await page.query_selector_all(selector)
                        if links:
                            print(f"    ✓ 셀렉터 '{selector[:40]}...'로 {len(links)}개 발견")
                            file_links.extend(links)
                            break
                    
                    # 중복 제거
                    if not file_links:
                        # 모든 링크에서 파일 관련 찾기
                        all_links = await page.query_selector_all('a')
                        for link in all_links:
                            try:
                                text = await link.text_content()
                                href = await link.get_attribute('href')
                                onclick = await link.get_attribute('onclick')
                                
                                # 파일 관련 링크 패턴
                                if text and any(ext in text.lower() for ext in ['.hwp', '.pdf', '.doc', '.xls', '.zip', '다운로드', 'download']):
                                    file_links.append(link)
                                elif onclick and any(word in onclick.lower() for word in ['download', 'file', '다운']):
                                    file_links.append(link)
                                elif href and any(ext in href.lower() for ext in ['.hwp', '.pdf', '.doc', '.xls', 'download']):
                                    file_links.append(link)
                            except:
                                pass
                        
                        if file_links:
                            print(f"    ✓ 확장 검색으로 {len(file_links)}개 파일 링크 발견")
                    
                    # 중복 제거 (텍스트 기준)
                    unique_links = []
                    seen_texts = set()
                    for link in file_links:
                        try:
                            text = await link.text_content()
                            if text and text.strip() and text not in seen_texts:
                                seen_texts.add(text)
                                unique_links.append(link)
                        except:
                            pass
                    
                    if unique_links:
                        print(f"    총 {len(unique_links)}개 고유 파일")
                        
                        # 4. 첨부파일 다운로드
                        post_folder = os.path.join(download_dir, f"post_{post['id']}")
                        os.makedirs(post_folder, exist_ok=True)
                        
                        for file_idx, file_link in enumerate(unique_links[:3], 1):  # 최대 3개
                            try:
                                file_text = await file_link.text_content()
                                print(f"    파일 {file_idx}: {file_text[:50] if file_text else 'Unknown'}")
                                
                                # onclick 속성 확인
                                onclick = await file_link.get_attribute('onclick')
                                href = await file_link.get_attribute('href')
                                
                                if onclick:
                                    print(f"      onclick: {onclick[:80]}")
                                if href:
                                    print(f"      href: {href[:80]}")
                                
                                # 다운로드 시도
                                try:
                                    async with page.expect_download(timeout=30000) as download_info:
                                        if onclick:
                                            # JavaScript 함수 실행
                                            await page.evaluate(onclick)
                                        else:
                                            # 직접 클릭
                                            await file_link.click()
                                    
                                    download = await download_info.value
                                    
                                    # 파일 저장
                                    suggested_name = download.suggested_filename
                                    # 파일명 정리
                                    safe_name = re.sub(r'[<>:"/\\|?*]', '_', suggested_name)
                                    file_path = os.path.join(post_folder, safe_name)
                                    
                                    await download.save_as(file_path)
                                    
                                    print(f"      ✅ 다운로드 성공: {safe_name}")
                                    print(f"      💾 저장: {file_path}")
                                    download_count += 1
                                    
                                except asyncio.TimeoutError:
                                    print(f"      ⏱️ 다운로드 타임아웃")
                                except Exception as e:
                                    print(f"      ❌ 다운로드 실패: {str(e)[:50]}")
                                
                            except Exception as e:
                                print(f"    [ERROR] 파일 {file_idx} 처리 실패: {str(e)[:50]}")
                    else:
                        print(f"    ❌ 첨부파일을 찾을 수 없음")
                        
                        # 디버깅: 페이지 내용 일부 출력
                        page_text = await page.text_content('body')
                        if '첨부' in page_text:
                            print(f"      (페이지에 '첨부' 텍스트는 있음)")
                        
                        # 모든 링크 수 확인
                        all_links = await page.query_selector_all('a')
                        print(f"      (전체 링크 수: {len(all_links)}개)")
                    
                except Exception as e:
                    print(f"  [ERROR] 게시물 처리 실패: {str(e)[:100]}")
            
            # 최종 결과
            print(f"""
            ==============================================================
                                    완료!
            ==============================================================
            
              🎉 총 {download_count}개 파일 다운로드 성공
              
              📁 저장 위치: {download_dir}/post_[ID]/
              📸 스크린샷: logs/screenshots/
            
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

if __name__ == "__main__":
    print("\n🚀 첨부파일 다운로드 시작\n")
    asyncio.run(download_attachments())
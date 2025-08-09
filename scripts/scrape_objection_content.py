#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 게시판 - 본문 내용 추출 고급 기법
네트워크 모니터링, 동적 로딩 대기, 다양한 접근 방식
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

class ObjectionContentScraper:
    """이의신청 본문 내용 추출기"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.network_requests = []
        self.collected_posts = []
        
    async def scrape_with_content(self):
        """본문 내용까지 포함한 완전한 스크래핑"""
        
        print("""
        ==============================================================
                이의신청 게시판 - 본문 내용 추출 
        ==============================================================
        """)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False, 
                slow_mo=300,
                args=['--disable-web-security', '--disable-features=VizDisplayCompositor']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # 네트워크 요청 모니터링
            page.on('request', self.handle_request)
            page.on('response', self.handle_response)
            
            # 1단계: 목록에서 게시물 ID 수집
            post_ids = await self.collect_post_ids(page)
            
            # 2단계: 각 게시물의 본문 내용 추출
            for idx, post_id in enumerate(post_ids[:5], 1):  # 처음 5개만
                print(f"\n[{idx}/{len(post_ids[:5])}] 게시물 {post_id} 본문 추출")
                
                content_data = await self.extract_post_content(context, post_id)
                if content_data:
                    self.collected_posts.append(content_data)
                    print(f"  ✅ 본문 추출 완료 ({len(content_data.get('본문', ''))} 글자)")
                else:
                    print(f"  ❌ 본문 추출 실패")
            
            # 결과 저장
            await self.save_results()
            
            print(f"\n[INFO] 5초 대기...")
            await page.wait_for_timeout(5000)
            await browser.close()
    
    async def collect_post_ids(self, page):
        """게시물 ID 수집"""
        list_url = "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinList.web?menuId=npe0000002542"
        
        print(f"[1단계] 게시물 ID 수집")
        await page.goto(list_url, wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        # iframe 확인
        iframes = await page.query_selector_all('iframe')
        current_context = page
        
        if iframes:
            frame = await iframes[0].content_frame()
            if frame:
                current_context = frame
                print(f"  iframe으로 전환")
                
                # iframe 로딩 대기
                await self.wait_for_content_load(current_context)
        
        # 게시물 링크에서 ID 추출
        post_ids = []
        
        # 방법 1: 링크에서 artiId 추출
        links = await current_context.query_selector_all('a[href*="artiId"]')
        for link in links:
            href = await link.get_attribute('href')
            if href:
                match = re.search(r'artiId=([^&]+)', href)
                if match:
                    post_ids.append(match.group(1))
        
        # 방법 2: 알려진 ID들 사용 (fallback)
        if not post_ids:
            print(f"  링크에서 ID를 찾을 수 없어 알려진 ID 사용")
            post_ids = [
                "EG000858892", "EG000858889", "EG000858888", 
                "EG000858887", "EG000858886"
            ]
        
        print(f"  수집된 게시물 ID: {len(post_ids)}개")
        return post_ids
    
    async def extract_post_content(self, context, post_id):
        """개별 게시물의 본문 내용 추출"""
        detail_url = f"https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinDtl.web?blbdId=&artiId={post_id}"
        
        # 새 페이지에서 상세 내용 추출
        detail_page = await context.new_page()
        
        try:
            await detail_page.goto(detail_url, wait_until='networkidle')
            await detail_page.wait_for_timeout(3000)
            
            # 기본 정보
            post_data = {
                'artiId': post_id,
                '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'URL': detail_url
            }
            
            # iframe에서 본문 추출
            iframes = await detail_page.query_selector_all('iframe')
            if iframes:
                frame = await iframes[0].content_frame()
                if frame:
                    # 더 긴 대기 및 다양한 로딩 시도
                    await self.wait_for_content_load(frame)
                    
                    # 스크롤하여 lazy loading 콘텐츠 로드
                    await self.trigger_content_loading(frame)
                    
                    # 본문 내용 추출
                    content_info = await self.extract_content_from_frame(frame)
                    post_data.update(content_info)
                    
                    # HTML 소스도 저장 (디버깅용)
                    frame_html = await frame.content()
                    post_data['HTML길이'] = len(frame_html)
                    
                    # HTML 파일로 저장
                    html_dir = f"logs/html_sources"
                    os.makedirs(html_dir, exist_ok=True)
                    html_file = f"{html_dir}/{post_id}_{self.timestamp}.html"
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(frame_html)
                    post_data['HTML파일'] = html_file
            
            # 메인 페이지에서도 시도
            main_content = await self.extract_content_from_page(detail_page)
            if main_content:
                for key, value in main_content.items():
                    if key not in post_data:
                        post_data[f'메인_{key}'] = value
            
            return post_data
            
        except Exception as e:
            print(f"    오류: {str(e)[:100]}")
            return None
        finally:
            await detail_page.close()
    
    async def wait_for_content_load(self, context):
        """콘텐츠 로딩 대기"""
        # 다양한 대기 방식 시도
        try:
            # 1. 기본 대기
            await context.wait_for_timeout(3000)
            
            # 2. 특정 요소 대기
            selectors_to_wait = [
                'table', '.content', '.view', 'form', 
                'textarea', 'div[id]', 'span[id]'
            ]
            
            for selector in selectors_to_wait:
                try:
                    await context.wait_for_selector(selector, timeout=2000)
                    print(f"    '{selector}' 요소 로드됨")
                    break
                except:
                    continue
                    
            # 3. 추가 대기
            await context.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"    콘텐츠 로딩 대기 중 오류: {str(e)[:50]}")
    
    async def trigger_content_loading(self, context):
        """동적 콘텐츠 로딩 트리거"""
        try:
            # 스크롤하여 lazy loading 트리거
            await context.evaluate('() => { window.scrollTo(0, 100); }')
            await context.wait_for_timeout(1000)
            
            await context.evaluate('() => { window.scrollTo(0, document.body.scrollHeight); }')
            await context.wait_for_timeout(1000)
            
            # 클릭 이벤트 트리거
            buttons = await context.query_selector_all('button, input[type="button"]')
            for button in buttons[:2]:  # 처음 2개 버튼만
                try:
                    button_text = await button.text_content()
                    if button_text and ('보기' in button_text or '상세' in button_text):
                        await button.click()
                        await context.wait_for_timeout(1000)
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"    동적 로딩 트리거 오류: {str(e)[:50]}")
    
    async def extract_content_from_frame(self, frame):
        """frame에서 상세 내용 추출"""
        content_info = {}
        
        try:
            # 전체 텍스트 추출
            full_text = await frame.text_content('body')
            if full_text:
                content_info['전체텍스트길이'] = len(full_text.strip())
                content_info['전체텍스트샘플'] = full_text.strip()[:200]
            
            # 제목 추출
            title_selectors = [
                'h1', 'h2', 'h3', '.title', '.subject', 
                'input[name*="title"]', 'input[name*="subject"]',
                'td:contains("제목")', 'th:contains("제목")'
            ]
            
            for selector in title_selectors:
                try:
                    element = await frame.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        value = await element.get_attribute('value')
                        
                        content = text or value
                        if content and content.strip() and len(content.strip()) > 3:
                            content_info['제목'] = content.strip()
                            print(f"    제목 발견: {content.strip()[:30]}...")
                            break
                except:
                    continue
            
            # 본문 내용 추출
            content_selectors = [
                'textarea[name*="content"]', 'textarea[name*="cont"]',
                '.content', '.view-content', '.board-content',
                'div[id*="content"]', 'div[id*="cont"]',
                'td.content', 'div.content'
            ]
            
            for selector in content_selectors:
                try:
                    elements = await frame.query_selector_all(selector)
                    for element in elements:
                        text = await element.text_content()
                        value = await element.get_attribute('value')
                        inner_html = await element.inner_html()
                        
                        content = text or value or inner_html
                        if content and content.strip() and len(content.strip()) > 20:
                            content_info['본문'] = content.strip()
                            print(f"    본문 발견: {len(content.strip())}글자")
                            break
                    
                    if '본문' in content_info:
                        break
                except:
                    continue
            
            # 테이블 데이터 추출
            tables = await frame.query_selector_all('table')
            table_data = []
            
            for table_idx, table in enumerate(tables):
                rows = await table.query_selector_all('tr')
                for row in rows:
                    cells = await row.query_selector_all('td, th')
                    if len(cells) >= 2:
                        cell_texts = []
                        for cell in cells:
                            cell_text = await cell.text_content()
                            if cell_text and cell_text.strip():
                                cell_texts.append(cell_text.strip())
                        
                        if cell_texts:
                            table_data.append(' | '.join(cell_texts))
            
            if table_data:
                content_info['테이블데이터'] = '\n'.join(table_data[:5])  # 처음 5행만
            
            # 폼 데이터 추출
            inputs = await frame.query_selector_all('input, textarea, select')
            form_data = {}
            
            for input_elem in inputs:
                name = await input_elem.get_attribute('name')
                value = await input_elem.get_attribute('value')
                text = await input_elem.text_content()
                
                if name and (value or text):
                    form_data[name] = value or text
            
            if form_data:
                content_info['폼데이터'] = str(form_data)[:300]
            
        except Exception as e:
            content_info['추출오류'] = str(e)[:100]
        
        return content_info
    
    async def extract_content_from_page(self, page):
        """메인 페이지에서 내용 추출"""
        try:
            page_text = await page.text_content('body')
            if page_text and len(page_text.strip()) > 100:
                return {
                    '페이지텍스트길이': len(page_text.strip()),
                    '페이지텍스트샘플': page_text.strip()[:200]
                }
        except:
            pass
        
        return {}
    
    def handle_request(self, request):
        """네트워크 요청 처리"""
        if any(keyword in request.url for keyword in ['Opinion', 'selectIndi', 'board']):
            self.network_requests.append({
                'type': 'request',
                'url': request.url,
                'method': request.method,
                'timestamp': datetime.now().isoformat()
            })
    
    def handle_response(self, response):
        """네트워크 응답 처리"""
        if any(keyword in response.url for keyword in ['Opinion', 'selectIndi', 'board']):
            self.network_requests.append({
                'type': 'response',
                'url': response.url,
                'status': response.status,
                'timestamp': datetime.now().isoformat()
            })
    
    async def save_results(self):
        """결과 저장"""
        if self.collected_posts:
            # Excel 저장
            df = pd.DataFrame(self.collected_posts)
            excel_file = f"data/objection_content_{self.timestamp}.xlsx"
            df.to_excel(excel_file, index=False, sheet_name='본문내용')
            
            # JSON 저장
            json_file = f"data/objection_content_{self.timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_posts, f, ensure_ascii=False, indent=2)
            
            # 네트워크 로그 저장
            network_file = f"logs/network_requests_{self.timestamp}.json"
            os.makedirs(os.path.dirname(network_file), exist_ok=True)
            with open(network_file, 'w', encoding='utf-8') as f:
                json.dump(self.network_requests, f, ensure_ascii=False, indent=2)
            
            print(f"""
            ==============================================================
                            본문 내용 추출 완료
            ==============================================================
            수집 게시물: {len(self.collected_posts)}개
            Excel: {excel_file}
            JSON: {json_file}
            네트워크 로그: {network_file}
            ==============================================================
            """)
            
            # 추출 성공률 분석
            success_count = len([p for p in self.collected_posts if '본문' in p])
            title_count = len([p for p in self.collected_posts if '제목' in p])
            
            print(f"""
            [추출 성공률]
            제목 추출: {title_count}/{len(self.collected_posts)}개
            본문 추출: {success_count}/{len(self.collected_posts)}개
            네트워크 요청: {len(self.network_requests)}개
            """)

async def main():
    """메인 실행 함수"""
    scraper = ObjectionContentScraper()
    await scraper.scrape_with_content()

if __name__ == "__main__":
    print("이의신청 본문 내용 추출 시작")
    asyncio.run(main())
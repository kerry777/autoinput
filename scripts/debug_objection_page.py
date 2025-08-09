#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
이의신청 게시판 페이지 구조 디버깅
"""

import asyncio
from playwright.async_api import async_playwright
import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def debug_objection_page():
    """이의신청 페이지 구조 분석"""
    
    url = "https://longtermcare.or.kr/npbs/e/g/570/selectIndiOpinList.web?menuId=npe0000002542"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print(f"[INFO] 페이지 접속: {url}")
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(5000)
        
        # 페이지 제목 확인
        title = await page.title()
        print(f"페이지 제목: {title}")
        
        # iframe 확인
        iframes = await page.query_selector_all('iframe')
        print(f"iframe 수: {len(iframes)}개")
        
        # 메인 페이지 HTML 구조
        print(f"\n[메인 페이지 구조]")
        body_text = await page.text_content('body')
        if body_text:
            print(f"페이지 텍스트 길이: {len(body_text)}")
            print(f"텍스트 샘플: {body_text[:300]}")
        
        # 모든 링크 확인
        links = await page.query_selector_all('a')
        print(f"링크 수: {len(links)}개")
        
        if iframes:
            frame = await iframes[0].content_frame()
            if frame:
                print(f"\n[iframe 내부 구조]")
                
                # iframe 내용 확인
                frame_text = await frame.text_content('body')
                if frame_text:
                    print(f"iframe 텍스트 길이: {len(frame_text)}")
                    print(f"iframe 텍스트 샘플: {frame_text[:500]}")
                
                # iframe 내부 HTML 구조
                frame_html = await frame.content()
                if frame_html:
                    print(f"iframe HTML 길이: {len(frame_html)}")
                
                # iframe 내부 요소들
                frame_tables = await frame.query_selector_all('table')
                print(f"iframe 테이블 수: {len(frame_tables)}개")
                
                frame_forms = await frame.query_selector_all('form')
                print(f"iframe 폼 수: {len(frame_forms)}개")
                
                frame_divs = await frame.query_selector_all('div')
                print(f"iframe div 수: {len(frame_divs)}개")
                
                # 주요 클래스들 확인
                common_selectors = [
                    '.list', '.board', '.table', '.content', 
                    '.container', '.wrapper', '.main'
                ]
                
                for selector in common_selectors:
                    elements = await frame.query_selector_all(selector)
                    if elements:
                        print(f"'{selector}' 요소: {len(elements)}개")
                
                # 스크린샷 저장
                screenshot_path = "logs/screenshots/objection/debug_frame.png"
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                # frame으로 직접 스크린샷은 안 되므로 페이지로
                await page.screenshot(path=screenshot_path)
                print(f"스크린샷 저장: {screenshot_path}")
                
                # HTML 저장
                html_path = "logs/objection_frame.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(frame_html)
                print(f"HTML 저장: {html_path}")
        
        print(f"\n[10초 대기 - 페이지 확인]")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    print("이의신청 페이지 구조 디버깅")
    asyncio.run(debug_objection_page())
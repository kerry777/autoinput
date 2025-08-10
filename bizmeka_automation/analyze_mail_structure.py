#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
메일 페이지 구조 분석 스크립트
저장된 스크린샷과 HTML을 분석
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from cookie_manager import CookieManager
from utils import load_config, print_banner, print_status


async def analyze_mail_page():
    """메일 페이지 상세 분석"""
    
    print_banner("MAIL PAGE ANALYZER")
    
    config = load_config()
    cookie_manager = CookieManager()
    
    # 쿠키 로드
    cookies = cookie_manager.load_cookies()
    if not cookies:
        print_status('error', '쿠키 없음')
        return
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 화면 보이게
        context = await browser.new_context(
            locale=config['browser']['locale'],
            timezone_id=config['browser']['timezone']
        )
        
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        # 메인 페이지 접속
        print_status('info', '메인 페이지 접속...')
        await page.goto(config['urls']['main'])
        await page.wait_for_timeout(3000)
        
        # 메일 버튼 클릭
        print_status('info', '메일 버튼을 클릭하세요')
        print("메일 버튼 클릭 후 Enter...")
        input()
        
        # 팝업 처리
        try:
            popup = await page.wait_for_selector('button:has-text("확인")', timeout=1000)
            if popup:
                await popup.click()
                print_status('info', '팝업 확인 클릭')
        except:
            pass
        
        # 새 탭 확인
        if len(context.pages) > 1:
            page = context.pages[-1]
            print_status('info', '새 탭으로 전환')
        
        await page.wait_for_timeout(2000)
        
        # 받은메일함 클릭
        print_status('info', '받은메일함을 클릭하세요')
        print("받은메일함 클릭 후 Enter...")
        input()
        
        await page.wait_for_timeout(3000)
        
        # 페이지 구조 분석
        print("\n" + "="*60)
        print("페이지 구조 분석")
        print("="*60)
        
        # 1. 프레임 분석
        frames = page.frames
        print(f"\n프레임 수: {len(frames)}")
        
        for i, frame in enumerate(frames):
            try:
                url = frame.url
                name = await frame.evaluate('() => window.name || "unnamed"')
                print(f"\n프레임 {i}:")
                print(f"  URL: {url}")
                print(f"  Name: {name}")
                
                # 각 프레임에서 테이블 찾기
                tables = await frame.query_selector_all('table')
                print(f"  테이블 수: {len(tables)}")
                
                # 테이블 분석
                for j, table in enumerate(tables[:3]):  # 처음 3개만
                    rows = await table.query_selector_all('tr')
                    print(f"    테이블 {j}: {len(rows)}개 행")
                    
                    if rows:
                        # 첫 번째 데이터 행 분석
                        for row_idx in range(min(3, len(rows))):
                            cells = await rows[row_idx].query_selector_all('td, th')
                            cell_texts = []
                            for cell in cells[:5]:  # 처음 5개 셀만
                                text = await cell.inner_text()
                                cell_texts.append(text.strip()[:20] if text else "")
                            
                            if cell_texts:
                                print(f"      행 {row_idx}: {cell_texts}")
                
                # 메일 관련 요소 찾기
                mail_elements = await frame.query_selector_all('[class*="mail"], [id*="mail"], [class*="list"]')
                if mail_elements:
                    print(f"  메일 관련 요소: {len(mail_elements)}개")
                    for elem in mail_elements[:3]:
                        class_name = await elem.evaluate('el => el.className')
                        id_name = await elem.evaluate('el => el.id')
                        tag = await elem.evaluate('el => el.tagName')
                        print(f"    [{tag}] class='{class_name}' id='{id_name}'")
                        
            except Exception as e:
                print(f"  프레임 {i} 분석 실패: {e}")
        
        # 2. 현재 페이지 HTML 저장
        print("\n전체 HTML 저장 중...")
        html = await page.content()
        with open('data/full_mail_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print_status('success', 'full_mail_page.html 저장')
        
        # 3. 각 프레임 HTML 저장
        for i, frame in enumerate(frames):
            try:
                frame_html = await frame.content()
                with open(f'data/frame_{i}.html', 'w', encoding='utf-8') as f:
                    f.write(frame_html)
                print_status('success', f'frame_{i}.html 저장')
            except:
                pass
        
        # 4. JavaScript로 직접 데이터 추출 시도
        print("\n" + "="*60)
        print("JavaScript 데이터 추출 시도")
        print("="*60)
        
        for frame in frames:
            try:
                # jQuery 사용 가능 여부 확인
                has_jquery = await frame.evaluate('() => typeof jQuery !== "undefined"')
                print(f"\njQuery 사용 가능: {has_jquery}")
                
                if has_jquery:
                    # jQuery로 메일 데이터 추출
                    mail_data = await frame.evaluate('''() => {
                        const mails = [];
                        // 여러 선택자 시도
                        const selectors = ['tr.mail-item', 'tr[class*="list"]', 'tbody tr', '.mail-list tr'];
                        
                        for (let selector of selectors) {
                            const rows = jQuery(selector);
                            if (rows.length > 0) {
                                rows.each(function(idx) {
                                    if (idx > 5) return false;  // 처음 5개만
                                    const cells = jQuery(this).find('td');
                                    const rowData = [];
                                    cells.each(function() {
                                        const text = jQuery(this).text().trim();
                                        if (text) rowData.push(text.substring(0, 30));
                                    });
                                    if (rowData.length > 0) {
                                        mails.push(rowData);
                                    }
                                });
                                break;
                            }
                        }
                        return mails;
                    }''')
                    
                    if mail_data:
                        print("jQuery로 추출한 데이터:")
                        for row in mail_data:
                            print(f"  {row}")
                
            except Exception as e:
                print(f"JavaScript 추출 실패: {e}")
        
        print("\n분석 완료. 브라우저를 닫으려면 Enter...")
        input()
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(analyze_mail_page())
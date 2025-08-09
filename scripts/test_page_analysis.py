#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
페이지 구조 상세 분석 - 정확한 검색 방법 찾기
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os

async def test_page_analysis():
    """페이지 구조 상세 분석"""
    
    print("\n" + "="*60)
    print("   페이지 구조 상세 분석")
    print("="*60)
    
    os.makedirs("logs/screenshots/test", exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        
        # 새 탭/창 감지
        new_windows = []
        context.on('page', lambda page: new_windows.append(page))
        
        page = await context.new_page()
        
        try:
            # 1. 페이지 이동
            print("\n[1] Loading page...")
            url = "https://longtermcare.or.kr/npbs/r/a/201/selectLtcoSrch.web?menuId=npe0000000650"
            await page.goto(url, wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 스크린샷
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            await page.screenshot(path=f"logs/screenshots/test/page_{timestamp}.png")
            
            # 2. 서울 선택
            print("\n[2] Selecting Seoul...")
            await page.select_option('select[name="siDoCd"]', value="11")
            await page.wait_for_timeout(1000)
            
            # 3. 모든 검색 관련 요소 찾기
            print("\n[3] Finding all search-related elements...")
            
            # a 태그 중 검색 관련
            search_links = await page.query_selector_all('a[id*="search"], a[class*="search"], a[title*="검색"]')
            print(f"Search links found: {len(search_links)}")
            
            for i, link in enumerate(search_links):
                link_id = await link.get_attribute('id')
                link_class = await link.get_attribute('class')
                link_title = await link.get_attribute('title')
                link_href = await link.get_attribute('href')
                link_onclick = await link.get_attribute('onclick')
                
                print(f"\n  Link {i+1}:")
                print(f"    id: {link_id}")
                print(f"    class: {link_class}")
                print(f"    title: {link_title}")
                print(f"    href: {link_href}")
                print(f"    onclick: {link_onclick[:50] if link_onclick else None}")
                
                # 이미지 자식 요소 확인
                img = await link.query_selector('img')
                if img:
                    img_alt = await img.get_attribute('alt')
                    img_src = await img.get_attribute('src')
                    print(f"    has img: alt='{img_alt}', src='{img_src}'")
            
            # 4. #btn_search_pop 상세 분석
            print("\n[4] Analyzing #btn_search_pop...")
            btn_search_pop = await page.query_selector('#btn_search_pop')
            
            if btn_search_pop:
                print("Found #btn_search_pop")
                
                # JavaScript 이벤트 리스너 확인
                listeners = await page.evaluate('''(element) => {
                    const listeners = [];
                    // jQuery 이벤트 확인
                    if (typeof $ !== 'undefined' && $(element).data('events')) {
                        const events = $(element).data('events');
                        for (const type in events) {
                            listeners.push(`jQuery ${type}: ${events[type].length} handlers`);
                        }
                    }
                    // onclick 속성
                    if (element.onclick) {
                        listeners.push(`onclick: ${element.onclick.toString().substring(0, 100)}`);
                    }
                    // href 속성
                    if (element.href) {
                        listeners.push(`href: ${element.href}`);
                    }
                    return listeners;
                }''', btn_search_pop)
                
                print("  Event listeners:")
                for listener in listeners:
                    print(f"    {listener}")
                
                # 5. 클릭 시도 - 다양한 방법
                print("\n[5] Testing different click methods...")
                
                # 방법 1: 일반 클릭
                print("\n  Method 1: Regular click")
                await btn_search_pop.click()
                await page.wait_for_timeout(3000)
                
                if len(context.pages) > 1:
                    print("  [SUCCESS] New window opened!")
                    new_page = context.pages[-1]
                    await new_page.screenshot(path=f"logs/screenshots/test/popup1_{timestamp}.png")
                    
                    # 다운로드 버튼 찾기
                    download_btn = await new_page.query_selector('#btn_map_excel')
                    if download_btn:
                        print("  Found download button!")
                else:
                    print("  No new window")
                    
                    # 방법 2: JavaScript 클릭
                    print("\n  Method 2: JavaScript click")
                    await page.evaluate('(element) => element.click()', btn_search_pop)
                    await page.wait_for_timeout(3000)
                    
                    if len(context.pages) > 1:
                        print("  [SUCCESS] New window opened!")
                    else:
                        print("  No new window")
                        
                        # 방법 3: 강제 새 창 열기
                        print("\n  Method 3: Force new window")
                        await page.evaluate('''(element) => {
                            const href = element.href || '#';
                            window.open(href, '_blank');
                        }''', btn_search_pop)
                        await page.wait_for_timeout(3000)
                        
                        if len(context.pages) > 1:
                            print("  [SUCCESS] New window opened!")
            
            # 6. JavaScript 함수 직접 호출
            print("\n[6] Testing JavaScript functions...")
            
            # fn_rstLtcoInfo 함수 시도
            result = await page.evaluate('''() => {
                if (typeof fn_rstLtcoInfo === 'function') {
                    fn_rstLtcoInfo();
                    return 'fn_rstLtcoInfo called';
                }
                return 'Function not found';
            }''')
            print(f"  fn_rstLtcoInfo: {result}")
            
            await page.wait_for_timeout(3000)
            
            # 7. 최종 확인
            print(f"\n[7] Final check:")
            print(f"  Total pages: {len(context.pages)}")
            print(f"  New windows detected: {len(new_windows)}")
            
            if len(context.pages) > 1:
                for i, p in enumerate(context.pages):
                    print(f"  Page {i}: {p.url[:80]}...")
            
            print("\n[INFO] Browser will remain open for 10 seconds...")
            await page.wait_for_timeout(10000)
            
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()
            print("\n[COMPLETE] Test finished")

if __name__ == "__main__":
    print("""
    ============================================
       페이지 구조 상세 분석
    ============================================
    목표: 검색 버튼과 팝업 메커니즘 이해
    ============================================
    """)
    
    asyncio.run(test_page_analysis())
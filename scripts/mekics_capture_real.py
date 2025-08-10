#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 실제 요청 캡처 - 수동 클릭 시 네트워크 요청 정확히 캡처
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def capture_real_request():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        # 쿠키 로드
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 모든 네트워크 요청 캡처
        captured_requests = []
        
        async def capture_request(request):
            # 모든 POST 요청 캡처
            if request.method == 'POST':
                headers = dict(request.headers)
                post_data = request.post_data
                
                captured = {
                    'url': request.url,
                    'method': request.method,
                    'headers': headers,
                    'post_data': post_data,
                    'timestamp': datetime.now().isoformat()
                }
                
                captured_requests.append(captured)
                
                # 다운로드 관련 요청은 즉시 출력
                if 'download' in request.url.lower() or 'excel' in request.url.lower():
                    print(f"\n[CAPTURED DOWNLOAD REQUEST]")
                    print(f"URL: {request.url}")
                    print(f"Method: {request.method}")
                    print(f"Headers: {json.dumps(headers, indent=2)}")
                    if post_data:
                        print(f"POST Data: {post_data}")
                    print("-" * 60)
        
        page.on('request', capture_request)
        
        # Response도 캡처
        async def capture_response(response):
            if 'download' in response.url.lower() or 'excel' in response.url.lower():
                print(f"\n[RESPONSE] {response.status} {response.url}")
                headers = await response.all_headers()
                if 'content-disposition' in headers:
                    print(f"  Content-Disposition: {headers['content-disposition']}")
        
        page.on('response', capture_response)
        
        try:
            print("\n실제 요청 캡처 모드")
            print("="*60)
            print("이 스크립트는 수동으로 엑셀 버튼을 클릭할 때의")
            print("네트워크 요청을 정확히 캡처합니다.")
            print("="*60)
            
            # 페이지 접속
            print("\n[1] 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/sales/ssa450skrv.do?authoUser=A")
            await page.wait_for_timeout(5000)
            
            # 조회 실행
            print("\n[2] 자동 조회 실행...")
            await page.evaluate("""
                () => {
                    // 조건 설정
                    const noRadio = Ext.getCmp('radiofield-1078');
                    if(noRadio) noRadio.setValue(true);
                    
                    const allRadio = Ext.getCmp('radiofield-1081');
                    if(allRadio) allRadio.setValue(true);
                    
                    // 짧은 기간으로 설정 (팝업 방지)
                    const dateFields = Ext.ComponentQuery.query('datefield');
                    if(dateFields.length >= 2) {
                        dateFields[0].setValue(new Date(2025, 7, 1));  // 8월 1일
                        dateFields[1].setValue(new Date(2025, 7, 10)); // 8월 10일
                    }
                }
            """)
            
            await page.keyboard.press('F2')
            
            print("   데이터 로딩 중...")
            await page.wait_for_timeout(10000)
            
            print("\n" + "="*60)
            print("이제 수동으로 엑셀 버튼을 클릭해주세요!")
            print("클릭 후 발생하는 모든 네트워크 요청을 캡처합니다.")
            print("="*60)
            
            # 60초 동안 대기하며 요청 캡처
            for i in range(60):
                await page.wait_for_timeout(1000)
                if i % 10 == 9:
                    print(f"대기 중... {i+1}초")
            
            # 캡처된 요청 저장
            if captured_requests:
                print(f"\n총 {len(captured_requests)}개의 POST 요청 캡처됨")
                
                # JSON 파일로 저장
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                capture_file = data_dir / f"captured_requests_{timestamp}.json"
                
                with open(capture_file, 'w', encoding='utf-8') as f:
                    json.dump(captured_requests, f, ensure_ascii=False, indent=2)
                
                print(f"캡처된 요청 저장: {capture_file}")
                
                # 다운로드 관련 요청만 필터링
                download_requests = [
                    req for req in captured_requests 
                    if 'download' in req['url'].lower() or 'excel' in req['url'].lower()
                ]
                
                if download_requests:
                    print(f"\n다운로드 관련 요청 {len(download_requests)}개:")
                    for req in download_requests:
                        print(f"\n  URL: {req['url']}")
                        print(f"  POST Data 일부: {req['post_data'][:200] if req['post_data'] else 'None'}")
            
            # 스크린샷
            screenshot = data_dir / f"capture_{timestamp}.png"
            await page.screenshot(path=str(screenshot))
            print(f"\n스크린샷: {screenshot}")
            
        except Exception as e:
            print(f"\n오류: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            print("\n브라우저를 열어둡니다. 수동으로 닫아주세요.")
            await page.wait_for_timeout(120000)  # 2분 대기
            await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_real_request())
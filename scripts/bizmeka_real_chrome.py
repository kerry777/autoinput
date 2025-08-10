#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실제 Chrome 브라우저 사용 - 2차 인증 없음
"""

import asyncio
from playwright.async_api import async_playwright
import subprocess
import os
import time
import psutil

def kill_chrome():
    """기존 Chrome 프로세스 종료"""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'chrome.exe':
            try:
                proc.kill()
            except:
                pass

async def real_chrome_login():
    print("\n[REAL CHROME LOGIN]")
    print("="*60)
    
    # Chrome 경로 찾기
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_exe = None
    for path in chrome_paths:
        if os.path.exists(path):
            chrome_exe = path
            break
    
    if not chrome_exe:
        print("Chrome을 찾을 수 없습니다")
        return
    
    print(f"Chrome 경로: {chrome_exe}")
    
    # 기존 Chrome 종료
    kill_chrome()
    time.sleep(2)
    
    # Chrome을 디버그 모드로 실행
    print("\n[1] Chrome 디버그 모드 실행...")
    chrome_process = subprocess.Popen([
        chrome_exe,
        '--remote-debugging-port=9222',
        '--start-maximized',
        f'--user-data-dir={os.path.expanduser("~\\AppData\\Local\\Temp\\chrome_automation")}'
    ])
    
    # Chrome 시작 대기
    time.sleep(5)
    
    async with async_playwright() as p:
        # 실행 중인 Chrome에 연결
        print("\n[2] Chrome에 연결...")
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            print("   연결 성공!")
        except:
            print("   연결 실패 - Chrome이 실행되지 않았습니다")
            return
        
        # 첫 번째 페이지 가져오기
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
        else:
            print("   컨텍스트를 찾을 수 없습니다")
            return
        
        # 로그인 페이지로 이동
        print("\n[3] 로그인 페이지 이동...")
        await page.goto("https://ezsso.bizmeka.com/loginForm.do")
        await page.wait_for_timeout(3000)
        
        # 로그인 정보 입력
        print("\n[4] 로그인 정보 입력...")
        await page.fill('#username', 'kilmoon@mek-ics.com')
        await page.wait_for_timeout(500)
        await page.fill('#password', 'moon7410!@')
        await page.wait_for_timeout(500)
        
        # 로그인 버튼 클릭
        print("\n[5] 로그인 버튼 클릭...")
        await page.click('#btnSubmit')
        
        # 결과 대기
        await page.wait_for_timeout(5000)
        
        # 결과 확인
        current_url = page.url
        print(f"\n[6] 결과 URL: {current_url}")
        
        if 'secondStep' in current_url:
            print("   [FAILED] 2차 인증 페이지 나타남")
        elif 'main' in current_url or 'portal' in current_url:
            print("   [SUCCESS] 로그인 성공! (2차 인증 없음)")
        elif 'fail' in current_url:
            print("   [FAILED] 로그인 실패 (비밀번호 오류)")
        else:
            print("   [SUCCESS] 로그인 완료!")
        
        # 스크린샷 저장
        os.makedirs("logs/real_chrome", exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"logs/real_chrome/result_{timestamp}.png"
        await page.screenshot(path=screenshot_path)
        print(f"\n[7] 스크린샷 저장: {screenshot_path}")
        
        print("\n브라우저를 30초간 유지합니다...")
        await page.wait_for_timeout(30000)
        
        await browser.close()
    
    # Chrome 프로세스 종료
    chrome_process.terminate()
    print("\n[DONE]")

if __name__ == "__main__":
    # psutil 설치 확인
    try:
        import psutil
    except ImportError:
        print("psutil 설치 중...")
        subprocess.check_call(["pip", "install", "psutil"])
        import psutil
    
    asyncio.run(real_chrome_login())
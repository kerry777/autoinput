#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 프로덕션 솔루션 - 쿠키 기반 세션 관리
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class BizmekaSessionManager:
    def __init__(self):
        self.profile_dir = "C:\\projects\\autoinput\\browser_profiles\\bizmeka_production"
        self.cookies_file = "C:\\projects\\autoinput\\data\\bizmeka_cookies.json"
        self.logs_dir = "logs/production"
        
        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
    
    async def manual_login_and_save_cookies(self):
        """수동 로그인 후 쿠키 저장"""
        print("\n[수동 로그인 모드]")
        print("="*60)
        print("1. 브라우저에서 수동으로 로그인하세요")
        print("2. 2차 인증까지 완료하세요")
        print("3. 메인 페이지가 보이면 Enter를 누르세요")
        print("="*60)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                locale="ko-KR",
                timezone_id="Asia/Seoul"
            )
            
            page = browser.pages[0] if browser.pages else await browser.new_page()
            
            # 로그인 페이지로 이동
            await page.goto("https://ezsso.bizmeka.com/loginForm.do")
            
            print("\n브라우저에서 로그인을 완료하세요...")
            input("로그인 완료 후 Enter: ")
            
            # 메인 페이지로 이동해서 쿠키 수집
            await page.goto("https://www.bizmeka.com/app/main.do")
            await page.wait_for_timeout(2000)
            
            # 쿠키 저장
            cookies = await browser.cookies()
            
            # 쿠키 파일로 저장
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            print(f"\n[성공] 쿠키 {len(cookies)}개 저장됨")
            print(f"저장 위치: {self.cookies_file}")
            
            # 중요 쿠키 확인
            for cookie in cookies:
                if cookie['name'] == 'JSESSIONID':
                    print(f"JSESSIONID: {cookie['value'][:30]}...")
                    break
            
            await browser.close()
    
    async def automated_access_with_cookies(self):
        """저장된 쿠키로 자동 접근"""
        print("\n[자동 접근 모드]")
        print("="*60)
        
        # 쿠키 파일 확인
        if not Path(self.cookies_file).exists():
            print("[ERROR] 쿠키 파일이 없습니다!")
            print("먼저 수동 로그인을 실행하세요.")
            return False
        
        # 쿠키 로드
        with open(self.cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        print(f"쿠키 {len(cookies)}개 로드됨")
        
        async with async_playwright() as p:
            # 새 브라우저 컨텍스트
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale="ko-KR",
                timezone_id="Asia/Seoul"
            )
            
            # 쿠키 주입
            try:
                await context.add_cookies(cookies)
                print("[OK] 쿠키 주입 성공")
            except Exception as e:
                print(f"[ERROR] 쿠키 주입 실패: {e}")
                await browser.close()
                return False
            
            page = await context.new_page()
            
            # 메인 페이지 직접 접근
            print("\n[1] 메인 서비스 접근")
            await page.goto("https://www.bizmeka.com/app/main.do")
            await page.wait_for_timeout(3000)
            
            current_url = page.url
            print(f"현재 URL: {current_url}")
            
            # 로그인 상태 확인
            if 'loginForm' in current_url:
                print("[FAIL] 세션 만료 - 재로그인 필요")
                await browser.close()
                return False
            elif 'secondStep' in current_url:
                print("[WARN] 2차 인증 필요")
                await browser.close()
                return False
            else:
                print("[SUCCESS] 로그인 상태 확인!")
                
                # 실제 작업 수행 가능
                print("\n[2] 작업 수행 가능 상태")
                print("여기서 필요한 자동화 작업을 수행할 수 있습니다.")
                
                # 예시: 페이지 정보 수집
                title = await page.title()
                print(f"페이지 제목: {title}")
                
                # 스크린샷 저장
                screenshot_path = Path(self.logs_dir) / f"success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                print(f"스크린샷 저장: {screenshot_path}")
                
                print("\n브라우저는 10초 후 종료됩니다...")
                await page.wait_for_timeout(10000)
                
                await browser.close()
                return True
    
    async def check_session_validity(self):
        """세션 유효성 확인"""
        print("\n[세션 유효성 확인]")
        print("="*60)
        
        if not Path(self.cookies_file).exists():
            print("쿠키 파일이 없습니다.")
            return False
        
        # 쿠키 파일 수정 시간 확인
        cookie_mtime = datetime.fromtimestamp(Path(self.cookies_file).stat().st_mtime)
        age_hours = (datetime.now() - cookie_mtime).total_seconds() / 3600
        
        print(f"쿠키 생성 시간: {cookie_mtime}")
        print(f"경과 시간: {age_hours:.1f}시간")
        
        if age_hours > 24:
            print("[WARN] 쿠키가 24시간 이상 경과했습니다.")
            print("재로그인을 권장합니다.")
        
        # 실제 테스트
        with open(self.cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        # JSESSIONID 확인
        session_found = False
        for cookie in cookies:
            if cookie['name'] == 'JSESSIONID':
                session_found = True
                print(f"JSESSIONID: {cookie['value'][:30]}...")
                break
        
        if not session_found:
            print("[ERROR] JSESSIONID가 없습니다!")
            return False
        
        print("[OK] 세션 쿠키 존재")
        return True

async def main():
    manager = BizmekaSessionManager()
    
    while True:
        print("\n" + "="*60)
        print("Bizmeka 자동화 프로덕션 솔루션")
        print("="*60)
        print("1. 수동 로그인 (쿠키 저장)")
        print("2. 자동 접근 (쿠키 사용)")
        print("3. 세션 유효성 확인")
        print("0. 종료")
        
        choice = input("\n선택: ")
        
        if choice == "1":
            await manager.manual_login_and_save_cookies()
        elif choice == "2":
            success = await manager.automated_access_with_cookies()
            if success:
                print("\n[성공] 자동화 작업 완료!")
            else:
                print("\n[실패] 세션이 만료되었습니다. 옵션 1을 실행하세요.")
        elif choice == "3":
            valid = await manager.check_session_validity()
            if valid:
                print("\n세션이 유효할 가능성이 높습니다.")
            else:
                print("\n세션이 유효하지 않을 가능성이 높습니다.")
        elif choice == "0":
            print("종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    asyncio.run(main())
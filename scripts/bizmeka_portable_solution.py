#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 포터블 솔루션 - 다른 PC에서도 사용 가능
"""

import asyncio
import json
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

class BizmekaPortable:
    def __init__(self):
        self.portable_dir = Path("C:\\projects\\autoinput\\bizmeka_portable")
        self.portable_dir.mkdir(exist_ok=True)
    
    async def export_session(self):
        """현재 PC의 세션을 내보내기"""
        print("\n[세션 내보내기]")
        print("="*60)
        
        # 1. 쿠키 파일 복사
        cookies_src = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")
        cookies_dst = self.portable_dir / "cookies.json"
        
        if cookies_src.exists():
            shutil.copy(cookies_src, cookies_dst)
            print(f"✓ 쿠키 파일 복사됨")
        
        # 2. 브라우저 프로필 압축 (선택적)
        profile_src = Path("C:\\projects\\autoinput\\browser_profiles\\bizmeka_production")
        
        if profile_src.exists():
            # 중요 파일만 복사
            important_files = [
                "Default/Cookies",
                "Default/Cookies-journal", 
                "Default/Network/Cookies",
                "Default/Network/Cookies-journal",
                "Local State"
            ]
            
            profile_dst = self.portable_dir / "profile"
            profile_dst.mkdir(exist_ok=True)
            
            for file_path in important_files:
                src_file = profile_src / file_path
                if src_file.exists():
                    dst_file = profile_dst / file_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(src_file, dst_file)
                    print(f"✓ {file_path} 복사됨")
        
        # 3. 설정 정보 저장
        config = {
            "username": "kilmoon@mek-ics.com",
            "note": "다른 PC에서 사용시 2FA 필요할 수 있음",
            "tips": [
                "같은 네트워크에서 사용시 성공률 높음",
                "VPN 사용시 차단될 수 있음",
                "첫 사용시 2FA 인증 필요"
            ]
        }
        
        config_file = self.portable_dir / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"\n[완료] 포터블 폴더: {self.portable_dir}")
        print("이 폴더를 USB나 클라우드에 복사하세요.")
        
        return self.portable_dir
    
    async def import_session(self, portable_path=None):
        """다른 PC에서 세션 가져오기"""
        print("\n[세션 가져오기]")
        print("="*60)
        
        if portable_path:
            src_dir = Path(portable_path)
        else:
            src_dir = self.portable_dir
        
        if not src_dir.exists():
            print("포터블 폴더가 없습니다!")
            return False
        
        # 1. 쿠키 복원
        cookies_src = src_dir / "cookies.json"
        if cookies_src.exists():
            cookies_dst = Path("C:\\projects\\autoinput\\data\\bizmeka_imported.json")
            shutil.copy(cookies_src, cookies_dst)
            print(f"✓ 쿠키 가져옴")
            
            # 테스트
            await self.test_imported_cookies(cookies_dst)
        
        return True
    
    async def test_imported_cookies(self, cookies_file):
        """가져온 쿠키 테스트"""
        print("\n[쿠키 테스트]")
        
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                locale="ko-KR",
                timezone_id="Asia/Seoul"
            )
            
            # 쿠키 주입
            try:
                await context.add_cookies(cookies)
                print("✓ 쿠키 주입 성공")
            except Exception as e:
                print(f"✗ 쿠키 주입 실패: {e}")
                await browser.close()
                return
            
            page = await context.new_page()
            
            # 접속 시도
            print("\n접속 시도 중...")
            await page.goto("https://www.bizmeka.com/")
            await page.wait_for_timeout(3000)
            
            current_url = page.url
            
            if 'loginForm' in current_url:
                print("\n[결과] 재로그인 필요")
                print("→ PC가 바뀌어서 2FA 인증이 필요합니다.")
            elif 'secondStep' in current_url:
                print("\n[결과] 2차 인증 필요")
                print("→ 새 기기로 인식되었습니다.")
            else:
                print("\n[결과] 성공!")
                print("→ 같은 네트워크라서 성공한 것 같습니다.")
            
            print("\n30초 후 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()

async def main():
    portable = BizmekaPortable()
    
    print("\n선택:")
    print("1. 현재 세션 내보내기 (다른 PC로 이동용)")
    print("2. 세션 가져오기 (다른 PC에서)")
    print("3. 가져온 세션 테스트")
    
    # 자동 선택 (1번)
    choice = "1"
    
    if choice == "1":
        await portable.export_session()
    elif choice == "2":
        await portable.import_session()
    elif choice == "3":
        cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_imported.json")
        if cookies_file.exists():
            await portable.test_imported_cookies(cookies_file)

if __name__ == "__main__":
    asyncio.run(main())
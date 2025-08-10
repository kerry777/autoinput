#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래핑 실행 스크립트
새로운 모듈화된 구조 사용
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from sites.bizmeka import BizmekaAuth, BizmekaMailScraper


async def main():
    """메인 실행 함수"""
    print("="*60)
    print("Bizmeka 메일 스크래퍼 - 모듈화 버전")
    print("="*60)
    
    # 사용자 입력
    try:
        pages = int(input("수집할 페이지 수 (기본: 3): ") or "3")
    except ValueError:
        pages = 3
    
    async with async_playwright() as p:
        # 브라우저 실행
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()
        
        try:
            # 1. 인증 처리
            print("\n1. 인증 처리...")
            auth = BizmekaAuth()
            await auth.setup_browser(context, page)
            
            login_success = await auth.ensure_login()
            if not login_success:
                print("[ERROR] 로그인 실패")
                return
            
            # 2. 메일 스크래핑
            print("\n2. 메일 스크래핑 시작...")
            scraper = BizmekaMailScraper()
            await scraper.setup_browser(context, page)
            
            # 스크래핑 및 저장
            filepath = await scraper.scrape_and_save(max_pages=pages)
            
            print(f"\n✅ 스크래핑 완료!")
            print(f"📄 저장 파일: {filepath}")
            
            # 결과 요약
            import pandas as pd
            df = pd.read_excel(filepath)
            
            print(f"\n📊 수집 결과:")
            print(f"  • 총 메일: {len(df)}개")
            
            if '페이지' in df.columns:
                page_counts = df['페이지'].value_counts().sort_index()
                for page_num, count in page_counts.items():
                    print(f"  • 페이지 {page_num}: {count}개")
            
            if '읽음상태' in df.columns:
                status_counts = df['읽음상태'].value_counts()
                for status, count in status_counts.items():
                    print(f"  • {status}: {count}개")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
        print("\n🏁 프로그램 종료")
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n💥 프로그램 오류: {e}")
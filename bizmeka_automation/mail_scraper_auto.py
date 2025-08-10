#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래퍼 - 자동 실행 버전
입력 없이 자동으로 3페이지 스크래핑
"""

import asyncio
from mail_scraper import MailScraper
from utils import print_banner, print_status


async def run_auto():
    """자동 실행 - 3페이지 수집"""
    print_banner("MAIL SCRAPER AUTO")
    
    scraper = MailScraper()
    
    print_status('info', '3페이지 자동 수집을 시작합니다...')
    
    success = await scraper.run(max_pages=3)
    
    if success:
        print("\n" + "="*60)
        print("[OK] 메일 스크래핑 완료")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("[ERROR] 메일 스크래핑 실패")
        print("="*60)
    
    return success


if __name__ == "__main__":
    try:
        asyncio.run(run_auto())
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
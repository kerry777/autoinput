#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 스크래핑 실행
"""

import asyncio
from core.bizmeka_integrated import BizmekaIntegrated


async def main():
    biz = BizmekaIntegrated()
    
    print("\n" + "="*60)
    print("Bizmeka 메일 스크래핑 시작")
    print("="*60)
    
    # 메일 스크래핑 (로그인부터 Excel 저장까지)
    result = await biz.scrape_mails(max_pages=3)
    
    if result:
        print("\n메일 스크래핑 완료!")
    else:
        print("\n메일 스크래핑 실패")


if __name__ == "__main__":
    asyncio.run(main())
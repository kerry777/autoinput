#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
재가관리책임자 교육기관 페이지네이션 스크래퍼
https://longtermcare.or.kr/npbs/r/e/505/selectRftrEduAdminList
"""

import asyncio
import sys
import os

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.pagination_scraper import PaginationScraper

async def main():
    """재가관리책임자 교육기관 데이터 수집"""
    
    print("""
    ==============================================================
         재가관리책임자 교육기관 데이터 수집 시작              
    ==============================================================
      
      수집 대상: 재가관리책임자 교육기관 목록
      방식: 페이지네이션 자동 처리
      저장: 엑셀 파일 (페이지별 시트 분리)
      
    ==============================================================
    """)
    
    # 재가관리책임자 교육기관 조회 페이지
    url = "https://longtermcare.or.kr/npbs/r/e/505/selectRftrEduAdminList?menuId=npe0000002612"
    
    print(f"""
    URL: 재가관리책임자 교육기관 목록
    수집 페이지: 3페이지
    페이지 간 대기: 3초
    --------------------------------------------------------------
    
    진행 상황:
    """)
    
    # 스크래퍼 실행
    scraper = PaginationScraper(
        url=url,
        max_pages=3,  # 3페이지 수집
        delay_between_pages=3  # 3초 대기
    )
    
    # 파일명 커스터마이징을 위해 excel_file 속성 설정
    timestamp = asyncio.get_event_loop().time()
    from datetime import datetime
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    scraper.excel_file = f"data/scraped/rftr_edu_data_{timestamp_str}.xlsx"
    
    await scraper.run()
    
    print(f"""
    ==============================================================
                        수집 완료!                           
    ==============================================================
      
      재가관리책임자 교육기관 데이터 수집 완료
      
      저장 위치: {scraper.excel_file}
      
      엑셀 파일 구성:
      - [전체_데이터] 시트: 모든 페이지 통합 데이터
      - [페이지_1] 시트: 1페이지 데이터
      - [페이지_2] 시트: 2페이지 데이터  
      - [페이지_3] 시트: 3페이지 데이터
      - [메타데이터] 시트: 수집 정보
      
    ==============================================================
    """)

if __name__ == "__main__":
    print("\n재가관리책임자 교육기관 데이터 수집을 시작합니다...\n")
    asyncio.run(main())
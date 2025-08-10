#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
페이지네이션 자동 실행 스크립트
사용자 입력 없이 자동으로 실행됩니다
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
    """자동 실행"""
    
    print("""
    ==============================================================
             페이지네이션 자동 실행 (3페이지 수집)               
    ==============================================================
      
      실시간으로 다음 과정을 보여드립니다:
      
      1. 브라우저 창이 열립니다 (화면에서 확인 가능)
      2. 첫 페이지 데이터를 수집합니다
      3. 페이지 2로 이동합니다 (3초 대기)
      4. 페이지 2 데이터를 수집합니다
      5. 페이지 3으로 이동합니다 (3초 대기)
      6. 페이지 3 데이터를 수집합니다
      7. 엑셀 파일로 저장합니다
      
      * 각 페이지 데이터는 별도 시트로 저장됩니다
      * 전체 데이터도 통합 시트로 저장됩니다
      
    ==============================================================
    """)
    
    # 교육기관 조회 페이지
    url = "https://longtermcare.or.kr/npbs/r/e/501/openMdcareMcpcEduAdmin.web?menuId=npe0000001100"
    
    print(f"""
    대상 사이트: 장기요양보험 교육기관 조회
    수집 페이지: 3페이지
    페이지 간 대기: 3초
    --------------------------------------------------------------
    """)
    
    # 스크래퍼 실행
    scraper = PaginationScraper(
        url=url,
        max_pages=3,  # 3페이지 수집
        delay_between_pages=3  # 3초 대기
    )
    
    await scraper.run()
    
    print("""
    ==============================================================
                        실행 완료!                           
    ==============================================================
      
      엑셀 파일 위치: data/scraped/pagination_data_*.xlsx
      
      엑셀 파일 구성:
      - [전체_데이터] 시트: 모든 페이지 통합 데이터
      - [페이지_1] 시트: 1페이지 데이터
      - [페이지_2] 시트: 2페이지 데이터  
      - [페이지_3] 시트: 3페이지 데이터
      - [메타데이터] 시트: 수집 정보
      
    ==============================================================
    """)

if __name__ == "__main__":
    print("\n시작합니다... 브라우저가 열립니다.\n")
    asyncio.run(main())
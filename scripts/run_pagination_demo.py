#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
페이지네이션 데모 실행 스크립트
실시간으로 페이지별 데이터 수집 과정을 보여줍니다
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

async def run_demo():
    """페이지네이션 데모 실행"""
    
    print("""
    ==============================================================
                     페이지네이션 데모 실행                        
                                                            
      * 실시간으로 페이지별 데이터 수집 과정을 보여드립니다        
      * 각 페이지 데이터는 엑셀 파일에 즉시 저장됩니다            
      * 브라우저 창에서 진행 과정을 확인할 수 있습니다            
    ==============================================================
    """)
    
    # 사용자 입력
    print("\n[설정]")
    pages = input("  수집할 페이지 수 (기본값: 3, 최대: 5): ").strip()
    if not pages:
        pages = 3
    else:
        pages = min(int(pages), 5)  # 최대 5페이지로 제한
    
    delay = input("  페이지 간 대기시간 (초, 기본값: 3): ").strip()
    if not delay:
        delay = 3
    else:
        delay = int(delay)
    
    print(f"\n[확인] {pages}페이지를 {delay}초 간격으로 수집합니다.")
    input("Enter 키를 눌러 시작하세요...")
    
    # 교육기관 조회 페이지
    url = "https://longtermcare.or.kr/npbs/r/e/501/openMdcareMcpcEduAdmin.web?menuId=npe0000001100"
    
    print(f"""
    --------------------------------------------------------------
      대상 URL: 장기요양보험 교육기관 조회                        
      수집 페이지: {pages}페이지                                     
      페이지 간 대기: {delay}초                                      
    --------------------------------------------------------------
    """)
    
    # 스크래퍼 실행
    scraper = PaginationScraper(
        url=url,
        max_pages=pages,
        delay_between_pages=delay
    )
    
    await scraper.run()
    
    print("""
    ==============================================================
                        데모 실행 완료                           
                                                            
      수집된 데이터는 다음 위치에 저장되었습니다:                 
      - data/scraped/pagination_data_*.xlsx                    
                                                            
      엑셀 파일에는 다음 시트가 포함됩니다:                      
      - 전체_데이터: 모든 페이지 데이터                          
      - 페이지_1, 페이지_2...: 각 페이지별 데이터                
      - 메타데이터: 수집 정보                                    
    ==============================================================
    """)

if __name__ == "__main__":
    asyncio.run(run_demo())
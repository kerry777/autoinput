#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전국 17개 시도 장기요양기관 다운로드 - 브라우저 화면 표시 버전
진행 과정을 눈으로 확인하면서 실행 (교육용, 디버깅용)
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from download_all_regions_final_working import FinalRegionDownloader

async def main():
    """브라우저 화면을 보면서 실행"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     전국 17개 시도 다운로드 - 화면 표시 버전              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  ✓ 브라우저 화면이 표시됩니다                            ║
    ║  ✓ 진행 과정을 직접 확인할 수 있습니다                   ║
    ║  ✓ 문제 발생 시 어디서 멈췄는지 확인 가능               ║
    ║  ✗ 실행 속도가 느립니다                                  ║
    ╚══════════════════════════════════════════════════════════╝
    
    용도:
    - 처음 실행하여 작동 확인이 필요할 때
    - 문제가 발생하여 디버깅이 필요할 때
    - 진행 과정을 교육/시연해야 할 때
    
    예상 소요 시간:
    - 테스트 모드 (3개): 약 2-3분
    - 전체 실행 (17개): 약 15-20분
    """)
    
    print("\n실행 옵션을 선택하세요:")
    print("1. 테스트 모드 (처음 3개 시도만)")
    print("2. 전체 실행 (17개 시도 모두)")
    print("3. 종료")
    
    choice = input("\n선택 (1/2/3): ").strip()
    
    downloader = FinalRegionDownloader()
    
    if choice == "1":
        print("\n[테스트 모드] 처음 3개 시도만 다운로드합니다...")
        print("브라우저 화면을 확인하세요!\n")
        await downloader.run(test_mode=True, headless=False)
        
    elif choice == "2":
        confirm = input("\n정말 17개 시도 전체를 다운로드하시겠습니까? (y/n): ").strip().lower()
        if confirm == 'y':
            print("\n[전체 실행] 17개 시도 모두 다운로드합니다...")
            print("브라우저 화면을 확인하세요!\n")
            await downloader.run(test_mode=False, headless=False)
        else:
            print("취소되었습니다.")
            
    else:
        print("종료합니다.")

if __name__ == "__main__":
    asyncio.run(main())
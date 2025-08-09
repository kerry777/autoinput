#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
전국 17개 시도 장기요양기관 다운로드 - Headless 버전
백그라운드에서 빠르게 실행 (실무용, 자동화용)
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from download_all_regions_final_working import FinalRegionDownloader

async def main():
    """Headless 모드로 빠르게 실행"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     전국 17개 시도 다운로드 - Headless 버전               ║
    ╠══════════════════════════════════════════════════════════╣
    ║  ✓ 백그라운드에서 실행됩니다                             ║
    ║  ✓ 실행 속도가 빠릅니다 (30-50% 향상)                   ║
    ║  ✓ 시스템 리소스를 적게 사용합니다                       ║
    ║  ✗ 진행 과정을 눈으로 볼 수 없습니다                    ║
    ╚══════════════════════════════════════════════════════════╝
    
    용도:
    - 이미 테스트가 완료되어 빠른 실행이 필요할 때
    - 서버나 백그라운드에서 자동 실행할 때
    - 대량 데이터를 빠르게 수집해야 할 때
    
    예상 소요 시간:
    - 테스트 모드 (3개): 약 1-2분
    - 전체 실행 (17개): 약 10-15분
    """)
    
    print("\n실행 옵션을 선택하세요:")
    print("1. 테스트 모드 (처음 3개 시도만)")
    print("2. 전체 실행 (17개 시도 모두)")
    print("3. 커스텀 실행 (특정 위치부터)")
    print("4. 종료")
    
    choice = input("\n선택 (1/2/3/4): ").strip()
    
    downloader = FinalRegionDownloader()
    
    if choice == "1":
        print("\n[테스트 모드 - Headless] 처음 3개 시도만 다운로드합니다...")
        print("콘솔 로그를 확인하세요...\n")
        await downloader.run(test_mode=True, headless=True)
        
    elif choice == "2":
        confirm = input("\n정말 17개 시도 전체를 다운로드하시겠습니까? (y/n): ").strip().lower()
        if confirm == 'y':
            print("\n[전체 실행 - Headless] 17개 시도 모두 다운로드합니다...")
            print("콘솔 로그를 확인하세요...\n")
            await downloader.run(test_mode=False, headless=True)
        else:
            print("취소되었습니다.")
            
    elif choice == "3":
        try:
            start = int(input("시작할 위치 (1-17): ").strip()) - 1
            if 0 <= start < 17:
                count = int(input(f"{start+1}번째부터 몇 개를 다운로드할까요? ").strip())
                print(f"\n[커스텀 실행 - Headless] {start+1}번째부터 {count}개 다운로드합니다...")
                print("콘솔 로그를 확인하세요...\n")
                
                # 테스트 모드를 활용하여 특정 구간만 실행
                if count <= 3:
                    await downloader.run(test_mode=True, start_from=start, headless=True)
                else:
                    await downloader.run(test_mode=False, start_from=start, headless=True)
            else:
                print("잘못된 위치입니다.")
        except ValueError:
            print("잘못된 입력입니다.")
            
    else:
        print("종료합니다.")
    
    print("\n" + "="*60)
    print("작업이 완료되었습니다.")
    print("다운로드된 파일은 downloads/longtermcare/regions 폴더를 확인하세요.")

if __name__ == "__main__":
    asyncio.run(main())
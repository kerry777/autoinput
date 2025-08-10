#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
프로젝트 정리 스크립트
- 테스트 파일 이동
- 중복 날짜 접미사 제거
- 디렉토리 정리
"""

import os
import shutil
import glob
from pathlib import Path

def move_test_files():
    """테스트 파일들을 적절한 디렉토리로 이동"""
    
    # 테스트 파일 매핑
    test_mappings = {
        'tests/longtermcare/': 'scripts/test_longtermcare_*.py',
        'tests/hwp/': [
            'scripts/test_hwp_*.py',
            'scripts/test_libreoffice_*.py',
            'scripts/test_h2orestart_*.py',
            'scripts/test_pyhwpx_*.py'
        ],
        'tests/login/': [
            'scripts/test_login_*.py',
            'scripts/test_mdm_*.py',
            'scripts/test_msm_*.py',
            'scripts/test_flutter_*.py'
        ],
        'tests/board/': [
            'scripts/test_board_*.py',
            'scripts/test_boards_*.py',
            'scripts/test_forms_*.py',
            'scripts/test_attachment_*.py',
            'scripts/test_all_boards.py'
        ],
        'tests/scraping/': [
            'scripts/test_scraping_*.py',
            'scripts/test_pagination*.py',
            'scripts/test_speed_*.py',
            'scripts/test_with_*.py',
            'scripts/test_download_*.py',
            'scripts/test_facility_*.py',
            'scripts/test_search_*.py',
            'scripts/test_popup_*.py',
            'scripts/test_javascript_*.py',
            'scripts/test_form_*.py',
            'scripts/test_direct_*.py',
            'scripts/test_simple_*.py',
            'scripts/test_seoul_*.py',
            'scripts/test_page_*.py',
            'scripts/test_final_*.py'
        ]
    }
    
    moved_count = 0
    
    for target_dir, patterns in test_mappings.items():
        # 디렉토리 생성
        os.makedirs(target_dir, exist_ok=True)
        
        # 패턴이 리스트가 아니면 리스트로 변환
        if isinstance(patterns, str):
            patterns = [patterns]
        
        for pattern in patterns:
            files = glob.glob(pattern)
            for file in files:
                if os.path.exists(file):
                    filename = os.path.basename(file)
                    target_path = os.path.join(target_dir, filename)
                    try:
                        shutil.move(file, target_path)
                        print(f"Moved: {file} -> {target_path}")
                        moved_count += 1
                    except Exception as e:
                        print(f"Error moving {file}: {e}")
    
    return moved_count

def fix_duplicate_dates():
    """중복 날짜 접미사 제거 (_20250809_20250809 -> _20250809)"""
    
    fixed_count = 0
    patterns = [
        '**/*_20250809_20250809.*',
        'docs/*_20250809_20250809.*',
        '*_20250809_20250809.*'
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern, recursive=True)
        for old_path in files:
            new_path = old_path.replace('_20250809_20250809', '_20250809')
            if old_path != new_path and not os.path.exists(new_path):
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} -> {new_path}")
                    fixed_count += 1
                except Exception as e:
                    print(f"Error renaming {old_path}: {e}")
    
    return fixed_count

def clean_data_directories():
    """데이터 디렉토리 정리"""
    
    # 오래된 스크린샷 정리
    screenshot_dirs = [
        'logs/screenshots/test/',
        'logs/screenshots/scraping/',
        'logs/screenshots/pagination/'
    ]
    
    removed_count = 0
    
    for dir_path in screenshot_dirs:
        if os.path.exists(dir_path):
            files = glob.glob(f"{dir_path}*.png")
            # 2025-08-09 날짜의 파일들만 보관, 나머지 삭제
            for file in files:
                if '20250809' in file:
                    continue  # 최신 파일은 유지
                try:
                    os.remove(file)
                    print(f"Removed old screenshot: {file}")
                    removed_count += 1
                except Exception as e:
                    print(f"Error removing {file}: {e}")
    
    # 빈 디렉토리 제거
    empty_dirs = []
    for root, dirs, files in os.walk('data'):
        if not dirs and not files:
            empty_dirs.append(root)
    
    for dir_path in empty_dirs:
        try:
            os.rmdir(dir_path)
            print(f"Removed empty directory: {dir_path}")
            removed_count += 1
        except Exception as e:
            print(f"Error removing directory {dir_path}: {e}")
    
    return removed_count

def consolidate_scripts():
    """중복 스크립트 통합 정보 제공"""
    
    print("\n=== 통합 필요 스크립트 ===")
    
    consolidation_suggestions = {
        "download_all_regions 시리즈": [
            "scripts/download_all_regions_final.py",
            "scripts/download_all_regions_working.py",
            "scripts/download_all_regions_final_working.py",
            "scripts/download_regions_with_browser.py",
            "scripts/download_regions_headless.py"
        ],
        "HWP 변환기 시리즈": [
            "scripts/hwp_converter.py",
            "scripts/hwp_advanced_parser.py",
            "scripts/hwp_pyhwp_converter.py",
            "scripts/hwp_hwpapi_converter.py",
            "scripts/hwp_to_pdf_converter.py",
            "scripts/hwp_com_automation.py",
            "scripts/hwp_online_converter.py",
            "scripts/hwp2024_automation.py",
            "scripts/libreoffice_hwp_converter.py"
        ],
        "게시판 스크래퍼 시리즈": [
            "scripts/scrape_board_with_attachments.py",
            "scripts/scrape_notice_board.py",
            "scripts/scrape_forms_board.py",
            "scripts/scrape_forms_final.py",
            "scripts/board_scraper_with_metadata.py"
        ],
        "이의신청 스크래퍼 시리즈": [
            "scripts/scrape_objection_board.py",
            "scripts/scrape_objection_direct.py",
            "scripts/scrape_objection_api.py",
            "scripts/scrape_objection_final.py",
            "scripts/scrape_objection_content.py",
            "scripts/scrape_objection_quick.py"
        ]
    }
    
    for category, files in consolidation_suggestions.items():
        existing = [f for f in files if os.path.exists(f)]
        if len(existing) > 1:
            print(f"\n{category}:")
            for file in existing:
                print(f"  - {file}")
            print(f"  → 통합 권장: {category.replace(' 시리즈', '_unified.py')}")
    
    return len(consolidation_suggestions)

def main():
    """메인 실행 함수"""
    print("=== 프로젝트 정리 시작 ===\n")
    
    # 1. 테스트 파일 이동
    print("1. 테스트 파일 이동 중...")
    moved = move_test_files()
    print(f"   → {moved}개 파일 이동 완료\n")
    
    # 2. 중복 날짜 수정
    print("2. 중복 날짜 접미사 제거 중...")
    fixed = fix_duplicate_dates()
    print(f"   → {fixed}개 파일명 수정 완료\n")
    
    # 3. 데이터 디렉토리 정리
    print("3. 데이터 디렉토리 정리 중...")
    cleaned = clean_data_directories()
    print(f"   → {cleaned}개 항목 정리 완료\n")
    
    # 4. 통합 필요 스크립트 분석
    print("4. 중복 스크립트 분석...")
    suggestions = consolidate_scripts()
    print(f"   → {suggestions}개 카테고리 통합 권장\n")
    
    print("=== 프로젝트 정리 완료 ===")
    print(f"총 변경사항: {moved + fixed + cleaned}개")

if __name__ == "__main__":
    main()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
문서 파일명에 날짜 추가 스크립트
파일명 형식: filename_YYYYMMDD_YYYYMMDD.md
첫 번째 날짜: 생성일, 두 번째 날짜: 최종 수정일
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# 변경할 파일 목록과 새 이름
rename_list = [
    # 타겟 사이트 분석
    ("docs/target-site-analysis.md", 
     "docs/target-site-analysis_20250809_20250809.md"),
    
    ("docs/longtermcare-service-types.md",
     "docs/longtermcare-service-types_20250809_20250809.md"),
    
    ("docs/업무프로세스_확인서.md",
     "docs/업무프로세스_확인서_20250809_20250809.md"),
    
    ("docs/간단요약_업무흐름.md",
     "docs/간단요약_업무흐름_20250809_20250809.md"),
    
    # 배포 및 사용 환경
    ("docs/deployment-architecture.md",
     "docs/deployment-architecture_20250809_20250809.md"),
    
    ("docs/user-journey-map.md",
     "docs/user-journey-map_20250809_20250809.md"),
    
    # 웹 스크래핑 학습
    ("docs/web-scraping-dev-complete-guide.md",
     "docs/web-scraping-dev-complete-guide_20250809_20250809.md"),
    
    ("docs/web-scraping-master-roadmap.md",
     "docs/web-scraping-master-roadmap_20250809_20250809.md"),
    
    ("docs/web-scraping-skills-checklist.md",
     "docs/web-scraping-skills-checklist_20250809_20250809.md"),
    
    ("docs/scrapfly-advanced-techniques.md",
     "docs/scrapfly-advanced-techniques_20250809_20250809.md"),
    
    ("docs/learning-resources-catalog.md",
     "docs/learning-resources-catalog_20250809_20250809.md"),
    
    ("docs/implementation-priority-matrix.md",
     "docs/implementation-priority-matrix_20250809_20250809.md"),
    
    # 프로젝트 관리
    ("TASKMASTER.md",
     "TASKMASTER_20250809_20250809.md"),
    
    ("README.md",
     "README_20250809_20250809.md"),
    
    ("CONTRIBUTING.md",
     "CONTRIBUTING_20250809_20250809.md"),
    
    ("CODE_OF_CONDUCT.md",
     "CODE_OF_CONDUCT_20250809_20250809.md"),
    
    ("CHANGELOG.md",
     "CHANGELOG_20250809_20250809.md"),
]

def rename_files():
    """파일명 변경 실행"""
    
    renamed_count = 0
    failed_count = 0
    
    print("=" * 60)
    print("Document File Renaming - Adding Dates")
    print("=" * 60)
    
    for old_path, new_path in rename_list:
        try:
            if os.path.exists(old_path):
                # 새 파일이 이미 존재하는지 확인
                if os.path.exists(new_path):
                    print(f"[SKIP] {new_path} already exists")
                    continue
                
                # 파일 이름 변경
                shutil.move(old_path, new_path)
                print(f"[OK] Renamed: {old_path}")
                print(f"   → {new_path}")
                renamed_count += 1
            else:
                print(f"[FAIL] Not found: {old_path}")
                failed_count += 1
                
        except Exception as e:
            print(f"[ERROR] Renaming {old_path}: {str(e)}")
            failed_count += 1
    
    print("\n" + "=" * 60)
    print(f"Complete: {renamed_count} success, {failed_count} failed")
    print("=" * 60)
    
    # 변경 사항을 기록할 문서 생성
    create_version_log()
    
    return renamed_count, failed_count

def create_version_log():
    """버전 관리 로그 문서 생성"""
    
    log_content = f"""# 📅 Document Version Control Log

## 🔄 파일명 규칙
- 형식: `filename_YYYYMMDD_YYYYMMDD.md`
- 첫 번째 날짜: 최초 작성일
- 두 번째 날짜: 최종 수정일

## 📋 현재 문서 버전 ({datetime.now().strftime('%Y-%m-%d')})

### 타겟 사이트 분석 문서
| 문서명 | 생성일 | 최종수정일 | 설명 |
|--------|--------|------------|------|
| target-site-analysis_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 장기요양보험 사이트 분석 |
| longtermcare-service-types_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 서비스 유형별 상세 |
| 업무프로세스_확인서_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 업무 확인용 |
| 간단요약_업무흐름_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 요약 문서 |

### 배포 및 사용 환경
| 문서명 | 생성일 | 최종수정일 | 설명 |
|--------|--------|------------|------|
| deployment-architecture_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 배포 아키텍처 |
| user-journey-map_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 사용자 여정 |

### 웹 스크래핑 학습
| 문서명 | 생성일 | 최종수정일 | 설명 |
|--------|--------|------------|------|
| web-scraping-dev-complete-guide_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 완전 가이드 |
| web-scraping-master-roadmap_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 마스터 로드맵 |
| web-scraping-skills-checklist_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 스킬 체크리스트 |
| scrapfly-advanced-techniques_20250809_20250809.md | 2025-08-09 | 2025-08-09 | ScrapFly 고급 기술 |
| learning-resources-catalog_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 학습 리소스 |
| implementation-priority-matrix_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 구현 우선순위 |

### 프로젝트 관리
| 문서명 | 생성일 | 최종수정일 | 설명 |
|--------|--------|------------|------|
| README_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 프로젝트 소개 |
| TASKMASTER_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 작업 관리 |
| CONTRIBUTING_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 기여 가이드 |
| CODE_OF_CONDUCT_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 행동 규범 |
| CHANGELOG_20250809_20250809.md | 2025-08-09 | 2025-08-09 | 변경 이력 |

## 🔄 업데이트 규칙

### 날짜 변경 시점
1. **최종수정일 변경**: 내용의 실질적 변경이 있을 때
   - 새로운 섹션 추가
   - 기존 내용의 수정/삭제
   - 중요한 정보 업데이트

2. **변경하지 않는 경우**:
   - 오타 수정
   - 포맷팅 변경
   - 주석 추가

### 파일명 변경 방법
```bash
# 예시: target-site-analysis 문서 수정 시
# 기존: target-site-analysis_20250809_20250809.md
# 수정: target-site-analysis_20250809_20250815.md
mv docs/target-site-analysis_20250809_20250809.md docs/target-site-analysis_20250809_20250815.md
```

## 📝 변경 이력

### 2025-08-09
- 최초 버전 관리 시스템 도입
- 모든 주요 문서에 날짜 추가
- 자동 변경 스크립트 생성

---

*이 문서는 자동으로 생성되었습니다.*
*마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    with open("docs/DOCUMENT_VERSION_CONTROL_20250809.md", "w", encoding="utf-8") as f:
        f.write(log_content)
    
    print("\n[INFO] Version control document created: docs/DOCUMENT_VERSION_CONTROL_20250809.md")

def main():
    """메인 실행 함수"""
    print("\nAutoInput Document Version Control System")
    print("Adding creation and modification dates to filenames\n")
    
    # 사용자 확인
    response = input("Rename files? (y/n): ")
    
    if response.lower() == 'y':
        renamed, failed = rename_files()
        
        if renamed > 0:
            print("\n[SUCCESS] File renaming complete!")
            print("Please update the second date when modifying documents.")
            print("Example: filename_20250809_20250815.md (modified on Aug 15)")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()
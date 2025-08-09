# 📝 AutoInput CHANGELOG Management Policy

## 추천 전략: 하이브리드 방식

### 구조
```
CHANGELOG.md          # 최근 3개월 또는 최신 10개 버전
CHANGELOG_FULL.md     # 전체 이력 (선택적 열람)
archives/changelog/   # 과거 버전 아카이브
```

### 운영 규칙

#### 1. CHANGELOG.md (메인 파일)
- **보관 기준**: 최근 3개월 OR 최신 메이저 버전 2개
- **크기 제한**: 최대 100KB (약 2000줄)
- **용도**: 빠른 참조, 최신 변경사항

#### 2. CHANGELOG_FULL.md (전체 이력)
- **보관 기준**: 모든 이력 누적
- **업데이트**: 분기별 1회
- **용도**: 전체 히스토리 검색

#### 3. 아카이브 전략
```bash
# 분기별 아카이브 (3개월마다)
archives/changelog/
  ├── 2025_Q1.md  (1-3월)
  ├── 2025_Q2.md  (4-6월)
  ├── 2025_Q3.md  (7-9월)
  └── 2025_Q4.md  (10-12월)
```

## 자동화 스크립트

### 1. 일일 변경사항 기록
```bash
# 새로운 항목 추가
python scripts/add_changelog.py "feat: 새 기능 추가"
python scripts/add_changelog.py "fix: 버그 수정" --version "1.2.3"
```

### 2. 자동 아카이브 (3개월마다)
```bash
# CHANGELOG 정리 및 아카이브
python scripts/archive_changelog.py --quarter
```

## 실제 적용 예시

### CHANGELOG.md (가벼운 버전)
```markdown
# Changelog

## [1.2.0] - 2025-08-09
### Added
- 파일 버전 관리 시스템
- DAILY_LOG 자동 업데이트

## [1.1.0] - 2025-08-01
### Fixed
- 인코딩 문제 해결

[이전 버전은 CHANGELOG_FULL.md 참조]
```

### CHANGELOG_FULL.md (전체 버전)
```markdown
# Full Changelog

[모든 버전 히스토리...]
```

## 파일 크기 관리

### 예상 증가율
- **일일 커밋 5개**: 월 150줄 (약 5KB)
- **연간 증가**: 약 60KB
- **5년 후**: 약 300KB (여전히 관리 가능)

### 임계점
- **100KB 초과**: 분기별 아카이브 시작
- **500KB 초과**: 연도별 분리 고려
- **1MB 초과**: 필수 분리

## 결론

### 단기 (1년 미만)
- ✅ 단일 CHANGELOG.md 유지
- ✅ 매주 DAILY_LOG 업데이트

### 중기 (1-3년)
- ✅ CHANGELOG.md + CHANGELOG_FULL.md 분리
- ✅ 분기별 아카이브

### 장기 (3년 이상)
- ✅ 연도별/버전별 완전 분리
- ✅ 검색 인덱스 구축

---

**Policy Created**: 2025-08-09
**Review Period**: 6개월마다 검토
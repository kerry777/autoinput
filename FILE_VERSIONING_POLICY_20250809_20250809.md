# 📁 AutoInput File Versioning Policy

## 파일 버전 관리 정책

### 1. 날짜 버전이 필요한 파일 (날짜 붙임)

#### 작업 문서 (/docs/)
```
filename_YYYYMMDD_YYYYMMDD.md
```
- 타겟 사이트 분석
- 배포 아키텍처 
- 사용자 여정
- 기술 문서
- 학습 자료

**이유**: 시점별 스냅샷이 필요하고, 변경 이력 추적이 중요

#### 프로젝트 정책 문서
- PROJECT_RULES_YYYYMMDD_YYYYMMDD.md
- CLAUDEMD_CONFIG_YYYYMMDD_YYYYMMDD.md

**이유**: 정책 변경 시점 명확히 구분 필요

---

### 2. 고정 파일명 유지 (날짜 안 붙임)

#### 누적 기록 파일
- **DAILY_LOG.md** - 매일 누적 기록
- **CHANGELOG.md** - 버전별 변경사항 누적
- **TODO.md** - 할 일 목록 (계속 업데이트)

**이유**: 하나의 파일에 모든 이력 누적 관리

#### 프로젝트 메타 파일
- **README.md** - 프로젝트 소개 (GitHub 표준)
- **LICENSE** - 라이선스
- **CONTRIBUTING.md** - 기여 가이드
- **CODE_OF_CONDUCT.md** - 행동 규범
- **.gitignore** - Git 제외 파일
- **.editorconfig** - 에디터 설정

**이유**: 표준 파일명 유지 필요

#### 설정 파일
- **package.json**
- **requirements.txt**
- **docker-compose.yml**
- **.env.example**

**이유**: 도구/프레임워크가 특정 이름 요구

---

### 3. 아카이브 폴더 (/archives/)

#### 오래된 버전 보관
```
/archives/
  ├── /changelog/
  │   └── CHANGELOG_2025Q1.md (분기별 백업)
  ├── /docs/
  │   └── old_docs_20250701/
  └── /configs/
      └── deprecated_configs/
```

**이유**: 주 작업 공간 깔끔하게 유지

---

## 📋 Quick Reference

### 새 문서 만들 때
```bash
# 날짜 필요한 문서
python scripts/create_md_with_date.py "guide" "Guide Title" docs

# 날짜 불필요한 문서 (직접 생성)
echo "# TODO List" > TODO.md
```

### 파일 정리할 때
```bash
# 오래된 파일 아카이브
mv docs/old-doc_20250101_20250301.md archives/docs/

# CHANGELOG 분기별 백업
cp CHANGELOG.md archives/changelog/CHANGELOG_2025Q1.md
```

---

## 🎯 판단 기준

### 날짜를 붙여야 할 때:
- ✅ 특정 시점의 상태가 중요한 문서
- ✅ 여러 버전이 동시에 존재할 수 있는 문서
- ✅ 변경 추적이 중요한 설계 문서

### 날짜를 붙이지 말아야 할 때:
- ❌ 누적 기록 문서 (CHANGELOG, DAILY_LOG)
- ❌ 표준 프로젝트 파일 (README, LICENSE)
- ❌ 도구가 특정 이름을 요구하는 파일
- ❌ 항상 최신 버전만 필요한 파일

---

**Policy Version**: 1.0.0
**Created**: 2025-08-09
**Enforcement**: MANDATORY
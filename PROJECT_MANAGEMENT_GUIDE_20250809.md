# 📚 AutoInput 프로젝트 관리 가이드

> 이 문서는 AutoInput 프로젝트의 관리 철학과 실무 방법론을 정의합니다.

---

## 🎯 핵심 관리 원칙

### 1. 문서 우선 (Documentation First)
- **모든 작업은 문서화로 시작**: 코딩 전 설계 문서 작성
- **변경사항 즉시 기록**: DAILY_LOG.md에 매일 업데이트
- **의사결정 근거 보존**: 왜 그런 결정을 했는지 기록

### 2. 추적 가능성 (Traceability)
- **파일명에 날짜 포함**: `filename_YYYYMMDD_YYYYMMDD.md`
- **변경 이력 관리**: Git + 날짜 버전 이중 관리
- **작업 연속성 보장**: 언제든 중단하고 재개 가능

### 3. 자동화 우선 (Automation First)
- **반복 작업 스크립트화**: Python 스크립트로 자동화
- **규칙 자동 적용**: Pre-commit hooks로 표준 강제
- **일관성 유지**: 수동 작업 최소화

---

## 📁 파일 관리 체계

### 디렉토리 구조
```
autoinput/
├── 📝 DAILY_LOG.md          # [고정] 매일 작업 기록 (첫 확인 파일)
├── 📝 CHANGELOG.md          # [고정] 버전별 변경사항
├── 📝 README_*.md           # [날짜] 프로젝트 소개
├── 📂 docs/                 # [날짜] 모든 문서
├── 📂 scripts/              # 자동화 스크립트
├── 📂 archives/             # 오래된 파일 보관
└── 📂 src/                  # 소스 코드
```

### 파일명 규칙

#### 날짜가 붙는 파일
```bash
# 형식: filename_생성일_수정일.md
deployment-guide_20250809_20250815.md

# 생성: python scripts/create_md_with_date.py "filename" "Title"
# 수정: python scripts/update_md_date.py <filepath>
```

#### 고정 이름 파일
- DAILY_LOG.md - 작업 일지
- CHANGELOG.md - 변경 이력
- 설정 파일들 (.env, package.json 등)

---

## 🔄 일상 작업 흐름

### 작업 시작 (오전)
```bash
# 1. 이전 작업 확인
cat DAILY_LOG.md

# 2. TODO 확인
python scripts/taskmaster.py status

# 3. 브랜치 생성
git checkout -b feature/오늘작업
```

### 작업 중
```bash
# 문서 생성 시
python scripts/create_md_with_date.py "api-guide" "API Guide"

# 진행상황 기록
python scripts/update_daily_log.py "구현한 내용"

# MD를 Excel로 변환 (공유용)
python scripts/md2excel.py docs/*.md
```

### 작업 종료 (저녁)
```bash
# 1. 일일 로그 업데이트
python scripts/update_daily_log.py --summary

# 2. 변경사항 커밋
git add .
git commit -m "docs: 오늘 작업 내용 (20250809)"

# 3. 내일 할 일 메모
echo "- [ ] 내일 할 작업" >> DAILY_LOG.md
```

---

## 📊 프로젝트 추적 도구

### 1. DAILY_LOG.md (일일 추적)
- **용도**: "어디까지 했지?" 해결
- **위치**: 프로젝트 루트 (절대 이동 금지)
- **업데이트**: 매일 작업 시작/종료 시

### 2. Taskmaster (작업 관리)
```bash
# PRD 파싱
python scripts/taskmaster.py parse-prd requirements.txt

# 상태 확인
python scripts/taskmaster.py status

# 작업 목록
python scripts/taskmaster.py list
```

### 3. Git + 날짜 버전 (이중 관리)
- **Git**: 상세한 변경 이력
- **날짜**: 한눈에 보이는 시점 정보

---

## 🚀 재개 시나리오

### 며칠 후 프로젝트 재개 시
```bash
# 1. 작업 히스토리 확인
cat DAILY_LOG.md          # 최근 작업 내역
git log --oneline -10     # 최근 커밋

# 2. 현재 상태 파악
python scripts/taskmaster.py status  # 진행 상황
ls -la docs/*_*.md | tail -5        # 최근 문서

# 3. 변경된 파일 확인
git status                # 미완성 작업
git diff                  # 변경 내용

# 4. 작업 재개
python scripts/update_daily_log.py "프로젝트 재개"
```

---

## 📝 문서화 전략

### 문서 작성 시점
1. **사전 문서화**: 구현 전 설계 문서
2. **동시 문서화**: 구현하며 상세 기록
3. **사후 문서화**: 완료 후 정리

### 문서 종류
- **설계 문서**: 구현 전 작성 (what & why)
- **구현 문서**: 구현 중 작성 (how)
- **사용 문서**: 구현 후 작성 (usage)

---

## 🔧 자동화 스크립트

### 핵심 스크립트
| 스크립트 | 용도 | 사용 빈도 |
|---------|------|-----------|
| create_md_with_date.py | 새 문서 생성 | 자주 |
| update_daily_log.py | 일일 로그 | 매일 |
| md2excel.py | Excel 변환 | 필요시 |
| taskmaster.py | 작업 관리 | 매일 |

### Pre-commit Hooks
- 파일명 규칙 검증
- 날짜 자동 업데이트
- 코드 품질 검사

---

## 💡 베스트 프랙티스

### DO ✅
1. 매일 DAILY_LOG 업데이트
2. 의미 있는 커밋 메시지
3. 문서 먼저, 코드 나중
4. 자동화 도구 활용
5. 정기적 아카이브

### DON'T ❌
1. DAILY_LOG 파일명 변경
2. 날짜 없이 문서 생성
3. 변경사항 미기록
4. 수동으로 날짜 관리
5. 오래된 파일 방치

---

## 📈 성공 지표

### 일일 지표
- [ ] DAILY_LOG 업데이트 여부
- [ ] 의미 있는 커밋 1개 이상
- [ ] 문서 1개 이상 작성/수정

### 주간 지표
- [ ] 주요 기능 1개 완성
- [ ] 테스트 커버리지 유지
- [ ] 문서 최신화

### 월간 지표
- [ ] 마일스톤 달성
- [ ] 아카이브 정리
- [ ] 회고 및 개선

---

## 🔍 문제 해결

### "어디까지 했지?"
→ `cat DAILY_LOG.md`

### "이 파일 언제 만들었지?"
→ 파일명의 첫 번째 날짜 확인

### "뭐가 바뀌었지?"
→ `git diff` 또는 파일명의 두 번째 날짜

### "할 일이 뭐였지?"
→ `python scripts/taskmaster.py list`

---

## 🎓 팀 온보딩

### 신규 참여자 가이드
1. DAILY_LOG.md 읽기
2. PROJECT_RULES_*.md 숙지
3. 최근 docs/ 파일 3개 리뷰
4. scripts/ 사용법 학습
5. 첫 문서 작성 (with date)

---

**Guide Version**: 1.0.0
**Created**: 2025-08-09
**Philosophy**: "기록하지 않으면 잊혀진다"

> 💭 핵심 메시지: 며칠 후 돌아와도 DAILY_LOG.md만 보면 바로 이어서 작업 가능!
# 📋 Taskmaster 시스템 가이드

AutoInput 프로젝트의 작업 관리 시스템 사용 가이드입니다.

## 🎯 개요

Taskmaster는 PRD(Product Requirements Document)를 자동으로 파싱하여 체계적인 작업 목록으로 변환하고 관리하는 시스템입니다.

## 🛠️ 사용 가능한 도구

### 1. PRD Parser (`scripts/simple_prd_parser.py`)

PRD 문서를 파싱하여 작업 목록으로 변환합니다.

```bash
# 기본 사용법
python scripts/simple_prd_parser.py <prd_file> [output_file]

# 예시
python scripts/simple_prd_parser.py sample_prd.txt parsed_tasks.json
```

**지원 형식:**
- `.txt` - 텍스트 형식 PRD
- `.md` - Markdown 형식 PRD
- `.yaml` / `.yml` - YAML 형식 PRD
- `.json` - JSON 형식 PRD

### 2. Advanced PRD Parser (`scripts/parse_prd.py`)

고급 기능을 제공하는 PRD 파서입니다. (Rich 라이브러리 필요)

```bash
# 설치
pip install rich click

# 사용법
python scripts/parse_prd.py <prd_file> -o <output> -f <format> -v

# 형식 옵션
-f taskmaster  # Taskmaster 형식 (기본)
-f jira        # JIRA 형식
-f github      # GitHub Issues 형식
```

### 3. Taskmaster CLI (`scripts/taskmaster.py`)

작업 관리 CLI 도구입니다.

```bash
# 프로젝트 상태 확인
python scripts/taskmaster.py status

# 작업 트리 표시
python scripts/taskmaster.py list

# 로드맵 보기
python scripts/taskmaster.py roadmap

# 다음 추천 작업
python scripts/taskmaster.py next

# 작업 상태 업데이트
python scripts/taskmaster.py update <task_id> <status>

# 데이터 초기화
python scripts/taskmaster.py init

# 데이터 내보내기
python scripts/taskmaster.py export -o backup.json
```

## 📄 PRD 작성 가이드

### 텍스트 형식 PRD 구조

```text
제목

개요:
프로젝트 개요 설명

목적:
프로젝트 목적 설명

기능 요구사항:

1. 첫 번째 요구사항
   - 세부 항목 1
   - 세부 항목 2
   Priority: Critical

2. 두 번째 요구사항
   - 세부 항목 1
   - 세부 항목 2
   Priority: High

비기능 요구사항:

1. 성능 요구사항
   - 응답 시간: 200ms 이내
   - 동시 사용자: 1000명

마일스톤:
1. Phase 1 (4주): 기본 기능 구현
2. Phase 2 (6주): 고급 기능 구현
```

### 우선순위 레벨

- **P0 (Critical)**: 필수 기능, 즉시 구현 필요
- **P1 (High)**: 중요 기능, 초기 릴리스 포함
- **P2 (Medium)**: 일반 기능, 계획된 릴리스
- **P3 (Low)**: 선택 기능, 향후 고려

## 📊 생성되는 작업 구조

### Taskmaster 형식

```json
{
  "project": "프로젝트명",
  "version": "버전",
  "phases": [
    {
      "id": "phase-id",
      "name": "Phase 이름",
      "priority": "우선순위",
      "tasks": [
        {
          "id": "TASK-1",
          "name": "작업명",
          "status": "pending",
          "type": "functional",
          "subtasks": 5
        }
      ]
    }
  ],
  "statistics": {
    "total_tasks": 95,
    "priority_distribution": {
      "P0": 3,
      "P1": 4,
      "P2": 8
    }
  }
}
```

## 🔄 워크플로우

### 1단계: PRD 작성
```text
sample_prd.txt 파일에 요구사항 작성
```

### 2단계: PRD 파싱
```bash
python scripts/simple_prd_parser.py sample_prd.txt parsed_tasks.json
```

### 3단계: 작업 관리
```bash
# 상태 확인
python scripts/taskmaster.py status

# 작업 목록 보기
python scripts/taskmaster.py list

# 작업 시작
python scripts/taskmaster.py update TASK-1 in_progress

# 작업 완료
python scripts/taskmaster.py update TASK-1 completed
```

## 🎨 통합 시나리오

### GitHub Issues 생성

1. PRD를 GitHub 형식으로 파싱:
```bash
python scripts/parse_prd.py sample_prd.txt -f github
```

2. 생성된 JSON을 GitHub API로 전송:
```bash
# GitHub CLI 사용
gh issue create --title "작업명" --body "@parsed_tasks_github.json"
```

### JIRA 티켓 생성

1. PRD를 JIRA 형식으로 파싱:
```bash
python scripts/parse_prd.py sample_prd.txt -f jira
```

2. JIRA API로 벌크 임포트

## 📈 프로젝트 메트릭

파싱된 작업 통계를 활용한 프로젝트 관리:

- **총 작업 수**: 프로젝트 규모 파악
- **우선순위 분포**: 리소스 할당 계획
- **타입별 분포**: 팀 역량 매칭
- **예상 시간**: 일정 계획 수립

## 🚀 고급 기능

### 자동화 스크립트

```python
# auto_update.py
import json
import subprocess

# PRD 파싱
subprocess.run(['python', 'scripts/simple_prd_parser.py', 'prd.txt'])

# 작업 로드
with open('parsed_tasks.json', 'r') as f:
    data = json.load(f)

# 자동 우선순위 할당
for phase in data['phases']:
    if 'Critical' in phase['name']:
        # Critical 작업 자동 시작
        for task in phase['tasks']:
            subprocess.run(['python', 'scripts/taskmaster.py', 
                          'update', task['id'], 'in_progress'])
```

### CI/CD 통합

```yaml
# .github/workflows/taskmaster.yml
name: Taskmaster Update

on:
  push:
    paths:
      - 'docs/PRD.md'

jobs:
  parse-prd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Parse PRD
        run: |
          python scripts/simple_prd_parser.py docs/PRD.md
      
      - name: Create Issues
        run: |
          python scripts/create_github_issues.py parsed_tasks.json
```

## 📝 베스트 프랙티스

1. **PRD 구조화**: 명확한 섹션 구분과 일관된 포맷 사용
2. **우선순위 명시**: 각 요구사항에 우선순위 명확히 표시
3. **정기 업데이트**: 주기적으로 작업 상태 업데이트
4. **버전 관리**: PRD와 작업 목록 버전 관리
5. **팀 동기화**: 생성된 작업을 팀 도구와 연동

## 🔧 문제 해결

### 인코딩 오류
Windows에서 이모지 출력 오류 발생 시:
```python
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

### 파싱 오류
PRD 형식이 올바른지 확인:
- 섹션 헤더가 명확한지
- 번호 형식이 일관되는지 (1. 또는 1))
- 우선순위 키워드가 올바른지

## 📚 참고 자료

- [Taskmaster.ai](https://taskmaster.ai) - 작업 관리 시스템 참고
- [GitHub Projects](https://github.com/features/projects) - 프로젝트 관리
- [JIRA API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/) - JIRA 연동
- [Semantic Versioning](https://semver.org/) - 버전 관리

---

*최종 업데이트: 2025-08-09*
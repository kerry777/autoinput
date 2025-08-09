# Changelog

모든 주요 변경사항이 이 파일에 기록됩니다.

이 프로젝트는 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

### 추가예정
- 고급 셀렉터 자가치유 시스템
- 실시간 모니터링 대시보드
- 다중 브라우저 동시 실행 지원
- AI 기반 시나리오 자동 생성

## [0.1.0] - 2025-08-09

### 추가됨 ✨
- 프로젝트 초기 구조 설정
- Playwright 기반 자동화 엔진 구현
- FastAPI 웹 서버 구성
- Docker 및 Docker Compose 설정
- 기본 문서 작성 (README, CONTRIBUTING, CODE_OF_CONDUCT)
- GitHub 이슈 및 PR 템플릿 추가
- 개발 가이드 문서 작성

### 핵심 기능
- **AutomationEngine**: Playwright 기반 브라우저 자동화
- **설정 관리**: Pydantic Settings를 이용한 환경 변수 관리
- **프로젝트 구조**: 모듈화된 디렉토리 구조
- **보안**: 환경 변수 기반 민감 정보 관리

### 개발 환경
- Python 3.11+ 지원
- PostgreSQL 데이터베이스 연동
- 포괄적인 의존성 관리 (requirements.txt, pyproject.toml)

### 문서화
- 상세한 README.md
- 기여 가이드라인 (CONTRIBUTING.md)
- 개발자를 위한 개발 가이드 (docs/development.md)
- 행동 강령 (CODE_OF_CONDUCT.md)

### 인프라
- Docker 컨테이너화
- Docker Compose 오케스트레이션
- Git 버전 관리 (.gitignore)
- 환경 변수 템플릿 (.env.example)

---

## 버전 관리 정책

### 버전 형식
`MAJOR.MINOR.PATCH`

- **MAJOR**: 호환되지 않는 API 변경
- **MINOR**: 하위 호환 가능한 기능 추가
- **PATCH**: 하위 호환 가능한 버그 수정

### 변경 유형
- ✨ **추가됨** (Added): 새로운 기능
- 🔄 **변경됨** (Changed): 기존 기능의 변경
- ⚠️ **Deprecated**: 향후 제거될 기능
- 🗑️ **제거됨** (Removed): 제거된 기능
- 🐛 **수정됨** (Fixed): 버그 수정
- 🔒 **보안** (Security): 보안 취약점 수정

### 태그 규칙
- 릴리스 태그: `v0.1.0`
- 프리릴리스 태그: `v0.1.0-rc.1`
- 베타 버전: `v0.1.0-beta.1`
- 알파 버전: `v0.1.0-alpha.1`

---

## 향후 로드맵

### v0.2.0 (예정)
- [ ] 웹 UI 콘솔 구현
- [ ] 스케줄러 시스템 추가
- [ ] 로그 관리 시스템 개선
- [ ] 데이터베이스 마이그레이션 시스템

### v0.3.0 (예정)
- [ ] 장기요양보험 포털 전용 모듈
- [ ] HWP 파일 파싱 기능
- [ ] 엑셀 데이터 검증 시스템
- [ ] 이메일 알림 기능

### v1.0.0 (예정)
- [ ] 프로덕션 준비 완료
- [ ] 완전한 테스트 커버리지
- [ ] 성능 최적화
- [ ] 보안 강화
- [ ] 사용자 인증 시스템
- [ ] 라이선스 관리 시스템

---

## 기여자

- 프로젝트 관리자: @maintainer
- 주요 기여자: 
  - @contributor1
  - @contributor2

## 링크

- [GitHub Repository](https://github.com/yourusername/autoinput)
- [이슈 트래커](https://github.com/yourusername/autoinput/issues)
- [프로젝트 위키](https://github.com/yourusername/autoinput/wiki)
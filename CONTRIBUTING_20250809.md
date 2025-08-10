# 🤝 AutoInput 기여 가이드

AutoInput 프로젝트에 기여해주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

## 📋 목차

- [행동 강령](#행동-강령)
- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코딩 스타일](#코딩-스타일)
- [커밋 컨벤션](#커밋-컨벤션)
- [PR 프로세스](#pr-프로세스)
- [이슈 리포팅](#이슈-리포팅)
- [문서화](#문서화)
- [테스트](#테스트)
- [라이선스](#라이선스)

## 행동 강령

이 프로젝트는 [Code of Conduct](CODE_OF_CONDUCT.md)를 따릅니다. 프로젝트에 참여함으로써, 이 행동 강령을 준수하는 것에 동의하는 것으로 간주됩니다.

## 🚀 기여 방법

### 1. 이슈 확인 및 생성

- 기존 이슈를 먼저 확인해주세요
- 새로운 기능이나 버그를 발견했다면 이슈를 생성해주세요
- 이슈 템플릿을 사용하여 명확한 설명을 제공해주세요

### 2. 포크 및 브랜치 생성

```bash
# 저장소 포크
# GitHub에서 Fork 버튼 클릭

# 포크한 저장소 클론
git clone https://github.com/your-username/autoinput.git
cd autoinput

# 업스트림 저장소 추가
git remote add upstream https://github.com/original-owner/autoinput.git

# 새 브랜치 생성
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/your-bug-fix
```

### 3. 브랜치 네이밍 규칙

- `feature/기능명` - 새로운 기능 추가
- `fix/버그명` - 버그 수정
- `docs/문서명` - 문서 개선
- `refactor/모듈명` - 코드 리팩토링
- `test/테스트명` - 테스트 추가/수정
- `chore/작업명` - 빌드, 설정 등 기타 작업

## 💻 개발 환경 설정

### 필수 요구사항

- Python 3.11 이상
- Git
- Docker (선택사항)

### 환경 설정 단계

1. **가상환경 생성 및 활성화**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

2. **의존성 설치**

```bash
# 개발 의존성 포함 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 또는 Poetry 사용
poetry install
```

3. **Playwright 브라우저 설치**

```bash
playwright install chromium firefox
```

4. **Pre-commit 훅 설정**

```bash
pre-commit install
```

5. **환경 변수 설정**

```bash
cp .env.example .env
# .env 파일을 열어 필요한 값 설정
```

## 🎨 코딩 스타일

### Python 코드 스타일

- **PEP 8** 준수
- **Black** 포매터 사용 (line-length: 100)
- **Ruff** 린터 사용
- **Type hints** 사용 권장

### 코드 포맷팅

```bash
# 코드 포맷팅
black src/ tests/

# 린트 검사
ruff check src/ tests/

# 타입 체크
mypy src/

# 모든 검사 한번에 실행
make lint  # Makefile이 있는 경우
```

### 코드 스타일 예시

```python
"""모듈 설명 docstring"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """클래스 설명 docstring
    
    Attributes:
        name: 이름
        value: 값
    """
    
    def __init__(self, name: str, value: Optional[int] = None) -> None:
        """초기화 메서드
        
        Args:
            name: 객체 이름
            value: 초기값 (선택사항)
        """
        self.name = name
        self.value = value
    
    async def process_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """데이터 처리 메서드
        
        Args:
            data: 처리할 데이터 리스트
            
        Returns:
            처리된 결과 딕셔너리
            
        Raises:
            ValueError: 잘못된 데이터 형식
        """
        if not data:
            raise ValueError("데이터가 비어있습니다")
        
        # 처리 로직
        result = {"processed": len(data)}
        logger.info(f"Processed {len(data)} items")
        
        return result
```

## 📝 커밋 컨벤션

### 커밋 메시지 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 커밋 타입

- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅, 세미콜론 누락 등
- `refactor`: 코드 리팩토링
- `perf`: 성능 개선
- `test`: 테스트 추가/수정
- `chore`: 빌드, 패키지 매니저 설정 등
- `ci`: CI 설정 파일 수정
- `revert`: 커밋 되돌리기

### 커밋 예시

```bash
# 좋은 예시
git commit -m "feat(scraper): Playwright 기반 동적 페이지 스크래핑 기능 추가"
git commit -m "fix(auth): 로그인 세션 만료 시 재인증 처리 수정"
git commit -m "docs(readme): 설치 가이드 및 사용 예제 추가"

# 나쁜 예시
git commit -m "버그 수정"
git commit -m "업데이트"
git commit -m "작업 완료"
```

### 커밋 메시지 본문 작성 팁

```bash
git commit

# 에디터에서 작성
feat(parser): HWP 파일 파싱 기능 구현

- pyhwp 라이브러리를 사용한 HWP 파일 읽기
- PDF 변환 후 텍스트 추출 옵션 추가
- 테이블 데이터 정규화 처리
- 인코딩 오류 예외 처리 추가

Closes #123
```

## 🔄 PR 프로세스

### 1. PR 제출 전 체크리스트

- [ ] 최신 main 브랜치와 동기화
- [ ] 모든 테스트 통과
- [ ] 코드 스타일 검사 통과
- [ ] 문서 업데이트 (필요시)
- [ ] CHANGELOG.md 업데이트

### 2. 동기화 방법

```bash
# 업스트림 변경사항 가져오기
git fetch upstream
git checkout main
git merge upstream/main

# 작업 브랜치 리베이스
git checkout feature/your-feature
git rebase main
```

### 3. PR 제출

1. GitHub에서 Pull Request 생성
2. PR 템플릿 양식 작성
3. 리뷰어 지정 (필요시)
4. 라벨 추가

### 4. 코드 리뷰 대응

- 리뷰 코멘트에 적극적으로 응답
- 요청된 변경사항 수정
- 수정 후 리뷰어에게 알림

## 🐛 이슈 리포팅

### 버그 리포트

버그를 발견하면 다음 정보를 포함해주세요:

1. **환경 정보**
   - OS 및 버전
   - Python 버전
   - 브라우저 종류 및 버전

2. **재현 단계**
   - 버그를 재현하는 구체적인 단계
   - 예상 동작
   - 실제 동작

3. **로그 및 스크린샷**
   - 에러 메시지
   - 관련 로그
   - 스크린샷 (UI 관련)

### 기능 제안

새로운 기능을 제안할 때:

1. **사용 사례** 설명
2. **예상 동작** 설명
3. **대안** 고려사항
4. **추가 컨텍스트** 제공

## 📚 문서화

### 문서 작성 가이드

- 명확하고 간결한 한국어 사용
- 코드 예제 포함
- 마크다운 문법 준수
- 스크린샷 활용 (UI 관련)

### 문서 종류

1. **코드 문서화**
   - Docstring 작성 (Google 스타일)
   - 타입 힌트 사용
   - 인라인 주석 (복잡한 로직)

2. **API 문서**
   - OpenAPI/Swagger 스펙
   - 엔드포인트 설명
   - 요청/응답 예제

3. **사용자 가이드**
   - 설치 가이드
   - 사용 예제
   - FAQ

## 🧪 테스트

### 테스트 작성

```python
"""테스트 모듈 예시"""

import pytest
from src.core.automation import AutomationEngine


class TestAutomationEngine:
    """AutomationEngine 테스트"""
    
    @pytest.fixture
    async def engine(self):
        """테스트용 엔진 fixture"""
        engine = AutomationEngine()
        await engine.start()
        yield engine
        await engine.stop()
    
    async def test_navigate(self, engine):
        """페이지 네비게이션 테스트"""
        await engine.navigate("https://example.com")
        assert engine.page.url == "https://example.com/"
    
    async def test_fill_form(self, engine):
        """폼 입력 테스트"""
        # 테스트 구현
        pass
```

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 특정 파일 테스트
pytest tests/test_automation.py

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 마커 테스트만 실행
pytest -m "not slow"
```

### 테스트 커버리지 목표

- 전체 커버리지: 80% 이상
- 핵심 모듈: 90% 이상
- 새로운 코드: 95% 이상

## 🔐 보안

### 보안 이슈 보고

보안 취약점을 발견한 경우:

1. **공개 이슈로 보고하지 마세요**
2. security@example.com으로 이메일 보내주세요
3. 48시간 내 응답을 받으실 수 있습니다

### 보안 체크리스트

- [ ] 민감한 정보 하드코딩 금지
- [ ] 환경 변수 사용
- [ ] SQL 인젝션 방지
- [ ] XSS 방지
- [ ] CSRF 토큰 사용
- [ ] 적절한 인증/인가

## 📦 릴리스 프로세스

### 버전 관리

[Semantic Versioning](https://semver.org/) 사용:
- MAJOR.MINOR.PATCH (예: 1.2.3)
- MAJOR: 호환되지 않는 API 변경
- MINOR: 하위 호환 기능 추가
- PATCH: 하위 호환 버그 수정

### 릴리스 체크리스트

1. [ ] 모든 테스트 통과
2. [ ] CHANGELOG.md 업데이트
3. [ ] 버전 번호 업데이트
4. [ ] 문서 업데이트
5. [ ] 태그 생성
6. [ ] 릴리스 노트 작성

## 🎯 개발 팁

### 유용한 명령어

```bash
# 로컬 서버 실행
uvicorn src.main:app --reload

# Docker 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 데이터베이스 마이그레이션
alembic upgrade head

# 새 마이그레이션 생성
alembic revision --autogenerate -m "설명"
```

### 디버깅 팁

1. **로그 레벨 조정**: `LOG_LEVEL=DEBUG`
2. **브라우저 헤드리스 모드 끄기**: `HEADLESS=false`
3. **Playwright Inspector 사용**: `PWDEBUG=1`
4. **VS Code 디버거 설정 사용**

## 📧 연락처

- 프로젝트 메인테이너: @maintainer
- 이메일: contact@example.com
- Discord: [참여 링크](https://discord.gg/example)

## 📄 라이선스

이 프로젝트에 기여함으로써, 귀하의 기여가 프로젝트의 라이선스(MIT)에 따라 배포되는 것에 동의합니다.

---

🙏 **감사합니다!** AutoInput을 더 나은 프로젝트로 만들어주셔서 감사합니다!
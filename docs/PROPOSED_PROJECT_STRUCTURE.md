# 제안하는 프로젝트 구조 재편안

현재 평면적이고 파일이 산재된 구조를 **사이트별 모듈화** 구조로 개편

## 🔄 현재 문제점

### 현재 구조
```
autoinput/
├── bizmeka_automation/          # 한 사이트만의 폴더
│   ├── manual_login.py
│   ├── auto_access.py  
│   ├── mail_scraper_final.py
│   ├── mail_scraper_working.py
│   ├── mail_scraper_devtools.py
│   ├── mail_scraper_simple.py     # 너무 많은 버전들
│   ├── mail_scraper_correct.py
│   ├── mail_scraper_dynamic.py
│   ├── mail_scraper_manual.py
│   ├── mail_scraper_interactive.py
│   ├── mail_scraper_final_correct.py
│   └── ...
├── flutter_login_automation/    # 또 다른 평면적 폴더
├── hwp_conversion/             # 또 다른 평면적 폴더
└── docs/                      # 문서도 섞여있음
```

### 문제점
- ❌ 파일명이 너무 길고 버전별로 중복
- ❌ 사이트별 관련 파일들이 뭉쳐있지 않음  
- ❌ 공통 유틸리티와 사이트별 로직이 섞임
- ❌ 테스트, 설정, 문서가 따로 놀고 있음
- ❌ 확장시 더 복잡해질 구조

---

## ✅ 제안하는 새로운 구조

### 사이트별 모듈화 구조
```
autoinput/
├── 📁 sites/                    # 사이트별 모듈 
│   ├── 📁 bizmeka/             # 비즈메카 전용 폴더
│   │   ├── 📄 __init__.py
│   │   ├── 📁 auth/            # 인증 관련
│   │   │   ├── login.py        # 수동/자동 로그인
│   │   │   └── cookies.py      # 쿠키 관리
│   │   ├── 📁 scrapers/        # 스크래퍼들
│   │   │   ├── mail.py         # 메일 스크래퍼 (최종 버전만)
│   │   │   └── base.py         # 공통 스크래퍼 로직
│   │   ├── 📁 config/          # 설정 파일
│   │   │   ├── settings.json
│   │   │   └── selectors.json  # 선택자 모음
│   │   ├── 📁 tests/           # 테스트
│   │   │   ├── test_auth.py
│   │   │   └── test_scraper.py
│   │   ├── 📁 data/            # 데이터 폴더
│   │   │   └── cookies.json
│   │   └── 📁 docs/            # 사이트별 문서
│   │       ├── README.md
│   │       └── api_reference.md
│   │
│   ├── 📁 longtermcare/        # 장기요양보험 사이트
│   │   ├── 📁 auth/
│   │   ├── 📁 scrapers/
│   │   ├── 📁 config/
│   │   └── 📁 docs/
│   │
│   └── 📁 hwp_sites/           # HWP 관련 사이트들
│       ├── 📁 auth/
│       ├── 📁 scrapers/
│       └── 📁 converters/
│
├── 📁 core/                     # 공통 핵심 로직
│   ├── 📄 __init__.py
│   ├── 📁 base/                # 기본 클래스들
│   │   ├── scraper.py          # BaseScraper 클래스
│   │   ├── authenticator.py    # BaseAuth 클래스
│   │   └── browser.py          # Browser 관리
│   ├── 📁 utils/               # 유틸리티
│   │   ├── cookies.py          # 쿠키 관리 유틸
│   │   ├── popups.py           # 팝업 처리 유틸
│   │   ├── navigation.py       # 네비게이션 유틸
│   │   └── patterns.py         # 패턴 라이브러리
│   └── 📁 exceptions/          # 커스텀 예외
│       └── scraping.py
│
├── 📁 tools/                    # 개발 도구
│   ├── 📄 site_generator.py    # 새 사이트 모듈 생성기
│   ├── 📄 pattern_analyzer.py  # 패턴 분석 도구  
│   └── 📄 performance_monitor.py
│
├── 📁 tests/                    # 통합 테스트
│   ├── 📁 integration/
│   └── 📁 e2e/
│
├── 📁 docs/                     # 프로젝트 전체 문서
│   ├── 📁 guides/              # 가이드 문서
│   ├── 📁 patterns/            # 패턴 라이브러리 문서
│   └── 📁 api/                 # API 문서
│
├── 📁 scripts/                  # 실행 스크립트
│   ├── 📄 run_bizmeka_mail.py  # 비즈메카 메일 실행
│   ├── 📄 run_hwp_convert.py   # HWP 변환 실행
│   └── 📄 setup_site.py        # 새 사이트 설정
│
└── 📁 data/                     # 공통 데이터
    ├── 📁 logs/
    ├── 📁 outputs/
    └── 📁 temp/
```

---

## 🔧 구체적인 파일 구성 예시

### sites/bizmeka/ 구조
```python
# sites/bizmeka/auth/login.py
class BizmekaAuth(BaseAuth):
    def __init__(self):
        self.config = load_config('bizmeka')
    
    async def manual_login(self):
        """수동 로그인 + 쿠키 저장"""
        pass
    
    async def auto_login(self):
        """쿠키 기반 자동 로그인"""  
        pass

# sites/bizmeka/scrapers/mail.py  
class BizmekaMailScraper(BaseScraper):
    def __init__(self):
        super().__init__('bizmeka')
    
    async def scrape_mails(self, pages=3):
        """메일 스크래핑 (최종 완성 버전만)"""
        pass
```

### core/base/ 공통 클래스
```python
# core/base/scraper.py
class BaseScraper:
    def __init__(self, site_name):
        self.site_name = site_name
        self.config = load_site_config(site_name)
        self.popup_handler = PopupHandler()
        self.navigator = Navigator()
    
    async def close_popups(self):
        """공통 팝업 처리 로직"""
        return await self.popup_handler.close_all(self.page)
```

### 실행 스크립트 간소화
```python
# scripts/run_bizmeka_mail.py
from sites.bizmeka.auth.login import BizmekaAuth
from sites.bizmeka.scrapers.mail import BizmekaMailScraper

async def main():
    # 간단한 실행
    auth = BizmekaAuth()
    await auth.ensure_login()  # 자동으로 쿠키 확인/로그인
    
    scraper = BizmekaMailScraper()
    results = await scraper.scrape_mails(pages=3)
    
    print(f"수집 완료: {len(results)}개")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📈 새 구조의 장점

### 1. **모듈성**
- 사이트별로 완전히 분리된 모듈
- 한 사이트 작업이 다른 사이트에 영향 없음
- 독립적인 테스트와 배포 가능

### 2. **재사용성** 
- core/에 공통 로직 모아서 재사용
- 새로운 사이트 추가시 core/ 활용
- 패턴 라이브러리로 빠른 개발

### 3. **유지보수성**
- 파일 위치가 직관적이고 예측 가능
- 버전 관리가 명확 (최종 버전만 유지)
- 사이트별 문서화 체계적 관리

### 4. **확장성**
- 새 사이트 추가시 tools/site_generator.py 실행
- 표준화된 구조로 일관성 유지
- 팀 협업시 혼란 최소화

### 5. **성능**
- 불필요한 파일 로딩 방지
- 사이트별 최적화된 설정
- 명확한 의존성 관리

---

## 🚀 마이그레이션 계획

### Phase 1: 구조 생성
1. 새로운 폴더 구조 생성
2. core/ 모듈 개발
3. sites/bizmeka/ 모듈 개발

### Phase 2: 파일 이관
1. bizmeka_automation/ → sites/bizmeka/로 이관
2. 중복 파일 정리 (최종 버전만 유지)
3. 공통 로직 core/로 추출

### Phase 3: 검증 및 최적화  
1. 기능 테스트 및 검증
2. 문서 업데이트
3. 성능 최적화

### Phase 4: 확장
1. 다른 사이트 모듈화
2. 자동화 도구 개발
3. 패턴 라이브러리 확장

이 구조로 가면 **"한 눈에 보이는 깔끔함"**과 **"확장 용이성"**을 모두 얻을 수 있습니다! 어떻게 보시나요? 🎯
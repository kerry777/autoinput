# 웹 스크래핑 노하우 및 문제 해결 가이드

## 📚 프로젝트: 장기요양보험 사이트 스크래핑

### 1. 페이지네이션 처리

#### 문제점
- 동적 페이지 로딩으로 인한 데이터 누락
- 페이지 전환 시 타이밍 이슈

#### 해결책
```python
# 페이지 로딩 완료 대기
await page.wait_for_load_state('networkidle')
await page.wait_for_timeout(2000)  # 추가 안정화 시간

# 페이지별 데이터를 별도 시트로 저장
async def save_to_excel(self, page_num=None):
    with pd.ExcelWriter(excel_file, mode='a', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=f'페이지_{page_num}', index=False)
```

#### 핵심 노하우
- `networkidle` 상태 대기 + 추가 timeout으로 안정성 확보
- 각 페이지 데이터를 별도 Excel 시트로 저장하여 데이터 무결성 보장

---

### 2. 게시판 첨부파일 다운로드

#### 문제점 1: 게시물 목록에서 상세 페이지 접근 실패
```python
# 실패한 접근 방법
await page.locator('tr.notice_off').first.click()  # 요소를 찾을 수 없음
```

#### 해결책: 직접 URL 패턴 분석 및 활용
```python
# HTML 구조 분석
# <a href="?searchType=ALL&searchWord=&boardId=60093&act=VIEW">

# 직접 URL 생성
detail_url = f"https://longtermcare.or.kr/npbs/cms/board/board/Board.jsp?"
detail_url += f"communityKey={communityKey}&boardId={boardId}&act=VIEW"
```

#### 문제점 2: Community Key 오류
- 잘못된 community key 사용 (B0008, B0009 등)
- 각 게시판마다 고유한 community key 필요

#### 해결책: 정확한 매핑 테이블 구성
```python
boards = {
    '서식자료실': {'communityKey': 'B0017', 'boardId': '60123'},
    '법령자료실': {'communityKey': 'B0018', 'boardId': '60115'},
    '통계자료실': {'communityKey': 'B0020', 'boardId': '60076'},
    '자주하는질문': {'communityKey': 'B0019', 'boardId': '60184'}
}
```

#### 핵심 노하우
- **URL 패턴 분석이 핵심**: 브라우저 개발자 도구로 실제 URL 구조 파악
- **직접 URL 접근**: 복잡한 DOM 네비게이션보다 직접 URL 생성이 안정적
- **매개변수 매핑**: communityKey와 boardId의 정확한 매핑 필수

---

### 3. 다운로드 처리

#### 문제점
- 다운로드 타이밍 불일치
- 파일명 인코딩 문제

#### 해결책
```python
# expect_download 패턴 사용
async with page.expect_download(timeout=30000) as download_info:
    await file_link.click()

download = await download_info.value
suggested_name = download.suggested_filename

# 파일명 안전 처리
import re
safe_name = re.sub(r'[<>:"/\\|?*]', '_', suggested_name)[:100]
```

#### 핵심 노하우
- `expect_download()` 컨텍스트 매니저로 다운로드 보장
- 파일명 특수문자 처리로 저장 오류 방지
- 타임아웃 설정으로 무한 대기 방지

---

### 4. 동적 콘텐츠 처리

#### 문제점
- AJAX 로딩 콘텐츠 미표시
- 팝업 창 처리 실패

#### 해결책
```python
# 팝업 처리
async with context.expect_page() as new_page_info:
    await page.click('#popup_button')
popup = await new_page_info.value
await popup.wait_for_load_state('domcontentloaded')

# AJAX 콘텐츠 대기
await page.wait_for_selector('.dynamic-content', state='visible')
```

#### 핵심 노하우
- 새 페이지/팝업은 `expect_page()` 사용
- 동적 콘텐츠는 selector의 `state='visible'` 옵션 활용

---

### 5. 셀렉터 전략

#### 문제점
- 셀렉터 변경으로 인한 스크립트 실패
- 복잡한 DOM 구조

#### 해결책: 다중 셀렉터 폴백 전략
```python
# 다양한 셀렉터 시도
file_selectors = [
    'a[href*="/Download.jsp"]',  # 가장 구체적
    'a[href*="download"]',        # 일반적
    'a[onclick*="download"]',     # 이벤트 기반
    'a[href$=".hwp"]',           # 확장자 기반
    'a[href$=".pdf"]'
]

for selector in file_selectors:
    links = await page.query_selector_all(selector)
    if links:
        break
```

#### 핵심 노하우
- **우선순위 셀렉터 리스트**: 구체적 → 일반적 순서
- **폴백 메커니즘**: 첫 번째 실패 시 대안 시도
- **확장자 기반 셀렉터**: 파일 다운로드 링크 식별에 유용

---

### 6. 에러 처리 및 디버깅

#### 문제점
- 에러 발생 위치 파악 어려움
- 재현 가능한 테스트 환경 부재

#### 해결책
```python
# 스크린샷 저장
await page.screenshot(path=f'logs/error_{timestamp}.png')

# 페이지 HTML 저장
content = await page.content()
with open(f'logs/page_{timestamp}.html', 'w', encoding='utf-8') as f:
    f.write(content)

# 상세 로깅
print(f"[{datetime.now()}] Selector: {selector} - Found: {len(elements)} elements")
```

#### 핵심 노하우
- **증거 수집**: 에러 시점의 스크린샷과 HTML 저장
- **타임스탬프 로깅**: 문제 발생 시점 정확히 기록
- **headless=False**: 개발 중에는 브라우저 표시로 문제 확인

---

---

### 7. iframe 처리

#### 문제점
- 게시판 콘텐츠가 iframe 내부에 있어 접근 불가
- 일반 selector로 테이블을 찾을 수 없음

#### 해결책
```python
# iframe 확인 및 전환
iframes = await page.query_selector_all('iframe')
if iframes:
    frame = await iframes[0].content_frame()
    if frame:
        page = frame  # 이후 모든 작업은 frame에서 수행
        await page.wait_for_timeout(2000)
```

#### 핵심 노하우
- **iframe 우선 확인**: 콘텐츠가 보이지 않으면 iframe 존재 의심
- **content_frame() 사용**: iframe 내부 DOM에 접근
- **컨텍스트 전환**: frame을 page로 재할당하여 이후 작업 단순화

---

### 8. 게시물 메타데이터 + 첨부파일 통합 수집

#### 문제점
- 게시물 정보와 첨부파일을 별도로 관리하면 연결 어려움
- 대량 데이터 수집 시 추적 관리 필요

#### 해결책
```python
# 통합 데이터 구조
post_data = {
    '게시판': board_name,
    '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    '순번': idx,
    '번호': board_num,
    '제목': title,
    '작성자': author,
    '작성일': date,
    '조회수': views,
    '내용': content[:200],  # 요약
    '첨부파일수': file_count,
    '첨부파일목록': ' | '.join(file_names),
    '첨부파일1': file1_name,
    '파일경로1': file1_path
}

# Excel 저장 (다중 시트)
with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
    df_all.to_excel(writer, sheet_name='전체_데이터', index=False)
    for board_name in boards:
        df_board.to_excel(writer, sheet_name=board_name, index=False)
```

#### 핵심 노하우
- **통합 데이터 구조**: 메타데이터와 파일 정보를 하나의 레코드로
- **파일명 규칙**: `{순번}_{원본파일명}` 형식으로 추적 용이
- **다중 시트 Excel**: 전체 데이터 + 게시판별 시트로 구성

---

## 🎯 핵심 교훈

### 1. URL 패턴 우선
- DOM 네비게이션보다 직접 URL 접근이 안정적
- URL 구조 분석이 스크래핑의 첫 단계

### 2. 대기 전략
- `networkidle` + 추가 timeout
- 명시적 대기 > 암묵적 대기

### 3. 폴백 메커니즘
- 다중 셀렉터 준비
- 에러 시 대안 경로 확보

### 4. 데이터 무결성
- 페이지별 별도 저장
- 중간 저장으로 데이터 손실 방지

### 5. 디버깅 준비
- 스크린샷과 HTML 저장 자동화
- 상세한 로깅으로 문제 추적

---

## 📂 재사용 가능한 코드 패턴

### 페이지네이션 처리 엔진
```python
class PaginationScraper:
    async def scrape_all_pages(self):
        while True:
            # 현재 페이지 처리
            await self.scrape_current_page()
            
            # 다음 페이지 확인
            next_button = await page.query_selector('.next:not(.disabled)')
            if not next_button:
                break
                
            # 페이지 전환
            await next_button.click()
            await page.wait_for_load_state('networkidle')
```

### 첨부파일 다운로드 패턴
```python
async def download_attachments(page, download_dir):
    file_links = await page.query_selector_all('a[href*="Download"]')
    
    for link in file_links:
        async with page.expect_download() as download_info:
            await link.click()
        
        download = await download_info.value
        safe_name = sanitize_filename(download.suggested_filename)
        await download.save_as(os.path.join(download_dir, safe_name))
```

### 직접 URL 접근 패턴
```python
def build_detail_url(base_url, params):
    """게시물 상세 페이지 URL 생성"""
    query_params = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_params}"
```

---

## 🔧 도구 및 라이브러리

### 필수 라이브러리
- **playwright**: 브라우저 자동화
- **pandas**: 데이터 처리 및 Excel 저장
- **openpyxl**: Excel 다중 시트 처리

### 유용한 도구
- **브라우저 개발자 도구**: URL 패턴 및 셀렉터 분석
- **Postman**: API 엔드포인트 테스트
- **스크린샷 도구**: 문제 상황 기록

---

## 📝 체크리스트

### 새로운 사이트 스크래핑 시작 전
- [ ] robots.txt 확인
- [ ] URL 패턴 분석
- [ ] 페이지 로딩 방식 확인 (SPA/MPA)
- [ ] 인증 필요 여부 확인
- [ ] Rate limiting 정책 확인

### 구현 중
- [ ] 에러 처리 및 로깅
- [ ] 폴백 메커니즘
- [ ] 데이터 검증
- [ ] 중간 저장 기능
- [ ] 재시도 로직

### 테스트
- [ ] 단일 페이지 테스트
- [ ] 다중 페이지 테스트
- [ ] 엣지 케이스 테스트
- [ ] 성능 테스트
- [ ] 에러 복구 테스트
# 메일함 서핑 완전 마스터 가이드

Bizmeka 웹메일의 모든 폴더를 자유자재로 탐색하고 스크래핑하는 완전 가이드

## 🎯 현재 상황 분석

### ✅ 이미 마스터한 것들
- **받은메일함** 스크래핑
- 팝업 자동 처리
- 페이지네이션
- 쿠키 기반 2FA 우회
- li.m_data 구조 파싱

### ❓ 아직 모르는 것들 (탐구 대상)
- **보낸메일함** 접근 및 구조
- **임시보관함** (Draft) 처리
- **휴지통** 메일 복구
- **스팸메일함** 필터링
- **사용자 정의 폴더** (있다면)
- **폴더간 메일 이동**
- **메일 검색** 기능
- **첨부파일** 다운로드

---

## 📂 메일 폴더 구조 분석

### 예상되는 폴더 구조
```
📧 메일함
├── 📥 받은메일함 (Inbox) ✅ 완료
├── 📤 보낸메일함 (Sent)
├── 📝 임시보관함 (Draft)
├── 🗑️ 휴지통 (Trash)
├── 🚫 스팸메일함 (Spam)
├── 📁 사용자 폴더 1 (커스텀)
└── 📁 사용자 폴더 2 (커스텀)
```

### 동적 선택자 패턴 추정
```javascript
// 받은메일함 (이미 확인됨)
"#mnu_Inbox_kilmoon"

// 추정되는 다른 폴더들
"#mnu_Sent_kilmoon"     // 보낸메일함
"#mnu_Draft_kilmoon"    // 임시보관함  
"#mnu_Trash_kilmoon"    // 휴지통
"#mnu_Spam_kilmoon"     // 스팸메일함

// 일반적인 패턴
"#mnu_{FolderType}_{UserId}"
```

---

## 🔍 탐구 계획

### Phase 1: 폴더 발견 및 매핑
1. **모든 폴더 선택자 찾기**
   ```python
   # 모든 mnu_ 로 시작하는 링크 수집
   folder_links = await page.query_selector_all('[id^="mnu_"]')
   for link in folder_links:
       folder_id = await link.get_attribute('id')
       folder_text = await link.inner_text()
       print(f"{folder_id}: {folder_text}")
   ```

2. **폴더별 접근 테스트**
   - 각 폴더 클릭해보기
   - URL 변화 패턴 분석
   - 구조 차이점 확인

### Phase 2: 폴더별 데이터 구조 분석
1. **보낸메일함 구조**
   - 받는사람 필드 위치
   - 날짜/시간 표시 방식
   - 상태 표시 (읽음확인 등)

2. **임시보관함 구조**
   - 저장 상태 정보
   - 편집 가능 여부
   - 자동저장 시간

3. **휴지통 구조**
   - 삭제 일시 정보
   - 복구 가능 기간
   - 원본 폴더 정보

### Phase 3: 범용 폴더 스크래퍼 개발
1. **FolderNavigator 클래스**
2. **UniversalMailScraper 클래스**
3. **폴더별 특화 로직**

---

## 🛠️ 구현 계획

### 1. 폴더 탐색기 개발
```python
class MailFolderExplorer:
    async def discover_all_folders(self):
        """모든 메일 폴더 발견"""
        folders = []
        folder_links = await self.page.query_selector_all('[id^="mnu_"]')
        
        for link in folder_links:
            folder_info = {
                'id': await link.get_attribute('id'),
                'name': await link.inner_text(),
                'onclick': await link.get_attribute('onclick'),
                'href': await link.get_attribute('href')
            }
            folders.append(folder_info)
        
        return folders
    
    async def analyze_folder_structure(self, folder_id):
        """특정 폴더의 구조 분석"""
        # 폴더 클릭
        await self.click_folder(folder_id)
        
        # 구조 분석
        structure = {
            'mail_items': await self.count_mail_items(),
            'columns': await self.analyze_columns(),
            'pagination': await self.check_pagination(),
            'special_features': await self.detect_special_features()
        }
        
        return structure
```

### 2. 범용 메일 스크래퍼
```python
class UniversalMailScraper(BaseScraper):
    def __init__(self):
        super().__init__('bizmeka')
        self.folder_configs = self._load_folder_configs()
    
    async def scrape_folder(self, folder_type, max_pages=3):
        """특정 폴더 스크래핑"""
        # 폴더별 설정 로드
        config = self.folder_configs.get(folder_type, self.folder_configs['default'])
        
        # 폴더 이동
        await self.navigate_to_folder(folder_type)
        
        # 폴더별 특화 스크래핑
        if folder_type == 'Sent':
            return await self._scrape_sent_mails(max_pages, config)
        elif folder_type == 'Draft':
            return await self._scrape_draft_mails(max_pages, config)
        elif folder_type == 'Trash':
            return await self._scrape_trash_mails(max_pages, config)
        else:
            return await self._scrape_generic_mails(max_pages, config)
```

### 3. 폴더별 설정 파일
```json
// sites/bizmeka/config/folders.json
{
  "Inbox": {
    "selector_pattern": "#mnu_Inbox_{user_id}",
    "data_fields": ["sender", "subject", "date", "size", "read_status"],
    "special_features": ["attachments", "importance"]
  },
  "Sent": {
    "selector_pattern": "#mnu_Sent_{user_id}", 
    "data_fields": ["recipient", "subject", "date", "size", "delivery_status"],
    "special_features": ["read_receipt", "delivery_confirmation"]
  },
  "Draft": {
    "selector_pattern": "#mnu_Draft_{user_id}",
    "data_fields": ["recipient", "subject", "saved_date", "auto_save"],
    "special_features": ["edit_mode", "auto_save_interval"]
  }
}
```

---

## 🧪 실험 스크립트

### 폴더 탐색 실험 스크립트
```python
# scripts/explore_mail_folders.py
async def explore_all_folders():
    """모든 메일 폴더 탐색 실험"""
    
    # 1. 폴더 발견
    folders = await explorer.discover_all_folders()
    print("📂 발견된 폴더들:")
    for folder in folders:
        print(f"  - {folder['name']}: {folder['id']}")
    
    # 2. 각 폴더 구조 분석
    for folder in folders:
        print(f"\n🔍 {folder['name']} 분석 중...")
        try:
            structure = await explorer.analyze_folder_structure(folder['id'])
            print(f"  📊 메일 수: {structure['mail_items']}")
            print(f"  📋 컬럼: {structure['columns']}")
            print(f"  📄 페이징: {structure['pagination']}")
        except Exception as e:
            print(f"  ❌ 분석 실패: {e}")
    
    # 3. 샘플 데이터 추출
    for folder in folders[:3]:  # 처음 3개만
        print(f"\n📤 {folder['name']} 샘플 추출...")
        try:
            samples = await explorer.extract_sample_data(folder['id'], limit=5)
            for i, sample in enumerate(samples, 1):
                print(f"  {i}. {sample}")
        except Exception as e:
            print(f"  ❌ 추출 실패: {e}")
```

---

## 📈 예상 노하우들

### 1. 폴더별 특이사항
- **보낸메일함**: 수신자 정보, 읽음 확인 상태
- **임시보관함**: 자동저장 시간, 편집 링크
- **휴지통**: 삭제 날짜, 원본 폴더 정보
- **스팸메일함**: 스팸 점수, 필터링 이유

### 2. 공통 패턴
- 모든 폴더가 li.m_data 구조 사용할 가능성 높음
- data-* 속성은 폴더마다 다를 수 있음
- 페이지네이션은 공통일 가능성 높음

### 3. 주의사항
- 일부 폴더는 접근 권한 제한 있을 수 있음
- 휴지통은 자동 삭제 정책 있을 수 있음
- 스팸메일함은 별도 확인 과정 필요할 수 있음

---

## 🎯 최종 목표

### 완성될 기능들
```python
# 모든 폴더 스크래핑
scraper.scrape_all_folders()

# 특정 폴더만 스크래핑  
scraper.scrape_folder('Sent', pages=5)

# 폴더 간 비교 분석
scraper.compare_folders(['Inbox', 'Sent'])

# 전체 메일함 백업
scraper.backup_entire_mailbox()

# 메일 검색 및 필터링
scraper.search_mails(query="중요", folders=['Inbox', 'Sent'])
```

이제 진짜 **"메일함 서핑 마스터"**가 되기 위한 체계적인 계획이 완성됐습니다! 

한 번에 모든 걸 알 수는 없으니까, 하나씩 탐구해가면서 패턴을 찾고 노하우를 쌓아나가는 거죠. 이런 식으로 축적해나가면 나중에 다른 메일 시스템 만나도 "아, 이런 패턴이구나!" 하고 빠르게 적용할 수 있을 겁니다! 🚀
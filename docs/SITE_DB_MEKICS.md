# MEK-ICS ERP 시스템 - 사이트 정보

## 🏢 기본 정보

| 항목 | 내용 |
|------|------|
| **사이트 ID** | mekics |
| **사이트 명** | MEK-ICS ERP (OMEGA Plus) |
| **사이트 설명** | 엔터프라이즈 자원 관리 시스템 |
| **로그인 URL** | https://it.mek-ics.com/mekics/login/login.do |
| **메인 URL** | https://it.mek-ics.com/mekics/main/main.do |
| **분류** | ERP 시스템 |
| **운영사** | MEK-ICS |

## 🔐 로그인 정보

```yaml
Authentication:
  URL: https://it.mek-ics.com/mekics/login/login.do
  Method: POST
  Type: Form
  Selectors:
    username: 'input[name="userid"]'
    password: 'input[type="password"]'
    submit: 'Enter key'
  Success_URL: https://it.mek-ics.com/mekics/main_mics.do
  2FA: Optional (필요시 수동 처리)
```

### 세션 관리
- **쿠키 저장 파일**: `sites/mekics/data/cookies.json`
- **유효 기간**: 세션 기반 (브라우저 종료시 만료)
- **갱신 방법**: 재로그인 필요

## 🛠️ 기술 정보

### 웹 기술 스택
```yaml
Technology_Stack:
  Framework: ExtJS 6.2.0
  Type: Single Page Application (SPA)
  Backend: Java
  UI_Library: OMEGA Plus UI
  Data_Format: JSON
  Architecture: Component-based
```

### ExtJS 특징
- **Store 기반 데이터**: 모든 그리드 데이터가 Store에 저장
- **동적 ID 생성**: `ext-gen-*` 형태의 동적 ID
- **ComponentQuery**: CSS 선택자 대신 ExtJS ComponentQuery 사용

### 핵심 선택자 및 메서드
```javascript
// 그리드 데이터 추출
Ext.ComponentQuery.query('grid')[0].getStore().getData().items

// 모듈 이동
changeModule('18')  // 재고관리: 18, 영업관리: 14

// 데이터 조회
page.keyboard.press('F2')  // F2키로 조회 실행
```

## 📊 주요 모듈

### 모듈 ID 매핑
```yaml
Modules:
  영업관리: '14'
  생산관리: '15'
  구매/자재: '16'
  재고관리: '18'
  품질관리: '65'
```

### 주요 화면
- **매출현황조회**: `/mekics/sales/ssa450skrv.do`
- **재고현황조회**: `/mekics/inventory/siv200skrv.do`
- **구매발주**: `/mekics/purchase/mpo501ukrv.do`

## 💾 데이터 추출

### Store 데이터 직접 추출 (핵심 노하우)
```javascript
// 서버 API 우회하여 메모리에서 직접 추출
const grid = Ext.ComponentQuery.query('grid')[0];
const store = grid.getStore();
const data = store.getData().items.map(record => record.data);
```

### 다운로드 전략
1. **서버 다운로드**: 404 오류 발생 (세션 컨텍스트 문제)
2. **Store 추출**: ✅ 성공 (모든 데이터가 메모리에 있음)
3. **Blob 다운로드**: 클라이언트 측에서 CSV 생성

## 🔧 자동화 정보

### 조회 조건 설정
```javascript
// 날짜 설정
Ext.ComponentQuery.query('datefield')[0].setValue(new Date(2021, 0, 1));

// 라디오 버튼
Ext.getCmp('radiofield-1078').setValue(true);

// 콤보박스
Ext.ComponentQuery.query('combo')[0].setValue('ALL');
```

### 페이지 대기 전략
```javascript
// ExtJS 로드 대기
await page.wait_for_function("typeof Ext !== 'undefined' && Ext.isReady")

// Store 로드 대기
await page.wait_for_function("Ext.ComponentQuery.query('grid')[0].getStore().getCount() > 0")
```

## 📝 주의사항

- **동적 ID 문제**: ID가 매번 변경되므로 ComponentQuery 사용 필수
- **2FA 처리**: 필요시 수동으로 처리 후 쿠키 저장
- **세션 유지**: 장시간 미사용시 자동 로그아웃
- **다운로드 이슈**: 서버 다운로드 대신 Store 추출 방식 사용

## 🎯 핵심 노하우

1. **ExtJS Store 활용**: 서버 API 없이도 전체 데이터 접근 가능
2. **ComponentQuery 마스터**: 동적 ID 문제 해결
3. **F2 조회 패턴**: 모든 화면에서 F2로 데이터 조회
4. **쿠키 재사용**: 2FA 우회 가능
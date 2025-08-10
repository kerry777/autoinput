# 엑셀-HWP 자동화 완전 가이드

## 📋 개요

엑셀 데이터를 활용하여 HWP 문서를 자동으로 생성, 편집, 변환하는 시스템입니다.

## 🎯 활용 사례

### 1. 대량 문서 생성
- **인사 발령 통지서**: 직원 정보 → 개인별 발령장
- **계약서 일괄 생성**: 계약 정보 → 계약서 PDF
- **증명서 발급**: 신청자 정보 → 증명서 자동 발급
- **성적 통지서**: 학생 성적 → 개인별 성적표

### 2. 문서 일괄 편집
- **텍스트 색상 변경**: 빨간색/파란색 → 검은색
- **특정 문구 치환**: 회사명, 날짜 등 일괄 변경
- **서식 통일**: 폰트, 크기, 정렬 일괄 적용

### 3. PDF 변환 및 병합
- **HWP → PDF 일괄 변환**
- **관련 문서 병합**: 주계약 + 특약 → 통합 PDF
- **보고서 통합**: 개별 보고서 → 종합 보고서

## 💻 핵심 코드

### 1. 엑셀 데이터 읽기
```python
import pandas as pd

# 엑셀 파일 읽기
df = pd.read_excel('직원명단.xlsx')

# 각 행에 대해 처리
for idx, row in df.iterrows():
    name = row['이름']
    dept = row['부서']
    position = row['직급']
```

### 2. HWP 템플릿 활용
```python
import win32com.client

# 한글 프로그램 실행
hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
hwp.RegisterModule('FilePathCheckDLL', 'AutomationModule')

# 템플릿 열기
hwp.Open("템플릿.hwp")

# 텍스트 찾기 및 바꾸기
def replace_text(hwp, find_text, replace_text):
    option = hwp.HParameterSet.HFindReplace
    hwp.HAction.GetDefault("AllReplace", option.HSet)
    option.FindString = find_text
    option.ReplaceString = replace_text
    option.IgnoreMessage = 1
    hwp.HAction.Execute("AllReplace", option.HSet)

# 템플릿 치환
replace_text(hwp, "{이름}", "김철수")
replace_text(hwp, "{부서}", "개발팀")
replace_text(hwp, "{직급}", "과장")
```

### 3. PDF 변환
```python
# HWP를 PDF로 저장
hwp.SaveAs("output.pdf", "PDF")

# 또는 인쇄 방식으로 PDF 생성
action = hwp.CreateAction("Print")
print_setting = action.CreateSet()
print_setting.SetItem("PrinterName", "Microsoft Print to PDF")
print_setting.SetItem("FileName", "output.pdf")
action.Execute(print_setting)
```

### 4. PDF 병합
```python
from PyPDF2 import PdfMerger

# PDF 파일들 병합
merger = PdfMerger()
merger.append("문서1.pdf")
merger.append("문서2.pdf")
merger.append("문서3.pdf")
merger.write("통합문서.pdf")
merger.close()
```

## 🚀 실전 예제: 증명서 자동 발급

### 1. 엑셀 데이터 준비 (신청자.xlsx)
| 이름 | 주민번호 | 용도 | 발급일 |
|------|----------|------|--------|
| 김철수 | 800101-1****** | 은행제출 | 2025-08-09 |
| 이영희 | 850202-2****** | 비자신청 | 2025-08-09 |

### 2. HWP 템플릿 (재직증명서_템플릿.hwp)
```
                재 직 증 명 서
                
성명: {이름}
주민등록번호: {주민번호}
부서: {부서}
직급: {직급}
재직기간: {입사일} ~ 현재

위 사람은 본 회사에 재직 중임을 증명합니다.

용도: {용도}
발급일: {발급일}

                    주식회사 ○○○
                    대표이사 (인)
```

### 3. 자동화 스크립트
```python
class CertificateAutomation:
    def __init__(self):
        self.hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
        
    def generate_certificates(self, excel_path, template_path, output_dir):
        # 엑셀 데이터 읽기
        df = pd.read_excel(excel_path)
        
        for idx, row in df.iterrows():
            # 템플릿 열기
            self.hwp.Open(template_path)
            
            # 데이터 치환
            for column, value in row.items():
                self.replace_text(f"{{{column}}}", str(value))
            
            # PDF로 저장
            output_file = f"{output_dir}/{row['이름']}_재직증명서.pdf"
            self.hwp.SaveAs(output_file, "PDF")
            
            print(f"✅ 생성 완료: {output_file}")
```

## 📊 텍스트 색상 일괄 변경 (블로그 예제)

### 빨간색/파란색 → 검은색 변경
```python
def change_text_color(hwp):
    """빨간글씨와 파란글씨를 검은글씨로 변경"""
    
    # 빨간색 → 검은색
    option = hwp.HParameterSet.HFindReplace
    hwp.HAction.GetDefault("AllReplace", option.HSet)
    option.FindString = ""  # 모든 텍스트
    option.ReplaceString = ""
    option.IgnoreMessage = 1
    option.FindCharShape.TextColor = hwp.RGBColor(255, 0, 0)  # 빨간색
    option.ReplaceCharShape.TextColor = hwp.RGBColor(0, 0, 0)  # 검은색
    hwp.HAction.Execute("AllReplace", option.HSet)
    
    # 파란색 → 검은색
    option.FindCharShape.TextColor = hwp.RGBColor(0, 0, 255)  # 파란색
    option.ReplaceCharShape.TextColor = hwp.RGBColor(0, 0, 0)  # 검은색
    hwp.HAction.Execute("AllReplace", option.HSet)
```

## 🔧 필수 설정

### 1. 환경 준비
```bash
# 필수 패키지 설치
pip install pywin32 pandas openpyxl PyPDF2

# COM 객체 등록 (관리자 권한)
cd "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin"
hwp.exe /regserver
```

### 2. 보안 모듈 등록
```python
hwp.RegisterModule('FilePathCheckDLL', 'AutomationModule')
```

## 💡 실무 팁

### 1. 템플릿 설계
- **치환 태그**: `{필드명}` 형식 사용
- **반복 구간**: 표나 목록은 별도 처리
- **서식 유지**: 템플릿에서 서식 미리 설정

### 2. 성능 최적화
- **배치 처리**: 한글 프로그램 한 번만 실행
- **병렬 처리**: 멀티프로세싱 활용
- **캐싱**: 반복 데이터 미리 로드

### 3. 오류 처리
```python
try:
    hwp.Open(file_path)
except:
    print(f"파일 열기 실패: {file_path}")
    continue
```

## 📈 효과

### 비용 절감
- **수작업 시간**: 문서당 5분 → 1초
- **인건비 절감**: 월 100만원 이상
- **오류 감소**: 휴먼 에러 제거

### 생산성 향상
- **대량 처리**: 1000개 문서 10분 내 처리
- **일관성**: 100% 동일한 서식 유지
- **자동화**: 24시간 무인 운영 가능

## 🎓 학습 자료

### YouTube 강의
- pyhwpx 활용 자동화 (조회수 1,446회)
- 위키독스: https://wikidocs.net/book/8956
- 오픈채팅방: https://open.kakao.com/o/gFCMxq8g

### 공식 문서
- pyhwpx: https://github.com/mete0r/pyhwpx
- 한컴 개발자 포럼: https://forum.developer.hancom.com

## 🚨 주의사항

1. **한컴 오피스 필수**: 한글 2020 이상 설치 필요
2. **Windows 전용**: Linux/Mac 지원 안됨
3. **라이선스**: 상업용 사용 시 한컴 라이선스 확인
4. **보안**: 민감 정보 처리 시 주의

## 📝 결론

엑셀-HWP 자동화는 반복적인 문서 작업을 획기적으로 개선합니다.
- **즉시 적용 가능**: 간단한 스크립트로 시작
- **확장 가능**: 복잡한 비즈니스 로직 구현
- **ROI 높음**: 투자 대비 효과 즉시 체감

**"수작업 1시간 → 자동화 1분"**
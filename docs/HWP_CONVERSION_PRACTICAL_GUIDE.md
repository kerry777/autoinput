# HWP 파일 변환 실용 가이드 (2025)

## 테스트 결과 요약

### ❌ 실패한 방법들
1. **LibreOffice 직접 변환** - HWP 파일을 읽지 못함
2. **H2Orestart 확장** - Java 의존성, 개인 제작 불안정
3. **HWP 직접 파싱** - 본문 텍스트 깨짐 (인코딩 문제)

## ✅ 검증된 실용적 방법

### 1. 한컴 오피스 2024 활용 (가장 확실)

#### A. GUI 일괄 변환
```
1. 한글 2024 실행
2. 파일 → 일괄 변환
3. HWP 파일들 선택
4. 출력 형식: PDF 선택
5. 변환 시작
```

#### B. COM API 자동화 (Python)
```python
import win32com.client as win32
import os

def hwp_to_pdf(hwp_path, pdf_path):
    """한컴 오피스 COM API를 사용한 변환"""
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
    
    hwp.Open(hwp_path)
    hwp.SaveAs(pdf_path, "PDF")
    hwp.Quit()

# 사용 예
hwp_to_pdf("document.hwp", "document.pdf")
```

### 2. pyhwp 라이브러리 (텍스트 추출용)

#### 설치
```bash
pip install pyhwp
```

#### 사용
```bash
# 명령줄
hwp5txt input.hwp --output output.txt

# Python
from hwp5 import filestructure
hwp = filestructure.File('document.hwp')
# 텍스트 추출 로직
```

**한계**: 서식 없는 텍스트만 추출 가능

### 3. 온라인 변환 서비스 (소량 파일)

#### 무료 서비스
- https://allinpdf.com/hwp-to-pdf
- https://anyconv.com/hwp-to-pdf-converter/
- https://hwpconverter.com/en/hwp-to-pdf

#### API 서비스 (자동화 가능)
- CloudConvert API (월 25분 무료)
```python
import cloudconvert

api = cloudconvert.Api('your-api-key')
process = api.convert({
    'inputformat': 'hwp',
    'outputformat': 'pdf',
    'input': 'upload',
    'file': open('document.hwp', 'rb')
})
process.wait()
process.download("output.pdf")
```

### 4. 하이브리드 워크플로우 (권장)

```python
from pathlib import Path
import pdfplumber

def smart_hwp_workflow(hwp_path):
    """실용적인 HWP 처리 워크플로우"""
    hwp_path = Path(hwp_path)
    
    # 1단계: 이미 변환된 PDF 확인
    pdf_path = hwp_path.with_suffix('.pdf')
    if pdf_path.exists():
        return extract_from_pdf(pdf_path)
    
    # 2단계: pyhwp로 텍스트 추출 시도
    try:
        text = extract_with_pyhwp(hwp_path)
        if text and len(text) > 100:
            return text
    except:
        pass
    
    # 3단계: 수동 변환 안내
    print(f"""
    자동 변환 실패. 다음 방법 중 선택:
    1. 한글 2024에서 PDF로 저장
    2. 온라인 변환: https://allinpdf.com/hwp-to-pdf
    파일: {hwp_path}
    """)
    
    return None

def extract_from_pdf(pdf_path):
    """PDF에서 텍스트 추출"""
    with pdfplumber.open(pdf_path) as pdf:
        return '\n'.join([
            page.extract_text() 
            for page in pdf.pages 
            if page.extract_text()
        ])
```

## 프로젝트별 권장 방법

### 대량 파일 처리
→ 한컴 오피스 일괄 변환 + PDF 텍스트 추출

### 자동화 시스템
→ COM API (Windows) 또는 CloudConvert API

### 텍스트만 필요
→ pyhwp 라이브러리

### 일회성 작업
→ 온라인 변환 서비스

## 핵심 교훈

1. **완벽한 자동화는 어렵다** - 한컴 오피스 없이는 제한적
2. **PDF 중간 단계가 효과적** - HWP → PDF → 텍스트
3. **하이브리드 접근이 현실적** - 자동화 + 수동 처리 조합
4. **범용 도구 우선** - 특정 개인 프로젝트 의존 지양

## 결론

- **즉시 사용 가능**: 한컴 오피스 2024 (이미 설치됨)
- **코드 자동화**: COM API 또는 pyhwp
- **대안**: 온라인 서비스 활용
- **LibreOffice는 HWP 변환에 부적합**
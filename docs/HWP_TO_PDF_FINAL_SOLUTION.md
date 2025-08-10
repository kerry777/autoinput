# HWP to PDF 변환 최종 솔루션 가이드

## 현실적인 문제
HWP 파일을 PDF로 **안정적으로 자동 변환**하는 것은 매우 어렵습니다.

### 주요 문제점
1. **한컴 오피스 COM 객체 등록 문제**: 한글 2024가 설치되어 있어도 COM 객체가 제대로 등록되지 않는 경우가 많음
2. **명령줄 인터페이스 부재**: HwpConverter.exe 등이 있지만 문서화되지 않음
3. **라이브러리 한계**: pyhwp 등은 텍스트 추출은 가능하지만 서식을 유지한 PDF 변환은 불가능

## 실용적인 해결 방법

### 1. 이미 변환된 PDF 활용 (가장 현실적) ✅

많은 경우 HWP 파일과 함께 PDF 버전이 이미 존재합니다.

```python
from pathlib import Path

def find_pdf_version(hwp_path):
    """HWP 파일과 동일한 이름의 PDF 찾기"""
    hwp_path = Path(hwp_path)
    pdf_path = hwp_path.with_suffix('.pdf')
    
    if pdf_path.exists():
        return pdf_path
    
    # 같은 디렉토리에서 비슷한 이름의 PDF 찾기
    for pdf in hwp_path.parent.glob("*.pdf"):
        if hwp_path.stem in pdf.stem:
            return pdf
    
    return None
```

### 2. 온라인 변환 서비스 (수동) 🌐

무료로 사용할 수 있는 온라인 서비스들:

- **https://allinpdf.com/hwp-to-pdf** - 무료, 빠름
- **https://anyconv.com/hwp-to-pdf-converter/** - 무료, 간단
- **https://hwpconverter.com/en/hwp-to-pdf** - 전문 HWP 변환
- **https://cloudconvert.com/hwp-to-pdf** - API 제공 (월 25분 무료)

### 3. LibreOffice 설치 후 사용 📦

LibreOffice는 HWP 파일을 부분적으로 지원합니다.

#### 설치
1. LibreOffice 다운로드: https://www.libreoffice.org
2. 설치 시 HWP 필터 포함 확인

#### 명령줄 변환
```bash
soffice --headless --convert-to pdf "파일.hwp"
```

#### Python 자동화
```python
import subprocess

def convert_with_libreoffice(hwp_path, pdf_path):
    cmd = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", str(pdf_path.parent),
        str(hwp_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0
```

### 4. 한글 2024 수동 일괄 변환 (권장) ✅

한글 2024가 설치되어 있다면 **일괄 변환** 기능을 사용하는 것이 가장 확실합니다.

#### 일괄 변환 방법
1. 한글 2024 실행
2. **파일** > **일괄 변환** 메뉴 선택
3. HWP 파일들 선택 (여러 개 가능)
4. 출력 형식: **PDF** 선택
5. 출력 폴더 지정
6. **변환 시작** 클릭

이 방법은 GUI를 사용하지만 여러 파일을 한 번에 처리할 수 있어 효율적입니다.

### 5. PDF 텍스트 추출 (변환 후)

PDF로 변환된 후에는 텍스트 추출이 쉽습니다:

```python
import pdfplumber

def extract_text_from_pdf(pdf_path):
    text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return '\n'.join(text)
```

## 완전 자동화가 어려운 이유

1. **한컴 오피스 API 제한**: 
   - COM 객체가 제대로 등록되지 않음
   - Python에서 직접 호출 어려움
   - 문서화 부족

2. **HWP 형식의 복잡성**:
   - 독자적인 바이너리 형식
   - 한컴 전용 인코딩
   - 복잡한 서식과 객체 포함

3. **대안 도구의 한계**:
   - pyhwp: 텍스트만 추출 가능
   - LibreOffice: 부분적 지원
   - 온라인 서비스: API 키 필요

## 권장 워크플로우

```python
def smart_hwp_to_pdf_workflow(hwp_path):
    """
    스마트 HWP to PDF 워크플로우
    """
    hwp_path = Path(hwp_path)
    
    # 1단계: 이미 변환된 PDF 확인
    pdf = find_pdf_version(hwp_path)
    if pdf:
        print(f"PDF 발견: {pdf}")
        return pdf
    
    # 2단계: LibreOffice 시도 (설치된 경우)
    if shutil.which("soffice"):
        pdf_path = hwp_path.with_suffix('.pdf')
        if convert_with_libreoffice(hwp_path, pdf_path):
            print(f"LibreOffice 변환 성공: {pdf_path}")
            return pdf_path
    
    # 3단계: 수동 변환 안내
    print(f"""
    자동 변환 실패. 다음 방법을 사용하세요:
    
    1. 한글 2024 일괄 변환 (권장)
       - 한글 2024 > 파일 > 일괄 변환
    
    2. 온라인 변환
       - https://allinpdf.com/hwp-to-pdf
    
    HWP 파일: {hwp_path}
    """)
    
    return None
```

## 결론

### ✅ 가능한 것
- PDF가 이미 있는 경우 활용
- PDF에서 텍스트 추출
- 한글 2024 GUI로 일괄 변환
- 온라인 서비스 수동 사용

### ❌ 어려운 것
- 완전 자동화된 HWP → PDF 변환
- 한컴 오피스 없이 서식 유지 변환
- 대량 파일의 무인 자동 변환

### 💡 실용적 조언
1. **가능하면 PDF 버전을 함께 관리**하세요
2. 한글 2024의 **일괄 변환** 기능을 활용하세요
3. 텍스트만 필요하면 **pyhwp + pdfplumber** 조합을 사용하세요
4. 완벽한 자동화보다는 **반자동화**를 목표로 하세요

## 참고 자료
- [pyhwp GitHub](https://github.com/mete0r/pyhwp)
- [LibreOffice](https://www.libreoffice.org)
- [CloudConvert API](https://cloudconvert.com/api/v2)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
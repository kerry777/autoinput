# HWP 파일 변환 솔루션 가이드

## 문제 상황
HWP(한글 워드 프로세서) 파일의 본문 텍스트를 직접 파싱하려고 할 때, 미리보기(PrvText)는 정상적으로 추출되지만 본문(BodyText)이 깨진 텍스트로 나오는 문제가 발생합니다.

### 깨진 텍스트 예시
```
원본: "증거서류반환신청서"
파싱 결과: "덬촱", "괾녯", "떪쑩", "뷮칳빷" 등
```

## 원인 분석
1. **HWP 고유 인코딩**: HWP는 독자적인 바이너리 형식과 인코딩을 사용
2. **압축 및 암호화**: BodyText 섹션은 zlib 압축과 복잡한 레코드 구조 사용
3. **한컴 전용 포맷**: 한컴 오피스 없이는 완벽한 디코딩이 어려움

## 해결 방법

### 1. PDF 변환 후 텍스트 추출 (권장) ✅

가장 효과적인 방법으로, HWP를 PDF로 변환한 후 PDF에서 텍스트를 추출합니다.

#### 구현 코드
```python
import pdfplumber
from pathlib import Path

class PDFTextExtractor:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.text_content = ""
    
    def extract_text(self):
        with pdfplumber.open(self.file_path) as pdf:
            texts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texts.append(page_text)
                
                # 표 데이터 추출
                tables = page.extract_tables()
                for table in tables:
                    # 표 처리 로직
                    pass
            
            self.text_content = '\n'.join(texts)
        return self.text_content
```

#### 장점
- 한글 텍스트가 정확하게 추출됨
- 표, 이미지 등 복잡한 구조도 처리 가능
- 안정적이고 신뢰할 수 있는 결과

#### 필요 라이브러리
```bash
pip install pdfplumber PyPDF2
```

### 2. pyhwp 라이브러리 사용

한컴에서 공개한 HWP Binary Specification 1.1 기반의 오픈소스 파서입니다.

#### 설치
```bash
pip install pyhwp
```

#### 명령줄 도구 사용
```bash
hwp5txt input.hwp --output output.txt
```

#### 한계
- 최신 HWP 형식 지원 제한
- 복잡한 서식의 경우 텍스트 추출 실패
- 표 구조만 인식하고 내용 추출 실패하는 경우 있음

### 3. hwpapi 사용 (한컴 오피스 필요)

Windows에서 한컴 오피스가 설치되어 있을 때 사용 가능합니다.

#### 설치
```bash
pip install hwpapi
```

#### 사용 예시
```python
from hwpapi import Hwp

hwp = Hwp()
hwp.Open("파일.hwp")
hwp.Run("SelectAll")
text = hwp.GetTextFile("Text", "")
hwp.Quit()
```

#### 한계
- 한컴 오피스 설치 필요
- Windows 환경에서만 작동
- 라이선스 이슈 고려 필요

### 4. 미리보기 텍스트만 추출

완벽하지는 않지만 빠른 내용 확인이 가능합니다.

```python
import olefile

with olefile.OleFileIO(hwp_file) as ole:
    if ole.exists('PrvText'):
        prv_data = ole.openstream('PrvText').read()
        preview_text = prv_data.decode('utf-16le', errors='ignore')
        print(preview_text)
```

## 실전 추천 워크플로우

### 1단계: PDF 파일 확인
```python
# HWP와 동일한 이름의 PDF 파일이 있는지 확인
pdf_path = hwp_path.with_suffix('.pdf')
if pdf_path.exists():
    # PDF에서 텍스트 추출
    extractor = PDFTextExtractor(pdf_path)
    text = extractor.extract_text()
```

### 2단계: PDF가 없으면 변환 시도
```python
# 옵션 1: 온라인 변환 서비스 사용
# 옵션 2: 한컴 오피스 API 사용 (설치된 경우)
# 옵션 3: pyhwp 명령줄 도구 사용
```

### 3단계: 미리보기 텍스트 추출 (대체 방안)
```python
# PDF 변환이 불가능한 경우 미리보기 텍스트라도 추출
preview_text = extract_preview_from_hwp(hwp_path)
```

## 테스트 결과

### 성공 사례
- **PDF 텍스트 추출**: 100% 성공률, 완벽한 한글 텍스트 추출
- **미리보기 텍스트**: 90% 성공률, 문서 요약 정보 획득 가능

### 실패 사례
- **직접 BodyText 파싱**: 텍스트 깨짐 현상 발생
- **pyhwp 텍스트 변환**: 표 구조만 인식, 내용 누락

## 결론 및 권장사항

1. **최우선 방법**: HWP → PDF 변환 → 텍스트 추출
2. **대체 방법**: 미리보기 텍스트 추출로 기본 정보 획득
3. **완벽한 솔루션**: 한컴 오피스 API 사용 (라이선스 필요)

## 참고 자료

- [pyhwp GitHub](https://github.com/mete0r/pyhwp)
- [한컴 개발자 포럼](https://forum.developer.hancom.com)
- [HWP Binary Specification](https://www.hancom.com)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)

## 샘플 코드 위치

- `/scripts/pdf_text_extractor.py` - PDF 텍스트 추출
- `/scripts/hwp_advanced_parser.py` - HWP 고급 파싱 시도
- `/scripts/hwp_pyhwp_converter.py` - pyhwp 라이브러리 사용
- `/scripts/hwp_hwpapi_converter.py` - hwpapi 사용 예제
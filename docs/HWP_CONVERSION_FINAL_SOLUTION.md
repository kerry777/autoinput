# HWP 파일 변환 최종 정리 (2025.08 테스트 결과)

## 테스트 결과 요약

### ❌ 작동하지 않는 방법들

1. **LibreOffice 직접 변환**
   - 기본 LibreOffice는 HWP 파일을 읽지 못함
   - "Error: source file could not be loaded" 오류 발생

2. **H2Orestart 확장 프로그램**
   - Java 의존성 문제
   - 개인 제작 확장으로 안정성 문제

3. **pyhwpx / win32com**
   - 한컴 오피스 COM 객체가 등록되지 않음
   - "잘못된 클래스 문자열" 오류 발생
   - 한글 2024 설치만으로는 부족

## ✅ 실제로 작동하는 방법들

### 1. 한컴 오피스 GUI 사용 (가장 확실)

**일괄 변환 기능**
1. 한글 2024 실행
2. 파일 → 일괄 변환
3. HWP 파일들 선택
4. PDF로 출력 형식 선택
5. 변환 실행

**장점**: 100% 성공률, 완벽한 서식 유지
**단점**: 수동 작업 필요

### 2. pyhwp 라이브러리 (텍스트만)

```bash
pip install pyhwp
hwp5txt input.hwp --output output.txt
```

**장점**: 자동화 가능, Python 스크립트 지원
**단점**: 텍스트만 추출, 서식 손실, 표 내용 누락 가능

### 3. 온라인 변환 서비스

**무료 서비스**
- https://allinpdf.com/hwp-to-pdf
- https://anyconv.com/hwp-to-pdf-converter/
- https://hwpconverter.com/en/hwp-to-pdf

**장점**: 설치 불필요, 빠른 변환
**단점**: 파일 업로드 필요, 보안 우려, 대량 처리 어려움

### 4. 이미 변환된 PDF 활용

많은 경우 HWP와 함께 PDF 버전이 이미 존재:
```python
from pathlib import Path

def find_pdf_version(hwp_path):
    pdf_path = Path(hwp_path).with_suffix('.pdf')
    if pdf_path.exists():
        return pdf_path
    return None
```

## COM 객체 등록 문제 해결 (시도 가능)

### 관리자 권한으로 실행:
```cmd
# 관리자 명령 프롬프트에서:
cd "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin"
Hwp.exe /regserver
```

또는:
```cmd
regsvr32 "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin\HwpOle.dll"
```

**주의**: 이 방법도 작동하지 않을 수 있음

## 권장 워크플로우

```python
def smart_hwp_workflow(hwp_path):
    """실용적인 HWP 처리 방법"""
    
    # 1. PDF가 이미 있는지 확인
    pdf = find_pdf_version(hwp_path)
    if pdf:
        return extract_from_pdf(pdf)
    
    # 2. pyhwp로 텍스트 추출 시도
    try:
        text = extract_with_pyhwp(hwp_path)
        if text:
            return text
    except:
        pass
    
    # 3. 수동 변환 안내
    print(f"""
    자동 변환 실패. 다음 방법을 사용하세요:
    
    1. 한글 2024에서 PDF로 저장
    2. 온라인 변환: https://allinpdf.com/hwp-to-pdf
    
    파일: {hwp_path}
    """)
```

## 결론

### 현실적 선택:
1. **즉시 필요**: 한글 2024 GUI 사용
2. **텍스트만 필요**: pyhwp 라이브러리
3. **소량 파일**: 온라인 변환 서비스
4. **대량 자동화**: 한글 2024 일괄 변환 + PDF 파싱

### 중요 사실:
- **완전 자동화는 매우 어려움** (COM 객체 등록 문제)
- **LibreOffice는 HWP 지원 불가**
- **PDF 중간 단계가 가장 효과적**
- **한컴 오피스 없이는 완벽한 변환 불가능**

## YouTube 영상 (pyhwpx) 관련

pyhwpx는 좋은 도구지만, 한컴 오피스 COM 객체가 제대로 등록되어 있어야 작동합니다. 
현재 환경에서는 COM 객체 등록 문제로 작동하지 않습니다.

해결 방법:
1. 한글 2024 재설치 (COM 객체 자동 등록)
2. 관리자 권한으로 수동 등록
3. 32비트 Python 사용 (32비트 한글과 매칭)
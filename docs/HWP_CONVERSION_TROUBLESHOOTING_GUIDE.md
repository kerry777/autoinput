# HWP 파일 변환 문제 해결 가이드 (2025.08 실전)

## 🚨 핵심 해결책: 관리자 권한으로 COM 객체 등록

### 문제 상황
- pyhwpx 설치 후 실행 시 오류: `타입 라이브러리를 등록되지 않았습니다`
- win32com.client.Dispatch 실패: `잘못된 클래스 문자열입니다`
- LibreOffice로 HWP 변환 실패: `Error: source file could not be loaded`

### ✅ 최종 해결 방법

**관리자 권한 명령 프롬프트에서 실행:**
```cmd
cd "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin"
hwp.exe /regserver
```

**결과**: HWPFrame.HwpObject COM 객체가 정상 등록되어 pyhwpx 사용 가능!

## 시행착오 전체 과정

### 1차 시도: LibreOffice (실패)
```python
# LibreOffice로 HWP 변환 시도
soffice.exe --headless --convert-to pdf file.hwp
# 결과: Error: source file could not be loaded
```
**원인**: LibreOffice는 HWP 파일을 직접 읽을 수 없음

### 2차 시도: H2Orestart 확장 (포기)
- LibreOffice 확장 프로그램 설치 시도
- Java 의존성 문제 발생: `Could not create Java implementation loader`
- 개인 제작 확장으로 안정성 문제
**결론**: 범용적이지 않아 포기

### 3차 시도: pyhwpx 설치 (부분 실패)
```python
pip install pyhwpx
from pyhwpx import Hwp  # 오류 발생!
```
**오류**: `pywintypes.com_error: (-2147319779, '타입 라이브러리를 등록되지 않았습니다')`

### 4차 시도: win32com 직접 사용 (실패)
```python
import win32com.client
hwp = win32com.client.Dispatch("HWPFrame.HwpObject")  # 실패!
```
**오류**: `잘못된 클래스 문자열입니다`

### 5차 시도: 관리자 권한 COM 등록 (성공!) ✅
```cmd
# 관리자 권한 명령 프롬프트
C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin>hwp.exe /regserver
```
**결과**: COM 객체 등록 성공, pyhwpx 정상 작동!

## 검증된 작동 코드

### pyhwpx를 사용한 HWP → PDF 변환
```python
from pyhwpx import Hwp

# 한글 프로그램 실행
hwp = Hwp()

# HWP 파일 열기
hwp.open("document.hwp")

# PDF로 저장
hwp.save_as("output.pdf", "PDF")

# HTML로도 가능
hwp.save_as("output.html", "HTML")

# 종료
hwp.quit()
```

### 성공 결과
- **HWP → PDF**: ✅ 완벽한 변환 (서식 유지)
- **HWP → HTML**: ✅ 성공
- **HWP → DOCX**: ❌ 일부 버전에서 실패
- **텍스트 추출**: ⚠️ 메서드 차이로 수정 필요

## 중요 교훈

### 1. COM 객체 등록이 핵심
- 한컴 오피스 설치만으로는 부족
- **반드시 관리자 권한으로 COM 객체 등록 필요**
- `hwp.exe /regserver` 명령이 해결책

### 2. LibreOffice의 한계
- LibreOffice는 HWP 파일을 직접 읽을 수 없음
- H2Orestart 같은 확장도 불안정
- HWP 변환에는 한컴 오피스가 필수

### 3. Python 환경 고려사항
- 32비트 한글 → 32비트 Python 필요할 수 있음
- 64비트 시스템에서도 한글은 32비트로 설치됨
- pyhwpx는 win32com 기반으로 Windows 전용

## 문제 해결 체크리스트

### COM 객체 등록 확인
```python
import win32com.client
try:
    hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
    print("✅ COM 객체 정상")
except:
    print("❌ COM 객체 등록 필요")
```

### 관리자 권한 필요 작업
1. `hwp.exe /regserver` 실행
2. `regsvr32 HwpOle.dll` (있는 경우)
3. 레지스트리 수정

### 환경 변수 확인
```cmd
# 한글 설치 경로 확인
dir "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin\Hwp.exe"
```

## 최종 권장사항

### 즉시 사용 가능한 방법
1. **관리자 권한으로 COM 등록** → pyhwpx 사용
2. 한글 2024 GUI에서 일괄 변환
3. 온라인 변환 서비스 (소량)

### 자동화 구축
1. COM 객체 등록 (1회)
2. pyhwpx 설치
3. Python 스크립트로 자동화

### 대안 (COM 등록 실패 시)
1. 한글 2024 재설치
2. pyhwp 라이브러리 (텍스트만)
3. 온라인 API 서비스

## 참고 자료
- pyhwpx 공식 문서: https://github.com/mete0r/pyhwpx
- 한컴 개발자 포럼: https://forum.developer.hancom.com
- YouTube 강의: pyhwpx 활용 자동화
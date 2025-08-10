# 🚀 HWP 자동화 완벽 가이드 (2025 최신판)

## 📚 목차
1. [개요](#개요)
2. [패키지 비교](#패키지-비교)
3. [설치 및 설정](#설치-및-설정)
4. [실전 코드](#실전-코드)
5. [문제 해결](#문제-해결)
6. [고급 활용](#고급-활용)
7. [참고 자료](#참고-자료)

---

## 🎯 개요

HWP(한글) 문서 자동화는 반복적인 문서 작업을 혁신적으로 개선합니다.

### 주요 활용 분야
- **대량 문서 생성**: 계약서, 증명서, 보고서
- **문서 변환**: HWP → PDF 일괄 변환
- **데이터 병합**: 엑셀 데이터 → HWP 문서
- **서식 표준화**: 색상, 폰트, 스타일 일괄 변경

---

## 📦 패키지 비교

### 1. **pyhwpx** (가장 활발)
```bash
pip install pyhwpx
```
- **개발자**: 일동 차트
- **특징**: 직관적 API, 활발한 업데이트
- **문서**: https://wikidocs.net/book/8956
- **커뮤니티**: 오픈 카톡방 운영

### 2. **hwpapi** (PyCon KR 2023)
```bash
pip install hwpapi
```
- **개발자**: 전다민 (KOICA)
- **특징**: 사용자 친화적, 자동완성 지원
- **문서**: https://jundamin.github.io/hwpapi
- **발표**: PyCon KR 2023 발표

### 3. **xython.han**
```bash
pip install xython
```
- **개발자**: sjpkorea
- **특징**: 다양한 오피스 자동화 통합
- **문서**: https://sjpkorea.github.io/xython.github.io/

### 4. **pyhwp** (오픈소스)
```bash
pip install pyhwp
```
- **특징**: HWP 파일 직접 파싱
- **용도**: 텍스트 추출 전용
- **한계**: 서식 유지 불가

---

## 🔧 설치 및 설정

### 1. 필수 준비사항

#### 한컴 오피스 설치
- 한글 2020 이상 필요
- Windows 전용 (Mac/Linux 불가)

#### COM 객체 등록 (관리자 권한)
```cmd
cd "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin"
hwp.exe /regserver
```

#### Python 패키지 설치
```bash
pip install pywin32 pandas openpyxl PyPDF2
pip install pyhwpx  # 또는 hwpapi
```

### 2. 보안 설정

#### 보안 경고 최소화
```python
# 보안 모듈 등록
hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')

# 메시지 무시 설정
option.IgnoreMessage = 1
```

---

## 💻 실전 코드

### 1. 기본 문서 생성 (pyhwpx)
```python
from pyhwpx import Hwp

# 한글 시작
hwp = Hwp()

# 텍스트 입력
hwp.insert_text("제목: 자동화 테스트\n\n")
hwp.insert_text("이것은 자동으로 생성된 문서입니다.\n")

# 표 생성
hwp.create_table(3, 4)

# 저장
hwp.save_as("output.hwp")
hwp.save_as("output.pdf", "PDF")

# 종료
hwp.quit()
```

### 2. 엑셀 데이터로 문서 생성
```python
import pandas as pd
from pyhwpx import Hwp

def create_documents_from_excel(excel_path, template_path, output_dir):
    """엑셀 데이터로 문서 일괄 생성"""
    
    # 엑셀 읽기
    df = pd.read_excel(excel_path)
    
    # 한글 시작
    hwp = Hwp()
    
    for idx, row in df.iterrows():
        # 템플릿 열기
        hwp.open(template_path)
        
        # 데이터 치환
        for column, value in row.items():
            hwp.find_replace(f"{{{column}}}", str(value))
        
        # 저장
        file_name = f"{row['이름']}_{row['부서']}.pdf"
        hwp.save_as(f"{output_dir}/{file_name}", "PDF")
        
        print(f"✅ 생성: {file_name}")
    
    hwp.quit()
```

### 3. 텍스트 색상 일괄 변경
```python
def change_text_colors(hwp_file):
    """빨간색, 파란색 → 검은색 변경"""
    
    hwp = Hwp()
    hwp.open(hwp_file)
    
    # 색상 변경 설정
    option = hwp.HParameterSet.HFindReplace
    hwp.HAction.GetDefault("AllReplace", option.HSet)
    
    # 빨간색 → 검은색
    option.FindString = ""
    option.ReplaceString = ""
    option.IgnoreMessage = 1
    option.FindCharShape.TextColor = hwp.RGBColor(255, 0, 0)
    option.ReplaceCharShape.TextColor = hwp.RGBColor(0, 0, 0)
    hwp.HAction.Execute("AllReplace", option.HSet)
    
    # 파란색 → 검은색
    option.FindCharShape.TextColor = hwp.RGBColor(0, 0, 255)
    option.ReplaceCharShape.TextColor = hwp.RGBColor(0, 0, 0)
    hwp.HAction.Execute("AllReplace", option.HSet)
    
    hwp.save()
    hwp.quit()
```

### 4. PDF 병합
```python
from PyPDF2 import PdfMerger

def merge_pdfs(pdf_list, output_path):
    """여러 PDF를 하나로 병합"""
    
    merger = PdfMerger()
    
    for pdf in pdf_list:
        merger.append(pdf)
    
    merger.write(output_path)
    merger.close()
    
    print(f"✅ PDF 병합 완료: {output_path}")
```

### 5. 고급 자동화 (개선된 버전)
```python
class SmartHWPAutomation:
    """스마트 HWP 자동화 클래스"""
    
    def __init__(self):
        self.hwp = None
        self.init_hwp()
    
    def init_hwp(self):
        """한글 초기화 (개선된 버전)"""
        try:
            self.hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
            
            # 보안 모듈 등록
            self.hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
            
            # 메시지 무시
            self.hwp.HAction.GetDefault("OptionDialog", 
                                       self.hwp.HParameterSet.HOptionDialog.HSet)
            
            print("✅ 한글 초기화 성공")
            return True
        except Exception as e:
            print(f"❌ 초기화 실패: {e}")
            return False
    
    def safe_open(self, file_path):
        """안전한 파일 열기"""
        try:
            # 파일 경로 정규화 (인코딩 문제 해결)
            file_path = os.path.abspath(file_path)
            
            # forceopen으로 보안 경고 최소화
            self.hwp.Open(file_path, "HWP", "forceopen:true")
            return True
        except Exception as e:
            print(f"❌ 파일 열기 실패: {e}")
            return False
    
    def batch_convert_to_pdf(self, input_dir, output_dir):
        """디렉토리 전체 PDF 변환"""
        from pathlib import Path
        
        hwp_files = Path(input_dir).glob("*.hwp")
        
        for hwp_file in hwp_files:
            if self.safe_open(str(hwp_file)):
                pdf_path = Path(output_dir) / f"{hwp_file.stem}.pdf"
                self.hwp.SaveAs(str(pdf_path), "PDF")
                print(f"✅ 변환: {hwp_file.name} → {pdf_path.name}")
        
        self.hwp.Quit()
```

---

## 🔨 문제 해결

### 1. COM 객체 등록 오류
```
오류: "잘못된 클래스 문자열입니다"
해결: 관리자 권한으로 hwp.exe /regserver 실행
```

### 2. 파일명 깨짐
```python
# UTF-8 인코딩 명시
file_path = file_path.encode('utf-8').decode('utf-8')

# 안전한 파일명 생성
def safe_filename(name):
    for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(char, '_')
    return name
```

### 3. 보안 경고 팝업
```python
# forceopen 옵션 사용
hwp.Open(file_path, "HWP", "forceopen:true")

# IgnoreMessage 설정
option.IgnoreMessage = 1
```

### 4. XHwpWindows 오류
```python
# XHwpWindows 사용 피하기
# hwp.XHwpWindows.Item(0).Visible = False  # ❌

# 대신 다른 방법 사용
hwp.Run("FileNew")  # ✅
```

---

## 🎓 고급 활용

### 1. 병렬 처리
```python
from multiprocessing import Pool

def process_file(file_path):
    automation = SmartHWPAutomation()
    automation.convert_to_pdf(file_path)

with Pool(processes=4) as pool:
    pool.map(process_file, file_list)
```

### 2. 에러 로깅
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hwp_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

### 3. 진행률 표시
```python
from tqdm import tqdm

for file in tqdm(file_list, desc="처리 중"):
    process_file(file)
```

---

## 📊 성과 측정

### 시간 절감
- **수작업**: 문서당 5-10분
- **자동화**: 문서당 1-2초
- **효율**: 300배 향상

### 비용 절감
- **RPA 솔루션**: 1,400-2,000만원
- **Python 자동화**: 무료 (개발 시간만)
- **절감액**: 연간 수천만원

---

## 📚 참고 자료

### 공식 문서
- [pyhwpx 위키독스](https://wikidocs.net/book/8956)
- [hwpapi GitHub](https://github.com/JunDamin/hwpapi)
- [한컴 개발자 포럼](https://forum.developer.hancom.com)

### 커뮤니티
- [pyhwpx 오픈채팅방](https://open.kakao.com/o/gFCMxq8g)
- [PyCon KR 2023 발표영상](https://www.youtube.com/pyconkr)

### 강의
- [구름에듀 40시간 과정](https://edu.goorm.io/lecture/43213)
- [인프런 강의](https://inf.run/ChCF)
- [클래스101](https://101.gg/3G3IF6Z)

---

## ✨ 핵심 요약

### 시작하기
1. **한컴 오피스 설치** → **COM 등록** → **패키지 설치**
2. **pyhwpx 추천** (가장 활발한 커뮤니티)
3. **보안 설정** 미리 처리

### 실무 팁
- 템플릿 활용으로 효율 극대화
- 에러 처리 필수
- 로깅으로 디버깅 용이

### 주의사항
- Windows 전용
- 한컴 라이선스 필요
- 대용량 처리 시 메모리 관리

---

**"수작업 1시간 → 자동화 1분"** 🚀

이제 HWP 자동화의 모든 것을 마스터했습니다!
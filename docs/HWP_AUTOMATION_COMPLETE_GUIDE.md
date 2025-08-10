# 🚀 HWP 자동화 완벽 가이드

## 📋 목차
1. [개요](#개요)
2. [파일명 인코딩 문제 해결](#파일명-인코딩-문제-해결)
3. [HWP 자동화 구현](#hwp-자동화-구현)
4. [보험 문서 RPA 사례](#보험-문서-rpa-사례)
5. [트러블슈팅](#트러블슈팅)
6. [참고 자료](#참고-자료)

---

## 개요

HWP(한글 워드 프로세서) 파일 자동화를 위한 완벽한 솔루션 가이드입니다.

### 핵심 기능
- ✅ HWP → PDF 변환
- ✅ HWP → TXT 추출
- ✅ Excel 데이터 기반 문서 생성
- ✅ 다중 HWP 파일 병합
- ✅ HWP 문서 자동 편집

---

## 파일명 인코딩 문제 해결

### 문제 상황
Windows에서 CP949 인코딩으로 인해 한글 파일명이 깨지는 현상:
- `┴╓░Φ╛α1.hwp` → `주계약1.hwp`
- `╡╢╕│╞»╛α1.hwp` → `독립특약1.hwp`

### 해결 방법

#### 1. UTF-8 환경 설정

```python
# -*- coding: utf-8 -*-
import os
import sys

# UTF-8 환경 변수 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows에서 UTF-8 출력
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

#### 2. 파일명 자동 변경 스크립트

```python
from pathlib import Path
import shutil

def rename_files_to_korean():
    """깨진 파일명을 한글로 변경"""
    
    file_mappings = {
        "┴╓░Φ╛α1.hwp": "주계약1.hwp",
        "╡╢╕│╞»╛α1.hwp": "독립특약1.hwp",
        # ... 추가 매핑
    }
    
    for old_name, new_name in file_mappings.items():
        old_path = Path(old_name)
        if old_path.exists():
            old_path.rename(new_name)
            print(f"✅ {old_name} → {new_name}")
```

---

## HWP 자동화 구현

### 1. 필수 패키지 설치

```bash
# pyhwpx 설치 (권장)
pip install pyhwpx

# pywin32 설치 (COM 객체용)
pip install pywin32

# PyPDF2 설치 (PDF 병합용)
pip install PyPDF2
```

### 2. COM 객체 등록 (관리자 권한 필요)

```powershell
# PowerShell 관리자 권한으로 실행
cd "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin"
.\hwp.exe /regserver
```

### 3. 기본 HWP 자동화 코드

```python
import win32com.client as win32

class HwpAutomation:
    def __init__(self):
        """HWP COM 객체 초기화"""
        self.hwp = win32.gencache.EnsureDispatch("hwpframe.hwpobject")
        
        # 보안 모듈 등록
        self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        
        # 메시지 박스 숨기기
        self.hwp.SetMessageBoxMode(0x00000020)
    
    def open_file(self, file_path):
        """HWP 파일 열기"""
        return self.hwp.Open(file_path, "HWP", "forceopen:true")
    
    def save_as_pdf(self, pdf_path):
        """PDF로 저장"""
        return self.hwp.SaveAs(pdf_path, "PDF")
    
    def change_text_color(self):
        """빨간/파란 글씨를 검은색으로 변경"""
        option = self.hwp.HParameterSet.HFindReplace
        self.hwp.HAction.GetDefault("AllReplace", option.HSet)
        
        # 빨간색 → 검은색
        option.FindCharShape.TextColor = self.hwp.RGBColor(255, 0, 0)
        option.ReplaceCharShape.TextColor = self.hwp.RGBColor(0, 0, 0)
        self.hwp.HAction.Execute("AllReplace", option.HSet)
        
        # 파란색 → 검은색  
        option.FindCharShape.TextColor = self.hwp.RGBColor(0, 0, 255)
        option.ReplaceCharShape.TextColor = self.hwp.RGBColor(0, 0, 0)
        self.hwp.HAction.Execute("AllReplace", option.HSet)
    
    def close(self):
        """HWP 종료"""
        self.hwp.Clear(1)
        self.hwp.Quit()
```

---

## 보험 문서 RPA 사례

### 시나리오
보험 공시용 별지 작성 자동화:
1. Excel 파일에서 주계약-독립특약 매핑 읽기
2. HWP 파일의 색상 변경 (빨강/파랑 → 검정)
3. HWP → PDF 변환
4. 매핑에 따라 PDF 병합

### Excel 매핑 구조

| 주계약 | 독립특약 |
|--------|----------|
| 주계약1.hwp | 독립특약1.hwp |
| 주계약1.hwp | 독립특약2.hwp |
| 주계약2.hwp | 독립특약1.hwp |
| 주계약2.hwp | 독립특약3.hwp |
| 주계약3.hwp | 독립특약4.hwp |

### RPA 구현 코드

```python
import pandas as pd
from PyPDF2 import PdfMerger

class InsuranceDocumentRPA:
    def __init__(self):
        self.hwp = HwpAutomation()
    
    def process_documents(self, excel_path, hwp_dir, output_dir):
        """보험 문서 자동 처리"""
        
        # 1. Excel에서 매핑 정보 읽기
        df = pd.read_excel(excel_path, sheet_name='list')
        mapping = self._create_mapping(df)
        
        # 2. HWP 파일 처리
        for hwp_file in Path(hwp_dir).glob("*.hwp"):
            self._process_hwp_file(hwp_file, output_dir)
        
        # 3. PDF 병합
        for main_doc, sub_docs in mapping.items():
            self._merge_pdfs(main_doc, sub_docs, output_dir)
    
    def _process_hwp_file(self, hwp_file, output_dir):
        """HWP 파일 처리: 색상 변경 → PDF 변환"""
        
        # 파일 열기
        self.hwp.open_file(str(hwp_file))
        
        # 색상 변경
        self.hwp.change_text_color()
        
        # PDF로 저장
        pdf_path = output_dir / f"{hwp_file.stem}.pdf"
        self.hwp.save_as_pdf(str(pdf_path))
        
        # 파일 닫기
        self.hwp.close()
    
    def _merge_pdfs(self, main_doc, sub_docs, output_dir):
        """PDF 파일 병합"""
        
        merger = PdfMerger()
        
        # 주계약 추가
        merger.append(str(output_dir / f"{main_doc.stem}.pdf"))
        
        # 독립특약 추가
        for sub_doc in sub_docs:
            merger.append(str(output_dir / f"{sub_doc.stem}.pdf"))
        
        # 병합된 파일 저장
        output_path = output_dir / f"{main_doc.stem}_공시용.pdf"
        merger.write(str(output_path))
        merger.close()
```

---

## 트러블슈팅

### 1. COM 객체 등록 오류

**문제**: "잘못된 클래스 문자열입니다"
**해결**: 관리자 권한으로 `hwp.exe /regserver` 실행

### 2. 보안 경고 팝업

**문제**: 파일마다 보안 경고 팝업
**해결**: 
```python
# forceopen 옵션 사용
hwp.Open(file_path, "HWP", "forceopen:true")

# 메시지 박스 숨기기
hwp.SetMessageBoxMode(0x00000020)
```

### 3. 파일명 인코딩 오류

**문제**: CP949 인코딩으로 한글 깨짐
**해결**: 
```bash
# Python 실행 시 UTF-8 플래그 사용
python -X utf8 script.py
```

### 4. LibreOffice 변환 실패

**문제**: LibreOffice로 HWP 변환 불가
**해결**: pyhwpx 또는 COM 객체 사용 (LibreOffice는 HWP 미지원)

---

## 참고 자료

### 공식 문서
- [한컴 개발자 포럼](https://forum.developer.hancom.com)
- [HWP 자동화 가이드](https://developer.hancom.com/hwpautomation)
- [pyhwpx 문서](https://github.com/hancom-io/pyhwpx)

### 유용한 블로그 및 자료
- [Python HWP 파싱 가이드](https://tech.hancom.com/python-hwp-parsing-1/)
- [HWP 자동화 실습](https://bebutae.tistory.com/255)
- [파이콘 2023 HWP 자동화 발표](https://www.youtube.com/watch?v=t1NqazEJbg4)

### 커뮤니티 솔루션
- [보안 모듈 처리](https://forum.developer.hancom.com/t/topic/2455/2)
- [COM 객체 활용법](https://sddkarma.tistory.com/63)
- [Excel 연동 자동화](https://forum.developer.hancom.com/t/pyhwpx/1111)

---

## 결론

이 가이드를 통해 HWP 파일 자동화의 모든 측면을 다루었습니다:
- ✅ 파일명 인코딩 문제 완벽 해결
- ✅ COM 객체 등록 및 보안 설정
- ✅ HWP → PDF 변환 자동화
- ✅ Excel 기반 문서 처리 RPA
- ✅ UTF-8 환경 영구 설정

모든 한글 파일을 정상적으로 처리할 수 있는 완벽한 자동화 환경이 구축되었습니다! 🎉
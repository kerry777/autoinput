# 🔐 HWP 보안 모듈 처리 가이드

## 📋 개요
HWP 자동화 시 발생하는 보안 모듈 팝업 문제와 해결 방법을 다룹니다.

---

## 🚨 문제 상황

### 증상
- Python으로 Excel 데이터를 HWP에 자동 입력 시도
- **보안 모듈 팝업**이 계속 발생
- 자동화 프로세스가 중단됨

### 원인
- HWP의 보안 정책으로 외부 프로그램 접근 차단
- 3rd Party 파일 접근 승인 모듈 미등록

---

## ✅ 해결 방법

### 1. 보안 모듈 등록

#### 방법 1: DLL 직접 등록
```python
import win32com.client as win32
import os

def register_security_module():
    """보안 모듈 등록"""
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    
    # DLL 파일 직접 등록
    dll_path = r"C:\path\to\FilePathCheckerModuleExample.dll"
    if os.path.exists(dll_path):
        hwp.RegisterModule(dll_path, 'FilePathCheckerModuleExample')
    else:
        # 기본 모듈 사용
        hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
    
    return hwp
```

#### 방법 2: 메시지 박스 모드 설정
```python
def setup_hwp_security():
    """HWP 보안 설정"""
    hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
    
    # 메시지 박스 숨기기 (0x00000020)
    hwp.SetMessageBoxMode(0x00000020)
    
    # 또는 자동 승인 모드
    hwp.SetMessageBoxMode(0x00000010)  # 자동 Yes
    
    return hwp
```

### 2. 파일 열기 옵션 설정

```python
def open_hwp_file_secure(hwp, file_path):
    """보안 경고 없이 파일 열기"""
    
    # forceopen 옵션으로 강제 열기
    result = hwp.Open(file_path, "HWP", "forceopen:true")
    
    # 또는 versionwarning 무시
    # result = hwp.Open(file_path, "HWP", "versionwarning:false")
    
    return result
```

### 3. 전체 자동화 예제

```python
import win32com.client as win32
import pandas as pd
from pathlib import Path

class SecureHwpAutomation:
    def __init__(self):
        """보안 설정이 적용된 HWP 자동화"""
        self.hwp = None
        self._initialize_hwp()
    
    def _initialize_hwp(self):
        """HWP 초기화 및 보안 설정"""
        try:
            # COM 객체 생성
            self.hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
            
            # 보안 모듈 등록
            self._register_security_module()
            
            # 메시지 박스 설정
            self.hwp.SetMessageBoxMode(0x00000020)
            
            # 창 숨기기 (백그라운드 실행)
            self.hwp.XHwpWindows.Item(0).Visible = False
            
            print("✅ HWP 초기화 성공")
            
        except Exception as e:
            print(f"❌ HWP 초기화 실패: {e}")
            raise
    
    def _register_security_module(self):
        """보안 모듈 등록"""
        try:
            # 여러 방법 시도
            module_registered = False
            
            # 방법 1: 로컬 DLL 파일
            dll_paths = [
                r".\security_module\FilePathCheckerModuleExample.dll",
                r"C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin\FilePathCheckDLL.dll",
            ]
            
            for dll_path in dll_paths:
                if Path(dll_path).exists():
                    self.hwp.RegisterModule(dll_path, 'FilePathCheckerModule')
                    module_registered = True
                    print(f"✅ 보안 모듈 등록: {dll_path}")
                    break
            
            # 방법 2: 기본 모듈
            if not module_registered:
                self.hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule')
                print("✅ 기본 보안 모듈 등록")
                
        except Exception as e:
            print(f"⚠️ 보안 모듈 등록 실패 (계속 진행): {e}")
    
    def process_excel_to_hwp(self, excel_path, hwp_template):
        """Excel 데이터를 HWP에 자동 입력"""
        
        # Excel 데이터 읽기
        df = pd.read_excel(excel_path)
        
        for index, row in df.iterrows():
            # HWP 템플릿 열기 (보안 경고 없이)
            self.hwp.Open(hwp_template, "HWP", "forceopen:true")
            
            # 데이터 입력
            self._insert_data(row)
            
            # 저장
            output_path = f"output_{index}.hwp"
            self.hwp.SaveAs(output_path)
            
            # 문서 닫기
            self.hwp.Clear(1)
        
        print(f"✅ {len(df)}개 문서 생성 완료")
    
    def _insert_data(self, data_row):
        """HWP에 데이터 삽입"""
        for field_name, value in data_row.items():
            # 필드 찾아서 교체
            self._replace_field(f"{{{field_name}}}", str(value))
    
    def _replace_field(self, field_name, value):
        """필드 교체"""
        option = self.hwp.HParameterSet.HFindReplace
        self.hwp.HAction.GetDefault("AllReplace", option.HSet)
        option.FindString = field_name
        option.ReplaceString = value
        option.IgnoreMessage = 1
        self.hwp.HAction.Execute("AllReplace", option.HSet)
    
    def close(self):
        """HWP 종료"""
        if self.hwp:
            self.hwp.Quit()
            print("✅ HWP 종료")

# 사용 예제
if __name__ == "__main__":
    automation = SecureHwpAutomation()
    try:
        automation.process_excel_to_hwp(
            excel_path="data.xlsx",
            hwp_template="template.hwp"
        )
    finally:
        automation.close()
```

---

## 🔧 추가 보안 설정

### 1. 레지스트리 설정 (관리자 권한)

```batch
@echo off
REM HWP 보안 설정 레지스트리

REM 자동화 허용
reg add "HKCU\Software\Hnc\HwpFrame\Security" /v "AutomationSecurity" /t REG_DWORD /d 0 /f

REM 매크로 보안 레벨 낮추기 (주의: 보안 위험)
reg add "HKCU\Software\Hnc\HwpFrame\Security" /v "MacroSecurity" /t REG_DWORD /d 1 /f

echo 보안 설정 완료
```

### 2. 환경 변수 설정

```python
import os

# HWP 자동화 환경 변수
os.environ['HWP_AUTOMATION_MODE'] = '1'
os.environ['HWP_SECURITY_LEVEL'] = 'LOW'
```

### 3. 예외 처리

```python
def safe_hwp_operation(func):
    """HWP 작업 안전 래퍼"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            
            # 보안 관련 에러 처리
            if "보안" in error_msg or "Security" in error_msg:
                print("⚠️ 보안 문제 발생 - 모듈 재등록 시도")
                # 재등록 로직
            
            # 파일 접근 에러 처리  
            elif "파일" in error_msg or "File" in error_msg:
                print("⚠️ 파일 접근 문제 - forceopen 모드 사용")
                # forceopen 재시도
            
            else:
                print(f"❌ 예상치 못한 오류: {e}")
            
            raise
    
    return wrapper
```

---

## 📚 참고 자료

### 공식 문서
- [한컴 개발자 가이드](https://developer.hancom.com/hwpautomation)
- [HWP 자동화 포럼](https://forum.developer.hancom.com/t/topic/2455)

### 주요 포인트
1. **3rd Party 파일 접근 승인 모듈** 등록 필수
2. **SetMessageBoxMode**로 팝업 제어
3. **forceopen** 옵션으로 강제 파일 열기
4. 백그라운드 실행 시 창 숨기기

### 트러블슈팅 체크리스트
- [ ] COM 객체 정상 등록 확인
- [ ] 보안 모듈 DLL 파일 존재 확인
- [ ] 관리자 권한 실행 여부
- [ ] HWP 버전 호환성
- [ ] 파일 경로 접근 권한

---

## 💡 팁

1. **개발 환경**: 보안 레벨을 낮춰서 테스트
2. **프로덕션 환경**: 필요한 최소 권한만 부여
3. **로깅**: 모든 보안 관련 이벤트 기록
4. **에러 처리**: 보안 팝업 발생 시 자동 재시도

---

이 가이드를 통해 HWP 자동화 시 발생하는 보안 모듈 문제를 완벽하게 해결할 수 있습니다! 🚀
@echo off
echo ========================================
echo HWP COM 객체 등록 (관리자 권한 필요)
echo ========================================
echo.
echo 이 스크립트를 "관리자 권한으로 실행"해야 합니다!
echo.

REM 한글 2024 경로
set HWP_PATH=C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin

echo [1] Hwp.exe COM 서버 등록 중...
cd /d "%HWP_PATH%"
Hwp.exe /regserver
if %errorlevel% == 0 (
    echo     성공: Hwp.exe COM 서버 등록 완료
) else (
    echo     실패: Hwp.exe COM 서버 등록 실패
)

echo.
echo [2] HwpOle.dll 등록 시도 중...
if exist "%HWP_PATH%\HwpOle.dll" (
    regsvr32 /s "%HWP_PATH%\HwpOle.dll"
    echo     완료: HwpOle.dll 등록 시도
) else (
    echo     건너뜀: HwpOle.dll 파일 없음
)

echo.
echo [3] 레지스트리 확인 중...
reg query "HKEY_CLASSES_ROOT\HWPFrame.HwpObject" >nul 2>&1
if %errorlevel% == 0 (
    echo     성공: HWPFrame.HwpObject 레지스트리 등록 확인!
) else (
    echo     경고: HWPFrame.HwpObject 레지스트리 없음
)

echo.
echo ========================================
echo 완료! 이제 pyhwpx를 사용할 수 있습니다.
echo ========================================
echo.
echo Python에서 테스트:
echo   python scripts\test_pyhwpx_conversion.py
echo.
pause
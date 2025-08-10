@echo off
REM HWP to PDF 일괄 변환 배치 파일
REM LibreOffice가 설치되어 있어야 작동합니다

set SOFFICE="C:\Program Files (x86)\LibreOffice\program\soffice.exe"
set INPUT_DIR=C:\projects\autoinput\data\downloads
set OUTPUT_DIR=C:\projects\autoinput\data\libreoffice_converted

echo ========================================
echo HWP to PDF 일괄 변환
echo ========================================
echo.
echo LibreOffice 경로: %SOFFICE%
echo 입력 디렉토리: %INPUT_DIR%
echo 출력 디렉토리: %OUTPUT_DIR%
echo.

REM 출력 디렉토리 생성
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM HWP 파일 변환
echo 변환 시작...
echo.

REM 개별 파일 변환 (경로에 한글이 포함된 경우)
echo [1] 증거서류반환신청서.hwp 변환 중...
%SOFFICE% --headless --convert-to pdf --outdir "%OUTPUT_DIR%" "%INPUT_DIR%\attachments_working\post_60125\증거서류반환신청서.hwp"

echo [2] 수령증.hwp 변환 중...
%SOFFICE% --headless --convert-to pdf --outdir "%OUTPUT_DIR%" "%INPUT_DIR%\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"

echo [3] 장기요양인정신청서.hwp 변환 중...
%SOFFICE% --headless --convert-to pdf --outdir "%OUTPUT_DIR%" "%INPUT_DIR%\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"

echo.
echo ========================================
echo 변환 완료!
echo 출력 디렉토리를 확인하세요: %OUTPUT_DIR%
echo ========================================
pause
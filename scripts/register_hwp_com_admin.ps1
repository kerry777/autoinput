# HWP COM 객체 등록 PowerShell 스크립트
# 관리자 권한으로 실행 필요

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HWP COM 객체 등록 (관리자 권한)" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 관리자 권한 확인
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[경고] 관리자 권한이 없습니다!" -ForegroundColor Red
    Write-Host "이 스크립트를 관리자 권한으로 다시 실행합니다..." -ForegroundColor Yellow
    
    # 관리자 권한으로 재실행
    Start-Process powershell.exe -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "[확인] 관리자 권한으로 실행 중입니다." -ForegroundColor Green
Write-Host ""

# 한글 2024 경로
$hwpPath = "C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin"
$hwpExe = Join-Path $hwpPath "Hwp.exe"

# 1. Hwp.exe 존재 확인
if (Test-Path $hwpExe) {
    Write-Host "[1] Hwp.exe 찾음: $hwpExe" -ForegroundColor Green
    
    # COM 서버 등록
    Write-Host "[2] COM 서버 등록 중..." -ForegroundColor Yellow
    try {
        $process = Start-Process -FilePath $hwpExe -ArgumentList "/regserver" -PassThru -Wait
        if ($process.ExitCode -eq 0) {
            Write-Host "    성공: Hwp.exe COM 서버 등록 완료!" -ForegroundColor Green
        } else {
            Write-Host "    경고: 종료 코드 $($process.ExitCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "    오류: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[오류] Hwp.exe를 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "경로: $hwpExe" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. HwpOle.dll 등록 (있는 경우)
$hwpOle = Join-Path $hwpPath "HwpOle.dll"
if (Test-Path $hwpOle) {
    Write-Host "[3] HwpOle.dll 등록 중..." -ForegroundColor Yellow
    try {
        Start-Process regsvr32.exe -ArgumentList "/s `"$hwpOle`"" -Wait
        Write-Host "    완료: HwpOle.dll 등록" -ForegroundColor Green
    } catch {
        Write-Host "    오류: $_" -ForegroundColor Red
    }
} else {
    Write-Host "[3] HwpOle.dll 파일 없음 (건너뜀)" -ForegroundColor Gray
}

Write-Host ""

# 3. 레지스트리 확인
Write-Host "[4] 레지스트리 등록 확인 중..." -ForegroundColor Yellow

$registryKeys = @(
    "HKCR:\HWPFrame.HwpObject",
    "HKCR:\CLSID\{BD9C32DE-3155-4691-8972-097D53B10052}",
    "HKCR:\Hwp.Application"
)

$foundAny = $false
foreach ($key in $registryKeys) {
    if (Test-Path $key) {
        Write-Host "    ✓ 발견: $key" -ForegroundColor Green
        $foundAny = $true
    } else {
        Write-Host "    × 없음: $key" -ForegroundColor Gray
    }
}

Write-Host ""

if ($foundAny) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "성공! COM 객체가 등록되었습니다." -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "이제 다음 명령으로 테스트할 수 있습니다:" -ForegroundColor Yellow
    Write-Host "  python scripts\test_pyhwpx_conversion.py" -ForegroundColor White
} else {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "경고: COM 객체 등록을 확인할 수 없습니다." -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "다음을 시도해보세요:" -ForegroundColor Yellow
    Write-Host "1. 한글 2024를 관리자 권한으로 한 번 실행" -ForegroundColor White
    Write-Host "2. 한글 2024 재설치" -ForegroundColor White
}

Write-Host ""
Write-Host "아무 키나 누르면 종료합니다..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
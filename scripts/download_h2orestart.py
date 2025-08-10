"""
H2Orestart LibreOffice 확장 프로그램 다운로드 스크립트
HWP/HWPX 파일 지원을 위한 LibreOffice 확장 프로그램
"""

import requests
import os
from pathlib import Path

def download_h2orestart():
    """H2Orestart 확장 프로그램 다운로드"""
    
    # LibreOffice Extensions 페이지 URL
    extension_url = "https://extensions.libreoffice.org/en/extensions/show/27504"
    
    print("=" * 60)
    print("H2Orestart Extension 다운로드 정보")
    print("=" * 60)
    print()
    print("[INFO] H2Orestart 확장 프로그램 정보:")
    print("- HWP 및 HWPX 파일 지원 추가")
    print("- LibreOffice에서 한컴 파일을 ODT로 변환 가능")
    print("- PDF 변환 지원 (headless 모드)")
    print()
    print("[DOWNLOAD] 다운로드 페이지:")
    print(f"  {extension_url}")
    print()
    print("[설치 방법]")
    print("1. 위 링크에서 .oxt 파일 다운로드")
    print("2. LibreOffice 실행")
    print("3. 도구 > 확장 관리자 (또는 Ctrl+Alt+E)")
    print("4. '추가' 버튼 클릭")
    print("5. 다운로드한 .oxt 파일 선택")
    print("6. LibreOffice 재시작")
    print()
    print("[명령줄 사용법 (설치 후)]")
    print('soffice.exe --headless --infilter="Hwp2002_File" --convert-to pdf:writer_pdf_Export YOUR_FILE.hwp')
    print('soffice.exe --headless --convert-to pdf:writer_pdf_Export YOUR_FILE.hwpx')
    print()
    print("=" * 60)
    
    # 다운로드 디렉토리 생성
    download_dir = Path(r"C:\projects\autoinput\data\libreoffice_extensions")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[INFO] 확장 프로그램 다운로드 디렉토리: {download_dir}")
    print("\n브라우저에서 수동으로 다운로드하세요:")
    print(extension_url)
    
    # Windows에서 기본 브라우저로 URL 열기
    import webbrowser
    webbrowser.open(extension_url)
    
    print("\n[SUCCESS] 브라우저에서 페이지가 열렸습니다.")
    print("다운로드 후 LibreOffice Extension Manager에서 설치하세요.")

if __name__ == "__main__":
    download_h2orestart()
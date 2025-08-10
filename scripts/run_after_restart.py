#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
시스템 재시작 후 실행할 HWP to PDF 변환 스크립트
LibreOffice가 정상적으로 작동할 때 사용하세요.
"""

import subprocess
from pathlib import Path
import sys
import os

def convert_hwp_files():
    """HWP 파일들을 PDF로 변환"""
    
    # LibreOffice 경로
    soffice = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    
    # 변환할 파일들
    hwp_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    # 출력 디렉토리
    output_dir = r"C:\projects\autoinput\data\libreoffice_converted"
    Path(output_dir).mkdir(exist_ok=True)
    
    print("="*60)
    print("LibreOffice HWP to PDF 변환")
    print("="*60)
    
    success_count = 0
    
    for hwp_file in hwp_files:
        if not Path(hwp_file).exists():
            print(f"❌ 파일 없음: {hwp_file}")
            continue
        
        file_name = Path(hwp_file).name
        print(f"\n변환 중: {file_name}")
        
        # LibreOffice 명령 실행
        cmd = [
            soffice,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            hwp_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # 결과 확인
            expected_pdf = Path(output_dir) / f"{Path(hwp_file).stem}.pdf"
            
            if expected_pdf.exists():
                print(f"✅ 성공: {expected_pdf.name}")
                success_count += 1
            else:
                print(f"❌ 실패: PDF 파일이 생성되지 않음")
                if result.stderr:
                    print(f"   오류: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            print(f"❌ 시간 초과")
        except Exception as e:
            print(f"❌ 오류: {e}")
    
    print(f"\n{'='*60}")
    print(f"변환 완료: {success_count}/{len(hwp_files)} 성공")
    print(f"출력 디렉토리: {output_dir}")
    print(f"{'='*60}")
    
    # 변환된 PDF 파일 목록
    pdf_files = list(Path(output_dir).glob("*.pdf"))
    if pdf_files:
        print("\n생성된 PDF 파일:")
        for pdf in pdf_files:
            size_kb = pdf.stat().st_size / 1024
            print(f"  - {pdf.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    print("시스템 재시작 후 LibreOffice가 정상 작동하는지 확인하고 실행하세요.")
    print()
    
    # LibreOffice 설치 확인
    soffice_path = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    if Path(soffice_path).exists():
        print(f"✅ LibreOffice 설치 확인: {soffice_path}")
        
        # 버전 확인 시도
        try:
            result = subprocess.run([soffice_path, "--version"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   버전: {result.stdout.strip()}")
                print("\n변환을 시작하시겠습니까? (y/n): ", end="")
                
                if input().lower() == 'y':
                    convert_hwp_files()
            else:
                print("⚠️ LibreOffice가 응답하지 않습니다. 재시작이 필요합니다.")
        except:
            print("⚠️ LibreOffice 실행 오류. 시스템 재시작 후 다시 시도하세요.")
    else:
        print("❌ LibreOffice가 설치되어 있지 않습니다.")
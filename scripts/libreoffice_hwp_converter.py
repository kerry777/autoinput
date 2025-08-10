#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LibreOffice를 사용한 HWP to PDF 변환 자동화
LibreOffice가 설치되어 있어야 작동합니다.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import codecs
import json

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

class LibreOfficeConverter:
    """LibreOffice를 사용한 HWP 변환기"""
    
    def __init__(self):
        self.soffice_path = self.find_libreoffice()
        
    def find_libreoffice(self):
        """LibreOffice 설치 경로 찾기"""
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            r"C:\Program Files\LibreOffice 7\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice 7\program\soffice.exe",
            r"C:\Program Files\LibreOffice 24.8\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice 24.8\program\soffice.exe"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                print(f"LibreOffice 발견: {path}")
                return path
        
        # PATH에서 찾기
        try:
            result = subprocess.run(["where", "soffice"], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                print(f"LibreOffice 발견 (PATH): {path}")
                return path
        except:
            pass
        
        print("LibreOffice를 찾을 수 없습니다.")
        print("LibreOffice를 설치하고 시스템을 재시작해주세요.")
        return None
    
    def convert_to_pdf(self, hwp_path, output_dir=None):
        """HWP를 PDF로 변환"""
        if not self.soffice_path:
            print("LibreOffice가 설치되어 있지 않습니다.")
            return None
        
        hwp_path = Path(hwp_path)
        if not hwp_path.exists():
            print(f"파일이 존재하지 않습니다: {hwp_path}")
            return None
        
        # 출력 디렉토리 설정
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
        else:
            output_dir = hwp_path.parent
        
        # 예상 출력 파일 경로
        pdf_path = output_dir / f"{hwp_path.stem}.pdf"
        
        # 이미 PDF가 있는지 확인
        if pdf_path.exists():
            print(f"PDF가 이미 존재합니다: {pdf_path}")
            overwrite = input("덮어쓰시겠습니까? (y/n): ")
            if overwrite.lower() != 'y':
                return pdf_path
        
        # LibreOffice 명령 실행
        cmd = [
            str(self.soffice_path),
            "--headless",  # GUI 없이 실행
            "--convert-to", "pdf",  # PDF로 변환
            "--outdir", str(output_dir),  # 출력 디렉토리
            str(hwp_path)  # 입력 파일
        ]
        
        print(f"변환 시작: {hwp_path.name}")
        print(f"명령: {' '.join(cmd)}")
        
        try:
            # 변환 실행
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # 결과 확인
            if result.returncode == 0:
                # PDF 파일 생성 확인 (약간의 지연 필요할 수 있음)
                time.sleep(1)
                
                if pdf_path.exists():
                    file_size = pdf_path.stat().st_size
                    print(f"✅ 변환 성공: {pdf_path}")
                    print(f"   파일 크기: {file_size:,} bytes")
                    return pdf_path
                else:
                    print(f"⚠️ 변환이 완료되었지만 PDF 파일을 찾을 수 없습니다.")
                    print(f"   예상 경로: {pdf_path}")
            else:
                print(f"❌ 변환 실패")
                print(f"   오류: {result.stderr}")
                
                # HWP 필터 문제일 수 있음
                if "source file could not be loaded" in result.stderr:
                    print("\n💡 해결 방법:")
                    print("   1. 시스템 재시작 후 다시 시도")
                    print("   2. LibreOffice에서 HWP 파일을 직접 열어보기")
                    print("   3. LibreOffice 최신 버전 설치")
                
        except subprocess.TimeoutExpired:
            print("❌ 변환 시간 초과 (60초)")
        except Exception as e:
            print(f"❌ 변환 오류: {e}")
        
        return None
    
    def batch_convert(self, hwp_files, output_dir=None):
        """여러 HWP 파일 일괄 변환"""
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        for hwp_file in hwp_files:
            hwp_path = Path(hwp_file)
            
            if not hwp_path.exists():
                print(f"⏭️ 파일 없음: {hwp_path}")
                results['skipped'].append(str(hwp_path))
                continue
            
            print(f"\n{'='*60}")
            print(f"파일 {len(results['success'])+1}/{len(hwp_files)}: {hwp_path.name}")
            print(f"{'='*60}")
            
            pdf_path = self.convert_to_pdf(hwp_path, output_dir)
            
            if pdf_path:
                results['success'].append({
                    'hwp': str(hwp_path),
                    'pdf': str(pdf_path),
                    'size': pdf_path.stat().st_size
                })
            else:
                results['failed'].append(str(hwp_path))
        
        # 결과 요약
        print(f"\n{'='*60}")
        print("변환 완료 요약")
        print(f"{'='*60}")
        print(f"✅ 성공: {len(results['success'])}개")
        print(f"❌ 실패: {len(results['failed'])}개")
        print(f"⏭️ 건너뜀: {len(results['skipped'])}개")
        
        return results
    
    def test_libreoffice(self):
        """LibreOffice 설치 테스트"""
        if not self.soffice_path:
            return False
        
        try:
            # 버전 확인
            cmd = [str(self.soffice_path), "--version"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"✅ LibreOffice 정상 작동")
                print(f"   버전: {version}")
                return True
            else:
                print(f"❌ LibreOffice 실행 오류")
                return False
                
        except Exception as e:
            print(f"❌ LibreOffice 테스트 실패: {e}")
            return False


def main():
    """메인 함수"""
    print("LibreOffice HWP to PDF 변환기")
    print("="*60)
    
    # 변환기 생성
    converter = LibreOfficeConverter()
    
    # LibreOffice 테스트
    if not converter.test_libreoffice():
        print("\n⚠️ LibreOffice가 제대로 설치되지 않았습니다.")
        print("설치 후 시스템을 재시작하고 다시 시도해주세요.")
        return
    
    # 테스트 파일들
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    # 존재하는 파일만 필터링
    existing_files = [f for f in test_files if Path(f).exists()]
    
    if not existing_files:
        print("\n변환할 HWP 파일이 없습니다.")
        return
    
    print(f"\n변환할 파일: {len(existing_files)}개")
    
    # 출력 디렉토리
    output_dir = Path(r"C:\projects\autoinput\data\libreoffice_converted")
    output_dir.mkdir(exist_ok=True)
    
    # 일괄 변환
    results = converter.batch_convert(existing_files, output_dir)
    
    # 결과 저장
    result_file = output_dir / f"conversion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 결과 저장: {result_file}")
    
    # 성공한 PDF 파일들에서 텍스트 추출
    if results['success']:
        print(f"\n{'='*60}")
        print("PDF 텍스트 추출")
        print(f"{'='*60}")
        
        try:
            import pdfplumber
            
            for item in results['success']:
                pdf_path = Path(item['pdf'])
                print(f"\n📄 {pdf_path.name}")
                
                with pdfplumber.open(pdf_path) as pdf:
                    # 첫 페이지 텍스트 미리보기
                    if pdf.pages:
                        text = pdf.pages[0].extract_text()
                        if text:
                            preview = text[:200] + "..." if len(text) > 200 else text
                            print(f"   텍스트 미리보기: {preview}")
                        else:
                            print("   텍스트를 추출할 수 없습니다.")
                            
        except ImportError:
            print("\npdfplumber가 설치되어 있지 않습니다.")
            print("PDF 텍스트 추출을 원하시면: pip install pdfplumber")


if __name__ == "__main__":
    main()
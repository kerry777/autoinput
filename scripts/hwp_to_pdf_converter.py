#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HWP to PDF 변환 솔루션
여러 방법을 시도하여 안정적으로 HWP를 PDF로 변환
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
import codecs

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

class HWPtoPDFConverter:
    """HWP to PDF 변환기"""
    
    def __init__(self, hwp_path):
        self.hwp_path = Path(hwp_path)
        self.pdf_path = None
        self.conversion_method = None
        
    def convert(self, output_path=None):
        """HWP를 PDF로 변환 (여러 방법 시도)"""
        
        if output_path:
            self.pdf_path = Path(output_path)
        else:
            self.pdf_path = self.hwp_path.with_suffix('.pdf')
        
        # 이미 PDF가 존재하는지 확인
        if self.pdf_path.exists():
            print(f"PDF 파일이 이미 존재합니다: {self.pdf_path}")
            self.conversion_method = "existing"
            return True
        
        # 방법 1: LibreOffice 사용
        if self._convert_with_libreoffice():
            return True
        
        # 방법 2: hwp5html을 사용한 HTML 변환 후 PDF 생성
        if self._convert_via_html():
            return True
        
        # 방법 3: 한컴 오피스 API 사용 (Windows)
        if self._convert_with_hancom_api():
            return True
        
        # 방법 4: pyhwp의 실험적 변환 기능
        if self._convert_with_pyhwp():
            return True
        
        print("모든 변환 방법이 실패했습니다.")
        return False
    
    def _convert_with_libreoffice(self):
        """LibreOffice를 사용한 변환"""
        try:
            # LibreOffice 실행 파일 경로 확인
            soffice_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                "soffice"  # PATH에 있는 경우
            ]
            
            soffice = None
            for path in soffice_paths:
                if Path(path).exists() or self._command_exists(path):
                    soffice = path
                    break
            
            if not soffice:
                print("LibreOffice가 설치되어 있지 않습니다.")
                return False
            
            # 변환 명령 실행
            cmd = [
                soffice,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(self.pdf_path.parent),
                str(self.hwp_path)
            ]
            
            print(f"LibreOffice로 변환 시도: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and self.pdf_path.exists():
                print(f"LibreOffice 변환 성공: {self.pdf_path}")
                self.conversion_method = "libreoffice"
                return True
            else:
                print(f"LibreOffice 변환 실패: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"LibreOffice 변환 오류: {e}")
            return False
    
    def _convert_via_html(self):
        """HTML을 거쳐서 PDF로 변환"""
        try:
            # hwp5html 명령 사용
            html_path = self.hwp_path.with_suffix('.html')
            
            # HWP → HTML 변환
            cmd_html = ["hwp5html", str(self.hwp_path)]
            print(f"HTML 변환 시도: {' '.join(cmd_html)}")
            
            result = subprocess.run(cmd_html, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and html_path.exists():
                print(f"HTML 변환 성공: {html_path}")
                
                # HTML → PDF 변환 (pdfkit 또는 weasyprint 사용)
                if self._html_to_pdf(html_path):
                    self.conversion_method = "html_intermediate"
                    return True
            
            return False
            
        except Exception as e:
            print(f"HTML 경유 변환 오류: {e}")
            return False
    
    def _html_to_pdf(self, html_path):
        """HTML을 PDF로 변환"""
        try:
            # weasyprint 시도
            import weasyprint
            print(f"WeasyPrint로 PDF 변환 시도")
            weasyprint.HTML(filename=str(html_path)).write_pdf(str(self.pdf_path))
            
            if self.pdf_path.exists():
                print(f"WeasyPrint 변환 성공: {self.pdf_path}")
                return True
                
        except ImportError:
            print("WeasyPrint가 설치되어 있지 않습니다.")
        except Exception as e:
            print(f"WeasyPrint 변환 오류: {e}")
        
        try:
            # pdfkit 시도
            import pdfkit
            print(f"pdfkit으로 PDF 변환 시도")
            pdfkit.from_file(str(html_path), str(self.pdf_path))
            
            if self.pdf_path.exists():
                print(f"pdfkit 변환 성공: {self.pdf_path}")
                return True
                
        except ImportError:
            print("pdfkit이 설치되어 있지 않습니다.")
        except Exception as e:
            print(f"pdfkit 변환 오류: {e}")
        
        return False
    
    def _convert_with_hancom_api(self):
        """한컴 오피스 API를 사용한 변환"""
        try:
            import win32com.client
            
            print("한컴 오피스 API로 변환 시도")
            hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
            
            # 파일 열기
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModuleExample")
            hwp.Open(str(self.hwp_path))
            
            # PDF로 저장
            hwp.SaveAs(str(self.pdf_path), "PDF")
            hwp.Quit()
            
            if self.pdf_path.exists():
                print(f"한컴 API 변환 성공: {self.pdf_path}")
                self.conversion_method = "hancom_api"
                return True
                
        except ImportError:
            print("pywin32가 설치되어 있지 않습니다.")
        except Exception as e:
            print(f"한컴 API 변환 오류: {e}")
        
        return False
    
    def _convert_with_pyhwp(self):
        """pyhwp의 실험적 변환 기능 사용"""
        try:
            # ODT로 먼저 변환 후 PDF로
            odt_path = self.hwp_path.with_suffix('.odt')
            
            cmd_odt = ["hwp5odt", str(self.hwp_path), str(odt_path)]
            print(f"ODT 변환 시도: {' '.join(cmd_odt)}")
            
            result = subprocess.run(cmd_odt, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and odt_path.exists():
                print(f"ODT 변환 성공: {odt_path}")
                
                # ODT를 PDF로 변환 (LibreOffice 필요)
                if self._odt_to_pdf(odt_path):
                    self.conversion_method = "pyhwp_odt"
                    return True
                    
        except Exception as e:
            print(f"pyhwp 변환 오류: {e}")
        
        return False
    
    def _odt_to_pdf(self, odt_path):
        """ODT를 PDF로 변환"""
        try:
            # LibreOffice로 ODT → PDF 변환
            cmd = [
                "soffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(self.pdf_path.parent),
                str(odt_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and self.pdf_path.exists():
                print(f"ODT→PDF 변환 성공: {self.pdf_path}")
                return True
                
        except Exception as e:
            print(f"ODT→PDF 변환 오류: {e}")
        
        return False
    
    def _command_exists(self, command):
        """명령어 존재 여부 확인"""
        try:
            subprocess.run([command, "--version"], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def get_conversion_info(self):
        """변환 정보 반환"""
        return {
            "hwp_file": str(self.hwp_path),
            "pdf_file": str(self.pdf_path) if self.pdf_path else None,
            "conversion_method": self.conversion_method,
            "timestamp": datetime.now().isoformat()
        }


def batch_convert_hwp_to_pdf(hwp_files, output_dir=None):
    """여러 HWP 파일을 PDF로 일괄 변환"""
    
    results = []
    success_count = 0
    
    for hwp_file in hwp_files:
        if not Path(hwp_file).exists():
            print(f"파일이 존재하지 않습니다: {hwp_file}")
            continue
        
        print(f"\n{'='*60}")
        print(f"변환 시작: {Path(hwp_file).name}")
        print(f"{'='*60}")
        
        converter = HWPtoPDFConverter(hwp_file)
        
        if output_dir:
            pdf_path = Path(output_dir) / f"{Path(hwp_file).stem}.pdf"
        else:
            pdf_path = None
        
        if converter.convert(pdf_path):
            success_count += 1
            results.append(converter.get_conversion_info())
            print(f"✅ 변환 성공: {converter.conversion_method} 방법 사용")
        else:
            results.append({
                "hwp_file": str(hwp_file),
                "pdf_file": None,
                "conversion_method": "failed",
                "timestamp": datetime.now().isoformat()
            })
            print(f"❌ 변환 실패")
    
    print(f"\n{'='*60}")
    print(f"변환 완료: {success_count}/{len(hwp_files)} 성공")
    print(f"{'='*60}")
    
    return results


def test_conversion():
    """변환 테스트"""
    
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    # 존재하는 파일만 필터링
    existing_files = [f for f in test_files if Path(f).exists()]
    
    if not existing_files:
        print("테스트할 HWP 파일이 없습니다.")
        return
    
    output_dir = Path(r"C:\projects\autoinput\data\hwp_to_pdf_converted")
    output_dir.mkdir(exist_ok=True)
    
    results = batch_convert_hwp_to_pdf(existing_files, output_dir)
    
    # 결과 저장
    result_file = output_dir / "conversion_results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n변환 결과 저장: {result_file}")


if __name__ == "__main__":
    print("HWP to PDF 변환 테스트")
    print("여러 방법을 시도하여 안정적으로 변환합니다.")
    test_conversion()
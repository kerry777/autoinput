#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
hwpapi를 사용한 HWP 파일 변환 스크립트
한컴 오피스가 설치되어 있어야 사용 가능
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import codecs

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

try:
    from hwpapi import Hwp
except ImportError:
    print("hwpapi 설치 필요: pip install hwpapi")
    sys.exit(1)

class HwpApiConverter:
    """hwpapi를 사용한 HWP 변환기"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.hwp = None
        self.text_content = ""
        self.metadata = {}
        
    def open_file(self):
        """HWP 파일 열기"""
        try:
            # Hwp 객체 생성
            self.hwp = Hwp()
            
            # 파일 열기
            if not self.hwp.Open(str(self.file_path)):
                print(f"파일 열기 실패: {self.file_path}")
                return False
            
            # 메타데이터 수집
            self.metadata['file_name'] = self.file_path.name
            self.metadata['file_size'] = os.path.getsize(self.file_path)
            
            return True
            
        except Exception as e:
            print(f"파일 열기 오류: {e}")
            return False
    
    def extract_text(self):
        """텍스트 추출"""
        try:
            if not self.hwp:
                return False
            
            # 전체 텍스트 선택
            self.hwp.Run("SelectAll")
            
            # 선택된 텍스트 가져오기
            self.text_content = self.hwp.GetTextFile("Text", "")
            
            # 텍스트 정리
            if self.text_content:
                # 빈 줄 정리
                lines = self.text_content.split('\n')
                lines = [line.strip() for line in lines if line.strip()]
                self.text_content = '\n'.join(lines)
            
            return True
            
        except Exception as e:
            print(f"텍스트 추출 오류: {e}")
            return False
    
    def save_as_text(self, output_path=None):
        """텍스트 파일로 저장"""
        if not output_path:
            output_path = self.file_path.with_suffix('.txt')
        
        try:
            # SaveAs 메서드 사용
            self.hwp.SaveAs(str(output_path), "Text")
            return output_path
        except:
            # 직접 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"파일: {self.file_path.name}\n")
                f.write(f"변환 시간: {datetime.now()}\n")
                f.write("=" * 60 + "\n\n")
                f.write(self.text_content)
            return output_path
    
    def save_as_pdf(self, output_path=None):
        """PDF로 저장"""
        if not output_path:
            output_path = self.file_path.with_suffix('.pdf')
        
        try:
            self.hwp.SaveAs(str(output_path), "PDF")
            return output_path
        except Exception as e:
            print(f"PDF 저장 오류: {e}")
            return None
    
    def close(self):
        """파일 닫기"""
        try:
            if self.hwp:
                self.hwp.Quit()
        except:
            pass


def test_hwpapi_converter():
    """hwpapi 변환기 테스트"""
    
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    output_dir = Path(r"C:\projects\autoinput\data\hwp_api_converted")
    output_dir.mkdir(exist_ok=True)
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            print(f"파일: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            converter = HwpApiConverter(file_path)
            
            if converter.open_file():
                print("파일 열기 성공")
                
                if converter.extract_text():
                    print("텍스트 추출 성공")
                    
                    # 텍스트 미리보기
                    preview = converter.text_content[:500] if len(converter.text_content) > 500 else converter.text_content
                    print(f"\n텍스트 미리보기:\n{preview}")
                    
                    # 파일 저장
                    base_name = Path(file_path).stem
                    text_output = output_dir / f"{base_name}_api.txt"
                    pdf_output = output_dir / f"{base_name}_api.pdf"
                    
                    # 텍스트 저장
                    txt_result = converter.save_as_text(text_output)
                    if txt_result:
                        print(f"\n텍스트 저장: {txt_result}")
                    
                    # PDF 저장
                    pdf_result = converter.save_as_pdf(pdf_output)
                    if pdf_result:
                        print(f"PDF 저장: {pdf_result}")
                else:
                    print("텍스트 추출 실패")
                
                converter.close()
            else:
                print("파일 열기 실패")


if __name__ == "__main__":
    print("hwpapi를 사용한 HWP 파일 변환 테스트")
    print("한컴 오피스가 설치되어 있어야 작동합니다")
    test_hwpapi_converter()
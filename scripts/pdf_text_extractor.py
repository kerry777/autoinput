#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PDF 파일에서 텍스트 추출 스크립트
HWP 파일의 PDF 버전에서 텍스트를 추출
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
    import pdfplumber
    import PyPDF2
except ImportError:
    print("필요한 라이브러리 설치: pip install pdfplumber PyPDF2")
    sys.exit(1)

class PDFTextExtractor:
    """PDF 텍스트 추출기"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.text_content = ""
        self.metadata = {}
        
    def extract_with_pdfplumber(self):
        """pdfplumber를 사용한 텍스트 추출"""
        try:
            texts = []
            with pdfplumber.open(self.file_path) as pdf:
                # 메타데이터 추출
                self.metadata['pages'] = len(pdf.pages)
                if pdf.metadata:
                    self.metadata.update({
                        'title': pdf.metadata.get('Title', ''),
                        'author': pdf.metadata.get('Author', ''),
                        'subject': pdf.metadata.get('Subject', ''),
                        'creator': pdf.metadata.get('Creator', ''),
                        'producer': pdf.metadata.get('Producer', '')
                    })
                
                # 각 페이지에서 텍스트 추출
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(f"[페이지 {i+1}]\n{page_text}")
                    
                    # 표 추출 시도
                    tables = page.extract_tables()
                    for table in tables:
                        table_text = self._format_table(table)
                        if table_text:
                            texts.append(f"[표]\n{table_text}")
            
            self.text_content = '\n\n'.join(texts)
            return True
            
        except Exception as e:
            print(f"pdfplumber 추출 오류: {e}")
            return False
    
    def extract_with_pypdf2(self):
        """PyPDF2를 사용한 텍스트 추출 (대체 방법)"""
        try:
            texts = []
            with open(self.file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # 메타데이터 추출
                self.metadata['pages'] = len(pdf_reader.pages)
                if pdf_reader.metadata:
                    self.metadata.update({
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', '')
                    })
                
                # 각 페이지에서 텍스트 추출
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        texts.append(f"[페이지 {i+1}]\n{page_text}")
            
            self.text_content = '\n\n'.join(texts)
            return True
            
        except Exception as e:
            print(f"PyPDF2 추출 오류: {e}")
            return False
    
    def _format_table(self, table):
        """표 데이터를 텍스트로 포맷팅"""
        if not table:
            return ""
        
        formatted = []
        for row in table:
            # None 값을 빈 문자열로 변환
            row_clean = [str(cell) if cell is not None else "" for cell in row]
            formatted.append(" | ".join(row_clean))
        
        return "\n".join(formatted)
    
    def extract_text(self):
        """텍스트 추출 (여러 방법 시도)"""
        # 먼저 pdfplumber 시도
        if self.extract_with_pdfplumber():
            return True
        
        # 실패시 PyPDF2 시도
        print("pdfplumber 실패, PyPDF2로 재시도...")
        return self.extract_with_pypdf2()
    
    def save_as_text(self, output_path=None):
        """텍스트 파일로 저장"""
        if not output_path:
            output_path = self.file_path.with_suffix('.txt')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"PDF 파일: {self.file_path.name}\n")
            f.write(f"추출 시간: {datetime.now()}\n")
            f.write(f"페이지 수: {self.metadata.get('pages', 'N/A')}\n")
            f.write("=" * 60 + "\n\n")
            f.write(self.text_content)
        
        return output_path
    
    def save_as_json(self, output_path=None):
        """JSON 파일로 저장"""
        if not output_path:
            output_path = self.file_path.with_suffix('.json')
        
        result = {
            'file': str(self.file_path),
            'metadata': self.metadata,
            'content': self.text_content,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return output_path


def compare_hwp_pdf_text():
    """HWP와 대응하는 PDF 파일의 텍스트 비교"""
    
    # HWP-PDF 파일 쌍
    file_pairs = [
        {
            'hwp': r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
            'pdf': r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.pdf"
        },
        {
            'hwp': r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp",
            'pdf': r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서_예시서식.pdf"
        }
    ]
    
    output_dir = Path(r"C:\projects\autoinput\data\pdf_extracted")
    output_dir.mkdir(exist_ok=True)
    
    for pair in file_pairs:
        pdf_path = pair['pdf']
        if os.path.exists(pdf_path):
            print(f"\n{'='*60}")
            print(f"PDF 파일: {os.path.basename(pdf_path)}")
            print(f"HWP 원본: {os.path.basename(pair['hwp'])}")
            print(f"{'='*60}")
            
            extractor = PDFTextExtractor(pdf_path)
            
            if extractor.extract_text():
                print("텍스트 추출 성공!")
                
                # 텍스트 미리보기
                preview = extractor.text_content[:1000] if len(extractor.text_content) > 1000 else extractor.text_content
                print(f"\n텍스트 미리보기:\n{preview}")
                
                # 파일 저장
                base_name = Path(pdf_path).stem
                text_output = output_dir / f"{base_name}_from_pdf.txt"
                json_output = output_dir / f"{base_name}_from_pdf.json"
                
                extractor.save_as_text(text_output)
                extractor.save_as_json(json_output)
                
                print(f"\n저장 완료:")
                print(f"  - 텍스트: {text_output}")
                print(f"  - JSON: {json_output}")
            else:
                print("텍스트 추출 실패")


if __name__ == "__main__":
    print("PDF 파일에서 텍스트 추출")
    print("HWP 파일의 PDF 버전을 사용하여 텍스트 추출")
    compare_hwp_pdf_text()
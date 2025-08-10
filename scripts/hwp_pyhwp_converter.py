#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pyhwp를 사용한 HWP 파일 변환 스크립트
한컴 공식 HWP Binary Specification 1.1 기반 파서 사용
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
    from hwp5 import filestructure
    from hwp5.xmlmodel import Hwp5File
    from hwp5.hwp5html import HTMLTransform
    from hwp5.hwp5txt import TextTransform
except ImportError:
    print("hwp5 모듈 임포트 실패, pyhwp 직접 사용")
    import pyhwp
    from pyhwp import hwp5
    from pyhwp.hwp5 import filestructure
    from pyhwp.hwp5.xmlmodel import Hwp5File
    from pyhwp.hwp5.hwp5txt import TextTransform

class PyHWPConverter:
    """pyhwp를 사용한 HWP 변환기"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.hwp = None
        self.text_content = ""
        self.metadata = {}
        
    def convert_to_text(self):
        """HWP를 텍스트로 변환"""
        try:
            # HWP 파일 열기
            with open(self.file_path, 'rb') as f:
                hwp = Hwp5File(f)
                
                # 메타데이터 추출
                self.metadata['file_name'] = self.file_path.name
                self.metadata['file_size'] = os.path.getsize(self.file_path)
                
                # 문서 정보 추출
                if hasattr(hwp, 'summaryinfo'):
                    summary = hwp.summaryinfo
                    if summary:
                        self.metadata['title'] = getattr(summary, 'title', '')
                        self.metadata['author'] = getattr(summary, 'author', '')
                        self.metadata['subject'] = getattr(summary, 'subject', '')
                
                # 텍스트 변환
                text_transform = TextTransform()
                self.text_content = text_transform(hwp)
                
                return True
                
        except Exception as e:
            print(f"변환 오류: {e}")
            # 대체 방법 시도
            return self.alternative_conversion()
    
    def alternative_conversion(self):
        """대체 변환 방법"""
        try:
            with open(self.file_path, 'rb') as f:
                hwp = filestructure.HwpFile(f)
                
                # 스트림 정보 추출
                self.metadata['streams'] = []
                for name in hwp.listdir():
                    self.metadata['streams'].append(name)
                
                # 텍스트 추출 시도
                texts = []
                
                # PrvText 스트림 추출
                if hwp.exists('PrvText'):
                    prv_stream = hwp.openstream('PrvText')
                    prv_data = prv_stream.read()
                    try:
                        preview_text = prv_data.decode('utf-16le', errors='ignore')
                        texts.append(f"[미리보기]\n{preview_text}\n")
                    except:
                        pass
                
                # BodyText 섹션 추출
                section_idx = 0
                while hwp.exists(f'BodyText/Section{section_idx}'):
                    section_stream = hwp.openstream(f'BodyText/Section{section_idx}')
                    section_data = section_stream.read()
                    
                    # 섹션 텍스트 추출 시도
                    section_text = self.extract_text_from_section(section_data)
                    if section_text:
                        texts.append(f"\n[섹션 {section_idx}]\n{section_text}")
                    
                    section_idx += 1
                
                self.text_content = '\n'.join(texts)
                return True
                
        except Exception as e:
            print(f"대체 변환 오류: {e}")
            return False
    
    def extract_text_from_section(self, data):
        """섹션 데이터에서 텍스트 추출"""
        texts = []
        
        # UTF-16LE 디코딩 시도
        try:
            text = data.decode('utf-16le', errors='ignore')
            # 제어 문자 제거
            import re
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
            text = re.sub(r'\s+', ' ', text)
            if text.strip():
                texts.append(text.strip())
        except:
            pass
        
        return ' '.join(texts) if texts else None
    
    def save_as_text(self, output_path=None):
        """텍스트 파일로 저장"""
        if not output_path:
            output_path = self.file_path.with_suffix('.txt')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"파일: {self.file_path.name}\n")
            f.write(f"변환 시간: {datetime.now()}\n")
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


def test_pyhwp_converter():
    """pyhwp 변환기 테스트"""
    
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    output_dir = Path(r"C:\projects\autoinput\data\hwp_pyhwp_converted")
    output_dir.mkdir(exist_ok=True)
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            print(f"파일: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            converter = PyHWPConverter(file_path)
            if converter.convert_to_text():
                # 텍스트 미리보기
                preview = converter.text_content[:500] if len(converter.text_content) > 500 else converter.text_content
                print(f"텍스트 미리보기:\n{preview}")
                
                # 파일 저장
                base_name = Path(file_path).stem
                text_output = output_dir / f"{base_name}_pyhwp.txt"
                json_output = output_dir / f"{base_name}_pyhwp.json"
                
                converter.save_as_text(text_output)
                converter.save_as_json(json_output)
                
                print(f"\n변환 완료:")
                print(f"  - 텍스트: {text_output}")
                print(f"  - JSON: {json_output}")
            else:
                print("변환 실패")


if __name__ == "__main__":
    print("pyhwp를 사용한 HWP 파일 변환 테스트")
    print("한컴 공식 스펙 기반 파서 사용")
    test_pyhwp_converter()
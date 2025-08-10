#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HWP 파일 파싱 테스트 스크립트
HWP 파일을 읽고 텍스트를 추출하는 다양한 방법을 테스트합니다.
"""

import os
import sys
import json
import struct
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import olefile
import re

class HWPParser:
    """HWP 파일 파싱 클래스"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.content = {}
        self.metadata = {}
        self.text_content = []
        
    def parse_with_olefile(self):
        """OLE 구조를 사용한 HWP 파싱"""
        try:
            with olefile.OleFileIO(str(self.file_path)) as ole:
                # HWP 파일 구조 분석
                self.metadata['streams'] = ole.listdir()
                
                # 문서 정보 스트림 읽기
                if ole.exists('DocInfo'):
                    doc_info = ole.openstream('DocInfo').read()
                    self.metadata['doc_info_size'] = len(doc_info)
                
                # 바디텍스트 섹션 읽기
                body_text = []
                section_num = 0
                
                while True:
                    section_name = f'BodyText/Section{section_num}'
                    if ole.exists(section_name):
                        section_data = ole.openstream(section_name).read()
                        text = self._extract_text_from_section(section_data)
                        if text:
                            body_text.append(text)
                        section_num += 1
                    else:
                        break
                
                self.text_content = body_text
                
                # PrvText 스트림에서 미리보기 텍스트 추출
                if ole.exists('PrvText'):
                    prv_text = ole.openstream('PrvText').read()
                    preview_text = self._decode_preview_text(prv_text)
                    if preview_text:
                        self.metadata['preview_text'] = preview_text
                
                return True
                
        except Exception as e:
            print(f"OLE 파싱 오류: {e}")
            return False
    
    def parse_hwpx(self):
        """HWPX (ZIP 기반) 형식 파싱 시도"""
        try:
            with zipfile.ZipFile(str(self.file_path), 'r') as z:
                # HWPX 파일 구조 확인
                file_list = z.namelist()
                self.metadata['hwpx_files'] = file_list
                
                # content.hpf 파일에서 텍스트 추출
                if 'Contents/content.hpf' in file_list:
                    content = z.read('Contents/content.hpf')
                    # XML 파싱 시도
                    try:
                        root = ET.fromstring(content)
                        texts = []
                        for elem in root.iter():
                            if elem.text:
                                texts.append(elem.text.strip())
                        self.text_content = [' '.join(texts)]
                    except:
                        pass
                
                return True
                
        except zipfile.BadZipFile:
            # HWPX 형식이 아님
            return False
        except Exception as e:
            print(f"HWPX 파싱 오류: {e}")
            return False
    
    def _extract_text_from_section(self, section_data):
        """섹션 데이터에서 텍스트 추출"""
        texts = []
        
        # HWP 텍스트 레코드 구조 파싱
        # 간단한 휴리스틱 방법으로 텍스트 추출
        try:
            # UTF-16LE로 디코딩 시도
            text_parts = []
            i = 0
            while i < len(section_data) - 1:
                # 텍스트 레코드 찾기 (0x0067 = 텍스트 레코드 태그)
                if i < len(section_data) - 4:
                    tag = struct.unpack('<H', section_data[i:i+2])[0]
                    if tag == 0x0067:  # TEXT_RECORD
                        # 레코드 크기 읽기
                        size = struct.unpack('<I', section_data[i+2:i+6])[0]
                        if i + 6 + size <= len(section_data):
                            text_data = section_data[i+6:i+6+size]
                            try:
                                # UTF-16LE 디코딩
                                text = text_data.decode('utf-16le', errors='ignore')
                                # 제어 문자 제거
                                text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
                                text = ' '.join(text.split())
                                if text:
                                    text_parts.append(text)
                            except:
                                pass
                        i += 6 + size
                    else:
                        i += 1
                else:
                    i += 1
            
            if text_parts:
                return ' '.join(text_parts)
                
        except Exception as e:
            pass
        
        # 대체 방법: 간단한 UTF-16 디코딩
        try:
            decoded = section_data.decode('utf-16le', errors='ignore')
            # 출력 가능한 문자만 추출
            printable = ''.join(c for c in decoded if c.isprintable() or c.isspace())
            printable = ' '.join(printable.split())
            if len(printable) > 10:  # 최소 길이 체크
                return printable
        except:
            pass
        
        return None
    
    def _decode_preview_text(self, prv_data):
        """PrvText 스트림에서 미리보기 텍스트 디코딩"""
        try:
            # UTF-16LE로 디코딩
            text = prv_data.decode('utf-16le', errors='ignore')
            # 제어 문자 제거 및 정리
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
            text = ' '.join(text.split())
            if len(text) > 10:
                return text
        except:
            pass
        
        # UTF-8 시도
        try:
            text = prv_data.decode('utf-8', errors='ignore')
            text = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', text)
            text = ' '.join(text.split())
            if len(text) > 10:
                return text
        except:
            pass
        
        return None
    
    def extract_all_text(self):
        """모든 가능한 방법으로 텍스트 추출"""
        results = {
            'file': str(self.file_path),
            'success': False,
            'methods_tried': [],
            'text': [],
            'metadata': {}
        }
        
        # HWPX 형식 시도
        if self.parse_hwpx():
            results['methods_tried'].append('HWPX')
            if self.text_content:
                results['text'].extend(self.text_content)
                results['success'] = True
        
        # OLE 형식 시도
        if self.parse_with_olefile():
            results['methods_tried'].append('OLE')
            if self.text_content:
                results['text'].extend(self.text_content)
                results['success'] = True
            if self.metadata:
                results['metadata'].update(self.metadata)
        
        # 텍스트 정리
        if results['text']:
            # 중복 제거 및 정리
            unique_texts = []
            for text in results['text']:
                if text and text not in unique_texts:
                    unique_texts.append(text)
            results['text'] = unique_texts
        
        return results


def test_hwp_files():
    """다운로드된 HWP 파일들을 테스트"""
    
    # HWP 파일 경로들
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60093\2025년_장기요양기관_운영_관련_서식_모음집.hwp",
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    results = []
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            print(f"파일 테스트: {os.path.basename(file_path)}")
            print(f"파일 크기: {os.path.getsize(file_path):,} bytes")
            print(f"{'='*60}")
            
            parser = HWPParser(file_path)
            result = parser.extract_all_text()
            
            print(f"시도한 방법: {', '.join(result['methods_tried'])}")
            print(f"성공 여부: {result['success']}")
            
            if result['metadata']:
                print(f"\n메타데이터:")
                for key, value in result['metadata'].items():
                    if key == 'streams':
                        print(f"  - {key}: {len(value)} 스트림")
                    elif key == 'preview_text':
                        preview = value[:100] + '...' if len(value) > 100 else value
                        print(f"  - {key}: {preview}")
                    else:
                        print(f"  - {key}: {value}")
            
            if result['text']:
                print(f"\n추출된 텍스트 (첫 500자):")
                for i, text in enumerate(result['text']):
                    preview = text[:500] + '...' if len(text) > 500 else text
                    print(f"  섹션 {i+1}: {preview}")
            else:
                print(f"\n텍스트 추출 실패")
            
            results.append(result)
    
    # 결과 저장
    output_file = r"C:\projects\autoinput\data\hwp_parsing_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n결과가 {output_file}에 저장되었습니다.")
    
    return results


if __name__ == "__main__":
    print("HWP 파일 파싱 테스트 시작...")
    results = test_hwp_files()
    
    # 요약
    print(f"\n\n{'='*60}")
    print(f"테스트 요약:")
    print(f"{'='*60}")
    success_count = sum(1 for r in results if r['success'])
    print(f"전체 파일: {len(results)}개")
    print(f"성공: {success_count}개")
    print(f"실패: {len(results) - success_count}개")
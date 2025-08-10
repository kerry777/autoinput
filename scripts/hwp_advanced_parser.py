#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HWP 파일 고급 파싱 스크립트
한글 텍스트를 정확하게 추출하는 개선된 파서
"""

import os
import sys
import json
import struct
import zipfile
import zlib
from pathlib import Path
from datetime import datetime
import olefile
import re

class AdvancedHWPParser:
    """개선된 HWP 파일 파서"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.content = {}
        self.metadata = {}
        self.text_content = []
        self.sections = []
        
    def parse(self):
        """HWP 파일 파싱"""
        try:
            with olefile.OleFileIO(str(self.file_path)) as ole:
                # 메타데이터 수집
                self.metadata['file_name'] = self.file_path.name
                self.metadata['file_size'] = os.path.getsize(self.file_path)
                self.metadata['streams'] = ole.listdir()
                
                # 문서 정보 파싱
                if ole.exists('DocInfo'):
                    doc_info = ole.openstream('DocInfo').read()
                    self.metadata['doc_info_size'] = len(doc_info)
                
                # FileHeader 파싱 - HWP 버전 정보 등
                if ole.exists('FileHeader'):
                    header_data = ole.openstream('FileHeader').read()
                    self._parse_file_header(header_data)
                
                # PrvText에서 미리보기 텍스트 추출
                if ole.exists('PrvText'):
                    prv_data = ole.openstream('PrvText').read()
                    preview_text = self._extract_preview_text(prv_data)
                    if preview_text:
                        self.metadata['preview_text'] = preview_text
                
                # BodyText 섹션별 파싱
                section_num = 0
                while ole.exists(f'BodyText/Section{section_num}'):
                    section_data = ole.openstream(f'BodyText/Section{section_num}').read()
                    
                    # 압축 여부 확인 및 해제
                    if self._is_compressed(section_data):
                        section_data = self._decompress_section(section_data)
                    
                    # 텍스트 추출
                    texts = self._extract_text_from_section(section_data)
                    if texts:
                        self.sections.append({
                            'section': section_num,
                            'texts': texts
                        })
                    
                    section_num += 1
                
                return True
                
        except Exception as e:
            print(f"파싱 오류: {e}")
            return False
    
    def _parse_file_header(self, data):
        """FileHeader 파싱"""
        if len(data) >= 256:
            # HWP 시그니처 확인
            signature = data[:32]
            # 버전 정보 등 추출
            version = struct.unpack('<I', data[32:36])[0] if len(data) > 36 else 0
            self.metadata['version'] = version
    
    def _is_compressed(self, data):
        """섹션 데이터 압축 여부 확인"""
        # HWP는 zlib 압축 사용
        try:
            # zlib 압축 시그니처 확인
            if len(data) > 2:
                # zlib 헤더 확인 (0x78 0x9C 등)
                if data[0] == 0x78 and data[1] in [0x01, 0x5E, 0x9C, 0xDA]:
                    return True
        except:
            pass
        return False
    
    def _decompress_section(self, data):
        """압축된 섹션 데이터 해제"""
        try:
            return zlib.decompress(data)
        except:
            return data
    
    def _extract_preview_text(self, data):
        """PrvText에서 미리보기 텍스트 추출"""
        try:
            # UTF-16LE 디코딩
            text = data.decode('utf-16le', errors='ignore')
            
            # 제어 문자 제거 및 정리
            text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
            text = re.sub(r'\s+', ' ', text)
            
            # < > 태그 사이의 텍스트만 추출
            tags = re.findall(r'<([^>]+)>', text)
            if tags:
                # 태그 내용 정리
                clean_tags = []
                for tag in tags:
                    tag = tag.strip()
                    if tag and not tag.isspace():
                        clean_tags.append(tag)
                return ' '.join(clean_tags)
            
            return text.strip() if text.strip() else None
            
        except Exception as e:
            return None
    
    def _extract_text_from_section(self, data):
        """섹션 데이터에서 텍스트 추출"""
        texts = []
        
        # 방법 1: 텍스트 레코드 파싱 (0x0067)
        pos = 0
        while pos < len(data) - 10:
            try:
                # 레코드 헤더 읽기
                if pos + 4 <= len(data):
                    tag_id = struct.unpack('<H', data[pos:pos+2])[0]
                    level = data[pos+2] if pos+2 < len(data) else 0
                    size = struct.unpack('<H', data[pos+3:pos+5])[0] if pos+5 <= len(data) else 0
                    
                    # 확장 크기 처리
                    header_size = 5
                    if size == 0xFFFF and pos + 9 <= len(data):
                        size = struct.unpack('<I', data[pos+5:pos+9])[0]
                        header_size = 9
                    
                    # 텍스트 레코드인 경우 (0x0067 = HWPTAG_PARA_TEXT)
                    if tag_id == 0x0067 and pos + header_size + size <= len(data):
                        text_data = data[pos+header_size:pos+header_size+size]
                        text = self._decode_text_data(text_data)
                        if text:
                            texts.append(text)
                    
                    # 다음 레코드로 이동
                    pos += header_size + size
                else:
                    pos += 1
                    
            except Exception as e:
                pos += 1
        
        # 방법 2: UTF-16 문자열 직접 검색
        if not texts:
            texts.extend(self._find_utf16_strings(data))
        
        return texts
    
    def _decode_text_data(self, data):
        """텍스트 데이터 디코딩"""
        try:
            # HWP 텍스트는 UTF-16LE로 저장
            text = data.decode('utf-16le', errors='ignore')
            
            # 특수 제어 문자 처리
            # HWP 특수 문자 코드 매핑
            text = text.replace('\x00', '')
            text = text.replace('\x01', ' ')  # 공백
            text = text.replace('\x02', '\t')  # 탭
            text = text.replace('\x0D', '\n')  # 줄바꿈
            
            # 깨끗한 텍스트만 추출
            cleaned = []
            for char in text:
                if char.isprintable() or char in '\n\t ':
                    cleaned.append(char)
            
            result = ''.join(cleaned).strip()
            return result if len(result) > 2 else None
            
        except Exception as e:
            return None
    
    def _find_utf16_strings(self, data):
        """바이너리 데이터에서 UTF-16 문자열 찾기"""
        strings = []
        
        # 한글 범위를 포함한 UTF-16LE 패턴
        # 한글: 0xAC00-0xD7AF
        i = 0
        while i < len(data) - 4:
            try:
                # 2바이트씩 읽어서 UTF-16LE로 디코딩 시도
                if i + 2 <= len(data):
                    char = struct.unpack('<H', data[i:i+2])[0]
                    
                    # 한글 또는 ASCII 범위 확인
                    if (0xAC00 <= char <= 0xD7AF) or (0x20 <= char <= 0x7E):
                        # 연속된 문자 추출
                        text_bytes = bytearray()
                        j = i
                        while j < len(data) - 1:
                            next_char = struct.unpack('<H', data[j:j+2])[0]
                            if (0xAC00 <= next_char <= 0xD7AF) or (0x20 <= next_char <= 0x7E) or next_char in [0x20, 0x09]:
                                text_bytes.extend(data[j:j+2])
                                j += 2
                            else:
                                break
                        
                        if len(text_bytes) >= 4:  # 최소 2글자
                            try:
                                text = text_bytes.decode('utf-16le', errors='ignore').strip()
                                if text and len(text) > 1:
                                    strings.append(text)
                            except:
                                pass
                        
                        i = j
                    else:
                        i += 1
                else:
                    i += 1
                    
            except:
                i += 1
        
        return strings
    
    def get_text(self):
        """추출된 모든 텍스트 반환"""
        all_text = []
        
        # 미리보기 텍스트
        if 'preview_text' in self.metadata:
            all_text.append(f"[미리보기]\n{self.metadata['preview_text']}\n")
        
        # 섹션별 텍스트
        for section in self.sections:
            if section['texts']:
                all_text.append(f"\n[섹션 {section['section']}]")
                for text in section['texts']:
                    if text:
                        all_text.append(text)
        
        return '\n'.join(all_text)
    
    def to_json(self):
        """JSON 형식으로 변환"""
        return {
            'file': str(self.file_path),
            'metadata': self.metadata,
            'sections': self.sections,
            'extracted_text': self.get_text(),
            'timestamp': datetime.now().isoformat()
        }


def test_advanced_parser():
    """고급 파서 테스트"""
    
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp",
        r"C:\projects\autoinput\data\downloads\metadata_test\20250809_234415\001_[별지_제1호의2서식]_장기요양인정_신청서(노인장기요양보험법_시행규칙).hwp"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            print(f"\n{'='*60}")
            print(f"파일: {os.path.basename(file_path)}")
            print(f"{'='*60}")
            
            parser = AdvancedHWPParser(file_path)
            if parser.parse():
                # 텍스트 출력
                text = parser.get_text()
                print(text[:1000] if len(text) > 1000 else text)
                
                # JSON 저장
                output_dir = Path(r"C:\projects\autoinput\data\hwp_advanced")
                output_dir.mkdir(exist_ok=True)
                
                output_file = output_dir / f"{Path(file_path).stem}_advanced.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(parser.to_json(), f, ensure_ascii=False, indent=2)
                
                print(f"\n결과 저장: {output_file}")
            else:
                print("파싱 실패")


if __name__ == "__main__":
    # 출력 인코딩 설정
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    
    print("HWP 고급 파싱 테스트")
    test_advanced_parser()
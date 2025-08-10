#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HWP 파일 변환 및 처리 스크립트
HWP 파일을 다양한 형식으로 변환하고 텍스트를 추출합니다.
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
import codecs

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

class HWPConverter:
    """HWP 파일 변환 클래스"""
    
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.content = {}
        self.metadata = {}
        self.text_content = []
        self.structured_data = {}
        
    def parse_hwp(self):
        """HWP 파일 파싱 메인 함수"""
        try:
            with olefile.OleFileIO(str(self.file_path)) as ole:
                # 스트림 정보 수집
                self.metadata['streams'] = ole.listdir()
                self.metadata['file_size'] = os.path.getsize(self.file_path)
                self.metadata['file_name'] = self.file_path.name
                
                # 문서 정보 파싱
                self._parse_document_info(ole)
                
                # 바디 텍스트 파싱
                self._parse_body_text(ole)
                
                # 미리보기 텍스트 파싱
                self._parse_preview_text(ole)
                
                # 바이너리 데이터 정보
                self._parse_binary_data(ole)
                
                return True
                
        except Exception as e:
            print(f"HWP 파싱 오류: {e}")
            return False
    
    def _parse_document_info(self, ole):
        """문서 정보 스트림 파싱"""
        if ole.exists('DocInfo'):
            doc_info = ole.openstream('DocInfo').read()
            self.metadata['doc_info_size'] = len(doc_info)
            
            # 문서 속성 추출 시도
            try:
                # HWP 문서 정보 구조 파싱 (간단한 버전)
                if len(doc_info) > 256:
                    # 문서 제목, 작성자 등의 정보가 포함될 수 있음
                    info_text = self._extract_strings_from_binary(doc_info[:1024])
                    if info_text:
                        self.metadata['doc_properties'] = info_text
            except:
                pass
    
    def _parse_body_text(self, ole):
        """바디 텍스트 섹션 파싱"""
        body_texts = []
        section_num = 0
        
        while True:
            section_name = f'BodyText/Section{section_num}'
            if ole.exists(section_name):
                section_data = ole.openstream(section_name).read()
                
                # 섹션별 텍스트 추출
                section_info = {
                    'section': section_num,
                    'size': len(section_data),
                    'text': []
                }
                
                # 다양한 방법으로 텍스트 추출
                texts = self._extract_text_multiple_methods(section_data)
                if texts:
                    section_info['text'] = texts
                    body_texts.append(section_info)
                
                section_num += 1
            else:
                break
        
        self.structured_data['sections'] = body_texts
    
    def _parse_preview_text(self, ole):
        """미리보기 텍스트 추출"""
        if ole.exists('PrvText'):
            prv_data = ole.openstream('PrvText').read()
            
            # UTF-16LE 디코딩
            try:
                text = prv_data.decode('utf-16le', errors='ignore')
                text = self._clean_text(text)
                if text:
                    self.metadata['preview_text'] = text[:1000]  # 처음 1000자만
                    self.text_content.append(('preview', text))
            except:
                pass
    
    def _parse_binary_data(self, ole):
        """바이너리 데이터 스트림 정보 수집"""
        if ole.exists('BinData'):
            bindata_streams = []
            for stream in ole.listdir():
                if stream[0] == 'BinData':
                    stream_path = '/'.join(stream)
                    stream_size = ole.get_size(stream_path)
                    bindata_streams.append({
                        'path': stream_path,
                        'size': stream_size
                    })
            
            if bindata_streams:
                self.metadata['binary_data'] = bindata_streams
    
    def _extract_text_multiple_methods(self, data):
        """여러 방법으로 텍스트 추출"""
        texts = []
        
        # 방법 1: HWP 텍스트 레코드 파싱
        hwp_texts = self._parse_hwp_records(data)
        if hwp_texts:
            texts.extend(hwp_texts)
        
        # 방법 2: UTF-16 디코딩으로 직접 추출
        utf16_text = self._extract_utf16_text(data)
        if utf16_text:
            texts.append(utf16_text)
        
        # 방법 3: 문자열 패턴 찾기
        pattern_texts = self._extract_strings_from_binary(data)
        if pattern_texts:
            texts.extend(pattern_texts)
        
        return texts
    
    def _parse_hwp_records(self, data):
        """HWP 레코드 구조 파싱"""
        texts = []
        pos = 0
        
        while pos < len(data) - 6:
            try:
                # 레코드 헤더 읽기
                tag = struct.unpack('<H', data[pos:pos+2])[0]
                level = struct.unpack('<H', data[pos+2:pos+4])[0]
                size = struct.unpack('<H', data[pos+4:pos+6])[0]
                
                # 확장 크기 처리
                if size == 0xFFFF and pos + 10 <= len(data):
                    size = struct.unpack('<I', data[pos+6:pos+10])[0]
                    header_size = 10
                else:
                    header_size = 6
                
                # 텍스트 레코드 처리 (0x0067)
                if tag == 0x0067 and pos + header_size + size <= len(data):
                    text_data = data[pos+header_size:pos+header_size+size]
                    text = self._decode_hwp_text(text_data)
                    if text:
                        texts.append(text)
                
                pos += header_size + size
                
            except:
                pos += 1
        
        return texts
    
    def _decode_hwp_text(self, data):
        """HWP 텍스트 데이터 디코딩"""
        try:
            # UTF-16LE로 디코딩
            text = data.decode('utf-16le', errors='ignore')
            text = self._clean_text(text)
            if len(text) > 5:  # 최소 길이 체크
                return text
        except:
            pass
        return None
    
    def _extract_utf16_text(self, data):
        """UTF-16 텍스트 직접 추출"""
        try:
            text = data.decode('utf-16le', errors='ignore')
            text = self._clean_text(text)
            if len(text) > 20:
                return text
        except:
            pass
        return None
    
    def _extract_strings_from_binary(self, data):
        """바이너리 데이터에서 문자열 패턴 추출"""
        strings = []
        
        # UTF-16LE 문자열 찾기
        pattern = re.compile(b'(?:[\x20-\x7E][\x00]){5,}')
        matches = pattern.findall(data)
        
        for match in matches:
            try:
                text = match.decode('utf-16le', errors='ignore')
                text = self._clean_text(text)
                if text and len(text) > 5:
                    strings.append(text)
            except:
                pass
        
        return strings
    
    def _clean_text(self, text):
        """텍스트 정리"""
        # 제어 문자 제거
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', ' ', text)
        # 특수 문자 정리
        text = re.sub(r'[\uE000-\uF8FF]', '', text)  # Private Use Area 제거
        text = re.sub(r'[\uFFF0-\uFFFF]', '', text)  # Specials 제거
        # 공백 정리
        text = ' '.join(text.split())
        return text
    
    def convert_to_json(self, output_path=None):
        """JSON 형식으로 변환"""
        result = {
            'file': str(self.file_path),
            'metadata': self.metadata,
            'content': {
                'sections': self.structured_data.get('sections', []),
                'all_text': self.get_all_text()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if output_path:
            output_file = Path(output_path)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            return output_file
        
        return result
    
    def convert_to_text(self, output_path=None):
        """텍스트 파일로 변환"""
        all_text = self.get_all_text()
        
        if output_path:
            output_file = Path(output_path)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"HWP 파일: {self.file_path.name}\n")
                f.write(f"변환 시간: {datetime.now()}\n")
                f.write("="*60 + "\n\n")
                f.write(all_text)
            return output_file
        
        return all_text
    
    def get_all_text(self):
        """모든 텍스트 통합"""
        all_texts = []
        
        # 섹션별 텍스트
        if 'sections' in self.structured_data:
            for section in self.structured_data['sections']:
                for text in section.get('text', []):
                    if text and text not in all_texts:
                        all_texts.append(text)
        
        # 미리보기 텍스트
        if 'preview_text' in self.metadata:
            preview = self.metadata['preview_text']
            if preview and preview not in all_texts:
                all_texts.append(preview)
        
        return '\n\n'.join(all_texts)


def test_conversion():
    """HWP 파일 변환 테스트"""
    
    # 테스트할 파일
    test_file = r"C:\projects\autoinput\data\downloads\attachments_working\post_60093\2025년_장기요양기관_운영_관련_서식_모음집.hwp"
    
    if not os.path.exists(test_file):
        print(f"파일을 찾을 수 없습니다: {test_file}")
        return
    
    print(f"HWP 파일 변환 테스트")
    print(f"파일: {os.path.basename(test_file)}")
    print(f"크기: {os.path.getsize(test_file):,} bytes")
    print("="*60)
    
    # 변환기 생성
    converter = HWPConverter(test_file)
    
    # HWP 파싱
    if converter.parse_hwp():
        print("✓ HWP 파일 파싱 성공")
        
        # JSON으로 변환
        json_output = r"C:\projects\autoinput\data\hwp_converted.json"
        json_file = converter.convert_to_json(json_output)
        print(f"✓ JSON 변환 완료: {json_file}")
        
        # 텍스트로 변환
        text_output = r"C:\projects\autoinput\data\hwp_converted.txt"
        text_file = converter.convert_to_text(text_output)
        print(f"✓ 텍스트 변환 완료: {text_file}")
        
        # 추출된 텍스트 미리보기
        all_text = converter.get_all_text()
        if all_text:
            preview = all_text[:500] + "..." if len(all_text) > 500 else all_text
            print(f"\n추출된 텍스트 미리보기:")
            print("-"*40)
            print(preview)
            print("-"*40)
            print(f"전체 텍스트 길이: {len(all_text):,} 문자")
        else:
            print("텍스트를 추출할 수 없습니다.")
        
        # 메타데이터 출력
        print(f"\n메타데이터:")
        for key, value in converter.metadata.items():
            if key == 'preview_text':
                continue
            elif key == 'streams':
                print(f"  - {key}: {len(value)} 스트림")
            elif key == 'binary_data':
                print(f"  - {key}: {len(value)} 바이너리 스트림")
            else:
                print(f"  - {key}: {value}")
    else:
        print("✗ HWP 파일 파싱 실패")


def batch_convert():
    """여러 HWP 파일 일괄 변환"""
    
    # HWP 파일 목록
    hwp_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60093\2025년_장기요양기관_운영_관련_서식_모음집.hwp",
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    ]
    
    results = []
    output_dir = Path(r"C:\projects\autoinput\data\hwp_converted")
    output_dir.mkdir(exist_ok=True)
    
    for hwp_file in hwp_files:
        if os.path.exists(hwp_file):
            print(f"\n변환 중: {os.path.basename(hwp_file)}")
            
            converter = HWPConverter(hwp_file)
            if converter.parse_hwp():
                # 파일명 기반 출력 파일 생성
                base_name = Path(hwp_file).stem
                
                # JSON 변환
                json_output = output_dir / f"{base_name}.json"
                converter.convert_to_json(json_output)
                
                # 텍스트 변환
                text_output = output_dir / f"{base_name}.txt"
                converter.convert_to_text(text_output)
                
                results.append({
                    'file': hwp_file,
                    'success': True,
                    'json': str(json_output),
                    'text': str(text_output),
                    'text_length': len(converter.get_all_text())
                })
                
                print(f"  ✓ 변환 완료")
            else:
                results.append({
                    'file': hwp_file,
                    'success': False
                })
                print(f"  ✗ 변환 실패")
    
    # 결과 요약
    print(f"\n{'='*60}")
    print(f"변환 결과 요약:")
    print(f"{'='*60}")
    success_count = sum(1 for r in results if r['success'])
    print(f"전체: {len(results)}개")
    print(f"성공: {success_count}개")
    print(f"실패: {len(results) - success_count}개")
    
    return results


if __name__ == "__main__":
    print("HWP 파일 변환 프로그램")
    print("="*60)
    
    # 단일 파일 테스트
    test_conversion()
    
    # 일괄 변환
    print(f"\n\n일괄 변환 시작...")
    batch_convert()
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown to Excel Converter
MD 파일을 Excel 파일로 변환하는 유틸리티

사용법:
    python md2excel.py <md_file> [output_file]
    python md2excel.py docs/target-site-analysis.md
    python md2excel.py docs/*.md --merge
"""

import pandas as pd
import re
import sys
import os
from pathlib import Path
from datetime import datetime
import argparse
from typing import List, Dict, Any, Tuple

class MarkdownToExcel:
    """Markdown 파일을 Excel로 변환하는 클래스"""
    
    def __init__(self):
        self.tables = []
        self.sections = []
        self.lists = []
        
    def parse_markdown_file(self, file_path: str) -> Dict[str, Any]:
        """MD 파일을 파싱하여 구조화된 데이터로 변환"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = {
            'file_name': Path(file_path).name,
            'tables': self.extract_tables(content),
            'sections': self.extract_sections(content),
            'lists': self.extract_lists(content),
            'code_blocks': self.extract_code_blocks(content)
        }
        
        return result
    
    def extract_tables(self, content: str) -> List[Dict]:
        """마크다운 테이블 추출"""
        tables = []
        
        # 테이블 패턴 찾기 (| 로 구분된 행들)
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 테이블 시작 감지
            if '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
                table_lines = []
                
                # 테이블 헤더
                headers = [cell.strip() for cell in line.split('|') if cell.strip()]
                table_lines.append(headers)
                
                # 구분선 건너뛰기
                i += 2
                
                # 테이블 본문
                while i < len(lines) and '|' in lines[i]:
                    row = [cell.strip() for cell in lines[i].split('|') if cell.strip()]
                    if row:  # 빈 행 제외
                        table_lines.append(row)
                    i += 1
                
                if table_lines:
                    # DataFrame으로 변환
                    df_data = []
                    headers = table_lines[0]
                    for row in table_lines[1:]:
                        # 열 수 맞추기
                        while len(row) < len(headers):
                            row.append('')
                        df_data.append(dict(zip(headers, row[:len(headers)])))
                    
                    if df_data:
                        tables.append({
                            'data': pd.DataFrame(df_data),
                            'title': self.find_section_title(content, i)
                        })
            else:
                i += 1
        
        return tables
    
    def extract_sections(self, content: str) -> List[Dict]:
        """섹션별 내용 추출"""
        sections = []
        
        # 헤더 패턴 (#, ##, ###)
        pattern = r'^(#{1,6})\s+(.+)$'
        lines = content.split('\n')
        
        current_section = None
        section_content = []
        
        for line in lines:
            match = re.match(pattern, line)
            if match:
                # 이전 섹션 저장
                if current_section:
                    sections.append({
                        'level': len(current_section['level']),
                        'title': current_section['title'],
                        'content': '\n'.join(section_content).strip()
                    })
                
                # 새 섹션 시작
                current_section = {
                    'level': match.group(1),
                    'title': match.group(2).strip()
                }
                section_content = []
            else:
                section_content.append(line)
        
        # 마지막 섹션 저장
        if current_section:
            sections.append({
                'level': len(current_section['level']),
                'title': current_section['title'],
                'content': '\n'.join(section_content).strip()
            })
        
        return sections
    
    def extract_lists(self, content: str) -> List[Dict]:
        """리스트 항목 추출"""
        lists = []
        lines = content.split('\n')
        
        current_list = []
        list_type = None
        
        for line in lines:
            # 순서 없는 리스트
            if re.match(r'^\s*[-*+]\s+', line):
                if list_type != 'unordered':
                    if current_list:
                        lists.append({'type': list_type, 'items': current_list})
                    current_list = []
                    list_type = 'unordered'
                
                item = re.sub(r'^\s*[-*+]\s+', '', line)
                current_list.append(item)
            
            # 순서 있는 리스트
            elif re.match(r'^\s*\d+\.\s+', line):
                if list_type != 'ordered':
                    if current_list:
                        lists.append({'type': list_type, 'items': current_list})
                    current_list = []
                    list_type = 'ordered'
                
                item = re.sub(r'^\s*\d+\.\s+', '', line)
                current_list.append(item)
            
            # 체크리스트
            elif re.match(r'^\s*-\s*\[[ xX]\]\s+', line):
                if list_type != 'checklist':
                    if current_list:
                        lists.append({'type': list_type, 'items': current_list})
                    current_list = []
                    list_type = 'checklist'
                
                checked = '[x]' in line.lower() or '[X]' in line
                item = re.sub(r'^\s*-\s*\[[ xX]\]\s+', '', line)
                current_list.append({'item': item, 'checked': checked})
            
            else:
                # 리스트 종료
                if current_list:
                    lists.append({'type': list_type, 'items': current_list})
                    current_list = []
                    list_type = None
        
        # 마지막 리스트 저장
        if current_list:
            lists.append({'type': list_type, 'items': current_list})
        
        return lists
    
    def extract_code_blocks(self, content: str) -> List[Dict]:
        """코드 블록 추출"""
        code_blocks = []
        
        # 코드 블록 패턴 (```언어 ... ```)
        pattern = r'```(\w*)\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for language, code in matches:
            code_blocks.append({
                'language': language or 'text',
                'code': code.strip()
            })
        
        return code_blocks
    
    def find_section_title(self, content: str, position: int) -> str:
        """현재 위치 이전의 가장 가까운 섹션 제목 찾기"""
        lines = content.split('\n')
        
        for i in range(min(position, len(lines) - 1), -1, -1):
            if re.match(r'^#{1,6}\s+', lines[i]):
                return re.sub(r'^#{1,6}\s+', '', lines[i]).strip()
        
        return 'Table'
    
    def to_excel(self, parsed_data: Dict, output_file: str):
        """파싱된 데이터를 Excel 파일로 저장"""
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            sheet_num = 1
            
            # 1. Overview 시트 - 파일 정보 및 요약
            overview_data = {
                'Category': ['File Name', 'Total Tables', 'Total Sections', 'Total Lists', 'Total Code Blocks'],
                'Value': [
                    parsed_data['file_name'],
                    len(parsed_data['tables']),
                    len(parsed_data['sections']),
                    len(parsed_data['lists']),
                    len(parsed_data['code_blocks'])
                ]
            }
            pd.DataFrame(overview_data).to_excel(writer, sheet_name='Overview', index=False)
            
            # 2. 섹션 구조 시트
            if parsed_data['sections']:
                sections_df = pd.DataFrame([
                    {
                        'Level': s['level'],
                        'Title': s['title'],
                        'Content Preview': s['content'][:200] + '...' if len(s['content']) > 200 else s['content']
                    }
                    for s in parsed_data['sections']
                ])
                sections_df.to_excel(writer, sheet_name='Sections', index=False)
            
            # 3. 테이블들을 각각의 시트로
            for i, table in enumerate(parsed_data['tables'], 1):
                sheet_name = self.clean_sheet_name(table['title'], i)
                table['data'].to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 4. 리스트들을 하나의 시트로
            if parsed_data['lists']:
                lists_data = []
                for lst in parsed_data['lists']:
                    if lst['type'] == 'checklist':
                        for item in lst['items']:
                            lists_data.append({
                                'Type': lst['type'],
                                'Item': item['item'],
                                'Checked': 'Yes' if item['checked'] else 'No'
                            })
                    else:
                        for item in lst['items']:
                            lists_data.append({
                                'Type': lst['type'],
                                'Item': item,
                                'Checked': ''
                            })
                
                if lists_data:
                    pd.DataFrame(lists_data).to_excel(writer, sheet_name='Lists', index=False)
            
            # 5. 코드 블록들
            if parsed_data['code_blocks']:
                code_data = []
                for i, block in enumerate(parsed_data['code_blocks'], 1):
                    code_data.append({
                        'No': i,
                        'Language': block['language'],
                        'Code': block['code'][:1000] + '...' if len(block['code']) > 1000 else block['code']
                    })
                
                pd.DataFrame(code_data).to_excel(writer, sheet_name='Code Blocks', index=False)
    
    def clean_sheet_name(self, name: str, index: int) -> str:
        """Excel 시트 이름 정리 (31자 제한, 특수문자 제거)"""
        # 특수문자 제거
        clean_name = re.sub(r'[^\w\s-]', '', name)
        clean_name = clean_name.strip()
        
        # 비어있으면 기본 이름
        if not clean_name:
            clean_name = f'Table_{index}'
        
        # 31자 제한
        if len(clean_name) > 28:
            clean_name = clean_name[:25] + f'_{index}'
        else:
            clean_name = f'{clean_name}_{index}'
        
        return clean_name
    
    def convert_file(self, input_file: str, output_file: str = None):
        """단일 파일 변환"""
        if not os.path.exists(input_file):
            print(f"Error: File not found: {input_file}")
            return False
        
        # 출력 파일명 생성
        if not output_file:
            base_name = Path(input_file).stem
            output_dir = Path('excel_reports')
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        try:
            # 파싱 및 변환
            parsed_data = self.parse_markdown_file(input_file)
            self.to_excel(parsed_data, str(output_file))
            
            print(f"Success: Converted {input_file} to {output_file}")
            print(f"  - Tables: {len(parsed_data['tables'])}")
            print(f"  - Sections: {len(parsed_data['sections'])}")
            print(f"  - Lists: {len(parsed_data['lists'])}")
            
            return True
            
        except Exception as e:
            print(f"Error converting {input_file}: {str(e)}")
            return False
    
    def convert_multiple(self, input_files: List[str], merge: bool = False):
        """여러 파일 변환"""
        if merge:
            # 모든 파일을 하나의 Excel로 병합
            output_file = Path('excel_reports') / f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            with pd.ExcelWriter(str(output_file), engine='openpyxl') as writer:
                for file_path in input_files:
                    if os.path.exists(file_path):
                        parsed_data = self.parse_markdown_file(file_path)
                        
                        # 파일별로 시트 추가
                        file_sheet_name = self.clean_sheet_name(Path(file_path).stem, 0)[:31]
                        
                        # 각 테이블을 시트로 추가
                        for i, table in enumerate(parsed_data['tables'], 1):
                            sheet_name = f"{file_sheet_name}_{i}"[:31]
                            table['data'].to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"Merged {len(input_files)} files into {output_file}")
        
        else:
            # 각각 개별 파일로 변환
            for file_path in input_files:
                self.convert_file(file_path)

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Convert Markdown files to Excel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python md2excel.py docs/target-site-analysis.md
  python md2excel.py docs/target-site-analysis.md output.xlsx
  python md2excel.py docs/*.md --merge
  python md2excel.py --help
        """
    )
    
    parser.add_argument('input', nargs='+', help='Input markdown file(s)')
    parser.add_argument('output', nargs='?', help='Output Excel file (optional)')
    parser.add_argument('--merge', action='store_true', help='Merge multiple files into one Excel')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    # 변환기 생성
    converter = MarkdownToExcel()
    
    # 입력 파일 처리
    input_files = []
    for pattern in args.input:
        if '*' in pattern:
            # 와일드카드 처리
            from glob import glob
            input_files.extend(glob(pattern))
        else:
            input_files.append(pattern)
    
    if not input_files:
        print("Error: No input files found")
        sys.exit(1)
    
    # 단일 파일 vs 다중 파일 처리
    if len(input_files) == 1 and not args.merge:
        converter.convert_file(input_files[0], args.output)
    else:
        converter.convert_multiple(input_files, merge=args.merge)

if __name__ == "__main__":
    main()
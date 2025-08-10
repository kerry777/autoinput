"""
엑셀 데이터를 활용한 HWP 문서 자동 생성/편집 시스템
Excel 데이터를 읽어서 HWP 문서를 자동으로 생성, 편집, PDF 변환

사용 사례:
1. 계약서 일괄 생성
2. 증명서 대량 발급
3. 보고서 자동 생성
4. 양식 문서 일괄 작성
"""

import win32com.client
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import shutil
from typing import Dict, List
import time

class ExcelHWPAutomation:
    """엑셀 데이터 기반 HWP 문서 자동화 클래스"""
    
    def __init__(self):
        """초기화"""
        self.hwp = None
        self.current_file = None
        
    def init_hwp(self):
        """한글 프로그램 초기화"""
        try:
            self.hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
            self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            print("[SUCCESS] 한글 프로그램 초기화 완료")
            return True
        except Exception as e:
            print(f"[ERROR] 한글 초기화 실패: {e}")
            return False
    
    def read_excel_data(self, excel_path: str) -> pd.DataFrame:
        """엑셀 파일에서 데이터 읽기"""
        try:
            df = pd.read_excel(excel_path)
            print(f"[SUCCESS] 엑셀 데이터 로드: {len(df)}개 행")
            return df
        except Exception as e:
            print(f"[ERROR] 엑셀 읽기 실패: {e}")
            return None
    
    def create_document_from_template(self, template_path: str, data: Dict, output_path: str):
        """템플릿 기반 문서 생성"""
        try:
            # 템플릿 파일 열기
            self.hwp.Open(template_path)
            self.current_file = template_path
            
            # 데이터 치환
            for field, value in data.items():
                self.replace_text(f"{{{field}}}", str(value))
            
            # 저장
            self.hwp.SaveAs(output_path)
            print(f"[SUCCESS] 문서 생성: {Path(output_path).name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 문서 생성 실패: {e}")
            return False
    
    def replace_text(self, find_text: str, replace_text: str):
        """텍스트 찾기 및 바꾸기"""
        try:
            # 문서 처음으로 이동
            self.hwp.MoveDocBegin()
            
            # 찾기 및 바꾸기 설정
            self.hwp.HAction.GetDefault("RepeatFind", self.hwp.HParameterSet.HFindReplace.HSet)
            self.hwp.HParameterSet.HFindReplace.FindString = find_text
            self.hwp.HParameterSet.HFindReplace.ReplaceString = replace_text
            self.hwp.HParameterSet.HFindReplace.IgnoreMessage = 1
            self.hwp.HParameterSet.HFindReplace.ReplaceMode = 1
            self.hwp.HParameterSet.HFindReplace.ReplaceAll = 1
            
            # 실행
            self.hwp.HAction.Execute("RepeatFind", self.hwp.HParameterSet.HFindReplace.HSet)
            
        except Exception as e:
            print(f"[WARNING] 텍스트 치환 실패 ({find_text}): {e}")
    
    def insert_table_from_dataframe(self, df: pd.DataFrame, position: str = "current"):
        """데이터프레임을 표로 삽입"""
        try:
            rows = len(df) + 1  # 헤더 포함
            cols = len(df.columns)
            
            # 표 생성
            self.hwp.HAction.GetDefault("TableCreate", self.hwp.HParameterSet.HTableCreation.HSet)
            self.hwp.HParameterSet.HTableCreation.Rows = rows
            self.hwp.HParameterSet.HTableCreation.Cols = cols
            self.hwp.HAction.Execute("TableCreate", self.hwp.HParameterSet.HTableCreation.HSet)
            
            # 헤더 입력
            for col_idx, col_name in enumerate(df.columns):
                self.hwp.HAction.GetDefault("TableCellBlock", self.hwp.HParameterSet.HTableCellBlock.HSet)
                self.hwp.HParameterSet.HTableCellBlock.Row = 0
                self.hwp.HParameterSet.HTableCellBlock.Col = col_idx
                self.hwp.HAction.Execute("TableCellBlock", self.hwp.HParameterSet.HTableCellBlock.HSet)
                self.hwp.HAction.Run("InsertText")
                self.hwp.HAction.GetDefault("InsertText", self.hwp.HParameterSet.HInsertText.HSet)
                self.hwp.HParameterSet.HInsertText.Text = str(col_name)
                self.hwp.HAction.Execute("InsertText", self.hwp.HParameterSet.HInsertText.HSet)
            
            # 데이터 입력
            for row_idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    self.hwp.HAction.GetDefault("TableCellBlock", self.hwp.HParameterSet.HTableCellBlock.HSet)
                    self.hwp.HParameterSet.HTableCellBlock.Row = row_idx + 1
                    self.hwp.HParameterSet.HTableCellBlock.Col = col_idx
                    self.hwp.HAction.Execute("TableCellBlock", self.hwp.HParameterSet.HTableCellBlock.HSet)
                    self.hwp.HAction.Run("InsertText")
                    self.hwp.HAction.GetDefault("InsertText", self.hwp.HParameterSet.HInsertText.HSet)
                    self.hwp.HParameterSet.HInsertText.Text = str(value)
                    self.hwp.HAction.Execute("InsertText", self.hwp.HParameterSet.HInsertText.HSet)
            
            print(f"[SUCCESS] 표 삽입 완료: {rows}행 x {cols}열")
            
        except Exception as e:
            print(f"[ERROR] 표 삽입 실패: {e}")
    
    def convert_to_pdf(self, hwp_path: str, pdf_path: str):
        """HWP를 PDF로 변환"""
        try:
            self.hwp.Open(hwp_path)
            self.hwp.SaveAs(pdf_path, "PDF")
            print(f"[SUCCESS] PDF 변환: {Path(pdf_path).name}")
            return True
        except Exception as e:
            print(f"[ERROR] PDF 변환 실패: {e}")
            return False
    
    def batch_process(self, excel_path: str, template_path: str, output_dir: str):
        """엑셀 데이터를 기반으로 일괄 처리"""
        
        # 출력 디렉토리 생성
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 엑셀 데이터 읽기
        df = self.read_excel_data(excel_path)
        if df is None:
            return
        
        # 한글 초기화
        if not self.init_hwp():
            return
        
        success_count = 0
        fail_count = 0
        
        print(f"\n[시작] 총 {len(df)}개 문서 생성")
        print("=" * 60)
        
        # 각 행에 대해 문서 생성
        for idx, row in df.iterrows():
            try:
                # 파일명 생성 (예: 이름_날짜.hwp)
                filename = f"{row.get('이름', f'문서_{idx+1}')}_{datetime.now().strftime('%Y%m%d')}.hwp"
                output_file = output_path / filename
                
                # 데이터 딕셔너리 생성
                data = row.to_dict()
                
                # 문서 생성
                if self.create_document_from_template(template_path, data, str(output_file)):
                    success_count += 1
                    
                    # PDF로도 변환
                    pdf_file = output_file.with_suffix('.pdf')
                    self.convert_to_pdf(str(output_file), str(pdf_file))
                else:
                    fail_count += 1
                    
                print(f"진행: {idx+1}/{len(df)}")
                
            except Exception as e:
                print(f"[ERROR] 행 {idx+1} 처리 실패: {e}")
                fail_count += 1
        
        # 한글 종료
        try:
            self.hwp.Quit()
        except:
            pass
        
        # 결과 출력
        print("\n" + "=" * 60)
        print(f"[완료] 성공: {success_count}, 실패: {fail_count}")
        print(f"[위치] {output_path}")
    
    def close(self):
        """한글 프로그램 종료"""
        if self.hwp:
            try:
                self.hwp.Quit()
                print("[INFO] 한글 프로그램 종료")
            except:
                pass


def create_sample_excel(filepath: str):
    """테스트용 엑셀 파일 생성"""
    data = {
        '이름': ['김철수', '이영희', '박민수', '정미경', '최준호'],
        '부서': ['개발팀', '인사팀', '영업팀', '재무팀', '기획팀'],
        '직급': ['과장', '대리', '부장', '차장', '사원'],
        '입사일': ['2020-03-15', '2021-07-01', '2019-11-20', '2022-01-10', '2023-05-01'],
        '급여': [4500000, 3500000, 5500000, 4800000, 3000000],
        '연락처': ['010-1234-5678', '010-2345-6789', '010-3456-7890', '010-4567-8901', '010-5678-9012'],
        '이메일': ['kim@company.com', 'lee@company.com', 'park@company.com', 'jung@company.com', 'choi@company.com']
    }
    
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    print(f"[SUCCESS] 샘플 엑셀 파일 생성: {filepath}")
    return df


def create_sample_template(filepath: str):
    """테스트용 HWP 템플릿 생성 (수동 필요)"""
    template_content = """
    =====================================
    인 사 발 령 통 지 서
    =====================================
    
    성명: {이름}
    부서: {부서}
    직급: {직급}
    
    귀하는 {입사일}부로 위와 같이 임명되었음을 통지합니다.
    
    연봉: {급여}원
    연락처: {연락처}
    이메일: {이메일}
    
    발령일: {입사일}
    
    =====================================
    주식회사 테스트
    대표이사
    =====================================
    """
    
    print("[INFO] HWP 템플릿 내용:")
    print(template_content)
    print("\n[주의] HWP 템플릿은 한글에서 직접 만들어야 합니다.")
    print("위 내용을 복사하여 한글 문서를 만들고 {필드명} 형식으로 치환할 부분을 표시하세요.")
    

if __name__ == "__main__":
    print("=" * 60)
    print("엑셀-HWP 자동화 시스템")
    print("=" * 60)
    
    # 디렉토리 설정
    base_dir = Path(r"C:\projects\autoinput\data\excel_hwp_automation")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    excel_file = base_dir / "직원명단.xlsx"
    template_file = base_dir / "인사발령_템플릿.hwp"
    output_dir = base_dir / "output"
    
    # 1. 샘플 엑셀 파일 생성
    print("\n[1] 샘플 엑셀 파일 생성")
    create_sample_excel(str(excel_file))
    
    # 2. 템플릿 안내
    print("\n[2] HWP 템플릿 생성 안내")
    create_sample_template(str(template_file))
    
    # 3. 자동화 실행 (템플릿이 있는 경우)
    if template_file.exists():
        print("\n[3] 자동화 실행")
        automation = ExcelHWPAutomation()
        automation.batch_process(str(excel_file), str(template_file), str(output_dir))
    else:
        print("\n[3] 템플릿 파일이 없습니다.")
        print(f"   경로: {template_file}")
        print("   한글에서 템플릿을 먼저 만들어주세요.")
    
    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
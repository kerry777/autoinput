"""
엑셀-HWP 자동화 개선 버전
- 파일명 인코딩 문제 해결
- 보안 경고 최소화
- 에러 처리 강화
- 안정성 향상
"""

import win32com.client as win32
import pandas as pd
import os
from pathlib import Path
from PyPDF2 import PdfMerger
import time
import logging
from typing import Dict, List, Optional
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hwp_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImprovedHWPAutomation:
    """개선된 HWP 자동화 클래스"""
    
    def __init__(self, show_hwp_window: bool = False):
        """
        초기화
        
        Args:
            show_hwp_window: 한글 창 표시 여부 (False로 설정하면 백그라운드 실행)
        """
        self.hwp = None
        self.show_window = show_hwp_window
        self.security_module_registered = False
        
    def init_hwp(self) -> bool:
        """한글 프로그램 초기화 (개선된 버전)"""
        try:
            # COM 객체 생성
            self.hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")
            
            # 보안 모듈 등록 (한 번만)
            if not self.security_module_registered:
                self._register_security_module()
                self.security_module_registered = True
            
            # 한글 프로그램 설정
            self._configure_hwp()
            
            logger.info("한글 프로그램 초기화 성공")
            return True
            
        except Exception as e:
            logger.error(f"한글 초기화 실패: {e}")
            return False
    
    def _register_security_module(self):
        """보안 모듈 등록"""
        try:
            # 여러 방법 시도
            module_paths = [
                ('FilePathCheckDLL', 'FilePathCheckerModule'),
                ('FilePathCheckDLL', 'AutomationModule'),
            ]
            
            for dll_name, module_name in module_paths:
                try:
                    self.hwp.RegisterModule(dll_name, module_name)
                    logger.info(f"보안 모듈 등록 성공: {dll_name}")
                    break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"보안 모듈 등록 실패 (계속 진행): {e}")
    
    def _configure_hwp(self):
        """한글 프로그램 설정"""
        try:
            # 메시지 박스 표시 안함
            self.hwp.HAction.GetDefault("OptionDialog", self.hwp.HParameterSet.HOptionDialog.HSet)
            
            # 보안 경고 최소화 설정 시도
            try:
                # 자동 저장 비활성화
                self.hwp.HParameterSet.HAutoSave.AutoSave = 0
                # 백업 파일 생성 비활성화
                self.hwp.HParameterSet.HAutoSave.BackupFile = 0
            except:
                pass
                
        except Exception as e:
            logger.warning(f"한글 설정 실패 (계속 진행): {e}")
    
    def open_document(self, file_path: str, readonly: bool = False) -> bool:
        """
        문서 열기 (개선된 버전)
        
        Args:
            file_path: HWP 파일 경로
            readonly: 읽기 전용으로 열기
        """
        try:
            # 파일 경로 정규화 (인코딩 문제 해결)
            file_path = os.path.abspath(file_path)
            
            # 파일 존재 확인
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않음: {file_path}")
                return False
            
            # 문서 열기
            result = self.hwp.Open(file_path, "HWP", "forceopen:true")
            
            if result:
                logger.info(f"문서 열기 성공: {Path(file_path).name}")
                
                # 창 숨기기 (백그라운드 실행)
                if not self.show_window:
                    try:
                        # XHwpWindows 사용하지 않고 다른 방법 시도
                        self.hwp.Run("FileNew")  # 새 창 열기
                        self.hwp.Run("Cancel")    # 취소하여 원래 문서 유지
                    except:
                        pass  # 실패해도 계속 진행
                        
                return True
            else:
                logger.error(f"문서 열기 실패: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"문서 열기 중 오류: {e}")
            return False
    
    def save_document(self, file_path: str, format: str = "HWP") -> bool:
        """
        문서 저장 (개선된 버전)
        
        Args:
            file_path: 저장 경로
            format: 저장 형식 (HWP, PDF, DOCX, HTML, TXT)
        """
        try:
            # 파일 경로 정규화
            file_path = os.path.abspath(file_path)
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 형식별 저장
            if format.upper() == "PDF":
                # PDF 저장 (더 안정적인 방법)
                self.hwp.SaveAs(file_path, "PDF")
            else:
                # 다른 형식 저장
                self.hwp.SaveAs(file_path, format)
            
            logger.info(f"문서 저장 성공: {Path(file_path).name} ({format})")
            return True
            
        except Exception as e:
            logger.error(f"문서 저장 실패: {e}")
            return False
    
    def replace_text(self, find_text: str, replace_text: str, 
                    replace_all: bool = True) -> int:
        """
        텍스트 찾기 및 바꾸기 (개선된 버전)
        
        Args:
            find_text: 찾을 텍스트
            replace_text: 바꿀 텍스트
            replace_all: 모두 바꾸기 여부
            
        Returns:
            바뀐 개수
        """
        try:
            # 문서 처음으로 이동
            self.hwp.MoveDocBegin()
            
            # 찾기 및 바꾸기 설정
            option = self.hwp.HParameterSet.HFindReplace
            self.hwp.HAction.GetDefault("AllReplace", option.HSet)
            
            option.FindString = find_text
            option.ReplaceString = replace_text
            option.IgnoreMessage = 1  # 메시지 무시
            option.Direction = 0  # 정방향
            
            if replace_all:
                option.ReplaceAll = 1
                self.hwp.HAction.Execute("AllReplace", option.HSet)
                logger.info(f"텍스트 모두 바꾸기: '{find_text}' → '{replace_text}'")
            else:
                option.ReplaceAll = 0
                self.hwp.HAction.Execute("FindReplace", option.HSet)
                logger.info(f"텍스트 바꾸기: '{find_text}' → '{replace_text}'")
            
            return 1  # 실제 개수는 API에서 제공하지 않음
            
        except Exception as e:
            logger.error(f"텍스트 바꾸기 실패: {e}")
            return 0
    
    def change_text_color(self, from_color: tuple, to_color: tuple = (0, 0, 0)) -> bool:
        """
        텍스트 색상 변경 (개선된 버전)
        
        Args:
            from_color: 원래 색상 (R, G, B)
            to_color: 바꿀 색상 (R, G, B)
        """
        try:
            option = self.hwp.HParameterSet.HFindReplace
            self.hwp.HAction.GetDefault("AllReplace", option.HSet)
            
            option.FindString = ""
            option.ReplaceString = ""
            option.IgnoreMessage = 1
            option.FindCharShape.TextColor = self.hwp.RGBColor(*from_color)
            option.ReplaceCharShape.TextColor = self.hwp.RGBColor(*to_color)
            
            self.hwp.HAction.Execute("AllReplace", option.HSet)
            
            logger.info(f"색상 변경: RGB{from_color} → RGB{to_color}")
            return True
            
        except Exception as e:
            logger.error(f"색상 변경 실패: {e}")
            return False
    
    def batch_process_with_excel(self, excel_path: str, template_path: str, 
                                 output_dir: str, sheet_name: str = 'Sheet1'):
        """
        엑셀 데이터로 일괄 처리 (개선된 버전)
        
        Args:
            excel_path: 엑셀 파일 경로
            template_path: HWP 템플릿 경로
            output_dir: 출력 디렉토리
            sheet_name: 엑셀 시트 이름
        """
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 엑셀 데이터 읽기
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            logger.info(f"엑셀 데이터 로드: {len(df)}개 행")
        except Exception as e:
            logger.error(f"엑셀 읽기 실패: {e}")
            return
        
        # 한글 초기화
        if not self.init_hwp():
            return
        
        success_count = 0
        fail_count = 0
        
        # 각 행 처리
        for idx, row in df.iterrows():
            try:
                logger.info(f"처리 중: {idx + 1}/{len(df)}")
                
                # 템플릿 열기
                if not self.open_document(template_path):
                    fail_count += 1
                    continue
                
                # 데이터 치환
                for column, value in row.items():
                    placeholder = f"{{{column}}}"
                    self.replace_text(placeholder, str(value))
                
                # 파일명 생성 (안전한 파일명)
                safe_name = self._make_safe_filename(row, idx)
                
                # HWP 저장
                hwp_path = os.path.join(output_dir, f"{safe_name}.hwp")
                self.save_document(hwp_path, "HWP")
                
                # PDF 저장
                pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")
                self.save_document(pdf_path, "PDF")
                
                success_count += 1
                
                # 잠시 대기 (안정성)
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"행 {idx + 1} 처리 실패: {e}")
                fail_count += 1
        
        # 종료
        self.close()
        
        # 결과 출력
        logger.info(f"완료: 성공 {success_count}, 실패 {fail_count}")
    
    def _make_safe_filename(self, row: pd.Series, idx: int) -> str:
        """안전한 파일명 생성"""
        # 첫 번째 컬럼 값이나 인덱스 사용
        if not row.empty:
            name = str(row.iloc[0])
            # 특수문자 제거
            for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                name = name.replace(char, '_')
            return name[:50]  # 최대 50자
        return f"document_{idx + 1}"
    
    def close(self):
        """한글 프로그램 종료"""
        if self.hwp:
            try:
                self.hwp.Quit()
                logger.info("한글 프로그램 종료")
            except:
                pass


class ColorChangeAutomation(ImprovedHWPAutomation):
    """색상 변경 특화 자동화 클래스"""
    
    def process_color_changes(self, input_dir: str, output_dir: str):
        """
        디렉토리의 모든 HWP 파일 색상 변경
        빨간색, 파란색 → 검은색
        """
        # 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # HWP 파일 목록
        hwp_files = list(Path(input_dir).glob("*.hwp"))
        logger.info(f"처리할 파일: {len(hwp_files)}개")
        
        # 한글 초기화
        if not self.init_hwp():
            return
        
        for hwp_file in hwp_files:
            try:
                logger.info(f"처리 중: {hwp_file.name}")
                
                # 문서 열기
                if not self.open_document(str(hwp_file)):
                    continue
                
                # 색상 변경
                self.change_text_color((255, 0, 0), (0, 0, 0))  # 빨간색 → 검은색
                self.change_text_color((0, 0, 255), (0, 0, 0))  # 파란색 → 검은색
                
                # 저장
                output_path = output_dir / hwp_file.name
                self.save_document(str(output_path), "HWP")
                
                # PDF로도 저장
                pdf_path = output_path.with_suffix('.pdf')
                self.save_document(str(pdf_path), "PDF")
                
                logger.info(f"완료: {hwp_file.name}")
                
            except Exception as e:
                logger.error(f"파일 처리 실패 {hwp_file.name}: {e}")
        
        self.close()


def merge_pdfs(pdf_list: List[str], output_path: str):
    """PDF 파일 병합 (개선된 버전)"""
    try:
        merger = PdfMerger(strict=False)
        
        for pdf_path in pdf_list:
            if os.path.exists(pdf_path):
                merger.append(pdf_path)
                logger.info(f"PDF 추가: {Path(pdf_path).name}")
        
        merger.write(output_path)
        merger.close()
        
        logger.info(f"PDF 병합 완료: {Path(output_path).name}")
        
    except Exception as e:
        logger.error(f"PDF 병합 실패: {e}")


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("개선된 엑셀-HWP 자동화 시스템")
    print("=" * 60)
    
    # 예제 1: 엑셀 데이터로 문서 생성
    automation = ImprovedHWPAutomation(show_hwp_window=False)
    
    # 예제 2: 색상 변경 자동화
    color_automation = ColorChangeAutomation(show_hwp_window=False)
    
    print("\n사용 예시:")
    print("1. automation.batch_process_with_excel('data.xlsx', 'template.hwp', 'output/')")
    print("2. color_automation.process_color_changes('input/', 'output/')")
    

if __name__ == "__main__":
    main()
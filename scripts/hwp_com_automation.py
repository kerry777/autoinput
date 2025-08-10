#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
한컴 오피스 COM 자동화를 사용한 HWP to PDF 변환
Windows에서 한컴 오피스가 설치되어 있어야 작동
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime
import codecs

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

try:
    import win32com.client
    import pythoncom
except ImportError:
    print("pywin32가 필요합니다: pip install pywin32")
    sys.exit(1)

class HancomAutomation:
    """한컴 오피스 COM 자동화"""
    
    def __init__(self):
        self.hwp = None
        
    def initialize(self):
        """한컴 오피스 초기화"""
        try:
            # COM 초기화
            pythoncom.CoInitialize()
            
            # 한컴 오피스 객체 생성 시도
            try:
                # 한글 2018 이상
                self.hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
                print("한컴 오피스 객체 생성 성공 (HWPFrame.HwpObject)")
                return True
            except:
                pass
            
            try:
                # 한글 2014
                self.hwp = win32com.client.Dispatch("HancomOffice.HwpObject")
                print("한컴 오피스 객체 생성 성공 (HancomOffice.HwpObject)")
                return True
            except:
                pass
            
            try:
                # 한글 2010
                self.hwp = win32com.client.Dispatch("HWP.Application")
                print("한컴 오피스 객체 생성 성공 (HWP.Application)")
                return True
            except:
                pass
            
            print("한컴 오피스가 설치되어 있지 않거나 COM 객체를 생성할 수 없습니다.")
            return False
            
        except Exception as e:
            print(f"초기화 오류: {e}")
            return False
    
    def open_file(self, hwp_path):
        """HWP 파일 열기"""
        try:
            hwp_path = str(Path(hwp_path).absolute())
            
            # RegisterModule 시도 (보안 모듈)
            try:
                self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            except:
                pass
            
            # 파일 열기
            result = self.hwp.Open(hwp_path, "HWP", "forceopen:true")
            
            if result:
                print(f"파일 열기 성공: {hwp_path}")
                return True
            else:
                print(f"파일 열기 실패: {hwp_path}")
                return False
                
        except Exception as e:
            print(f"파일 열기 오류: {e}")
            return False
    
    def save_as_pdf(self, pdf_path):
        """PDF로 저장"""
        try:
            pdf_path = str(Path(pdf_path).absolute())
            
            # PDF 저장 옵션 설정
            try:
                self.hwp.HAction.GetDefault("FileSaveAsPdf", self.hwp.HParameterSet.HFileOpenSave.HSet)
                self.hwp.HParameterSet.HFileOpenSave.filename = pdf_path
                self.hwp.HParameterSet.HFileOpenSave.Format = "PDF"
                self.hwp.HAction.Execute("FileSaveAsPdf", self.hwp.HParameterSet.HFileOpenSave.HSet)
                print(f"PDF 저장 성공 (HAction): {pdf_path}")
                return True
            except:
                pass
            
            # 대체 방법 1: SaveAs 메서드
            try:
                self.hwp.SaveAs(pdf_path, "PDF")
                print(f"PDF 저장 성공 (SaveAs): {pdf_path}")
                return True
            except:
                pass
            
            # 대체 방법 2: HAction Run
            try:
                self.hwp.Run("FileSaveAsPdf")
                print(f"PDF 저장 시도 (Run): {pdf_path}")
                return True
            except:
                pass
            
            print(f"PDF 저장 실패: {pdf_path}")
            return False
            
        except Exception as e:
            print(f"PDF 저장 오류: {e}")
            return False
    
    def extract_text(self):
        """텍스트 추출"""
        try:
            # 전체 선택
            self.hwp.Run("SelectAll")
            
            # 텍스트 가져오기
            text = self.hwp.GetTextFile("Text", "")
            
            if text:
                print(f"텍스트 추출 성공: {len(text)} 문자")
                return text
            else:
                print("텍스트 추출 실패")
                return ""
                
        except Exception as e:
            print(f"텍스트 추출 오류: {e}")
            return ""
    
    def close(self):
        """한컴 오피스 종료"""
        try:
            if self.hwp:
                self.hwp.Clear(1)  # 문서 닫기
                self.hwp.Quit()    # 프로그램 종료
                print("한컴 오피스 종료")
        except:
            pass
        finally:
            pythoncom.CoUninitialize()
    
    def convert_hwp_to_pdf(self, hwp_path, pdf_path=None):
        """HWP를 PDF로 변환"""
        try:
            if not pdf_path:
                pdf_path = Path(hwp_path).with_suffix('.pdf')
            
            # 파일 열기
            if not self.open_file(hwp_path):
                return False
            
            # PDF로 저장
            if self.save_as_pdf(pdf_path):
                # PDF 파일 존재 확인
                if Path(pdf_path).exists():
                    print(f"✅ 변환 성공: {pdf_path}")
                    return True
                else:
                    # 잠시 대기 후 재확인
                    time.sleep(2)
                    if Path(pdf_path).exists():
                        print(f"✅ 변환 성공: {pdf_path}")
                        return True
            
            return False
            
        except Exception as e:
            print(f"변환 오류: {e}")
            return False


def test_hancom_automation():
    """한컴 자동화 테스트"""
    
    test_files = [
        r"C:\projects\autoinput\data\downloads\attachments_working\post_60125\증거서류반환신청서.hwp",
        r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    ]
    
    # PDF가 없는 HWP 파일 찾기
    hwp_without_pdf = []
    for hwp_file in test_files:
        if Path(hwp_file).exists():
            pdf_file = Path(hwp_file).with_suffix('.pdf')
            if not pdf_file.exists():
                hwp_without_pdf.append(hwp_file)
    
    if not hwp_without_pdf:
        print("변환할 HWP 파일이 없습니다. (모두 PDF가 이미 존재)")
        
        # 그래도 테스트를 위해 첫 번째 파일로 시도
        if test_files and Path(test_files[0]).exists():
            hwp_without_pdf = [test_files[0]]
    
    output_dir = Path(r"C:\projects\autoinput\data\hwp_com_converted")
    output_dir.mkdir(exist_ok=True)
    
    # 한컴 자동화 객체 생성
    hancom = HancomAutomation()
    
    if not hancom.initialize():
        print("한컴 오피스를 사용할 수 없습니다.")
        return
    
    success_count = 0
    
    for hwp_file in hwp_without_pdf:
        print(f"\n{'='*60}")
        print(f"변환 시작: {Path(hwp_file).name}")
        print(f"{'='*60}")
        
        pdf_path = output_dir / f"{Path(hwp_file).stem}_com.pdf"
        
        if hancom.convert_hwp_to_pdf(hwp_file, pdf_path):
            success_count += 1
            
            # 텍스트도 추출해보기
            text = hancom.extract_text()
            if text:
                text_path = output_dir / f"{Path(hwp_file).stem}_com.txt"
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"텍스트 저장: {text_path}")
        else:
            print(f"❌ 변환 실패")
    
    # 종료
    hancom.close()
    
    print(f"\n{'='*60}")
    print(f"변환 완료: {success_count}/{len(hwp_without_pdf)} 성공")
    print(f"{'='*60}")


def check_com_objects():
    """사용 가능한 COM 객체 확인"""
    print("한컴 오피스 COM 객체 확인")
    print("="*60)
    
    com_objects = [
        "HWPFrame.HwpObject",
        "HancomOffice.HwpObject", 
        "HWP.Application",
        "Hwp.Application",
        "HncHwpLib.HwpObject"
    ]
    
    for obj_name in com_objects:
        try:
            obj = win32com.client.Dispatch(obj_name)
            print(f"✅ {obj_name}: 사용 가능")
            obj.Quit()
        except Exception as e:
            print(f"❌ {obj_name}: 사용 불가 - {str(e)[:50]}")
    
    print("="*60)


if __name__ == "__main__":
    print("한컴 오피스 COM 자동화 테스트")
    print("Windows에서 한컴 오피스가 설치되어 있어야 작동합니다.")
    print()
    
    # COM 객체 확인
    check_com_objects()
    print()
    
    # 변환 테스트
    test_hancom_automation()
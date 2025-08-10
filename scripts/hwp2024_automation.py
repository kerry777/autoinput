#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
한글 2024 자동화 스크립트
pyautogui를 사용한 GUI 자동화로 HWP to PDF 변환
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import codecs

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

try:
    import pyautogui
    import pyperclip
except ImportError:
    print("필요한 라이브러리 설치:")
    print("pip install pyautogui pyperclip pillow")
    sys.exit(1)

class HWP2024Automation:
    """한글 2024 GUI 자동화"""
    
    def __init__(self):
        # 안전 설정
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        
    def find_hwp_exe(self):
        """한글 2024 실행 파일 찾기"""
        possible_paths = [
            r"C:\Program Files\Hnc\Office 2024\HOffice130\Bin\Hwp.exe",
            r"C:\Program Files (x86)\Hnc\Office 2024\HOffice130\Bin\Hwp.exe",
            r"C:\Program Files\HNC\HOffice130\Bin\Hwp.exe",
            r"C:\Program Files (x86)\HNC\HOffice130\Bin\Hwp.exe",
            r"C:\Program Files\Hnc\Office\HOffice130\Bin\Hwp.exe",
            r"C:\Program Files (x86)\Hnc\Office\HOffice130\Bin\Hwp.exe"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # 시작 메뉴 링크에서 찾기
        start_menu_link = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\한글 2024.lnk"
        if Path(start_menu_link).exists():
            return start_menu_link
        
        return None
    
    def launch_hwp(self):
        """한글 2024 실행"""
        hwp_path = self.find_hwp_exe()
        
        if not hwp_path:
            print("한글 2024 실행 파일을 찾을 수 없습니다.")
            print("직접 한글 2024를 실행해주세요.")
            return False
        
        try:
            subprocess.Popen([hwp_path])
            time.sleep(5)  # 프로그램 로딩 대기
            print(f"한글 2024 실행: {hwp_path}")
            return True
        except Exception as e:
            print(f"한글 2024 실행 실패: {e}")
            return False
    
    def open_file(self, hwp_path):
        """HWP 파일 열기"""
        try:
            # Ctrl+O (파일 열기)
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(1)
            
            # 파일 경로 입력
            pyperclip.copy(str(hwp_path))
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # Enter (열기)
            pyautogui.press('enter')
            time.sleep(3)  # 파일 로딩 대기
            
            print(f"파일 열기: {hwp_path}")
            return True
            
        except Exception as e:
            print(f"파일 열기 실패: {e}")
            return False
    
    def save_as_pdf(self, pdf_path):
        """PDF로 저장"""
        try:
            # Alt+F (파일 메뉴)
            pyautogui.hotkey('alt', 'f')
            time.sleep(0.5)
            
            # P (PDF로 저장) 또는 다른 이름으로 저장
            pyautogui.press('p')
            time.sleep(1)
            
            # PDF 저장 대화상자가 나타나지 않으면 다른 방법 시도
            # Ctrl+Shift+S (다른 이름으로 저장)
            pyautogui.hotkey('ctrl', 'shift', 's')
            time.sleep(1)
            
            # 파일 형식을 PDF로 변경
            pyautogui.press('tab', presses=3)  # 파일 형식 콤보박스로 이동
            pyautogui.press('p')  # PDF 선택
            time.sleep(0.5)
            
            # 파일 이름 입력
            pyautogui.hotkey('ctrl', 'a')  # 전체 선택
            pyperclip.copy(str(pdf_path))
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            # Enter (저장)
            pyautogui.press('enter')
            time.sleep(3)  # 저장 대기
            
            print(f"PDF 저장: {pdf_path}")
            return True
            
        except Exception as e:
            print(f"PDF 저장 실패: {e}")
            return False
    
    def close_hwp(self):
        """한글 2024 닫기"""
        try:
            pyautogui.hotkey('alt', 'f4')
            time.sleep(0.5)
            
            # 저장 확인 대화상자가 나타나면 '아니오' 선택
            pyautogui.press('n')
            
            print("한글 2024 종료")
        except:
            pass
    
    def convert_hwp_to_pdf(self, hwp_path, pdf_path=None):
        """HWP를 PDF로 변환 (GUI 자동화)"""
        
        if not pdf_path:
            pdf_path = Path(hwp_path).with_suffix('.pdf')
        
        print(f"\n{'='*60}")
        print("GUI 자동화로 HWP to PDF 변환")
        print(f"HWP: {hwp_path}")
        print(f"PDF: {pdf_path}")
        print("※ 변환 중에는 마우스와 키보드를 사용하지 마세요!")
        print(f"{'='*60}\n")
        
        # 한글 2024 실행
        if not self.launch_hwp():
            return False
        
        # 파일 열기
        if not self.open_file(hwp_path):
            self.close_hwp()
            return False
        
        # PDF로 저장
        success = self.save_as_pdf(pdf_path)
        
        # 한글 닫기
        self.close_hwp()
        
        # 결과 확인
        if success and Path(pdf_path).exists():
            print(f"✅ 변환 성공: {pdf_path}")
            return True
        else:
            print(f"❌ 변환 실패")
            return False


def manual_conversion_guide():
    """수동 변환 가이드"""
    guide = """
    === HWP to PDF 수동 변환 가이드 ===
    
    1. 한글 2024에서 HWP 파일 열기
       - 한글 2024 실행
       - 파일 > 열기 (Ctrl+O)
       - HWP 파일 선택
    
    2. PDF로 저장
       방법 1: 파일 > PDF로 저장
       방법 2: 파일 > 다른 이름으로 저장 (Ctrl+Shift+S)
               파일 형식: PDF 선택
    
    3. 일괄 변환 (여러 파일)
       - 파일 > 일괄 변환
       - HWP 파일들 선택
       - 출력 형식: PDF
       - 변환 시작
    
    4. 명령줄 변환 (한글 2024 지원 시)
       Hwp.exe /print /pdf "파일.hwp"
    """
    return guide


if __name__ == "__main__":
    print("한글 2024 자동화 변환")
    print("="*60)
    
    # 테스트 파일
    test_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    if not Path(test_file).exists():
        print(f"테스트 파일이 없습니다: {test_file}")
        print("\n" + manual_conversion_guide())
        sys.exit(1)
    
    # 자동화 시도
    automation = HWP2024Automation()
    
    output_dir = Path(r"C:\projects\autoinput\data\hwp_gui_converted")
    output_dir.mkdir(exist_ok=True)
    
    pdf_path = output_dir / f"{Path(test_file).stem}_gui.pdf"
    
    # GUI 자동화 변환
    success = automation.convert_hwp_to_pdf(test_file, pdf_path)
    
    if not success:
        print("\n자동화 실패. 수동 변환을 시도해주세요:")
        print(manual_conversion_guide())
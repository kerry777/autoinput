"""
실습 파일 실행 스크립트
"""

import sys
import os

# 경로 추가
practice_dir = r"C:\projects\autoinput\data\excel_hwp_practice"
sys.path.append(practice_dir)

# 작업 디렉토리 변경
os.chdir(practice_dir)

# main.py 실행
print("=" * 60)
print("엑셀-HWP 자동화 실습 실행")
print("=" * 60)
print()
print(f"작업 디렉토리: {os.getcwd()}")
print()

# main 모듈 import 및 실행
try:
    import main
    
    # Rpa 클래스 실행
    rpa = main.Rpa()
    
    print("[시작] HWP 문서 자동화 프로세스")
    print("-" * 60)
    
    # 실행
    rpa.run(
        exel_file_path='./input/list.xlsx',
        hwp_dir='./input',
        working_dir='./work',
        pdf_dir='./output'
    )
    
    print("-" * 60)
    print("[완료] 모든 작업이 완료되었습니다!")
    
except Exception as e:
    print(f"[오류] 실행 중 문제 발생: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
# -*- coding: utf-8 -*-
"""
HWP 파일 변환 실행 스크립트
"""
from pathlib import Path
import win32com.client as win32
import sys
import os

# UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

def convert_hwp_to_pdf():
    """HWP 파일을 PDF로 변환"""
    
    print("=" * 80)
    print("🚀 HWP → PDF 변환 시작")
    print("=" * 80)
    
    # 경로 설정
    hwp_dir = Path(r"C:\projects\autoinput\data\downloads\boards_test\서식자료실")
    pdf_dir = Path(r"C:\projects\autoinput\data\pdf_converted")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # HWP 파일 찾기
    hwp_files = list(hwp_dir.glob("*.hwp"))
    
    if not hwp_files:
        print("❌ HWP 파일을 찾을 수 없습니다.")
        return
    
    print(f"📁 발견된 HWP 파일: {len(hwp_files)}개")
    
    try:
        # HWP 객체 생성
        hwp = win32.gencache.EnsureDispatch("hwpframe.hwpobject")
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        
        # 보안 모듈 설정
        hwp.SetMessageBoxMode(0x00000020)  # 메시지박스 표시 안 함
        
        converted_count = 0
        
        for hwp_file in hwp_files:
            print(f"\n📄 변환 중: {hwp_file.name}")
            
            # 파일 열기
            if hwp.Open(str(hwp_file), "HWP", "forceopen:true"):
                # PDF로 저장
                pdf_path = pdf_dir / f"{hwp_file.stem}.pdf"
                
                # SaveAs 메서드 사용
                if hwp.SaveAs(str(pdf_path), "PDF"):
                    converted_count += 1
                    size_kb = pdf_path.stat().st_size / 1024 if pdf_path.exists() else 0
                    print(f"   ✅ 변환 성공: {pdf_path.name} ({size_kb:.1f}KB)")
                else:
                    print(f"   ❌ 변환 실패: {hwp_file.name}")
                
                # 파일 닫기
                hwp.Clear(1)  # 문서 닫기
            else:
                print(f"   ❌ 파일 열기 실패: {hwp_file.name}")
        
        # HWP 종료
        hwp.Quit()
        
        print(f"\n" + "=" * 80)
        print(f"🏆 변환 완료: {converted_count}/{len(hwp_files)} 파일")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    convert_hwp_to_pdf()
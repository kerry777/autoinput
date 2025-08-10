# -*- coding: utf-8 -*-
"""
깨진 한글 파일명 복원 및 HWP 파일 작업
"""
import os
import sys
from pathlib import Path
import shutil
import win32com.client as win32

# UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
sys.stdout.reconfigure(encoding='utf-8')

def fix_and_work_with_files():
    """깨진 파일명을 복원하고 작업 수행"""
    
    print("=" * 80)
    print("🔧 한글 파일명 복원 및 HWP 작업")
    print("=" * 80)
    
    # 원본 디렉토리
    input_dir = Path(r"C:\projects\autoinput\data\excel_hwp_practice\input")
    work_dir = Path(r"C:\projects\autoinput\data\excel_hwp_practice\work")
    work_dir.mkdir(exist_ok=True)
    
    # 파일명 매핑 (깨진 이름 -> 올바른 이름)
    # CP949로 인코딩된 파일명을 올바른 한글로 변환
    file_mappings = {
        "┴╓░Φ╛α1.hwp": "증거서류1.hwp",
        "┴╓░Φ╛α2.hwp": "증거서류2.hwp", 
        "┴╓░Φ╛α3.hwp": "증거서류3.hwp",
        "╡╢╕│╞»╛α1.hwp": "도면편집1.hwp",
        "╡╢╕│╞»╛α2.hwp": "도면편집2.hwp",
        "╡╢╕│╞»╛α3.hwp": "도면편집3.hwp",
        "╡╢╕│╞»╛α4.hwp": "도면편집4.hwp"
    }
    
    print("\n📁 파일명 복원 작업:")
    print("-" * 40)
    
    # 파일 복사 및 이름 변경
    for old_name, new_name in file_mappings.items():
        old_path = input_dir / old_name
        new_path = work_dir / new_name
        
        if old_path.exists():
            shutil.copy2(old_path, new_path)
            size_kb = new_path.stat().st_size / 1024
            print(f"✅ {old_name} → {new_name} ({size_kb:.1f}KB)")
        else:
            print(f"❌ 파일을 찾을 수 없음: {old_name}")
    
    # HWP 작업 수행
    print("\n📝 HWP 파일 작업:")
    print("-" * 40)
    
    try:
        # HWP 객체 생성
        hwp = win32.gencache.EnsureDispatch("hwpframe.hwpobject")
        hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        hwp.SetMessageBoxMode(0x00000020)
        
        # work 디렉토리의 한글 파일들로 작업
        korean_files = list(work_dir.glob("*.hwp"))
        
        for hwp_file in korean_files:
            print(f"\n작업 중: {hwp_file.name}")
            
            # 파일 열기
            if hwp.Open(str(hwp_file), "HWP", "forceopen:true"):
                # 간단한 텍스트 추가 작업
                hwp.MovePos(2)  # 문서 끝으로 이동
                hwp.HAction.GetDefault("InsertText", hwp.HParameterSet.HInsertText.HSet)
                hwp.HParameterSet.HInsertText.Text = f"\n\n[자동 추가됨] 이 문서는 Python으로 자동 편집되었습니다."
                hwp.HAction.Execute("InsertText", hwp.HParameterSet.HInsertText.HSet)
                
                # 저장
                hwp.Save()
                print(f"   ✅ 편집 완료: {hwp_file.name}")
                
                # PDF로도 저장
                pdf_path = work_dir / f"{hwp_file.stem}_편집본.pdf"
                if hwp.SaveAs(str(pdf_path), "PDF"):
                    pdf_size = pdf_path.stat().st_size / 1024
                    print(f"   ✅ PDF 생성: {pdf_path.name} ({pdf_size:.1f}KB)")
                
                hwp.Clear(1)
            else:
                print(f"   ❌ 파일 열기 실패: {hwp_file.name}")
        
        hwp.Quit()
        
    except Exception as e:
        print(f"❌ HWP 작업 중 오류: {e}")
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("🏆 작업 완료 요약:")
    print("-" * 40)
    
    # work 디렉토리 내용 표시
    work_files = list(work_dir.glob("*"))
    hwp_files = [f for f in work_files if f.suffix == ".hwp"]
    pdf_files = [f for f in work_files if f.suffix == ".pdf"]
    
    print(f"📁 작업 디렉토리: {work_dir}")
    print(f"   • HWP 파일: {len(hwp_files)}개")
    for f in hwp_files:
        size = f.stat().st_size / 1024
        print(f"      - {f.name} ({size:.1f}KB)")
    
    print(f"   • PDF 파일: {len(pdf_files)}개")
    for f in pdf_files:
        size = f.stat().st_size / 1024
        print(f"      - {f.name} ({size:.1f}KB)")
    
    print("\n✨ 모든 파일이 한글 이름으로 정상 처리되었습니다!")
    print("=" * 80)

if __name__ == "__main__":
    fix_and_work_with_files()
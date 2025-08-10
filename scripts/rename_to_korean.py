# -*- coding: utf-8 -*-
"""
깨진 파일명을 한글로 영구 변경
"""
import os
import sys
from pathlib import Path
import shutil

# UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
sys.stdout.reconfigure(encoding='utf-8')

def rename_files_to_korean():
    """input 폴더의 깨진 파일명을 한글로 변경"""
    
    print("=" * 80)
    print("🔧 깨진 파일명을 한글로 영구 변경")
    print("=" * 80)
    
    # input 디렉토리
    input_dir = Path(r"C:\projects\autoinput\data\excel_hwp_practice\input")
    
    # 파일명 매핑
    file_mappings = {
        "┴╓░Φ╛α1.hwp": "주계약1.hwp",
        "┴╓░Φ╛α2.hwp": "주계약2.hwp", 
        "┴╓░Φ╛α3.hwp": "주계약3.hwp",
        "╡╢╕│╞»╛α1.hwp": "독립특약1.hwp",
        "╡╢╕│╞»╛α2.hwp": "독립특약2.hwp",
        "╡╢╕│╞»╛α3.hwp": "독립특약3.hwp",
        "╡╢╕│╞»╛α4.hwp": "독립특약4.hwp",
        "╖╣┴÷╜║╞«╕«.JPG": "레지스터링.JPG"
    }
    
    print("\n📁 파일명 변경 작업:")
    print("-" * 40)
    
    # 백업 폴더 생성
    backup_dir = input_dir / "backup_original"
    backup_dir.mkdir(exist_ok=True)
    
    changed_count = 0
    
    for old_name, new_name in file_mappings.items():
        old_path = input_dir / old_name
        new_path = input_dir / new_name
        
        if old_path.exists():
            # 백업
            backup_path = backup_dir / old_name
            shutil.copy2(old_path, backup_path)
            
            # 이미 한글 이름 파일이 있으면 제거
            if new_path.exists():
                print(f"⚠️  기존 파일 덮어쓰기: {new_name}")
                new_path.unlink()
            
            # 이름 변경
            old_path.rename(new_path)
            
            size_kb = new_path.stat().st_size / 1024
            print(f"✅ {old_name}")
            print(f"   → {new_name} ({size_kb:.1f}KB)")
            changed_count += 1
        else:
            # 이미 변경되었는지 확인
            if new_path.exists():
                size_kb = new_path.stat().st_size / 1024
                print(f"ℹ️  이미 변경됨: {new_name} ({size_kb:.1f}KB)")
            else:
                print(f"❌ 파일 없음: {old_name}")
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 변경 결과:")
    print("-" * 40)
    
    # 현재 input 폴더 상태
    hwp_files = list(input_dir.glob("*.hwp"))
    print(f"\n📁 현재 HWP 파일 목록 ({len(hwp_files)}개):")
    
    # 주계약과 독립특약으로 분류
    main_contracts = sorted([f for f in hwp_files if "주계약" in f.name])
    sub_contracts = sorted([f for f in hwp_files if "독립특약" in f.name])
    
    if main_contracts:
        print("\n📄 주계약 문서:")
        for f in main_contracts:
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name} ({size_kb:.1f}KB)")
    
    if sub_contracts:
        print("\n📄 독립특약 문서:")
        for f in sub_contracts:
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name} ({size_kb:.1f}KB)")
    
    # JPG 파일 확인
    jpg_files = list(input_dir.glob("*.JPG"))
    if jpg_files:
        print("\n🖼️ 이미지 파일:")
        for f in jpg_files:
            size_kb = f.stat().st_size / 1024
            print(f"   • {f.name} ({size_kb:.1f}KB)")
    
    print(f"\n✅ 총 {changed_count}개 파일 이름 변경 완료!")
    print(f"📁 백업 위치: {backup_dir}")
    print("\n✨ 이제 모든 파일이 한글 이름으로 표시됩니다!")
    print("=" * 80)

if __name__ == "__main__":
    rename_files_to_korean()
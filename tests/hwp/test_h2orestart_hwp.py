"""
H2Orestart 확장 프로그램 설치 후 HWP 변환 테스트
LibreOffice + H2Orestart를 사용한 HWP/HWPX 파일 변환
"""

import subprocess
from pathlib import Path
import time

def test_h2orestart_conversion():
    """H2Orestart를 이용한 HWP 변환 테스트"""
    
    # LibreOffice 경로
    soffice_path = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    
    # 테스트할 HWP 파일
    hwp_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    # 출력 디렉토리
    output_dir = r"C:\projects\autoinput\data\h2orestart_converted"
    
    # 디렉토리 생성
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("H2Orestart를 이용한 HWP 변환 테스트")
    print("=" * 60)
    print()
    print("[IMPORTANT] H2Orestart 확장 프로그램이 설치되어 있어야 합니다!")
    print()
    
    # 1. infilter 옵션을 사용한 PDF 변환
    print("1. HWP → PDF 변환 (infilter 옵션 사용)...")
    pdf_cmd1 = [
        soffice_path,
        "--headless",
        '--infilter=Hwp2002_File',
        "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", output_dir,
        hwp_file
    ]
    
    try:
        result = subprocess.run(pdf_cmd1, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[SUCCESS] PDF 변환 성공! (infilter)")
            if result.stdout:
                print(f"출력: {result.stdout}")
        else:
            print("[FAIL] PDF 변환 실패 (infilter)")
            if result.stderr:
                print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] PDF 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] PDF 변환 오류: {e}")
    
    time.sleep(2)
    
    # 2. 일반 PDF 변환 (H2Orestart가 자동 인식)
    print("\n2. HWP → PDF 변환 (자동 인식)...")
    pdf_cmd2 = [
        soffice_path,
        "--headless",
        "--convert-to", "pdf:writer_pdf_Export",
        "--outdir", output_dir,
        hwp_file
    ]
    
    try:
        result = subprocess.run(pdf_cmd2, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[SUCCESS] PDF 변환 성공! (자동)")
            if result.stdout:
                print(f"출력: {result.stdout}")
        else:
            print("[FAIL] PDF 변환 실패 (자동)")
            if result.stderr:
                print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] PDF 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] PDF 변환 오류: {e}")
    
    time.sleep(2)
    
    # 3. ODT 변환
    print("\n3. HWP → ODT 변환...")
    odt_cmd = [
        soffice_path,
        "--headless",
        "--convert-to", "odt",
        "--outdir", output_dir,
        hwp_file
    ]
    
    try:
        result = subprocess.run(odt_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[SUCCESS] ODT 변환 성공!")
            if result.stdout:
                print(f"출력: {result.stdout}")
        else:
            print("[FAIL] ODT 변환 실패")
            if result.stderr:
                print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] ODT 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] ODT 변환 오류: {e}")
    
    time.sleep(2)
    
    # 4. TXT 변환
    print("\n4. HWP → TXT 변환...")
    txt_cmd = [
        soffice_path,
        "--headless",
        "--convert-to", "txt:Text",
        "--outdir", output_dir,
        hwp_file
    ]
    
    try:
        result = subprocess.run(txt_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[SUCCESS] TXT 변환 성공!")
            if result.stdout:
                print(f"출력: {result.stdout}")
        else:
            print("[FAIL] TXT 변환 실패")
            if result.stderr:
                print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] TXT 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] TXT 변환 오류: {e}")
    
    # 결과 확인
    print("\n" + "=" * 60)
    print("변환 결과 확인")
    print("=" * 60)
    
    output_path = Path(output_dir)
    files = list(output_path.glob("*"))
    
    if files:
        print(f"\n[SUCCESS] 생성된 파일들:")
        for file in files:
            size = file.stat().st_size
            print(f"  - {file.name} ({size:,} bytes)")
            
            # TXT 파일이면 내용 일부 출력
            if file.suffix.lower() == '.txt':
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read(500)
                        print(f"\n  [TXT 내용 미리보기]")
                        print(f"  {content[:300]}...")
                except:
                    try:
                        with open(file, 'r', encoding='cp949') as f:
                            content = f.read(500)
                            print(f"\n  [TXT 내용 미리보기 - CP949]")
                            print(f"  {content[:300]}...")
                    except:
                        print("  (텍스트 읽기 실패)")
            
            # PDF 파일이면 크기 확인
            elif file.suffix.lower() == '.pdf':
                print(f"  [PDF] 파일 크기: {size:,} bytes")
                if size > 1000:
                    print("  [PDF] 변환 성공으로 보임!")
    else:
        print("[FAIL] 변환된 파일이 없습니다.")
        print("\n[HINT] H2Orestart 확장 프로그램이 설치되었는지 확인하세요:")
        print("1. LibreOffice 실행")
        print("2. 도구 > 확장 관리자")
        print("3. H2Orestart가 목록에 있는지 확인")
        print("4. 없다면 '추가' 버튼으로 .oxt 파일 설치")
        print("5. LibreOffice 재시작 필요")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_h2orestart_conversion()
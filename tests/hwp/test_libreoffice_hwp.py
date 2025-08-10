"""
LibreOffice를 사용한 HWP 파일 변환 테스트
YouTube 노하우를 기반으로 구현
"""

import subprocess
from pathlib import Path
import sys

def test_libreoffice_conversion():
    """LibreOffice를 이용한 HWP 변환 테스트"""
    
    # LibreOffice 경로
    soffice_path = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    
    # 테스트할 HWP 파일
    hwp_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    # 출력 디렉토리
    output_dir = r"C:\projects\autoinput\data\libreoffice_converted"
    
    # 디렉토리 생성
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("LibreOffice HWP 변환 테스트")
    print("=" * 60)
    
    # 1. PDF 변환 테스트
    print("\n1. HWP → PDF 변환 시도...")
    pdf_cmd = [
        soffice_path,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        hwp_file
    ]
    
    try:
        result = subprocess.run(pdf_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[SUCCESS] PDF 변환 성공!")
            print(f"출력: {result.stdout}")
        else:
            print("[FAIL] PDF 변환 실패")
            print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] PDF 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] PDF 변환 오류: {e}")
    
    # 2. TXT 변환 테스트
    print("\n2. HWP → TXT 변환 시도...")
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
            print(f"출력: {result.stdout}")
        else:
            print("[FAIL] TXT 변환 실패")
            print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] TXT 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] TXT 변환 오류: {e}")
    
    # 3. ODT 변환 테스트 (OpenDocument Text)
    print("\n3. HWP → ODT 변환 시도...")
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
            print(f"출력: {result.stdout}")
        else:
            print("[FAIL] ODT 변환 실패")
            print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] ODT 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] ODT 변환 오류: {e}")
    
    # 4. HTML 변환 테스트
    print("\n4. HWP → HTML 변환 시도...")
    html_cmd = [
        soffice_path,
        "--headless",
        "--convert-to", "html:HTML",
        "--outdir", output_dir,
        hwp_file
    ]
    
    try:
        result = subprocess.run(html_cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[SUCCESS] HTML 변환 성공!")
            print(f"출력: {result.stdout}")
        else:
            print("[FAIL] HTML 변환 실패")
            print(f"에러: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] HTML 변환 시간 초과")
    except Exception as e:
        print(f"[ERROR] HTML 변환 오류: {e}")
    
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
                        print(f"  {content[:200]}...")
                except:
                    try:
                        with open(file, 'r', encoding='cp949') as f:
                            content = f.read(500)
                            print(f"\n  [TXT 내용 미리보기 - CP949]")
                            print(f"  {content[:200]}...")
                    except:
                        print("  (텍스트 읽기 실패)")
    else:
        print("[FAIL] 변환된 파일이 없습니다.")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n[INFO] YouTube 노하우:")
    print("- LibreOffice는 HWP를 부분적으로만 지원")
    print("- 완벽한 변환은 한컴 오피스 사용 권장")
    print("- PDF 변환 후 텍스트 추출이 가장 효과적")

if __name__ == "__main__":
    test_libreoffice_conversion()
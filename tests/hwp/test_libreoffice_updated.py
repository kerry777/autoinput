"""
LibreOffice 최신 버전 HWP 변환 테스트
업데이트 후 HWP 파일 지원 개선 여부 확인
"""

import subprocess
from pathlib import Path
import sys
import time

def check_libreoffice_version():
    """LibreOffice 버전 확인"""
    soffice_path = r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    
    # 64비트 경로도 확인
    if not Path(soffice_path).exists():
        soffice_path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    
    print("[INFO] LibreOffice 버전 확인 중...")
    try:
        # --version 대신 --help 사용 (GUI 열리지 않음)
        result = subprocess.run([soffice_path, "--help"], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines[:5]:  # 처음 몇 줄만 출력
                if line.strip():
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"[WARNING] 버전 확인 실패: {e}")
    
    return soffice_path

def test_hwp_conversion(soffice_path):
    """HWP 변환 테스트"""
    
    # 테스트할 HWP 파일
    hwp_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    # 출력 디렉토리
    output_dir = r"C:\projects\autoinput\data\libreoffice_updated"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "=" * 60)
    print("LibreOffice 최신 버전 HWP 변환 테스트")
    print("=" * 60)
    
    tests = [
        ("PDF", "pdf", "pdf:writer_pdf_Export"),
        ("PDF (필터 지정)", "pdf", "pdf:writer_pdf_Export"),
        ("ODT", "odt", "odt"),
        ("TXT", "txt", "txt:Text"),
        ("HTML", "html", "html:HTML"),
        ("DOCX", "docx", "docx")
    ]
    
    results = []
    
    for test_name, ext, convert_format in tests:
        print(f"\n[TEST] {test_name} 변환 시도...")
        
        cmd = [
            soffice_path,
            "--headless",
            "--convert-to", convert_format,
            "--outdir", output_dir,
            hwp_file
        ]
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                # 파일 생성 확인
                expected_file = Path(output_dir) / f"[별지_제45호_서식]_수령증.{ext}"
                if expected_file.exists():
                    size = expected_file.stat().st_size
                    print(f"  [SUCCESS] {test_name} 변환 성공! ({size:,} bytes, {elapsed:.1f}초)")
                    results.append((test_name, "SUCCESS", size))
                    
                    # TXT 파일이면 내용 확인
                    if ext == "txt" and size > 0:
                        try:
                            with open(expected_file, 'r', encoding='utf-8') as f:
                                content = f.read(200)
                                print(f"  [내용 미리보기]: {content[:100]}...")
                        except:
                            try:
                                with open(expected_file, 'r', encoding='cp949') as f:
                                    content = f.read(200)
                                    print(f"  [내용 미리보기 CP949]: {content[:100]}...")
                            except:
                                pass
                else:
                    print(f"  [FAIL] {test_name} 변환 실패 - 파일 생성 안됨")
                    results.append((test_name, "FAIL", 0))
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                print(f"  [FAIL] {test_name} 변환 실패: {error_msg[:100]}")
                results.append((test_name, "FAIL", 0))
                
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] {test_name} 변환 시간 초과")
            results.append((test_name, "TIMEOUT", 0))
        except Exception as e:
            print(f"  [ERROR] {test_name} 변환 오류: {e}")
            results.append((test_name, "ERROR", 0))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
    total_count = len(results)
    
    print(f"\n성공: {success_count}/{total_count}")
    print("\n상세 결과:")
    for name, status, size in results:
        if status == "SUCCESS":
            print(f"  ✓ {name}: {size:,} bytes")
        else:
            print(f"  ✗ {name}: {status}")
    
    # 변환된 파일 목록
    print("\n변환된 파일 확인:")
    output_path = Path(output_dir)
    files = list(output_path.glob("*"))
    if files:
        for file in files:
            print(f"  - {file.name} ({file.stat().st_size:,} bytes)")
    else:
        print("  변환된 파일 없음")
    
    # 결론
    print("\n" + "=" * 60)
    if success_count > 0:
        print("[GOOD NEWS] LibreOffice 최신 버전에서 일부 변환 성공!")
        print("특히 PDF나 ODT 변환이 성공했다면 HWP 지원이 개선된 것입니다.")
    else:
        print("[INFO] LibreOffice 최신 버전에서도 HWP 직접 변환 실패")
        print("한컴 오피스나 다른 방법을 사용해야 합니다.")
    print("=" * 60)

def main():
    print("LibreOffice 업데이트 후 HWP 변환 테스트")
    print("=" * 60)
    
    # LibreOffice 경로 확인 및 버전 체크
    soffice_path = check_libreoffice_version()
    
    if not Path(soffice_path).exists():
        print("\n[ERROR] LibreOffice를 찾을 수 없습니다.")
        print("설치 경로를 확인하세요.")
        return
    
    # 변환 테스트 실행
    test_hwp_conversion(soffice_path)
    
    print("\n[TIP] 만약 여전히 실패한다면:")
    print("1. LibreOffice가 최신 버전(7.6 이상)인지 확인")
    print("2. 한글 필터 지원 여부 확인 (도구 > 옵션 > 로드/저장)")
    print("3. 한컴 오피스 사용을 권장합니다.")

if __name__ == "__main__":
    main()
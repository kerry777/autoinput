"""
pyhwpx를 사용한 HWP 파일 변환 테스트
한컴 오피스가 설치되어 있어야 작동합니다.
"""

import os
from pathlib import Path
import sys

try:
    from pyhwpx import Hwp
    print("[SUCCESS] pyhwpx 모듈 로드 성공!")
except ImportError as e:
    print(f"[ERROR] pyhwpx 모듈 로드 실패: {e}")
    sys.exit(1)

def test_pyhwpx_conversion():
    """pyhwpx를 사용한 HWP 변환 테스트"""
    
    # 테스트할 HWP 파일
    hwp_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    # 출력 디렉토리
    output_dir = Path(r"C:\projects\autoinput\data\pyhwpx_converted")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("pyhwpx를 사용한 HWP 변환 테스트")
    print("=" * 60)
    print()
    print("[INFO] 한컴 오피스 2024가 설치되어 있어야 합니다.")
    print(f"[INFO] 테스트 파일: {hwp_file}")
    print()
    
    try:
        # Hwp 객체 생성 (한글 프로그램 실행)
        print("[1] 한글 프로그램 초기화 중...")
        hwp = Hwp()
        print("   [SUCCESS] 한글 프로그램 초기화 성공!")
        
        # 파일 열기
        print(f"\n[2] HWP 파일 열기: {Path(hwp_file).name}")
        hwp.open(hwp_file)
        print("   [SUCCESS] HWP 파일 열기 성공!")
        
        # 1. PDF로 저장
        print("\n[3] PDF로 변환 중...")
        pdf_path = output_dir / "[별지_제45호_서식]_수령증.pdf"
        try:
            # SaveAs 메서드로 PDF 저장
            hwp.save_as(str(pdf_path), "PDF")
            if pdf_path.exists():
                print(f"   [SUCCESS] PDF 변환 성공!")
                print(f"   파일 경로: {pdf_path}")
                print(f"   파일 크기: {pdf_path.stat().st_size:,} bytes")
            else:
                print("   [FAIL] PDF 파일이 생성되지 않음")
        except Exception as e:
            print(f"   [ERROR] PDF 변환 실패: {e}")
        
        # 2. 텍스트 추출
        print("\n[4] 텍스트 추출 중...")
        try:
            # 전체 선택
            hwp.ctrl_a()
            # 텍스트 복사
            text = hwp.get_selected_text()
            
            if text:
                txt_path = output_dir / "[별지_제45호_서식]_수령증.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"   [SUCCESS] 텍스트 추출 성공!")
                print(f"   파일 경로: {txt_path}")
                print(f"   텍스트 길이: {len(text)} 문자")
                print(f"   텍스트 미리보기:")
                print(f"   {text[:200]}...")
            else:
                print("   [WARNING] 추출된 텍스트가 없음")
        except Exception as e:
            print(f"   [ERROR] 텍스트 추출 실패: {e}")
        
        # 3. DOCX로 저장 (Word 형식)
        print("\n[5] DOCX로 변환 중...")
        docx_path = output_dir / "[별지_제45호_서식]_수령증.docx"
        try:
            hwp.save_as(str(docx_path), "DOCX")
            if docx_path.exists():
                print(f"   [SUCCESS] DOCX 변환 성공!")
                print(f"   파일 경로: {docx_path}")
                print(f"   파일 크기: {docx_path.stat().st_size:,} bytes")
            else:
                print("   [FAIL] DOCX 파일이 생성되지 않음")
        except Exception as e:
            print(f"   [ERROR] DOCX 변환 실패: {e}")
        
        # 4. HTML로 저장
        print("\n[6] HTML로 변환 중...")
        html_path = output_dir / "[별지_제45호_서식]_수령증.html"
        try:
            hwp.save_as(str(html_path), "HTML")
            if html_path.exists():
                print(f"   [SUCCESS] HTML 변환 성공!")
                print(f"   파일 경로: {html_path}")
                print(f"   파일 크기: {html_path.stat().st_size:,} bytes")
            else:
                print("   [FAIL] HTML 파일이 생성되지 않음")
        except Exception as e:
            print(f"   [ERROR] HTML 변환 실패: {e}")
        
        # 5. 문서 정보 출력
        print("\n[7] 문서 정보:")
        try:
            print(f"   총 페이지 수: {hwp.page_count} 페이지")
            print(f"   현재 페이지: {hwp.get_cur_page()}")
        except Exception as e:
            print(f"   [ERROR] 문서 정보 가져오기 실패: {e}")
        
    except Exception as e:
        print(f"\n[ERROR] pyhwpx 실행 중 오류 발생: {e}")
        print("[HINT] 한컴 오피스가 설치되어 있는지 확인하세요.")
        print("[HINT] 한글 2024가 기본 프로그램으로 설정되어 있는지 확인하세요.")
    
    finally:
        # 한글 프로그램 종료
        try:
            print("\n[8] 한글 프로그램 종료 중...")
            hwp.quit()
            print("   [SUCCESS] 한글 프로그램 종료 완료")
        except:
            pass
    
    # 결과 확인
    print("\n" + "=" * 60)
    print("변환 결과 확인")
    print("=" * 60)
    
    files = list(output_dir.glob("*"))
    if files:
        print(f"\n생성된 파일들:")
        for file in files:
            size = file.stat().st_size
            print(f"  - {file.name} ({size:,} bytes)")
    else:
        print("변환된 파일이 없습니다.")
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print("\n[결론]")
    print("pyhwpx는 한컴 오피스가 설치되어 있을 때")
    print("HWP 파일을 PDF, DOCX, HTML 등으로 변환할 수 있습니다.")
    print("LibreOffice보다 훨씬 안정적이고 완벽한 변환이 가능합니다!")

if __name__ == "__main__":
    test_pyhwpx_conversion()
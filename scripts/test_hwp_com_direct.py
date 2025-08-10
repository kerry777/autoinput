"""
win32com을 직접 사용한 HWP 변환 테스트
pyhwpx 없이 직접 COM 객체 접근
"""

import win32com.client as win32
from pathlib import Path
import sys

def test_hwp_com_direct():
    """win32com을 직접 사용한 HWP 변환"""
    
    print("=" * 60)
    print("win32com 직접 사용 HWP 변환 테스트")
    print("=" * 60)
    print()
    
    # 테스트할 HWP 파일
    hwp_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    # 출력 디렉토리
    output_dir = Path(r"C:\projects\autoinput\data\hwp_com_converted")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 가능한 ProgID 목록
    prog_ids = [
        "HWPFrame.HwpObject",        # 한글 2024
        "Hwp.Application",            # 다른 버전
        "HwpAutomation.HwpObject",    # 자동화 객체
        "HWP.Document",               # 문서 객체
    ]
    
    hwp = None
    success_prog_id = None
    
    # 각 ProgID 시도
    for prog_id in prog_ids:
        print(f"[시도] ProgID: {prog_id}")
        try:
            hwp = win32.Dispatch(prog_id)
            success_prog_id = prog_id
            print(f"   [SUCCESS] {prog_id} 연결 성공!")
            break
        except Exception as e:
            print(f"   [FAIL] {prog_id} 연결 실패: {str(e)[:50]}")
    
    if not hwp:
        print("\n[ERROR] 한컴 오피스 COM 객체를 찾을 수 없습니다.")
        print("\n가능한 원인:")
        print("1. 한컴 오피스가 설치되지 않음")
        print("2. COM 객체가 등록되지 않음")
        print("3. 32비트/64비트 불일치")
        
        print("\n해결 방법:")
        print("1. 한컴 오피스 2024 재설치")
        print("2. 관리자 권한으로 다음 명령 실행:")
        print('   regsvr32 "C:\\Program Files (x86)\\Hnc\\Office 2024\\HOffice130\\Bin\\Hwp.exe"')
        return
    
    try:
        # RegisterModule 시도
        try:
            hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
            print("[INFO] FilePathCheckDLL 등록 성공")
        except:
            print("[WARNING] FilePathCheckDLL 등록 실패 (계속 진행)")
        
        # 파일 열기
        print(f"\n[파일 열기] {Path(hwp_file).name}")
        result = hwp.Open(hwp_file)
        if result:
            print("   [SUCCESS] 파일 열기 성공!")
        else:
            print("   [FAIL] 파일 열기 실패")
            return
        
        # PDF로 저장
        pdf_path = str(output_dir / "[별지_제45호_서식]_수령증.pdf")
        print(f"\n[PDF 변환] {Path(pdf_path).name}")
        
        try:
            # SaveAs 메서드 시도
            hwp.SaveAs(pdf_path, "PDF")
            print("   [SUCCESS] PDF 변환 성공!")
        except:
            try:
                # HAction 방식 시도
                hwp.HAction.GetDefault("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
                hwp.HParameterSet.HFileOpenSave.filename = pdf_path
                hwp.HParameterSet.HFileOpenSave.Format = "PDF"
                hwp.HAction.Execute("FileSaveAs_S", hwp.HParameterSet.HFileOpenSave.HSet)
                print("   [SUCCESS] PDF 변환 성공! (HAction)")
            except Exception as e:
                print(f"   [FAIL] PDF 변환 실패: {e}")
        
        # 텍스트 추출
        print("\n[텍스트 추출]")
        try:
            # 전체 선택
            hwp.HAction.Run("SelectAll")
            # 텍스트 가져오기
            text = hwp.GetTextFile("UNICODE", "")
            
            if text:
                txt_path = output_dir / "[별지_제45호_서식]_수령증.txt"
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"   [SUCCESS] 텍스트 추출 성공! ({len(text)} 문자)")
                print(f"   미리보기: {text[:100]}...")
            else:
                print("   [WARNING] 추출된 텍스트 없음")
        except Exception as e:
            print(f"   [ERROR] 텍스트 추출 실패: {e}")
        
    except Exception as e:
        print(f"\n[ERROR] 실행 중 오류: {e}")
    
    finally:
        # 한글 프로그램 종료
        if hwp:
            try:
                hwp.Quit()
                print("\n[INFO] 한글 프로그램 종료")
            except:
                pass
    
    # 결과 확인
    print("\n" + "=" * 60)
    print("변환 결과")
    print("=" * 60)
    
    files = list(output_dir.glob("*"))
    if files:
        print("\n생성된 파일:")
        for file in files:
            print(f"  - {file.name} ({file.stat().st_size:,} bytes)")
    else:
        print("변환된 파일이 없습니다.")

if __name__ == "__main__":
    test_hwp_com_direct()
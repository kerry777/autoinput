"""
hwpapi 패키지 테스트
PyCon KR 2023에서 발표된 전다민님의 hwpapi 패키지 활용
"""

from hwpapi import Hwp
import os
from pathlib import Path

def test_hwpapi():
    """hwpapi 기본 기능 테스트"""
    
    print("=" * 60)
    print("hwpapi 패키지 테스트")
    print("PyCon KR 2023 - 전다민님 발표")
    print("=" * 60)
    print()
    
    # 테스트 디렉토리
    test_dir = Path(r"C:\projects\autoinput\data\hwpapi_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Hwp 객체 생성
        print("[1] 한글 프로그램 시작...")
        hwp = Hwp()
        print("   [SUCCESS] 한글 프로그램 시작 성공!")
        
        # 2. 텍스트 입력
        print("\n[2] 텍스트 입력 테스트...")
        hwp.insert_text("hwpapi 패키지 테스트\n\n")
        hwp.insert_text("이것은 PyCon KR 2023에서 발표된 hwpapi를 사용한 예제입니다.\n")
        hwp.insert_text("개발자: 전다민 (KOICA)\n\n")
        print("   [SUCCESS] 텍스트 입력 성공!")
        
        # 3. 표 생성
        print("\n[3] 표 생성 테스트...")
        hwp.create_table(3, 4)  # 3행 4열 표 생성
        
        # 표에 데이터 입력
        table_data = [
            ["번호", "이름", "부서", "직급"],
            ["1", "김철수", "개발팀", "과장"],
            ["2", "이영희", "인사팀", "대리"]
        ]
        
        for row_data in table_data:
            for cell_data in row_data:
                hwp.insert_text(cell_data)
                hwp.TableRightCell()  # 오른쪽 셀로 이동
        
        print("   [SUCCESS] 표 생성 및 데이터 입력 성공!")
        
        # 4. 문서 저장
        print("\n[4] 문서 저장...")
        save_path = str(test_dir / "hwpapi_test.hwp")
        hwp.save_as(save_path)
        print(f"   [SUCCESS] HWP 파일 저장: {save_path}")
        
        # 5. PDF로 저장
        print("\n[5] PDF 변환...")
        pdf_path = str(test_dir / "hwpapi_test.pdf")
        hwp.save_as(pdf_path, "PDF")
        print(f"   [SUCCESS] PDF 파일 저장: {pdf_path}")
        
        # 6. 추가 기능 테스트
        print("\n[6] 추가 기능 테스트...")
        
        # 새 페이지 추가
        hwp.insert_page_break()
        hwp.insert_text("두 번째 페이지입니다.\n\n")
        
        # 글자 서식 변경
        hwp.set_font("맑은 고딕", 14)
        hwp.insert_text("글꼴과 크기가 변경된 텍스트입니다.\n")
        
        print("   [SUCCESS] 추가 기능 테스트 완료!")
        
        # 7. 최종 저장
        hwp.save()
        print("\n[7] 최종 저장 완료!")
        
        # 8. 종료
        hwp.quit()
        print("\n[8] 한글 프로그램 종료")
        
    except Exception as e:
        print(f"\n[ERROR] 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("hwpapi 테스트 완료!")
    print("=" * 60)


def test_hwpapi_advanced():
    """hwpapi 고급 기능 테스트"""
    
    print("\n" + "=" * 60)
    print("hwpapi 고급 기능 테스트")
    print("=" * 60)
    print()
    
    test_dir = Path(r"C:\projects\autoinput\data\hwpapi_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        hwp = Hwp()
        
        # 1. 스타일 적용
        print("[1] 스타일 적용...")
        hwp.set_font("나눔고딕", 16, bold=True)
        hwp.insert_text("제목 스타일\n\n")
        
        hwp.set_font("맑은 고딕", 11, bold=False)
        hwp.insert_text("본문 스타일\n\n")
        
        # 2. 이미지 삽입 (경로가 있다면)
        # hwp.insert_picture("image.jpg")
        
        # 3. 머리말/꼬리말
        hwp.put_field_text("머리말", "hwpapi 테스트 문서")
        hwp.put_field_text("쪽번호", "1")
        
        # 4. 찾기 및 바꾸기
        hwp.find_replace("테스트", "TEST")
        
        print("   [SUCCESS] 고급 기능 적용 완료!")
        
        # 저장
        advanced_path = str(test_dir / "hwpapi_advanced.hwp")
        hwp.save_as(advanced_path)
        print(f"   [SUCCESS] 저장: {advanced_path}")
        
        hwp.quit()
        
    except Exception as e:
        print(f"[ERROR] 고급 기능 테스트 오류: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("hwpapi 패키지 테스트 시작")
    print("GitHub: https://github.com/JunDamin/hwpapi")
    print("문서: https://jundamin.github.io/hwpapi")
    print()
    
    # 기본 테스트
    test_hwpapi()
    
    # 고급 테스트
    # test_hwpapi_advanced()
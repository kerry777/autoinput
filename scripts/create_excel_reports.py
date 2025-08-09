"""
Excel 보고서 생성 스크립트
MD 문서의 주요 내용을 엑셀로 변환
"""

import pandas as pd
from datetime import datetime
import os

def create_excel_reports():
    """주요 문서를 엑셀로 변환"""
    
    # 출력 디렉토리 생성
    output_dir = "excel_reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Excel Writer 생성
    excel_file = os.path.join(output_dir, f"장기요양보험_청구자동화_분석_{datetime.now().strftime('%Y%m%d')}.xlsx")
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        
        # 1. 업무 프로세스 확인 체크리스트
        process_checklist = pd.DataFrame({
            '구분': ['일일업무', '일일업무', '월말업무', '월초청구', '월초청구', '월중업무'],
            '업무명': ['로그인', '급여제공기록 입력', '청구서 생성 준비', '청구서 작성', '전자청구 전송', '심사결과 확인'],
            '현재 소요시간': ['5분', '1-2시간', '4시간', '2-3일', '30분', '2시간'],
            '자동화 후 예상시간': ['10초', '10분', '30분', '1시간', '5분', '10분'],
            '절감율': ['97%', '92%', '88%', '95%', '83%', '92%'],
            '우선순위': ['중', '높음', '높음', '높음', '중', '중']
        })
        process_checklist.to_excel(writer, sheet_name='업무프로세스', index=False)
        
        # 2. 기술 요구사항 및 난이도
        tech_requirements = pd.DataFrame({
            '기술요소': [
                '공동인증서 로그인',
                '복잡한 폼 입력',
                '테이블 데이터 입력',
                '팝업/모달 처리',
                '파일 업로드/다운로드',
                '세션 유지 (30분)',
                'AJAX 동적 콘텐츠',
                '페이지네이션',
                '오류 검증 로직',
                '엑셀 처리'
            ],
            '난이도': ['★★★★★', '★★★★', '★★★★', '★★★', '★★', '★★★', '★★★', '★★', '★★★★', '★★'],
            '구현순서': [1, 2, 3, 4, 8, 5, 6, 9, 7, 10],
            '예상소요일': [5, 3, 3, 2, 1, 2, 2, 1, 3, 1],
            '필수여부': ['필수', '필수', '필수', '필수', '선택', '필수', '선택', '선택', '필수', '선택'],
            '비고': [
                '최우선 해결 과제',
                '수급자별 급여제공기록',
                '일별 서비스 내역',
                '상세내역 조회 등',
                '증빙서류 첨부',
                '자동 연장 필요',
                '실시간 데이터 로딩',
                '조회 결과 페이징',
                '청구 전 검증',
                '대량 데이터 처리'
            ]
        })
        tech_requirements.to_excel(writer, sheet_name='기술요구사항', index=False)
        
        # 3. 학습 로드맵
        learning_roadmap = pd.DataFrame({
            '주차': ['Week 1-2', 'Week 1-2', 'Week 1-2', 'Week 3-4', 'Week 3-4', 'Week 5', 'Week 5', 'Week 6', 'Week 7-8'],
            '학습영역': ['기초', '기초', '기초', '동적콘텐츠', '동적콘텐츠', '인증', '인증', '안티봇', '고급'],
            '핵심기술': [
                'CSS/XPath 선택자',
                '기본 네비게이션',
                '에러 처리',
                'AJAX 처리',
                '무한 스크롤',
                '폼 로그인',
                '세션 관리',
                'User-Agent 로테이션',
                '성능 최적화'
            ],
            '실습사이트': [
                'web-scraping.dev/products',
                'web-scraping.dev/navigation',
                'web-scraping.dev/errors',
                'web-scraping.dev/ajax',
                'web-scraping.dev/infinite-scroll',
                'web-scraping.dev/login',
                'web-scraping.dev/cookie-auth',
                'web-scraping.dev/user-agent',
                'web-scraping.dev/performance'
            ],
            '목표': [
                '정적 HTML 파싱',
                '페이지 이동',
                '예외 처리',
                '동적 로딩 대기',
                '스크롤 자동화',
                '인증 자동화',
                '세션 유지',
                '봇 감지 우회',
                '대량 처리'
            ],
            '완료': ['', '', '', '', '', '', '', '', '']
        })
        learning_roadmap.to_excel(writer, sheet_name='학습로드맵', index=False)
        
        # 4. 서비스별 청구 정보
        service_types = pd.DataFrame({
            '서비스유형': [
                '방문요양',
                '방문목욕',
                '방문간호',
                '주야간보호',
                '단기보호',
                '노인요양시설',
                '공동생활가정'
            ],
            '구분': ['재가', '재가', '재가', '재가', '재가', '시설', '시설'],
            '청구단위': ['시간당', '회당', '시간당', '일당', '일당', '일당', '일당'],
            '청구주기': ['월1회', '월1회', '월1회', '월1회', '월1회', '월1회', '월1회'],
            '주요입력항목': [
                '방문일시, 서비스내용',
                '방문일시, 차량여부',
                '방문일시, 간호행위',
                '이용일자, 송영여부',
                '입소일자, 이용일수',
                '재원일수, 외박일수',
                '재원일수, 외박일수'
            ],
            '본인부담률': ['15%', '15%', '15%', '15%', '15%', '20%', '20%']
        })
        service_types.to_excel(writer, sheet_name='서비스유형', index=False)
        
        # 5. 청구 오류 코드
        error_codes = pd.DataFrame({
            '오류코드': ['E001', 'E101', 'E201', 'E301', 'E401', 'E501'],
            '오류명': ['자격오류', '한도초과', '중복청구', '인력기준', '계약오류', '시스템오류'],
            '발생원인': [
                '수급자 자격 없음/만료',
                '월 한도액 초과',
                '동일시간 중복 서비스',
                '요양보호사 자격 미달',
                '계약서 미등록/만료',
                '시스템 오류'
            ],
            '해결방법': [
                '자격 확인 후 재청구',
                '한도 내 조정 청구',
                '시간 조정 후 재청구',
                '인력 정보 업데이트',
                '계약서 등록/갱신',
                '시스템 관리자 문의'
            ],
            '예방방법': [
                '청구 전 자격 확인',
                '한도 잔액 사전 체크',
                '중복 서비스 검증',
                '인력 자격 관리',
                '계약서 만료일 관리',
                '정기 시스템 점검'
            ]
        })
        error_codes.to_excel(writer, sheet_name='오류코드', index=False)
        
        # 6. 자동화 우선순위 매트릭스
        priority_matrix = pd.DataFrame({
            '작업': [
                '공동인증서 로그인',
                '급여제공기록 입력',
                '청구서 작성',
                '오류 검증',
                '심사결과 조회',
                '보고서 생성',
                '파일 다운로드',
                '이의신청',
                '통계 분석'
            ],
            '현재시간(월)': [2, 30, 24, 8, 4, 6, 2, 3, 4],
            '자동화후(월)': [0.1, 3, 2, 0.5, 0.5, 0.5, 0.2, 1, 0.5],
            '절감시간': [1.9, 27, 22, 7.5, 3.5, 5.5, 1.8, 2, 3.5],
            '난이도(1-5)': [5, 4, 4, 3, 2, 2, 1, 3, 2],
            '중요도(1-5)': [5, 5, 5, 4, 3, 3, 2, 3, 2],
            'ROI점수': [95, 135, 110, 60, 35, 33, 18, 20, 21],
            '구현순위': [2, 1, 3, 4, 6, 7, 9, 8, 5]
        })
        priority_matrix.to_excel(writer, sheet_name='우선순위', index=False)
        
        # 7. 확인 질문 체크리스트
        checklist = pd.DataFrame({
            '번호': range(1, 11),
            '질문': [
                '급여제공기록을 엑셀로 일괄 업로드 가능한가?',
                '일일 기록 입력에 걸리는 시간은?',
                '가장 시간이 많이 걸리는 작업은?',
                '청구서 작성 방식은?',
                '청구서 작성 시 가장 어려운 점은?',
                '엑셀 파일로 처리 가능한 업무는?',
                '엑셀 업로드 기능을 실제로 사용하는가?',
                '현재 가장 큰 업무 부담은?',
                '자동화되면 가장 도움이 될 업무는?',
                '현재 업무 시스템 만족도는?'
            ],
            '답변옵션': [
                '가능/불가능/일부가능',
                '30분미만/30분-1시간/1-2시간/2시간이상',
                '로그인/기록입력/청구서작성/오류수정/기타',
                '웹입력/엑셀업로드/프로그램/기타',
                '복잡한계산/반복입력/오류수정/시스템속도/기타',
                '기록업로드/청구서작성/결과다운로드/수급자등록/없음',
                '항상/가끔/사용안함/몰랐음',
                '반복입력/청구집중/오류재작업/정보관리/수가계산/기타',
                '자동로그인/일괄입력/자동생성/오류검증/보고서생성/기타',
                '매우만족/만족/보통/불만족/매우불만족'
            ],
            '답변': [''] * 10,
            '비고': [''] * 10
        })
        checklist.to_excel(writer, sheet_name='확인체크리스트', index=False)
        
        # 8. Web Scraping 챌린지 목록
        challenges = pd.DataFrame({
            '카테고리': [
                'Basic', 'Basic', 'Basic',
                'Dynamic', 'Dynamic', 'Dynamic',
                'Auth', 'Auth', 'Auth',
                'Anti-Bot', 'Anti-Bot',
                'Advanced', 'Advanced'
            ],
            '챌린지': [
                'CSS Selectors', 'XPath', 'Navigation',
                'AJAX Loading', 'Infinite Scroll', 'Lazy Loading',
                'Form Login', 'Cookie Auth', 'JWT Auth',
                'User-Agent', 'Rate Limiting',
                'iFrame', 'Shadow DOM'
            ],
            'URL': [
                '/products', '/complex-selectors', '/navigation',
                '/ajax', '/infinite-scroll', '/lazy-loading',
                '/login', '/cookie-auth', '/jwt-auth',
                '/user-agent', '/rate-limit',
                '/iframe', '/shadow-dom'
            ],
            '난이도': [1, 2, 1, 3, 2, 2, 2, 3, 4, 2, 3, 3, 4],
            '학습상태': [''] * 13,
            '메모': [''] * 13
        })
        challenges.to_excel(writer, sheet_name='웹스크래핑챌린지', index=False)
    
    print(f"Excel file created: {excel_file}")
    return excel_file

if __name__ == "__main__":
    file_path = create_excel_reports()
    print(f"\nFile location: {os.path.abspath(file_path)}")
    print("\nIncluded sheets:")
    print("1. Work Process - Current vs Automated comparison")
    print("2. Technical Requirements - Implementation skills and difficulty")
    print("3. Learning Roadmap - 8-week study plan")
    print("4. Service Types - Long-term care service information")
    print("5. Error Codes - Claim errors and solutions")
    print("6. Priority - Automation priority matrix")
    print("7. Checklist - For business user confirmation")
    print("8. Web Scraping Challenges - Learning task list")
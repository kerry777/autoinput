#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
온라인 HWP to PDF 변환 서비스 활용
여러 온라인 서비스를 통해 HWP를 PDF로 변환
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
import codecs
import json

# 출력 인코딩 설정
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)

class OnlineHWPConverter:
    """온라인 HWP 변환 서비스"""
    
    def __init__(self):
        self.services = {
            'cloudconvert': {
                'url': 'https://api.cloudconvert.com/v2',
                'api_key': None,  # API 키 필요
                'free_tier': True
            },
            'convertio': {
                'url': 'https://api.convertio.co/convert',
                'api_key': None,  # API 키 필요
                'free_tier': True
            },
            'zamzar': {
                'url': 'https://api.zamzar.com/v1',
                'api_key': None,  # API 키 필요
                'free_tier': True
            }
        }
    
    def convert_with_cloudconvert(self, hwp_path, pdf_path, api_key=None):
        """CloudConvert API를 사용한 변환"""
        if not api_key:
            print("CloudConvert API 키가 필요합니다.")
            print("https://cloudconvert.com/api/v2 에서 무료 API 키를 발급받을 수 있습니다.")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # 1. Job 생성
            job_data = {
                "tasks": {
                    "import-hwp": {
                        "operation": "import/upload"
                    },
                    "convert-to-pdf": {
                        "operation": "convert",
                        "input": "import-hwp",
                        "output_format": "pdf"
                    },
                    "export-pdf": {
                        "operation": "export/url",
                        "input": "convert-to-pdf"
                    }
                }
            }
            
            response = requests.post(
                f"{self.services['cloudconvert']['url']}/jobs",
                json=job_data,
                headers=headers
            )
            
            if response.status_code != 201:
                print(f"CloudConvert Job 생성 실패: {response.text}")
                return False
            
            job = response.json()
            job_id = job['data']['id']
            
            # 2. 파일 업로드
            upload_task = next(t for t in job['data']['tasks'] if t['operation'] == 'import/upload')
            upload_url = upload_task['result']['form']['url']
            
            with open(hwp_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(upload_url, files=files)
            
            if response.status_code != 200:
                print(f"파일 업로드 실패: {response.text}")
                return False
            
            # 3. 변환 대기
            max_wait = 60  # 최대 60초 대기
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                response = requests.get(
                    f"{self.services['cloudconvert']['url']}/jobs/{job_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    job_status = response.json()['data']['status']
                    
                    if job_status == 'finished':
                        # 4. PDF 다운로드
                        export_task = next(t for t in job_status['tasks'] 
                                         if t['operation'] == 'export/url')
                        download_url = export_task['result']['files'][0]['url']
                        
                        response = requests.get(download_url)
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        
                        print(f"CloudConvert 변환 성공: {pdf_path}")
                        return True
                    
                    elif job_status == 'error':
                        print("CloudConvert 변환 실패")
                        return False
                
                time.sleep(2)
            
            print("CloudConvert 변환 시간 초과")
            return False
            
        except Exception as e:
            print(f"CloudConvert 오류: {e}")
            return False
    
    def convert_with_local_tools(self, hwp_path, pdf_path):
        """로컬 도구를 사용한 변환 (대체 방법)"""
        
        # 1. hwp5txt로 텍스트 추출 후 PDF 생성
        try:
            import subprocess
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import simpleSplit
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 텍스트 추출
            text_file = Path(hwp_path).with_suffix('.txt')
            cmd = ['hwp5txt', str(hwp_path), '--output', str(text_file)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and text_file.exists():
                # 텍스트 읽기
                with open(text_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # PDF 생성
                c = canvas.Canvas(str(pdf_path), pagesize=A4)
                width, height = A4
                
                # 한글 폰트 설정 시도
                try:
                    # Windows 한글 폰트
                    font_paths = [
                        r"C:\Windows\Fonts\malgun.ttf",  # 맑은 고딕
                        r"C:\Windows\Fonts\gulim.ttc",   # 굴림
                        r"C:\Windows\Fonts\batang.ttc"   # 바탕
                    ]
                    
                    for font_path in font_paths:
                        if Path(font_path).exists():
                            pdfmetrics.registerFont(TTFont('Korean', font_path))
                            c.setFont('Korean', 12)
                            break
                except:
                    c.setFont('Helvetica', 12)
                
                # 텍스트를 페이지에 쓰기
                y = height - 50
                for line in text.split('\n'):
                    if y < 50:
                        c.showPage()
                        y = height - 50
                    
                    # 긴 줄은 자동 줄바꿈
                    if len(line) > 80:
                        lines = simpleSplit(line, 'Helvetica', 12, width - 100)
                        for l in lines:
                            c.drawString(50, y, l)
                            y -= 15
                    else:
                        c.drawString(50, y, line)
                        y -= 15
                
                c.save()
                
                if Path(pdf_path).exists():
                    print(f"로컬 도구 변환 성공: {pdf_path}")
                    return True
                    
        except ImportError:
            print("reportlab이 설치되어 있지 않습니다: pip install reportlab")
        except Exception as e:
            print(f"로컬 도구 변환 오류: {e}")
        
        return False
    
    def get_free_api_info(self):
        """무료 API 정보 제공"""
        info = """
        HWP to PDF 변환을 위한 무료 온라인 서비스:
        
        1. CloudConvert (https://cloudconvert.com)
           - 무료: 월 25분 변환 시간
           - API 키 발급: https://cloudconvert.com/api/v2
           - 고품질 변환 지원
        
        2. Convertio (https://convertio.co)
           - 무료: 일일 10개 파일 (최대 100MB)
           - API 키 발급: https://developers.convertio.co
        
        3. Zamzar (https://www.zamzar.com)
           - 무료: 일일 2개 파일 (최대 50MB)
           - API 키 발급: https://developers.zamzar.com
        
        4. 수동 변환 (브라우저 사용):
           - https://allinpdf.com/hwp-to-pdf
           - https://anyconv.com/hwp-to-pdf-converter/
           - https://hwpconverter.com/en/hwp-to-pdf
        """
        return info


def create_simple_converter_script():
    """간단한 변환 스크립트 생성"""
    
    script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HWP to PDF 변환 최종 솔루션
가장 실용적인 방법들을 통합
"""

import os
import sys
from pathlib import Path

def convert_hwp_to_pdf(hwp_path):
    """HWP를 PDF로 변환하는 최선의 방법"""
    
    hwp_path = Path(hwp_path)
    pdf_path = hwp_path.with_suffix('.pdf')
    
    # 1. 이미 PDF가 있는지 확인
    if pdf_path.exists():
        print(f"PDF가 이미 존재합니다: {pdf_path}")
        return str(pdf_path)
    
    # 2. 동일 디렉토리에서 비슷한 이름의 PDF 찾기
    similar_pdfs = list(hwp_path.parent.glob(f"*{hwp_path.stem}*.pdf"))
    if similar_pdfs:
        print(f"유사한 PDF 발견: {similar_pdfs[0]}")
        return str(similar_pdfs[0])
    
    # 3. 변환 방법 안내
    print(f"""
    HWP 파일: {hwp_path}
    
    자동 변환 방법이 없습니다. 다음 방법 중 하나를 사용하세요:
    
    방법 1: 온라인 변환 (권장)
    - https://allinpdf.com/hwp-to-pdf 접속
    - HWP 파일 업로드
    - PDF 다운로드
    
    방법 2: 한컴 오피스 사용
    - 한컴 오피스에서 HWP 파일 열기
    - 파일 > 다른 이름으로 저장 > PDF 선택
    
    방법 3: LibreOffice 설치 후 사용
    - LibreOffice 다운로드: https://www.libreoffice.org
    - 설치 후: soffice --convert-to pdf {hwp_path}
    """)
    
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        hwp_file = sys.argv[1]
        if Path(hwp_file).exists():
            result = convert_hwp_to_pdf(hwp_file)
            if result:
                print(f"변환 완료: {result}")
        else:
            print(f"파일이 존재하지 않습니다: {hwp_file}")
    else:
        print("사용법: python hwp_to_pdf.py [HWP파일경로]")
'''
    
    output_path = Path(r"C:\projects\autoinput\scripts\hwp_to_pdf_simple.py")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"간단한 변환 스크립트 생성: {output_path}")
    return output_path


if __name__ == "__main__":
    print("온라인 HWP to PDF 변환 서비스")
    print("="*60)
    
    converter = OnlineHWPConverter()
    
    # 무료 API 정보 출력
    print(converter.get_free_api_info())
    
    # 간단한 변환 스크립트 생성
    script_path = create_simple_converter_script()
    print(f"\n실용적인 변환 스크립트가 생성되었습니다: {script_path}")
    
    # 테스트 파일
    test_file = r"C:\projects\autoinput\data\downloads\boards_test\서식자료실\[별지_제45호_서식]_수령증.hwp"
    
    if Path(test_file).exists():
        print(f"\n테스트 파일: {test_file}")
        
        # 로컬 도구 시도
        output_dir = Path(r"C:\projects\autoinput\data\hwp_converted_local")
        output_dir.mkdir(exist_ok=True)
        
        pdf_path = output_dir / f"{Path(test_file).stem}_local.pdf"
        
        if converter.convert_with_local_tools(test_file, pdf_path):
            print("✅ 로컬 도구 변환 성공")
        else:
            print("❌ 로컬 도구 변환 실패")
            print("\n온라인 서비스를 사용하려면 API 키가 필요합니다.")
            print("위의 무료 서비스 중 하나를 선택하여 API 키를 발급받으세요.")
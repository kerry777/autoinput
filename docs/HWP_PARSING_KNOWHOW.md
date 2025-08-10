# HWP 파일 파싱 노하우 및 기술 가이드

## 개요
HWP(한글 워드 프로세서) 파일은 한국에서 널리 사용되는 문서 형식으로, 특히 공공기관과 기업에서 표준 문서 형식으로 활용됩니다. 이 문서는 HWP 파일을 파싱하고 변환하는 실전 노하우를 정리합니다.

## HWP 파일 구조

### 1. OLE 컴파운드 파일 구조
HWP 파일은 Microsoft OLE(Object Linking and Embedding) 컴파운드 파일 형식을 사용합니다.

```
HWP 파일 구조:
├── FileHeader (파일 헤더)
├── DocInfo (문서 정보)
├── BodyText/ (본문 텍스트)
│   ├── Section0
│   ├── Section1
│   └── ...
├── BinData/ (바이너리 데이터)
│   ├── BIN0001.jpg
│   └── ...
├── PrvText (미리보기 텍스트)
└── Scripts/ (스크립트)
```

### 2. 주요 스트림 설명

#### DocInfo 스트림
- 문서의 메타데이터 포함
- 작성자, 제목, 생성일자 등의 정보
- 압축된 형태로 저장

#### BodyText 스트림
- 실제 문서 내용이 저장되는 위치
- Section 단위로 구분
- 각 Section은 레코드 구조로 구성

#### PrvText 스트림
- 문서의 미리보기 텍스트
- UTF-16LE 인코딩으로 저장
- 빠른 내용 확인에 유용

## 파싱 구현 방법

### 1. 필요한 라이브러리

```python
# 기본 라이브러리
import olefile  # OLE 파일 구조 파싱
import struct   # 바이너리 데이터 언패킹
import re       # 텍스트 정리

# 설치 명령
pip install olefile
```

### 2. 기본 파싱 코드

```python
import olefile

def parse_hwp(file_path):
    with olefile.OleFileIO(file_path) as ole:
        # 스트림 목록 확인
        streams = ole.listdir()
        
        # 미리보기 텍스트 추출
        if ole.exists('PrvText'):
            prv_data = ole.openstream('PrvText').read()
            preview_text = prv_data.decode('utf-16le', errors='ignore')
        
        # 본문 섹션 추출
        section_num = 0
        while ole.exists(f'BodyText/Section{section_num}'):
            section_data = ole.openstream(f'BodyText/Section{section_num}').read()
            # 섹션 데이터 처리
            section_num += 1
```

### 3. HWP 레코드 구조 파싱

HWP 파일의 BodyText는 레코드 구조로 되어 있습니다:

```python
def parse_hwp_records(data):
    """HWP 레코드 구조 파싱"""
    texts = []
    pos = 0
    
    while pos < len(data) - 6:
        # 레코드 헤더 (6바이트)
        tag = struct.unpack('<H', data[pos:pos+2])[0]      # 태그 ID
        level = struct.unpack('<H', data[pos+2:pos+4])[0]  # 레벨
        size = struct.unpack('<H', data[pos+4:pos+6])[0]   # 크기
        
        # 확장 크기 처리 (크기가 0xFFFF인 경우)
        if size == 0xFFFF:
            size = struct.unpack('<I', data[pos+6:pos+10])[0]
            header_size = 10
        else:
            header_size = 6
        
        # 텍스트 레코드 (태그 0x0067) 처리
        if tag == 0x0067:
            text_data = data[pos+header_size:pos+header_size+size]
            text = text_data.decode('utf-16le', errors='ignore')
            texts.append(text)
        
        pos += header_size + size
    
    return texts
```

## 텍스트 추출 전략

### 1. 다중 방법 접근
HWP 파일의 복잡성 때문에 단일 방법으로는 모든 텍스트를 추출하기 어렵습니다.

```python
def extract_text_multiple_methods(data):
    """여러 방법으로 텍스트 추출"""
    texts = []
    
    # 방법 1: HWP 레코드 파싱
    hwp_texts = parse_hwp_records(data)
    texts.extend(hwp_texts)
    
    # 방법 2: UTF-16 직접 디코딩
    try:
        utf16_text = data.decode('utf-16le', errors='ignore')
        texts.append(clean_text(utf16_text))
    except:
        pass
    
    # 방법 3: 바이너리 패턴 매칭
    pattern = re.compile(b'(?:[\x20-\x7E][\x00]){5,}')
    matches = pattern.findall(data)
    for match in matches:
        text = match.decode('utf-16le', errors='ignore')
        texts.append(clean_text(text))
    
    return texts
```

### 2. 텍스트 정리

```python
def clean_text(text):
    """추출된 텍스트 정리"""
    # 제어 문자 제거
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', ' ', text)
    
    # Private Use Area 문자 제거
    text = re.sub(r'[\uE000-\uF8FF]', '', text)
    
    # 특수 문자 제거
    text = re.sub(r'[\uFFF0-\uFFFF]', '', text)
    
    # 연속 공백 정리
    text = ' '.join(text.split())
    
    return text
```

## 실전 노하우

### 1. 인코딩 처리
- HWP는 주로 UTF-16LE 인코딩 사용
- 한글 처리 시 cp949 인코딩 고려 필요
- 출력 시 UTF-8로 변환 권장

### 2. 에러 처리
```python
# 안전한 파싱 구조
try:
    with olefile.OleFileIO(file_path) as ole:
        # 파싱 로직
        pass
except olefile.OleFileError:
    # OLE 파일이 아닌 경우
    print("유효한 HWP 파일이 아닙니다")
except Exception as e:
    print(f"파싱 오류: {e}")
```

### 3. 성능 최적화
- 큰 파일의 경우 스트리밍 처리
- 필요한 스트림만 선택적 파싱
- 결과 캐싱 활용

### 4. 문서 유형별 처리
```python
def detect_document_type(ole):
    """문서 유형 감지"""
    if ole.exists('BodyText/Section0'):
        # 일반 HWP 문서
        return 'hwp'
    elif ole.exists('Contents/content.hpf'):
        # HWPX (새로운 형식)
        return 'hwpx'
    else:
        return 'unknown'
```

## 변환 출력 형식

### 1. JSON 변환
```python
result = {
    'file': file_path,
    'metadata': {
        'streams': stream_list,
        'file_size': file_size,
        'doc_info_size': doc_info_size
    },
    'content': {
        'sections': [
            {
                'section': 0,
                'size': section_size,
                'text': extracted_text
            }
        ],
        'all_text': combined_text
    },
    'timestamp': datetime.now().isoformat()
}
```

### 2. 텍스트 파일 변환
```python
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"HWP 파일: {file_name}\n")
    f.write(f"변환 시간: {datetime.now()}\n")
    f.write("="*60 + "\n\n")
    f.write(extracted_text)
```

## 문제 해결

### 1. 일반적인 문제

#### 문제: 깨진 문자 출력
**해결책:**
- UTF-16LE 디코딩 확인
- errors='ignore' 옵션 사용
- 출력 인코딩을 UTF-8로 설정

#### 문제: 텍스트 추출 실패
**해결책:**
- 여러 추출 방법 병행 사용
- PrvText 스트림 우선 확인
- 바이너리 패턴 매칭 활용

#### 문제: 메모리 부족
**해결책:**
- 스트리밍 방식으로 처리
- 섹션별 개별 처리
- 불필요한 데이터 즉시 해제

### 2. 디버깅 팁

```python
# 스트림 구조 확인
def debug_hwp_structure(file_path):
    with olefile.OleFileIO(file_path) as ole:
        print("스트림 목록:")
        for stream in ole.listdir():
            path = '/'.join(stream)
            size = ole.get_size(path)
            print(f"  {path}: {size:,} bytes")
```

## 실제 적용 사례

### 1. 공공기관 서식 파싱
- 장기요양보험 서식 문서
- 표준화된 구조 활용
- 메타데이터 추출 중요

### 2. 대량 파일 처리
```python
def batch_convert(hwp_files, output_dir):
    """여러 HWP 파일 일괄 변환"""
    results = []
    
    for hwp_file in hwp_files:
        converter = HWPConverter(hwp_file)
        if converter.parse_hwp():
            # JSON과 텍스트로 변환
            base_name = Path(hwp_file).stem
            
            json_output = output_dir / f"{base_name}.json"
            converter.convert_to_json(json_output)
            
            text_output = output_dir / f"{base_name}.txt"
            converter.convert_to_text(text_output)
            
            results.append({
                'file': hwp_file,
                'success': True,
                'outputs': [json_output, text_output]
            })
    
    return results
```

## 주의사항

1. **저작권**: HWP 파일 형식은 한글과컴퓨터의 지적 재산입니다
2. **호환성**: 버전별로 구조가 다를 수 있습니다
3. **보안**: 민감한 정보 처리 시 주의 필요
4. **성능**: 대용량 파일 처리 시 메모리 관리 중요

## 추가 리소스

- [olefile 공식 문서](https://olefile.readthedocs.io/)
- [HWP 파일 형식 분석 자료](https://github.com/mete0r/pyhwp)
- [한글과컴퓨터 개발자 센터](https://www.hancom.com/)
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 UTF-8 인코딩 및 이모지 설정 스크립트
한글과 이모지를 완벽하게 지원하도록 환경 설정
"""

import os
import sys
import locale
import io

def setup_utf8_environment():
    """UTF-8 환경 설정"""
    
    print("=" * 70)
    print("🔧 UTF-8 인코딩 환경 설정")
    print("=" * 70)
    
    # 1. 환경 변수 설정
    print("\n1️⃣ 환경 변수 설정")
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    print("   ✅ PYTHONIOENCODING = utf-8")
    print("   ✅ PYTHONUTF8 = 1")
    
    # 2. 시스템 인코딩 확인
    print("\n2️⃣ 현재 시스템 인코딩")
    print(f"   📌 sys.getdefaultencoding(): {sys.getdefaultencoding()}")
    print(f"   📌 sys.getfilesystemencoding(): {sys.getfilesystemencoding()}")
    print(f"   📌 locale.getpreferredencoding(): {locale.getpreferredencoding()}")
    
    # 3. stdout/stderr UTF-8 설정
    print("\n3️⃣ 표준 출력 UTF-8 설정")
    if sys.platform == 'win32':
        # Windows에서 UTF-8 출력 강제
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        print("   ✅ Windows UTF-8 출력 설정 완료")
    
    # 4. 이모지 테스트
    print("\n4️⃣ 이모지 출력 테스트")
    emojis = {
        "체크": "✅",
        "경고": "⚠️",
        "에러": "❌",
        "정보": "ℹ️",
        "로켓": "🚀",
        "파일": "📁",
        "문서": "📄",
        "차트": "📊",
        "트로피": "🏆",
        "별": "⭐",
        "하트": "❤️",
        "불": "🔥"
    }
    
    for name, emoji in emojis.items():
        print(f"   {emoji} {name}: 정상 출력")
    
    # 5. 한글 테스트
    print("\n5️⃣ 한글 출력 테스트")
    korean_tests = [
        "가나다라마바사",
        "안녕하세요",
        "한글 자동화 테스트",
        "엑셀-HWP 변환 성공!"
    ]
    
    for text in korean_tests:
        print(f"   ✅ {text}")
    
    print("\n" + "=" * 70)
    print("✨ UTF-8 설정 완료!")
    print("=" * 70)

def create_encoding_config():
    """영구적인 인코딩 설정 파일 생성"""
    
    # 1. sitecustomize.py 생성 (Python 시작 시 자동 실행)
    site_customize = '''# -*- coding: utf-8 -*-
"""
사이트 커스터마이즈 - UTF-8 기본 설정
"""
import sys
import io
import os

# UTF-8 환경 변수
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows에서 UTF-8 콘솔 출력
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass
'''
    
    # 2. .env 파일 생성
    env_content = '''# UTF-8 인코딩 설정
PYTHONIOENCODING=utf-8
PYTHONUTF8=1
LANG=ko_KR.UTF-8
LC_ALL=ko_KR.UTF-8
'''
    
    # 3. Windows 배치 파일 생성
    batch_content = '''@echo off
REM UTF-8 환경 설정
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo UTF-8 환경 설정 완료
'''
    
    # 파일 저장
    config_dir = Path(r"C:\projects\autoinput\config")
    config_dir.mkdir(exist_ok=True)
    
    # sitecustomize.py
    site_file = config_dir / "sitecustomize.py"
    site_file.write_text(site_customize, encoding='utf-8')
    print(f"✅ 생성: {site_file}")
    
    # .env
    env_file = config_dir / ".env"
    env_file.write_text(env_content, encoding='utf-8')
    print(f"✅ 생성: {env_file}")
    
    # setup_utf8.bat
    batch_file = config_dir / "setup_utf8.bat"
    batch_file.write_text(batch_content, encoding='utf-8')
    print(f"✅ 생성: {batch_file}")
    
    print("\n📌 사용 방법:")
    print("1. Python 스크립트 상단에 추가:")
    print("   # -*- coding: utf-8 -*-")
    print("2. 배치 파일 실행:")
    print(f"   {batch_file}")
    print("3. 환경 변수 영구 설정 (시스템 속성에서):")
    print("   PYTHONIOENCODING=utf-8")
    print("   PYTHONUTF8=1")

def create_universal_print():
    """범용 출력 함수 생성"""
    
    universal_print_code = '''# -*- coding: utf-8 -*-
"""
🌟 범용 출력 모듈 - 한글과 이모지 완벽 지원
"""

import sys
import io
import os

# UTF-8 설정
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Windows UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def uprint(*args, **kwargs):
    """UTF-8 안전 출력 함수"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 인코딩 에러 시 대체 출력
        text = ' '.join(str(arg) for arg in args)
        safe_text = text.encode('utf-8', errors='replace').decode('utf-8')
        print(safe_text, **kwargs)

def emoji_print(emoji, text):
    """이모지 포함 출력"""
    uprint(f"{emoji} {text}")

# 자주 사용하는 이모지
class Emoji:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    ROCKET = "🚀"
    FOLDER = "📁"
    FILE = "📄"
    CHART = "📊"
    TROPHY = "🏆"
    STAR = "⭐"
    FIRE = "🔥"
    CHECK = "✔️"
    CROSS = "✖️"
    ARROW = "➡️"
    SPARKLE = "✨"

# 사용 예시
if __name__ == "__main__":
    uprint("=" * 70)
    emoji_print(Emoji.ROCKET, "범용 출력 모듈 테스트")
    uprint("=" * 70)
    
    emoji_print(Emoji.SUCCESS, "한글 출력 성공!")
    emoji_print(Emoji.FOLDER, "폴더: C:\\projects\\autoinput")
    emoji_print(Emoji.FILE, "파일: 테스트.hwp")
    emoji_print(Emoji.CHART, "통계: 100% 완료")
    emoji_print(Emoji.TROPHY, "축하합니다!")
    
    uprint("\n모든 이모지와 한글이 정상 출력됩니다! 🎉")
'''
    
    # 파일 저장
    utils_dir = Path(r"C:\projects\autoinput\utils")
    utils_dir.mkdir(exist_ok=True)
    
    uprint_file = utils_dir / "uprint.py"
    uprint_file.write_text(universal_print_code, encoding='utf-8')
    print(f"✅ 범용 출력 모듈 생성: {uprint_file}")
    
    # __init__.py 생성
    init_file = utils_dir / "__init__.py"
    init_file.write_text("from .uprint import uprint, emoji_print, Emoji", encoding='utf-8')
    print(f"✅ __init__.py 생성: {init_file}")
    
    print("\n📌 사용 방법:")
    print("from utils.uprint import uprint, emoji_print, Emoji")
    print("uprint('한글과 이모지 🚀 완벽 지원!')")
    print("emoji_print(Emoji.SUCCESS, '성공!')")

from pathlib import Path

if __name__ == "__main__":
    print("🌟 UTF-8 및 이모지 영구 해결 스크립트")
    print("=" * 70)
    
    # 1. 현재 환경 설정
    setup_utf8_environment()
    
    # 2. 설정 파일 생성
    print("\n📁 설정 파일 생성")
    print("-" * 50)
    create_encoding_config()
    
    # 3. 범용 출력 모듈 생성
    print("\n📦 범용 출력 모듈 생성")
    print("-" * 50)
    create_universal_print()
    
    print("\n" + "=" * 70)
    print("✨ 모든 설정 완료!")
    print("이제 한글과 이모지를 자유롭게 사용할 수 있습니다! 🎉")
    print("=" * 70)
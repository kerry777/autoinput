# -*- coding: utf-8 -*-
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
    emoji_print(Emoji.FOLDER, "폴더: C:\projects\autoinput")
    emoji_print(Emoji.FILE, "파일: 테스트.hwp")
    emoji_print(Emoji.CHART, "통계: 100% 완료")
    emoji_print(Emoji.TROPHY, "축하합니다!")
    
    uprint("
모든 이모지와 한글이 정상 출력됩니다! 🎉")

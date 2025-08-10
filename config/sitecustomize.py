# -*- coding: utf-8 -*-
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
유틸리티 함수들
- 로깅 설정
- 환경 변수 로드
- 공통 함수
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """설정 파일과 환경 변수 로드"""
    # .env 파일 로드
    load_dotenv()
    
    # config.json 로드
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 환경 변수로 덮어쓰기
    if os.getenv('BIZMEKA_USERNAME'):
        config['credentials']['username'] = os.getenv('BIZMEKA_USERNAME')
    
    if os.getenv('BIZMEKA_PASSWORD'):
        config['credentials']['password'] = os.getenv('BIZMEKA_PASSWORD')
    
    if os.getenv('HEADLESS'):
        config['settings']['headless'] = os.getenv('HEADLESS').lower() == 'true'
    
    if os.getenv('COOKIE_EXPIRY_DAYS'):
        config['settings']['cookie_expiry_days'] = int(os.getenv('COOKIE_EXPIRY_DAYS'))
    
    if os.getenv('AUTO_REFRESH'):
        config['settings']['auto_refresh'] = os.getenv('AUTO_REFRESH').lower() == 'true'
    
    return config


def setup_logging(module_name: str) -> logging.Logger:
    """로깅 설정"""
    # 로그 디렉토리 생성
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 오늘 날짜로 로그 파일 생성
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}_{module_name}.log"
    
    # 로거 설정
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # 포맷터
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def print_banner(title: str):
    """배너 출력"""
    width = 60
    print("\n" + "="*width)
    print(f" {title.center(width-2)} ")
    print("="*width)


def print_status(status: str, message: str):
    """상태 메시지 출력"""
    symbols = {
        'success': '[OK]',
        'error': '[ERROR]',
        'warning': '[WARN]',
        'info': '[INFO]',
        'wait': '[WAIT]'
    }
    symbol = symbols.get(status, '[*]')
    print(f"{symbol} {message}")


def format_time_remaining(seconds: int) -> str:
    """남은 시간 포맷팅"""
    if seconds < 0:
        return "만료됨"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days}일 {hours}시간"
    elif hours > 0:
        return f"{hours}시간 {minutes}분"
    else:
        return f"{minutes}분"


def validate_credentials(config: Dict[str, Any]) -> bool:
    """로그인 정보 검증"""
    username = config.get('credentials', {}).get('username', '')
    password = config.get('credentials', {}).get('password', '')
    
    if not username or username == 'your_email@example.com':
        print_status('error', '사용자명이 설정되지 않았습니다')
        print("      .env 파일에 BIZMEKA_USERNAME을 설정하세요")
        return False
    
    if not password or password == 'your_password':
        print_status('error', '비밀번호가 설정되지 않았습니다')
        print("      .env 파일에 BIZMEKA_PASSWORD를 설정하세요")
        return False
    
    return True


def ensure_directories(config: Dict[str, Any]):
    """필요한 디렉토리 생성"""
    paths = [
        Path(config['paths']['cookies']).parent,
        Path(config['paths']['logs']),
        Path(config['paths']['profile'])
    ]
    
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def main():
    """CLI 인터페이스"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--show-logs':
            log_dir = Path("data/logs")
            if not log_dir.exists():
                print("로그 디렉토리가 없습니다")
                return
            
            # 오늘 로그 표시
            if len(sys.argv) > 2 and sys.argv[2] == 'today':
                today = datetime.now().strftime('%Y%m%d')
                log_files = list(log_dir.glob(f"{today}_*.log"))
            else:
                log_files = list(log_dir.glob("*.log"))
            
            if not log_files:
                print("로그 파일이 없습니다")
                return
            
            print("\n로그 파일:")
            for log_file in sorted(log_files):
                size = log_file.stat().st_size / 1024  # KB
                print(f"  - {log_file.name} ({size:.1f} KB)")
            
            # 최신 로그 내용 표시
            latest = sorted(log_files)[-1]
            print(f"\n최신 로그 ({latest.name}):")
            print("-" * 60)
            with open(latest, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-20:]:  # 마지막 20줄
                    print(line.rstrip())
        
        elif command == '--check-env':
            print_banner("환경 설정 확인")
            
            # .env 파일 확인
            if Path('.env').exists():
                print_status('success', '.env 파일 존재')
                load_dotenv()
                
                # 환경 변수 확인
                if os.getenv('BIZMEKA_USERNAME'):
                    print_status('success', f"사용자명: {os.getenv('BIZMEKA_USERNAME')}")
                else:
                    print_status('error', '사용자명 미설정')
                
                if os.getenv('BIZMEKA_PASSWORD'):
                    print_status('success', '비밀번호: ****')
                else:
                    print_status('error', '비밀번호 미설정')
            else:
                print_status('error', '.env 파일 없음')
                print("\n.env.example을 .env로 복사하고 설정하세요:")
                print("  copy .env.example .env")
    
    else:
        print("유틸리티 명령:")
        print("  python utils.py --show-logs [today]  # 로그 확인")
        print("  python utils.py --check-env          # 환경 설정 확인")


if __name__ == "__main__":
    main()
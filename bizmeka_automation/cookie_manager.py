#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
쿠키 관리 모듈
- 쿠키 저장/로드
- 만료 시간 관리
- 유효성 검증
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional


class CookieManager:
    def __init__(self, config_path: str = "config.json"):
        """쿠키 매니저 초기화"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.cookie_path = Path(self.config['paths']['cookies'])
        self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_cookies(self, cookies: List[Dict]) -> bool:
        """쿠키 저장"""
        try:
            # 쿠키 만료 시간 연장
            extended_cookies = self._extend_cookie_expiry(cookies)
            
            # 파일로 저장
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(extended_cookies, f, ensure_ascii=False, indent=2)
            
            print(f"[성공] {len(extended_cookies)}개 쿠키 저장됨")
            print(f"위치: {self.cookie_path}")
            return True
            
        except Exception as e:
            print(f"[오류] 쿠키 저장 실패: {e}")
            return False
    
    def load_cookies(self) -> Optional[List[Dict]]:
        """쿠키 로드"""
        if not self.cookie_path.exists():
            print("[오류] 쿠키 파일이 없습니다")
            return None
        
        try:
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            print(f"[성공] {len(cookies)}개 쿠키 로드됨")
            return cookies
            
        except Exception as e:
            print(f"[오류] 쿠키 로드 실패: {e}")
            return None
    
    def check_expiry(self) -> Dict:
        """쿠키 만료 시간 확인"""
        if not self.cookie_path.exists():
            return {"status": "no_cookies", "message": "쿠키 파일이 없습니다"}
        
        cookies = self.load_cookies()
        if not cookies:
            return {"status": "error", "message": "쿠키 로드 실패"}
        
        current_time = datetime.now()
        results = {
            "status": "valid",
            "total_cookies": len(cookies),
            "session_cookies": [],
            "expiring_soon": [],
            "expired": []
        }
        
        for cookie in cookies:
            name = cookie.get('name', 'unknown')
            expires = cookie.get('expires', -1)
            
            # 중요한 쿠키만 체크
            if name not in ['JSESSIONID', '_gid', '_ga', 'rememberMe', 'autoLogin']:
                continue
            
            if expires == -1:
                results['session_cookies'].append(name)
            else:
                expire_date = datetime.fromtimestamp(expires)
                remaining = expire_date - current_time
                
                if remaining.total_seconds() < 0:
                    results['expired'].append({
                        'name': name,
                        'expired_since': str(-remaining)
                    })
                    results['status'] = 'expired'
                elif remaining.days < 7:
                    results['expiring_soon'].append({
                        'name': name,
                        'days_remaining': remaining.days
                    })
                    if results['status'] == 'valid':
                        results['status'] = 'expiring'
        
        return results
    
    def _extend_cookie_expiry(self, cookies: List[Dict]) -> List[Dict]:
        """쿠키 만료 시간 연장"""
        extended = []
        expiry_days = self.config['settings']['cookie_expiry_days']
        future_time = datetime.now() + timedelta(days=expiry_days)
        
        for cookie in cookies:
            new_cookie = cookie.copy()
            
            # 세션 쿠키를 영구 쿠키로 변환
            if cookie['name'] in ['JSESSIONID', 'rememberMe'] and cookie.get('expires', -1) == -1:
                new_cookie['expires'] = future_time.timestamp()
                print(f"  {cookie['name']}: {expiry_days}일로 연장")
            
            extended.append(new_cookie)
        
        return extended
    
    def is_valid(self) -> bool:
        """쿠키 유효성 확인"""
        status = self.check_expiry()
        return status['status'] in ['valid', 'expiring']
    
    def get_session_id(self) -> Optional[str]:
        """JSESSIONID 값 반환"""
        cookies = self.load_cookies()
        if not cookies:
            return None
        
        for cookie in cookies:
            if cookie['name'] == 'JSESSIONID':
                return cookie['value']
        
        return None


def main():
    """CLI 인터페이스"""
    import sys
    
    manager = CookieManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == '--check-status':
            status = manager.check_expiry()
            print("\n" + "="*60)
            print("쿠키 상태 확인")
            print("="*60)
            print(f"상태: {status['status']}")
            print(f"전체 쿠키: {status['total_cookies']}개")
            
            if status['session_cookies']:
                print(f"세션 쿠키: {', '.join(status['session_cookies'])}")
            
            if status['expiring_soon']:
                print("\n⚠️ 곧 만료되는 쿠키:")
                for cookie in status['expiring_soon']:
                    print(f"  - {cookie['name']}: {cookie['days_remaining']}일 남음")
            
            if status['expired']:
                print("\n❌ 만료된 쿠키:")
                for cookie in status['expired']:
                    print(f"  - {cookie['name']}")
            
            print("="*60)
            
            if status['status'] == 'expired':
                print("\n재로그인이 필요합니다!")
                print("실행: python manual_login.py")
        
        elif command == '--get-session':
            session_id = manager.get_session_id()
            if session_id:
                print(f"JSESSIONID: {session_id[:30]}...")
            else:
                print("세션 ID를 찾을 수 없습니다")
    
    else:
        print("사용법:")
        print("  python cookie_manager.py --check-status  # 쿠키 상태 확인")
        print("  python cookie_manager.py --get-session   # 세션 ID 확인")


if __name__ == "__main__":
    main()
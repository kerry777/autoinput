#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
쿠키 만료 시간 확인
"""

import json
from datetime import datetime
from pathlib import Path

cookies_file = Path("C:\\projects\\autoinput\\data\\bizmeka_cookies.json")

with open(cookies_file, 'r', encoding='utf-8') as f:
    cookies = json.load(f)

print("\n" + "="*60)
print("쿠키 만료 시간 확인")
print("="*60)

current_time = datetime.now()
print(f"현재 시간: {current_time}\n")

for cookie in cookies:
    name = cookie['name']
    
    # 중요한 쿠키만
    if name in ['JSESSIONID', '_gid', '_ga', 'rememberMe', 'autoLogin']:
        print(f"쿠키: {name}")
        
        if 'expires' in cookie:
            expires = cookie['expires']
            if expires == -1:
                print("  → 세션 쿠키 (브라우저 종료시 만료)")
            else:
                # Unix timestamp를 datetime으로 변환
                expire_date = datetime.fromtimestamp(expires)
                remaining = expire_date - current_time
                
                print(f"  → 만료: {expire_date}")
                print(f"  → 남은 시간: {remaining.days}일 {remaining.seconds//3600}시간")
        else:
            print("  → 만료 시간 없음")
        
        if name == 'JSESSIONID':
            print(f"  → 값: {cookie['value'][:30]}...")
        print()

print("="*60)
print("결론:")
if any(c['name'] == 'JSESSIONID' for c in cookies):
    jsession = next(c for c in cookies if c['name'] == 'JSESSIONID')
    if jsession.get('expires', 0) == -1:
        print("JSESSIONID는 세션 쿠키입니다.")
        print("브라우저를 닫지 않으면 계속 유효합니다.")
    else:
        print("JSESSIONID가 영구 쿠키로 저장되었습니다.")
        print("내일도 사용 가능할 가능성이 높습니다.")
else:
    print("JSESSIONID가 없습니다. 재로그인이 필요할 수 있습니다.")
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CookieManager - 쿠키 관리 유틸리티
"""

import json
from pathlib import Path
from typing import List, Dict


class CookieManager:
    """쿠키 관리 클래스"""
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.site_dir = Path(f"sites/{site_name}")
        self.data_dir = self.site_dir / "data" 
        self.cookie_path = self.data_dir / "cookies.json"
    
    def load_cookies(self) -> List[Dict]:
        """쿠키 로드"""
        if self.cookie_path.exists():
            try:
                with open(self.cookie_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    def save_cookies(self, cookies: List[Dict]):
        """쿠키 저장"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
        except Exception:
            pass
    
    def clear_cookies(self):
        """쿠키 삭제"""
        try:
            if self.cookie_path.exists():
                self.cookie_path.unlink()
        except Exception:
            pass
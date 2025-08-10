#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PatternMatcher - 패턴 매칭 유틸리티
"""

import re
from typing import Dict, List, Any


class PatternMatcher:
    """웹 패턴 매칭 클래스"""
    
    def __init__(self):
        # 공통 패턴들
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.date_patterns = [
            re.compile(r'\d{4}-\d{2}-\d{2}'),
            re.compile(r'\d{2}/\d{2}/\d{4}'),
            re.compile(r'\d{4}\.\d{2}\.\d{2}')
        ]
        self.size_pattern = re.compile(r'\d+\.?\d*\s*(KB|MB|GB|TB)', re.IGNORECASE)
    
    def extract_emails(self, text: str) -> List[str]:
        """이메일 주소 추출"""
        return self.email_pattern.findall(text)
    
    def extract_dates(self, text: str) -> List[str]:
        """날짜 추출"""
        dates = []
        for pattern in self.date_patterns:
            dates.extend(pattern.findall(text))
        return dates
    
    def extract_sizes(self, text: str) -> List[str]:
        """파일 크기 추출"""
        return self.size_pattern.findall(text)
    
    def is_email(self, text: str) -> bool:
        """이메일 여부 확인"""
        return bool(self.email_pattern.match(text.strip()))
    
    def is_date(self, text: str) -> bool:
        """날짜 여부 확인"""
        text = text.strip()
        return any(pattern.match(text) for pattern in self.date_patterns)
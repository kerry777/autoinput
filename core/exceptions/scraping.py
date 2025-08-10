#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
스크래핑 관련 커스텀 예외들
"""


class ScrapingError(Exception):
    """스크래핑 일반 오류"""
    pass


class LoginError(ScrapingError):
    """로그인 오류"""
    pass


class NavigationError(ScrapingError):
    """네비게이션 오류"""
    pass


class ExtractionError(ScrapingError):
    """데이터 추출 오류"""
    pass


class PopupError(ScrapingError):
    """팝업 처리 오류"""
    pass
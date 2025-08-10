# AutoInput Core Module
# 공통 핵심 로직과 기본 클래스들

__version__ = "1.0.0"
__author__ = "AutoInput Team"

from .base.scraper import BaseScraper
from .base.authenticator import BaseAuth
from .base.browser import BrowserManager
from .utils.patterns import PatternMatcher

__all__ = [
    'BaseScraper',
    'BaseAuth', 
    'BrowserManager',
    'PatternMatcher'
]
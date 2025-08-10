# -*- coding: utf-8 -*-
"""
Anti-Bot 우회 전문 모듈
브라우저 핑거프린팅, CAPTCHA, Rate Limiting 등 우회
"""
import requests
import random
import time
import json
from typing import Dict, List, Optional, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from functools import wraps
import hashlib
from datetime import datetime, timedelta

class UserAgentRotator:
    """User-Agent 로테이션 관리"""
    
    def __init__(self):
        self.user_agents = [
            # Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            
            # Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            
            # Mobile
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        ]
        
        self.current_index = 0
    
    def get_random(self) -> str:
        """랜덤 User-Agent 반환"""
        return random.choice(self.user_agents)
    
    def get_next(self) -> str:
        """순차적 User-Agent 반환"""
        ua = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return ua
    
    def get_headers(self, user_agent: str = None) -> Dict:
        """완전한 헤더 세트 생성"""
        ua = user_agent or self.get_random()
        
        # 브라우저별 헤더 커스터마이징
        if 'Chrome' in ua:
            return {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"'
            }
        elif 'Firefox' in ua:
            return {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site'
            }
        else:
            return {
                'User-Agent': ua,
                'Accept': '*/*',
                'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }

class ProxyManager:
    """프록시 관리 및 로테이션"""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.current_index = 0
        self.proxy_stats = {}  # 프록시별 성공/실패 통계
    
    def add_proxy(self, proxy: str):
        """프록시 추가"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.proxy_stats[proxy] = {'success': 0, 'fail': 0}
    
    def get_next_proxy(self) -> Optional[str]:
        """다음 프록시 반환"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_best_proxy(self) -> Optional[str]:
        """성공률이 가장 높은 프록시 반환"""
        if not self.proxy_stats:
            return self.get_next_proxy()
        
        best_proxy = max(
            self.proxy_stats.keys(),
            key=lambda p: self.proxy_stats[p]['success'] / max(self.proxy_stats[p]['fail'], 1)
        )
        return best_proxy
    
    def mark_success(self, proxy: str):
        """프록시 성공 기록"""
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['success'] += 1
    
    def mark_failure(self, proxy: str):
        """프록시 실패 기록"""
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['fail'] += 1
            
            # 실패율이 높으면 제거
            if self.proxy_stats[proxy]['fail'] > 10 and \
               self.proxy_stats[proxy]['success'] / self.proxy_stats[proxy]['fail'] < 0.1:
                self.proxies.remove(proxy)
                del self.proxy_stats[proxy]
                print(f"❌ 프록시 제거: {proxy}")

class RateLimiter:
    """지능형 Rate Limiting"""
    
    def __init__(self, initial_delay: float = 1.0):
        self.base_delay = initial_delay
        self.current_delay = initial_delay
        self.last_request_time = {}
        self.request_history = []
        self.blocked_count = 0
    
    def wait(self, domain: str = None):
        """요청 전 대기"""
        current_time = time.time()
        
        # 도메인별 대기
        if domain:
            if domain in self.last_request_time:
                elapsed = current_time - self.last_request_time[domain]
                if elapsed < self.current_delay:
                    time.sleep(self.current_delay - elapsed)
            
            self.last_request_time[domain] = time.time()
        else:
            time.sleep(self.current_delay)
        
        # 요청 기록
        self.request_history.append(current_time)
        
        # 최근 1분간 요청 수 체크
        one_minute_ago = current_time - 60
        self.request_history = [t for t in self.request_history if t > one_minute_ago]
        
        # 동적 딜레이 조정
        if len(self.request_history) > 30:  # 분당 30회 초과
            self.increase_delay()
        elif len(self.request_history) < 10:  # 분당 10회 미만
            self.decrease_delay()
    
    def increase_delay(self):
        """딜레이 증가"""
        self.current_delay = min(self.current_delay * 1.5, 10.0)
        print(f"⚠️ Rate limit 조정: {self.current_delay:.2f}초")
    
    def decrease_delay(self):
        """딜레이 감소"""
        self.current_delay = max(self.current_delay * 0.8, self.base_delay)
    
    def handle_rate_limit(self, response):
        """Rate limit 응답 처리"""
        if response.status_code == 429:
            self.blocked_count += 1
            
            # Retry-After 헤더 확인
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
            else:
                wait_time = min(60 * (2 ** self.blocked_count), 300)  # 최대 5분
            
            print(f"⏰ Rate limit 감지. {wait_time}초 대기...")
            time.sleep(wait_time)
            
            # 딜레이 증가
            self.current_delay = min(self.current_delay * 2, 10.0)
            
            return True
        
        # 성공 시 blocked_count 리셋
        if response.status_code == 200:
            self.blocked_count = 0
        
        return False

class StealthBrowser:
    """탐지 회피 브라우저"""
    
    @staticmethod
    def create_stealth_driver(headless: bool = True) -> webdriver.Chrome:
        """스텔스 모드 Chrome 드라이버 생성"""
        options = webdriver.ChromeOptions()
        
        # 기본 옵션
        if headless:
            options.add_argument('--headless=new')  # 새로운 헤드리스 모드
        
        # 탐지 방지 옵션
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 추가 스텔스 옵션
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-permissions-api')
        
        # 창 크기 랜덤화
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # User-Agent 설정
        ua_rotator = UserAgentRotator()
        user_agent = ua_rotator.get_random()
        options.add_argument(f'--user-agent={user_agent}')
        
        # 언어 설정
        options.add_argument('--lang=ko-KR')
        
        # 프리퍼런스
        prefs = {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'profile.managed_default_content_settings.images': 1
        }
        options.add_experimental_option('prefs', prefs)
        
        # 드라이버 생성
        driver = webdriver.Chrome(options=options)
        
        # JavaScript로 추가 속성 수정
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    name: 'Chrome PDF Plugin',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format'
                }
            ]
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['ko-KR', 'ko', 'en-US', 'en']
        });
        
        window.chrome = {
            runtime: {}
        };
        
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({
                query: () => Promise.resolve({ state: 'granted' })
            })
        });
        """
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_js
        })
        
        return driver
    
    @staticmethod
    def check_detection(driver: webdriver.Chrome) -> bool:
        """봇 탐지 여부 확인"""
        detection_tests = [
            "return navigator.webdriver",
            "return window.navigator.webdriver",
            "return document.querySelector('meta[name=\"robots\"]')",
            "return window.__nightmare",
            "return window.phantom"
        ]
        
        for test in detection_tests:
            try:
                result = driver.execute_script(test)
                if result:
                    print(f"⚠️ 탐지 가능성: {test} = {result}")
                    return True
            except:
                pass
        
        print("✅ 봇 탐지 테스트 통과")
        return False

class CaptchaSolver:
    """CAPTCHA 해결 전략"""
    
    def __init__(self, service: str = None, api_key: str = None):
        self.service = service  # '2captcha', 'anticaptcha', etc.
        self.api_key = api_key
    
    def solve_recaptcha_v2(self, site_key: str, page_url: str) -> Optional[str]:
        """reCAPTCHA v2 해결"""
        if not self.api_key:
            print("❌ CAPTCHA 해결을 위한 API 키가 필요합니다")
            return None
        
        if self.service == '2captcha':
            return self._solve_with_2captcha(site_key, page_url)
        
        return None
    
    def _solve_with_2captcha(self, site_key: str, page_url: str) -> Optional[str]:
        """2captcha 서비스 사용"""
        # 실제 구현은 2captcha API 필요
        print("⚠️ 2captcha API 연동이 필요합니다")
        return None
    
    def solve_image_captcha(self, image_path: str) -> Optional[str]:
        """이미지 CAPTCHA 해결"""
        # OCR 또는 외부 서비스 사용
        print("⚠️ 이미지 CAPTCHA 해결 서비스가 필요합니다")
        return None
    
    def detect_captcha_type(self, driver: webdriver.Chrome) -> Optional[str]:
        """CAPTCHA 유형 감지"""
        captcha_indicators = {
            'recaptcha_v2': [
                "//iframe[contains(@src, 'recaptcha')]",
                "//div[@class='g-recaptcha']"
            ],
            'recaptcha_v3': [
                "//script[contains(@src, 'recaptcha/api.js?render=')]"
            ],
            'hcaptcha': [
                "//iframe[contains(@src, 'hcaptcha.com')]",
                "//div[@class='h-captcha']"
            ],
            'cloudflare': [
                "//div[contains(@class, 'cf-challenge')]",
                "//div[@id='cf-wrapper']"
            ]
        }
        
        for captcha_type, xpaths in captcha_indicators.items():
            for xpath in xpaths:
                try:
                    if driver.find_elements(By.XPATH, xpath):
                        print(f"🔍 {captcha_type} 감지됨")
                        return captcha_type
                except:
                    pass
        
        return None

class SmartSession:
    """지능형 세션 관리"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua_rotator = UserAgentRotator()
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter()
        self.cookies_cache = {}
        self.retry_count = 3
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """스마트 GET 요청"""
        return self._request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """스마트 POST 요청"""
        return self._request('POST', url, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """지능형 요청 처리"""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Rate limiting
        self.rate_limiter.wait(domain)
        
        # 헤더 설정
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers'].update(self.ua_rotator.get_headers())
        
        # 프록시 설정
        proxy = self.proxy_manager.get_next_proxy()
        if proxy:
            kwargs['proxies'] = {'http': proxy, 'https': proxy}
        
        # 쿠키 복원
        if domain in self.cookies_cache:
            self.session.cookies.update(self.cookies_cache[domain])
        
        # 재시도 로직
        for attempt in range(self.retry_count):
            try:
                response = self.session.request(method, url, **kwargs)
                
                # Rate limit 처리
                if self.rate_limiter.handle_rate_limit(response):
                    continue
                
                # 성공 시 쿠키 저장
                if response.status_code == 200:
                    self.cookies_cache[domain] = self.session.cookies.get_dict()
                    if proxy:
                        self.proxy_manager.mark_success(proxy)
                
                return response
                
            except Exception as e:
                print(f"❌ 요청 실패 (시도 {attempt + 1}/{self.retry_count}): {e}")
                if proxy:
                    self.proxy_manager.mark_failure(proxy)
                
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                else:
                    raise
        
        return None

# 사용 예제
if __name__ == "__main__":
    print("🛡️ Anti-Bot 우회 모듈 테스트")
    print("=" * 80)
    
    # 1. User-Agent 로테이션
    print("\n📱 User-Agent 로테이션:")
    ua_rotator = UserAgentRotator()
    for i in range(3):
        print(f"  {i+1}. {ua_rotator.get_next()[:50]}...")
    
    # 2. Rate Limiter
    print("\n⏱️ Rate Limiting:")
    rate_limiter = RateLimiter(initial_delay=0.5)
    print(f"  초기 딜레이: {rate_limiter.current_delay}초")
    
    # 3. 스텔스 브라우저
    print("\n🥷 스텔스 브라우저:")
    try:
        driver = StealthBrowser.create_stealth_driver(headless=True)
        is_detected = StealthBrowser.check_detection(driver)
        driver.quit()
    except Exception as e:
        print(f"  ⚠️ 브라우저 생성 실패: {e}")
    
    # 4. 스마트 세션
    print("\n🧠 스마트 세션:")
    smart_session = SmartSession()
    print("  ✅ 스마트 세션 초기화 완료")
    
    print("\n" + "=" * 80)
    print("✨ Anti-Bot 우회 모듈 준비 완료!")
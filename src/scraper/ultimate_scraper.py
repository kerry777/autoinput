# -*- coding: utf-8 -*-
"""
궁극의 웹 스크래핑 통합 모듈
모든 학습된 기술을 통합한 프로덕션 레벨 스크래퍼
"""
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import hashlib
import pickle
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import re
import logging
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
from queue import Queue, Empty
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cloudscraper

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScrapingStrategy(Enum):
    """스크래핑 전략"""
    SIMPLE = "simple"          # 단순 GET 요청
    SESSION = "session"        # 세션 유지
    BROWSER = "browser"        # 브라우저 자동화
    API = "api"               # API 직접 호출
    GRAPHQL = "graphql"       # GraphQL 쿼리
    HYBRID = "hybrid"         # 복합 전략

class DataFormat(Enum):
    """데이터 형식"""
    HTML = "html"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    BINARY = "binary"

@dataclass
class ScrapingConfig:
    """스크래핑 설정"""
    strategy: ScrapingStrategy = ScrapingStrategy.SIMPLE
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30
    rate_limit: float = 0.5
    use_proxy: bool = False
    use_cache: bool = True
    cache_ttl: int = 3600
    headers: Dict = field(default_factory=dict)
    cookies: Dict = field(default_factory=dict)
    
@dataclass
class ScrapingResult:
    """스크래핑 결과"""
    url: str
    status_code: int
    data: Any
    metadata: Dict
    timestamp: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    error: Optional[str] = None

class UltimateScraper:
    """궁극의 스크래퍼 - 모든 시나리오 대응"""
    
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self.session = self._create_session()
        self.cache = {}
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_data_size': 0,
            'start_time': datetime.now()
        }
        
        # 전략별 핸들러
        self.strategy_handlers = {
            ScrapingStrategy.SIMPLE: self._scrape_simple,
            ScrapingStrategy.SESSION: self._scrape_session,
            ScrapingStrategy.BROWSER: self._scrape_browser,
            ScrapingStrategy.API: self._scrape_api,
            ScrapingStrategy.GRAPHQL: self._scrape_graphql,
            ScrapingStrategy.HYBRID: self._scrape_hybrid
        }
        
        # Anti-bot 우회 컴포넌트
        self.user_agents = self._load_user_agents()
        self.proxies = []
        self.rate_limiter = RateLimiter(self.config.rate_limit)
        
    def _create_session(self) -> requests.Session:
        """강화된 세션 생성"""
        # Cloudscraper 사용 (Cloudflare 우회)
        session = cloudscraper.create_scraper()
        
        # 기본 헤더
        session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 사용자 정의 헤더 추가
        if self.config.headers:
            session.headers.update(self.config.headers)
        
        # 쿠키 설정
        if self.config.cookies:
            session.cookies.update(self.config.cookies)
        
        return session
    
    def _load_user_agents(self) -> List[str]:
        """User-Agent 목록 로드"""
        return [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def _get_random_user_agent(self) -> str:
        """랜덤 User-Agent 반환"""
        return random.choice(self.user_agents)
    
    def scrape(self, url: str, **kwargs) -> ScrapingResult:
        """메인 스크래핑 메서드"""
        start_time = time.time()
        self.metrics['total_requests'] += 1
        
        # 캐시 확인
        cache_key = self._get_cache_key(url, kwargs)
        if self.config.use_cache and cache_key in self.cache:
            cached_result, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.config.cache_ttl:
                logger.info(f"Cache hit for {url}")
                return cached_result
        
        # Rate limiting
        self.rate_limiter.wait()
        
        # 전략 선택
        strategy = kwargs.get('strategy', self.config.strategy)
        handler = self.strategy_handlers.get(strategy, self._scrape_simple)
        
        try:
            result = handler(url, **kwargs)
            self.metrics['successful_requests'] += 1
            
            # 캐시 저장
            if self.config.use_cache:
                self.cache[cache_key] = (result, time.time())
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            self.metrics['failed_requests'] += 1
            result = ScrapingResult(
                url=url,
                status_code=0,
                data=None,
                metadata={},
                error=str(e)
            )
        
        result.duration = time.time() - start_time
        return result
    
    def _get_cache_key(self, url: str, kwargs: Dict) -> str:
        """캐시 키 생성"""
        key_data = f"{url}{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _scrape_simple(self, url: str, **kwargs) -> ScrapingResult:
        """단순 스크래핑"""
        response = self._make_request(url, **kwargs)
        
        return ScrapingResult(
            url=url,
            status_code=response.status_code,
            data=response.text,
            metadata={
                'headers': dict(response.headers),
                'encoding': response.encoding
            }
        )
    
    def _scrape_session(self, url: str, **kwargs) -> ScrapingResult:
        """세션 기반 스크래핑"""
        # 로그인이 필요한 경우
        login_url = kwargs.get('login_url')
        credentials = kwargs.get('credentials', {})
        
        if login_url and credentials:
            # 로그인 수행
            self.session.post(login_url, data=credentials)
        
        response = self._make_request(url, **kwargs)
        
        return ScrapingResult(
            url=url,
            status_code=response.status_code,
            data=response.text,
            metadata={
                'cookies': self.session.cookies.get_dict(),
                'headers': dict(response.headers)
            }
        )
    
    def _scrape_browser(self, url: str, **kwargs) -> ScrapingResult:
        """브라우저 자동화 스크래핑"""
        driver = self._create_stealth_driver()
        
        try:
            driver.get(url)
            
            # 동적 콘텐츠 대기
            wait_for = kwargs.get('wait_for')
            if wait_for:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )
            else:
                time.sleep(2)  # 기본 대기
            
            # JavaScript 실행 (필요시)
            js_code = kwargs.get('execute_js')
            if js_code:
                driver.execute_script(js_code)
            
            # 데이터 추출
            page_source = driver.page_source
            
            return ScrapingResult(
                url=url,
                status_code=200,
                data=page_source,
                metadata={
                    'title': driver.title,
                    'cookies': driver.get_cookies()
                }
            )
            
        finally:
            driver.quit()
    
    def _scrape_api(self, url: str, **kwargs) -> ScrapingResult:
        """API 직접 호출"""
        method = kwargs.get('method', 'GET')
        data = kwargs.get('data')
        json_data = kwargs.get('json')
        
        response = self.session.request(
            method=method,
            url=url,
            data=data,
            json=json_data,
            timeout=self.config.timeout
        )
        
        # JSON 응답 파싱
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        return ScrapingResult(
            url=url,
            status_code=response.status_code,
            data=response_data,
            metadata={
                'headers': dict(response.headers),
                'content_type': response.headers.get('Content-Type')
            }
        )
    
    def _scrape_graphql(self, url: str, **kwargs) -> ScrapingResult:
        """GraphQL 쿼리"""
        query = kwargs.get('query', '')
        variables = kwargs.get('variables', {})
        
        payload = {
            'query': query,
            'variables': variables
        }
        
        response = self.session.post(url, json=payload)
        
        return ScrapingResult(
            url=url,
            status_code=response.status_code,
            data=response.json(),
            metadata={
                'query': query,
                'variables': variables
            }
        )
    
    def _scrape_hybrid(self, url: str, **kwargs) -> ScrapingResult:
        """복합 전략 스크래핑"""
        strategies = kwargs.get('strategies', [
            ScrapingStrategy.SIMPLE,
            ScrapingStrategy.API,
            ScrapingStrategy.BROWSER
        ])
        
        for strategy in strategies:
            try:
                kwargs['strategy'] = strategy
                result = self.scrape(url, **kwargs)
                if result.data:
                    return result
            except:
                continue
        
        return ScrapingResult(
            url=url,
            status_code=0,
            data=None,
            metadata={},
            error="All strategies failed"
        )
    
    def _make_request(self, url: str, **kwargs) -> requests.Response:
        """재시도 로직이 포함된 요청"""
        for attempt in range(self.config.max_retries):
            try:
                # User-Agent 로테이션
                self.session.headers['User-Agent'] = self._get_random_user_agent()
                
                # 프록시 사용
                proxies = None
                if self.config.use_proxy and self.proxies:
                    proxy = random.choice(self.proxies)
                    proxies = {'http': proxy, 'https': proxy}
                
                response = self.session.get(
                    url,
                    timeout=self.config.timeout,
                    proxies=proxies,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limit
                    wait_time = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay * (2 ** attempt))
        
        raise Exception(f"Failed after {self.config.max_retries} retries")
    
    def _create_stealth_driver(self) -> webdriver.Chrome:
        """스텔스 모드 드라이버 생성"""
        options = webdriver.ChromeOptions()
        
        # 스텔스 옵션
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={self._get_random_user_agent()}')
        
        # 헤드리스 모드
        if kwargs.get('headless', True):
            options.add_argument('--headless=new')
        
        driver = webdriver.Chrome(options=options)
        
        # WebDriver 속성 숨기기
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        return driver
    
    async def scrape_async(self, urls: List[str], max_concurrent: int = 10) -> List[ScrapingResult]:
        """비동기 배치 스크래핑"""
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def fetch(url):
                async with semaphore:
                    try:
                        async with session.get(url) as response:
                            data = await response.text()
                            return ScrapingResult(
                                url=url,
                                status_code=response.status,
                                data=data,
                                metadata={'headers': dict(response.headers)}
                            )
                    except Exception as e:
                        return ScrapingResult(
                            url=url,
                            status_code=0,
                            data=None,
                            metadata={},
                            error=str(e)
                        )
            
            tasks = [fetch(url) for url in urls]
            return await asyncio.gather(*tasks)
    
    def scrape_parallel(self, urls: List[str], max_workers: int = 10) -> List[ScrapingResult]:
        """병렬 스크래핑"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to scrape {url}: {e}")
                    results.append(ScrapingResult(
                        url=url,
                        status_code=0,
                        data=None,
                        metadata={},
                        error=str(e)
                    ))
        
        return results
    
    def extract_data(self, html: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """데이터 추출 헬퍼"""
        soup = BeautifulSoup(html, 'html.parser')
        extracted = {}
        
        for key, selector in selectors.items():
            if selector.startswith('//'):  # XPath
                # XPath는 lxml 필요
                continue
            else:  # CSS selector
                elements = soup.select(selector)
                if len(elements) == 1:
                    extracted[key] = elements[0].get_text(strip=True)
                elif len(elements) > 1:
                    extracted[key] = [elem.get_text(strip=True) for elem in elements]
                else:
                    extracted[key] = None
        
        return extracted
    
    def get_metrics(self) -> Dict:
        """성능 메트릭 반환"""
        runtime = (datetime.now() - self.metrics['start_time']).total_seconds()
        
        return {
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'success_rate': (self.metrics['successful_requests'] / 
                           max(self.metrics['total_requests'], 1)) * 100,
            'runtime_seconds': runtime,
            'requests_per_second': self.metrics['total_requests'] / max(runtime, 1)
        }

class RateLimiter:
    """지능형 Rate Limiter"""
    
    def __init__(self, min_delay: float = 0.5):
        self.min_delay = min_delay
        self.last_request_time = {}
        self.domain_delays = {}
    
    def wait(self, domain: str = None):
        """요청 전 대기"""
        if domain is None:
            time.sleep(self.min_delay)
            return
        
        current_time = time.time()
        
        if domain in self.last_request_time:
            elapsed = current_time - self.last_request_time[domain]
            delay = self.domain_delays.get(domain, self.min_delay)
            
            if elapsed < delay:
                time.sleep(delay - elapsed)
        
        self.last_request_time[domain] = time.time()
    
    def set_domain_delay(self, domain: str, delay: float):
        """도메인별 딜레이 설정"""
        self.domain_delays[domain] = delay

class DataProcessor:
    """스크래핑 데이터 처리기"""
    
    @staticmethod
    def parse_products(html: str) -> List[Dict]:
        """제품 정보 파싱"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # 다양한 제품 셀렉터 시도
        selectors = [
            'div.product',
            'article.product-card',
            'li.product-item',
            'div[data-testid="product"]'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            if items:
                for item in items:
                    product = DataProcessor._extract_product_info(item)
                    if product:
                        products.append(product)
                break
        
        return products
    
    @staticmethod
    def _extract_product_info(element) -> Dict:
        """제품 정보 추출"""
        product = {}
        
        # 제목
        title_selectors = ['h2', 'h3', 'a.title', '.product-name']
        for selector in title_selectors:
            title = element.select_one(selector)
            if title:
                product['title'] = title.get_text(strip=True)
                break
        
        # 가격
        price_selectors = ['.price', 'span.price', '.product-price']
        for selector in price_selectors:
            price = element.select_one(selector)
            if price:
                product['price'] = price.get_text(strip=True)
                break
        
        # 이미지
        img = element.select_one('img')
        if img:
            product['image'] = img.get('src', '')
        
        # 링크
        link = element.select_one('a[href]')
        if link:
            product['url'] = link.get('href', '')
        
        return product if product else None
    
    @staticmethod
    def extract_json_ld(html: str) -> List[Dict]:
        """JSON-LD 구조화 데이터 추출"""
        soup = BeautifulSoup(html, 'html.parser')
        json_ld_data = []
        
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                json_ld_data.append(data)
            except:
                pass
        
        return json_ld_data
    
    @staticmethod
    def extract_meta_tags(html: str) -> Dict[str, str]:
        """메타 태그 추출"""
        soup = BeautifulSoup(html, 'html.parser')
        meta_data = {}
        
        # Open Graph
        for meta in soup.find_all('meta', property=re.compile('^og:')):
            key = meta.get('property').replace('og:', '')
            meta_data[f'og_{key}'] = meta.get('content', '')
        
        # Twitter Card
        for meta in soup.find_all('meta', attrs={'name': re.compile('^twitter:')}):
            key = meta.get('name').replace('twitter:', '')
            meta_data[f'twitter_{key}'] = meta.get('content', '')
        
        # 일반 메타
        for meta in soup.find_all('meta', attrs={'name': True}):
            name = meta.get('name')
            if not name.startswith('twitter:'):
                meta_data[name] = meta.get('content', '')
        
        return meta_data

# 사용 예제
if __name__ == "__main__":
    print("🚀 Ultimate Scraper 테스트")
    print("=" * 80)
    
    # 설정
    config = ScrapingConfig(
        strategy=ScrapingStrategy.HYBRID,
        max_retries=3,
        rate_limit=1.0,
        use_cache=True
    )
    
    # 스크래퍼 초기화
    scraper = UltimateScraper(config)
    
    # 단일 URL 스크래핑
    result = scraper.scrape("https://httpbin.org/html")
    print(f"\n✅ 단일 스크래핑 완료")
    print(f"  상태 코드: {result.status_code}")
    print(f"  소요 시간: {result.duration:.2f}초")
    
    # 병렬 스크래핑
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/json",
        "https://httpbin.org/html"
    ]
    
    results = scraper.scrape_parallel(urls, max_workers=3)
    print(f"\n✅ 병렬 스크래핑 완료: {len(results)}개")
    
    # 메트릭 출력
    metrics = scraper.get_metrics()
    print(f"\n📊 성능 메트릭:")
    print(f"  총 요청: {metrics['total_requests']}")
    print(f"  성공률: {metrics['success_rate']:.1f}%")
    print(f"  처리 속도: {metrics['requests_per_second']:.2f} req/s")
    
    print("\n✨ Ultimate Scraper 준비 완료!")
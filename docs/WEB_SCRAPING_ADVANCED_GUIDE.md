# 🕷️ 고급 웹 스크래핑 완벽 가이드

## 📋 목차
1. [개요](#개요)
2. [핵심 기술](#핵심-기술)
3. [모듈 구조](#모듈-구조)
4. [실전 테크닉](#실전-테크닉)
5. [Anti-Bot 우회](#anti-bot-우회)
6. [실제 사용 예제](#실제-사용-예제)
7. [트러블슈팅](#트러블슈팅)

---

## 개요

web-scraping.dev에서 학습한 고급 웹 스크래핑 기술을 체계적으로 정리한 가이드입니다.

### 학습 소스
- **웹사이트**: https://web-scraping.dev
- **제작자**: ScrapFly
- **목적**: 실제 웹 스크래핑 시나리오 학습

---

## 핵심 기술

### 1. 페이지네이션 처리

#### 정적 HTML 페이징
```python
def scrape_with_pagination(url_pattern: str, max_pages: int = None):
    all_data = []
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
        
        url = url_pattern.format(page=page)
        response = session.get(url)
        
        # 데이터 추출
        soup = BeautifulSoup(response.text, 'html.parser')
        products = soup.find_all('div', class_='product')
        
        if not products:
            break
        
        all_data.extend(products)
        page += 1
        time.sleep(0.5)  # Rate limiting
    
    return all_data
```

#### 무한 스크롤
```python
def handle_infinite_scroll(base_url: str, max_items: int = 50):
    # API 엔드포인트 찾기
    api_url = f"{base_url}/api/items"
    
    items = []
    offset = 0
    limit = 20
    
    while len(items) < max_items:
        params = {'offset': offset, 'limit': limit}
        response = requests.get(api_url, params=params)
        data = response.json()
        
        if not data['items']:
            break
        
        items.extend(data['items'])
        offset += limit
    
    return items[:max_items]
```

#### "Load More" 버튼
```python
def handle_load_more(url: str):
    all_items = []
    next_url = url
    
    while next_url:
        response = requests.get(next_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 아이템 추출
        items = soup.find_all('div', class_='item')
        all_items.extend(items)
        
        # 다음 페이지 URL 찾기
        load_more = soup.find('button', {'data-action': 'load-more'})
        if load_more and load_more.get('data-next-url'):
            next_url = load_more['data-next-url']
        else:
            next_url = None
    
    return all_items
```

### 2. 인증 처리

#### 쿠키 기반 로그인
```python
def login_with_cookies(login_url: str, credentials: dict):
    session = requests.Session()
    
    # 로그인
    response = session.post(login_url, data=credentials)
    
    # 쿠키 저장
    cookies = session.cookies.get_dict()
    
    # 인증된 페이지 접근
    protected_url = "https://example.com/protected"
    response = session.get(protected_url)
    
    return response.text
```

#### CSRF 토큰 처리
```python
def handle_csrf_token(session: requests.Session, form_url: str):
    # 폼 페이지에서 CSRF 토큰 추출
    response = session.get(form_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    
    # 토큰과 함께 제출
    data = {
        'csrf_token': csrf_token,
        'username': 'user',
        'password': 'pass'
    }
    
    response = session.post(form_url, data=data)
    return response
```

#### API 키 인증
```python
def api_with_auth(api_url: str, api_key: str):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'X-API-Key': api_key
    }
    
    response = requests.get(api_url, headers=headers)
    return response.json()
```

### 3. 데이터 추출

#### 숨겨진 JSON 데이터
```python
def extract_hidden_json(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    hidden_data = {}
    
    # JavaScript 변수에서 추출
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # window.* 패턴
            matches = re.findall(
                r'window\.(\w+)\s*=\s*({.*?});', 
                script.string, 
                re.DOTALL
            )
            for var_name, json_str in matches:
                try:
                    hidden_data[var_name] = json.loads(json_str)
                except:
                    pass
    
    # JSON-LD 구조화 데이터
    json_ld = soup.find_all('script', type='application/ld+json')
    for script in json_ld:
        try:
            hidden_data['structured_data'] = json.loads(script.string)
        except:
            pass
    
    return hidden_data
```

#### Local Storage 데이터
```python
# Selenium을 사용한 Local Storage 접근
from selenium import webdriver

def get_local_storage_data(url: str):
    driver = webdriver.Chrome()
    driver.get(url)
    
    # Local Storage 데이터 가져오기
    local_storage = driver.execute_script(
        "return window.localStorage;"
    )
    
    # Session Storage 데이터
    session_storage = driver.execute_script(
        "return window.sessionStorage;"
    )
    
    driver.quit()
    
    return {
        'local': local_storage,
        'session': session_storage
    }
```

### 4. Anti-Bot 우회

#### User-Agent 로테이션
```python
import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
```

#### Rate Limiting
```python
import time
from functools import wraps

def rate_limit(calls_per_second=1):
    min_interval = 1.0 / calls_per_second
    
    def decorator(func):
        last_called = [0.0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            
            return result
        
        return wrapper
    
    return decorator

@rate_limit(calls_per_second=2)
def scrape_page(url):
    return requests.get(url)
```

#### Proxy 로테이션
```python
import itertools

class ProxyRotator:
    def __init__(self, proxies):
        self.proxies = proxies
        self.proxy_pool = itertools.cycle(proxies)
    
    def get_next_proxy(self):
        return next(self.proxy_pool)
    
    def make_request(self, url):
        proxy = self.get_next_proxy()
        
        try:
            response = requests.get(
                url,
                proxies={'http': proxy, 'https': proxy},
                timeout=10
            )
            return response
        except:
            # 실패 시 다음 프록시 시도
            return self.make_request(url)
```

---

## 모듈 구조

### AdvancedScraper 클래스

```python
from src.scraper.advanced_scraper import AdvancedScraper

# 초기화
scraper = AdvancedScraper(base_url="https://example.com")

# API 스크래핑
data = scraper.scrape_api('/api/products')

# 페이지네이션
products = scraper.scrape_with_pagination(
    url_pattern="https://example.com/products?page={page}",
    max_pages=5
)

# 숨겨진 데이터 추출
hidden = scraper.extract_hidden_data("https://example.com/product/1")

# 쿠키 사용
scraper.scrape_with_cookies(url, cookies={'session': 'abc123'})

# Referer 헤더
scraper.scrape_with_referer(url, referer='https://google.com')
```

### ScrapingOrchestrator 클래스

```python
from src.scraper.advanced_scraper import (
    ScrapingOrchestrator, 
    ScrapingTarget, 
    ScrapingMethod
)

# 조율자 초기화
orchestrator = ScrapingOrchestrator()

# 대상 추가
orchestrator.add_target(
    ScrapingTarget(
        url="https://example.com/api/products",
        method=ScrapingMethod.API,
        has_pagination=True
    )
)

# 실행
results = orchestrator.execute()
```

---

## 실전 테크닉

### 1. 동적 콘텐츠 처리

#### Selenium 사용
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_dynamic_content(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(url)
        
        # 요소가 로드될 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "product"))
        )
        
        # JavaScript 실행
        products = driver.execute_script(
            "return document.querySelectorAll('.product')"
        )
        
        return driver.page_source
        
    finally:
        driver.quit()
```

#### Playwright 사용
```python
from playwright.sync_api import sync_playwright

def scrape_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 네트워크 요청 가로채기
        def handle_request(request):
            if request.resource_type == "image":
                request.abort()
            else:
                request.continue_()
        
        page.route("**/*", handle_request)
        
        page.goto(url)
        page.wait_for_selector('.product')
        
        content = page.content()
        browser.close()
        
        return content
```

### 2. 대용량 데이터 처리

#### 스트리밍 파싱
```python
import requests
from lxml import etree

def stream_large_xml(url):
    response = requests.get(url, stream=True)
    parser = etree.iterparse(response.raw, events=('start', 'end'))
    
    for event, elem in parser:
        if event == 'end' and elem.tag == 'product':
            # 제품 처리
            process_product(elem)
            
            # 메모리 절약
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
```

#### 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

lock = threading.Lock()
results = []

def scrape_url(url):
    response = requests.get(url)
    data = parse_response(response)
    
    with lock:
        results.append(data)
    
    return data

def parallel_scraping(urls, max_workers=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_url, url): url for url in urls}
        
        for future in as_completed(futures):
            url = futures[future]
            try:
                data = future.result()
                print(f"✅ 완료: {url}")
            except Exception as e:
                print(f"❌ 실패: {url} - {e}")
    
    return results
```

---

## Anti-Bot 우회

### 1. Cloudflare 우회

```python
# cloudscraper 사용
import cloudscraper

scraper = cloudscraper.create_scraper()
response = scraper.get("https://protected-site.com")
```

### 2. reCAPTCHA 처리

```python
# 2captcha 서비스 사용 예제
import requests

def solve_recaptcha(site_key, page_url, api_key):
    # CAPTCHA 해결 요청
    response = requests.post(
        'http://2captcha.com/in.php',
        data={
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url
        }
    )
    
    captcha_id = response.text.split('|')[1]
    
    # 결과 대기
    time.sleep(20)
    
    # 결과 가져오기
    response = requests.get(
        f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}'
    )
    
    return response.text.split('|')[1]
```

### 3. 브라우저 핑거프린팅 우회

```python
from selenium import webdriver

def setup_anti_detection_browser():
    options = webdriver.ChromeOptions()
    
    # 자동화 감지 우회
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # WebDriver 속성 숨기기
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver
```

---

## 실제 사용 예제

### 전자상거래 사이트 스크래핑

```python
from src.scraper.advanced_scraper import AdvancedScraper

def scrape_ecommerce_site():
    scraper = AdvancedScraper()
    
    # 1. 카테고리 목록 가져오기
    categories = scraper.scrape_api('/api/categories')
    
    all_products = []
    
    for category in categories:
        # 2. 각 카테고리의 제품 가져오기 (페이지네이션)
        products = scraper.scrape_with_pagination(
            f"/category/{category['id']}/products?page={{page}}",
            max_pages=10
        )
        
        for product in products:
            # 3. 제품 상세 정보 가져오기
            details = scraper.extract_hidden_data(product['url'])
            product.update(details)
            
            all_products.append(product)
        
        # Rate limiting
        time.sleep(1)
    
    return all_products
```

### 뉴스 사이트 스크래핑

```python
def scrape_news_site():
    scraper = AdvancedScraper()
    
    # 최신 뉴스 API
    latest_news = scraper.scrape_api('/api/news/latest')
    
    articles = []
    
    for news_item in latest_news:
        # 전체 기사 내용 가져오기
        article_html = scraper.session.get(news_item['url']).text
        soup = BeautifulSoup(article_html, 'html.parser')
        
        article = {
            'title': soup.find('h1').text,
            'content': soup.find('div', class_='content').text,
            'author': soup.find('span', class_='author').text,
            'date': soup.find('time')['datetime'],
            'tags': [tag.text for tag in soup.find_all('a', class_='tag')]
        }
        
        articles.append(article)
    
    return articles
```

---

## 트러블슈팅

### 일반적인 문제와 해결책

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 403 Forbidden | User-Agent 차단 | User-Agent 로테이션 |
| 429 Too Many Requests | Rate limiting | 요청 간격 늘리기 |
| CAPTCHA 출현 | 봇 감지 | Selenium/Playwright 사용 |
| 빈 응답 | JavaScript 렌더링 | 동적 스크래핑 도구 사용 |
| IP 차단 | 과도한 요청 | 프록시 로테이션 |
| 세션 만료 | 쿠키 만료 | 세션 갱신 로직 구현 |

### 디버깅 팁

```python
# 요청/응답 로깅
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

# 응답 저장
def save_response_for_debugging(response, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print(f"Response saved to {filename}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
```

---

## 결론

이 가이드를 통해 다음을 학습했습니다:
- ✅ 다양한 페이지네이션 처리 방법
- ✅ 인증 및 세션 관리
- ✅ 숨겨진 데이터 추출
- ✅ Anti-Bot 메커니즘 우회
- ✅ 동적 콘텐츠 스크래핑
- ✅ 대용량 데이터 효율적 처리

고급 웹 스크래핑 기술을 마스터하여 어떤 웹사이트든 효과적으로 스크래핑할 수 있습니다! 🚀
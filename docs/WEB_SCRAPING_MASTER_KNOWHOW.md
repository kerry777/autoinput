# 🕷️ 웹 스크래핑 마스터 노하우

## 📋 목차
1. [실전 노하우 총정리](#실전-노하우-총정리)
2. [GraphQL 스크래핑](#graphql-스크래핑)
3. [Anti-Bot 우회 전략](#anti-bot-우회-전략)
4. [분산 스크래핑 아키텍처](#분산-스크래핑-아키텍처)
5. [실제 사례 연구](#실제-사례-연구)
6. [성능 최적화](#성능-최적화)
7. [법적/윤리적 고려사항](#법적윤리적-고려사항)

---

## 실전 노하우 총정리

### 🎯 핵심 원칙

1. **점진적 접근**
   - 작은 요청부터 시작
   - 패턴 파악 후 확대
   - 실패 지점 기록

2. **방어적 프로그래밍**
   - 모든 요청에 타임아웃
   - 예외 처리 필수
   - 재시도 로직 구현

3. **리소스 관리**
   - 메모리 누수 방지
   - 연결 풀 관리
   - 파일 핸들 정리

### 🔍 사이트 분석 체크리스트

```python
class SiteAnalyzer:
    """웹사이트 분석 도구"""
    
    def analyze(self, url: str) -> Dict:
        analysis = {
            'technology': self.detect_technology(url),
            'protection': self.detect_protection(url),
            'api': self.find_api_endpoints(url),
            'structure': self.analyze_structure(url)
        }
        return analysis
    
    def detect_technology(self, url):
        """기술 스택 감지"""
        indicators = {
            'React': ['_app.js', 'react', '__NEXT_DATA__'],
            'Vue': ['vue', 'v-if', 'v-for'],
            'Angular': ['ng-', 'angular'],
            'WordPress': ['/wp-content/', '/wp-admin/'],
            'Shopify': ['cdn.shopify.com', 'myshopify.com']
        }
        # 감지 로직
    
    def detect_protection(self, url):
        """보호 메커니즘 감지"""
        protections = {
            'cloudflare': 'cf-ray header',
            'recaptcha': 'recaptcha script',
            'rate_limit': 'X-RateLimit headers',
            'bot_detection': 'datadome, imperva'
        }
        # 감지 로직
```

---

## GraphQL 스크래핑

### 🔌 GraphQL 마스터 전략

#### 1. 스키마 탐색
```python
# Introspection 쿼리로 전체 구조 파악
introspection_query = """
{
  __schema {
    types {
      name
      fields {
        name
        type {
          name
          kind
        }
      }
    }
  }
}
"""
```

#### 2. 효율적 쿼리 작성
```python
# 필요한 필드만 정확히 요청
optimized_query = """
query GetProducts($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    edges {
      node {
        id
        name
        price
        # 불필요한 필드 제외
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""
```

#### 3. 배치 처리
```python
# 여러 쿼리를 한 번에 전송
batch_query = """
query BatchRequest {
  product1: product(id: "1") { ...ProductFields }
  product2: product(id: "2") { ...ProductFields }
  product3: product(id: "3") { ...ProductFields }
}

fragment ProductFields on Product {
  id
  name
  price
}
"""
```

### 📊 GraphQL 팁

1. **Fragment 활용**: 재사용 가능한 필드 세트 정의
2. **Alias 사용**: 같은 필드를 여러 번 쿼리
3. **Variables 활용**: 동적 쿼리 생성
4. **Persisted Queries**: 쿼리 ID로 캐싱

---

## Anti-Bot 우회 전략

### 🛡️ 단계별 우회 전략

#### Level 1: 기본 우회
```python
# User-Agent 로테이션
headers = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# 랜덤 딜레이
time.sleep(random.uniform(1, 3))
```

#### Level 2: 브라우저 시뮬레이션
```python
# Selenium 스텔스 모드
options = webdriver.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# CDP 명령으로 속성 수정
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    '''
})
```

#### Level 3: 고급 우회
```python
# TLS 핑거프린팅 우회
import ssl
import requests.adapters

class CustomAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', CustomAdapter())
```

### 🔍 탐지 회피 체크리스트

- [ ] User-Agent 다양화
- [ ] 헤더 순서 랜덤화
- [ ] 리퍼러 설정
- [ ] 쿠키 관리
- [ ] JavaScript 실행
- [ ] Canvas 핑거프린팅 우회
- [ ] WebRTC 누출 방지
- [ ] 시간대 설정
- [ ] 화면 해상도 랜덤화
- [ ] 플러그인 시뮬레이션

---

## 분산 스크래핑 아키텍처

### 🌐 확장 가능한 아키텍처

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Master    │────▶│   Queue     │────▶│   Workers   │
│ Coordinator │     │   (Redis)   │     │  (1...N)    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                         │
       ▼                                         ▼
┌─────────────┐                         ┌─────────────┐
│  Monitor    │                         │   Storage   │
│ (Dashboard) │                         │  (MongoDB)  │
└─────────────┘                         └─────────────┘
```

### 📈 성능 메트릭

```python
class PerformanceMonitor:
    """성능 모니터링"""
    
    def __init__(self):
        self.metrics = {
            'requests_per_second': 0,
            'success_rate': 0,
            'average_response_time': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'bandwidth_usage': 0
        }
    
    def calculate_metrics(self, results: List[ScrapingTask]):
        """메트릭 계산"""
        total = len(results)
        successful = sum(1 for r in results if r.status == TaskStatus.COMPLETED)
        
        self.metrics['success_rate'] = (successful / total) * 100
        
        # 응답 시간 계산
        response_times = [
            (r.completed_at - r.created_at).total_seconds()
            for r in results if r.completed_at
        ]
        
        if response_times:
            self.metrics['average_response_time'] = sum(response_times) / len(response_times)
        
        return self.metrics
```

### 🔄 로드 밸런싱

```python
class LoadBalancer:
    """로드 밸런서"""
    
    def __init__(self, workers: List[Worker]):
        self.workers = workers
        self.current = 0
    
    def get_worker(self) -> Worker:
        """라운드 로빈 방식"""
        worker = self.workers[self.current]
        self.current = (self.current + 1) % len(self.workers)
        return worker
    
    def get_least_loaded(self) -> Worker:
        """최소 부하 워커 선택"""
        return min(self.workers, key=lambda w: w.queue_size())
```

---

## 실제 사례 연구

### 📦 전자상거래 사이트 (Amazon 스타일)

```python
class EcommerceScraper:
    """전자상거래 스크래퍼"""
    
    def __init__(self):
        self.session = SmartSession()
        self.product_cache = {}
    
    async def scrape_category(self, category_url: str):
        """카테고리 스크래핑"""
        products = []
        page = 1
        
        while True:
            # 페이지 URL 구성
            url = f"{category_url}?page={page}"
            
            # 스마트 요청
            response = await self.session.get(url)
            
            # 제품 추출
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select('[data-component-type="s-search-result"]')
            
            if not items:
                break
            
            for item in items:
                product = self.extract_product(item)
                products.append(product)
                
                # 캐싱
                self.product_cache[product['asin']] = product
            
            # 다음 페이지 확인
            next_button = soup.select_one('a.s-pagination-next')
            if not next_button or 'disabled' in next_button.get('class', []):
                break
            
            page += 1
            await asyncio.sleep(random.uniform(1, 3))
        
        return products
    
    def extract_product(self, element):
        """제품 정보 추출"""
        return {
            'asin': element.get('data-asin'),
            'title': element.select_one('h2 span').text.strip(),
            'price': self.extract_price(element),
            'rating': self.extract_rating(element),
            'image': element.select_one('img')['src']
        }
```

### 📰 뉴스 사이트 (실시간 업데이트)

```python
class NewsScraper:
    """뉴스 스크래퍼"""
    
    def __init__(self):
        self.websocket = None
        self.articles = []
    
    async def connect_live_updates(self, ws_url: str):
        """WebSocket 연결"""
        async with websockets.connect(ws_url) as websocket:
            self.websocket = websocket
            
            # 구독 메시지
            await websocket.send(json.dumps({
                'action': 'subscribe',
                'channels': ['breaking_news', 'updates']
            }))
            
            # 실시간 수신
            async for message in websocket:
                data = json.loads(message)
                await self.handle_update(data)
    
    async def handle_update(self, data):
        """업데이트 처리"""
        if data['type'] == 'article':
            article = {
                'id': data['id'],
                'title': data['title'],
                'content': data['content'],
                'timestamp': datetime.now(),
                'category': data['category']
            }
            
            self.articles.append(article)
            
            # 실시간 처리
            await self.process_article(article)
```

### 🏢 비즈니스 디렉토리 (LinkedIn 스타일)

```python
class BusinessDirectoryScraper:
    """비즈니스 디렉토리 스크래퍼"""
    
    def __init__(self):
        self.graphql = GraphQLScraper("https://api.example.com/graphql")
    
    async def search_companies(self, query: str, filters: Dict):
        """회사 검색"""
        graphql_query = """
        query SearchCompanies($query: String!, $filters: CompanyFilters) {
          searchCompanies(query: $query, filters: $filters) {
            edges {
              node {
                id
                name
                industry
                size
                location {
                  city
                  country
                }
                employees {
                  totalCount
                }
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
        """
        
        variables = {
            'query': query,
            'filters': filters
        }
        
        return await self.graphql.paginate_query(
            graphql_query,
            variables=variables
        )
```

---

## 성능 최적화

### ⚡ 최적화 기법

#### 1. 연결 재사용
```python
# 세션 유지
session = requests.Session()
session.mount('http://', HTTPAdapter(pool_connections=100, pool_maxsize=100))
```

#### 2. 동시성 제어
```python
# 세마포어로 동시 요청 제한
semaphore = asyncio.Semaphore(10)

async def fetch_with_limit(url):
    async with semaphore:
        return await fetch(url)
```

#### 3. 캐싱 전략
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def cached_request(url: str) -> str:
    """캐시된 요청"""
    return requests.get(url).text

# Redis 캐싱
def redis_cache(expire=3600):
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = hashlib.md5(str(args).encode()).hexdigest()
            
            # 캐시 확인
            cached = redis_client.get(key)
            if cached:
                return pickle.loads(cached)
            
            # 실행 및 캐싱
            result = func(*args, **kwargs)
            redis_client.setex(key, expire, pickle.dumps(result))
            
            return result
        return wrapper
    return decorator
```

#### 4. 스트리밍 파싱
```python
# 대용량 파일 스트리밍
def stream_large_file(url):
    with requests.get(url, stream=True) as r:
        for chunk in r.iter_content(chunk_size=8192):
            process_chunk(chunk)
```

### 📊 벤치마크 결과

| 방법 | 1000 URL | 10000 URL | 100000 URL |
|------|----------|-----------|------------|
| 동기 | 16분 | 2.7시간 | 27시간 |
| 비동기 (10) | 1.6분 | 16분 | 2.7시간 |
| 분산 (10 워커) | 1.6분 | 16분 | 2.7시간 |
| 분산 (100 워커) | 10초 | 1.6분 | 16분 |

---

## 법적/윤리적 고려사항

### ⚖️ 법적 체크리스트

- [ ] robots.txt 준수
- [ ] 서비스 약관 확인
- [ ] 저작권 고려
- [ ] 개인정보 보호
- [ ] Rate limiting 준수

### 🤝 윤리적 가이드라인

1. **최소 영향 원칙**
   - 서버 부하 최소화
   - 필요한 데이터만 수집
   - 캐싱 적극 활용

2. **투명성**
   - User-Agent 명시
   - 연락처 정보 제공
   - 목적 명확화

3. **존중**
   - 콘텐츠 창작자 권리
   - 비즈니스 모델 존중
   - 사용자 프라이버시

### 📝 robots.txt 파서
```python
from urllib.robotparser import RobotFileParser

def can_fetch(url: str, user_agent: str = '*') -> bool:
    """robots.txt 확인"""
    rp = RobotFileParser()
    rp.set_url(url + "/robots.txt")
    rp.read()
    
    return rp.can_fetch(user_agent, url)
```

---

## 🎓 핵심 노하우 정리

### 실전 팁 Top 10

1. **항상 실패를 가정하라** - 모든 요청이 실패할 수 있다
2. **점진적으로 확대하라** - 작게 시작해서 크게 확장
3. **패턴을 찾아라** - API 엔드포인트, URL 구조 파악
4. **캐싱을 활용하라** - 불필요한 요청 최소화
5. **모니터링하라** - 실시간 상태 확인
6. **문서화하라** - 발견한 패턴과 해결책 기록
7. **백업 계획을 가져라** - Plan B, C 준비
8. **법적 경계를 지켜라** - 합법적 범위 내 작업
9. **성능을 측정하라** - 병목 지점 파악
10. **커뮤니티와 공유하라** - 지식 공유와 학습

### 🚀 다음 단계

1. **머신러닝 통합**: 패턴 자동 학습
2. **컴퓨터 비전**: 이미지 기반 데이터 추출
3. **자연어 처리**: 비정형 텍스트 분석
4. **실시간 처리**: 스트리밍 데이터 파이프라인
5. **클라우드 배포**: AWS/GCP 확장

---

## 결론

웹 스크래핑은 기술과 예술의 조합입니다. 
지속적인 학습과 실험을 통해 마스터할 수 있습니다.

**Remember**: With great scraping power comes great responsibility! 🕷️✨
# 🎮 web-scraping.dev Complete Guide

## 📚 Overview
**web-scraping.dev**는 웹 스크래핑 학습과 테스트를 위한 종합 플랫폼으로, 실제 웹사이트에서 마주치는 다양한 도전과제를 안전하게 연습할 수 있는 환경을 제공합니다.

---

## 🗺️ Site Structure

### Main Pages & Challenges

#### 1. **Product Catalog** (`/products`)
- **Type**: Static Paging
- **Features**: 
  - 28개 제품 (Books to Scrape 데이터셋)
  - 페이지네이션 (1-6 페이지)
  - 카테고리 필터링
  - 가격 정렬
- **Challenge**: 정적 페이지 크롤링, 페이지네이션 처리

#### 2. **Testimonials** (`/testimonials`)
- **Type**: Endless Scroll Paging
- **Features**:
  - 무한 스크롤
  - 동적 콘텐츠 로딩
  - Lazy loading 이미지
- **Challenge**: 스크롤 이벤트 처리, 동적 로딩 대기

#### 3. **Reviews** (`/reviews`)
- **Type**: Endless Button Paging + GraphQL
- **Features**:
  - "Load More" 버튼
  - GraphQL API 백그라운드 요청
  - CSRF 토큰 필요
- **Challenge**: GraphQL 처리, CSRF 토큰 관리

#### 4. **Login System** (`/login`)
- **Type**: Cookie-based Authentication
- **Features**:
  - 테스트 계정: `user123` / `password`
  - 세션 쿠키 관리
  - Protected routes
- **Challenge**: 로그인 자동화, 세션 유지

#### 5. **Product Details** (`/product/[1-28]`)
- **Type**: Individual Product Pages
- **Features**:
  - 상세 정보
  - 리뷰 섹션
  - 관련 제품
  - Variants 선택
- **Challenge**: 동적 URL 처리, 중첩 데이터 추출

---

## 🔌 API Endpoints

### REST API

#### Products API
```http
GET /api/products
```
- **Parameters**:
  - `page`: 1-6 (페이지 번호)
  - `order`: `asc` | `desc` (가격 정렬)
  - `category`: 제품 카테고리
- **Response**: JSON array of products

```http
GET /api/product?product_id={id}
```
- **Parameters**:
  - `product_id`: 1-28
- **Response**: Single product details

#### Reviews API
```http
GET /api/reviews
```
- **Requirements**: CSRF token
- **Parameters**:
  - `product_id`: 1-28
  - `page`: 페이지 번호
  - `order`: 정렬 방식

```http
GET /api/review?product_id={id}
```
- **Parameters**:
  - `product_id`: 1-28
- **Response**: Product reviews

#### Authentication API
```http
POST /api/login
```
- **Body**: 
  ```json
  {
    "username": "user123",
    "password": "password"
  }
  ```
- **Response**: Auth cookie

```http
GET /api/logout
```
- **Effect**: Clears auth cookie

### GraphQL API
```http
POST /api/graphql
```
- **Endpoint**: GraphQL queries for products and reviews
- **Schema**: Available at `/docs`

---

## 🎯 Built-in Challenges

### 1. **Paging Techniques**
- Static pagination
- Infinite scroll
- Load more buttons
- Offset/limit patterns

### 2. **Secret API Token Access**
- Hidden API endpoints
- Token extraction from JavaScript
- API key discovery

### 3. **GraphQL Background Requests**
- GraphQL query construction
- Subscription handling
- Batched queries

### 4. **Forced New Tab Links**
- `target="_blank"` handling
- Pop-up windows
- Multiple window management

### 5. **Hidden Web Data**
- Data in JavaScript variables
- JSON-LD structured data
- Meta tags
- Hidden form fields

### 6. **Local Storage**
- Reading localStorage
- Session storage
- IndexedDB access

### 7. **CSRF Token Locks**
- Token extraction
- Token refresh
- Header injection

### 8. **Cookie-based Authentication**
- Login automation
- Session management
- Cookie persistence

### 9. **PDF Downloads**
- Binary file handling
- Download management
- PDF parsing

### 10. **Cookie Popup**
- Consent handling
- Banner dismissal
- GDPR compliance

### 11. **Blocking Mechanisms**
- Rate limiting (`/blocked`)
- IP blocking
- User-agent detection
- Bot detection

---

## 📖 Documentation & Resources

### Official Documentation
- **API Docs**: `/docs` - Swagger/OpenAPI documentation
- **OpenAPI Spec**: `/openapi.json` - Machine-readable API specification
- **Sitemap**: `/sitemap.xml` - Complete site structure
- **Robots.txt**: `/robots.txt` - Crawling guidelines

### External Resources
- **ScrapFly Docs**: Official documentation
- **ScrapFly Academy**: Structured learning curriculum
- **ScrapFly Blog**: Tutorials and case studies

---

## 🧪 Practice Scenarios

### Beginner Level
1. **Basic Product Scraping**
   - URL: `/products`
   - Skills: CSS selectors, pagination
   - Goal: Extract all 28 products

2. **Simple API Usage**
   - URL: `/api/products`
   - Skills: HTTP requests, JSON parsing
   - Goal: Retrieve products via API

3. **Static Content Extraction**
   - URL: `/product/1`
   - Skills: HTML parsing, data extraction
   - Goal: Extract product details

### Intermediate Level
1. **Infinite Scroll Handling**
   - URL: `/testimonials`
   - Skills: Scroll automation, dynamic content
   - Goal: Load all testimonials

2. **Authentication Flow**
   - URL: `/login` → `/products`
   - Skills: Form submission, cookie management
   - Goal: Access protected content

3. **CSRF Token Management**
   - URL: `/reviews`
   - Skills: Token extraction, header management
   - Goal: Submit reviews with CSRF

### Advanced Level
1. **GraphQL Mastery**
   - URL: `/api/graphql`
   - Skills: GraphQL queries, mutations
   - Goal: Complex data retrieval

2. **Multi-Modal Scraping**
   - Multiple endpoints
   - Skills: API + HTML scraping combination
   - Goal: Complete data aggregation

3. **Anti-Bot Bypass**
   - URL: `/blocked`
   - Skills: Headers, proxies, rate limiting
   - Goal: Avoid detection

---

## 💻 Code Examples

### Basic Scraping (Python + Playwright)
```python
from playwright.async_api import async_playwright

async def scrape_products():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Navigate to products page
        await page.goto("https://web-scraping.dev/products")
        
        # Extract product data
        products = await page.query_selector_all(".product-item")
        for product in products:
            title = await product.query_selector(".product-name")
            price = await product.query_selector(".product-price")
            print(f"{await title.text_content()} - {await price.text_content()}")
        
        await browser.close()
```

### API Access (Python + Requests)
```python
import requests

# Get products via API
response = requests.get("https://web-scraping.dev/api/products?page=1")
products = response.json()

for product in products:
    print(f"{product['name']} - ${product['price']}")
```

### GraphQL Query (Python)
```python
import requests

query = """
query GetProducts {
  products(page: 1) {
    id
    name
    price
    reviews {
      rating
      comment
    }
  }
}
"""

response = requests.post(
    "https://web-scraping.dev/api/graphql",
    json={"query": query}
)
data = response.json()
```

### Infinite Scroll (Playwright)
```python
async def handle_infinite_scroll(page):
    await page.goto("https://web-scraping.dev/testimonials")
    
    # Scroll until no new content loads
    previous_height = 0
    while True:
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)
        previous_height = current_height
    
    # Extract all testimonials
    testimonials = await page.query_selector_all(".testimonial")
    return testimonials
```

---

## 🎯 Testing Checklist

### Phase 1: Basic Skills
- [ ] Navigate to `/products`
- [ ] Extract product titles and prices
- [ ] Handle pagination (pages 1-6)
- [ ] Use `/api/products` endpoint
- [ ] Parse JSON responses

### Phase 2: Dynamic Content
- [ ] Handle infinite scroll at `/testimonials`
- [ ] Process lazy-loaded images
- [ ] Click "Load More" button at `/reviews`
- [ ] Wait for AJAX content
- [ ] Monitor network requests

### Phase 3: Authentication
- [ ] Submit login form
- [ ] Store authentication cookies
- [ ] Access protected routes
- [ ] Maintain session across requests
- [ ] Handle logout

### Phase 4: Advanced Features
- [ ] Extract CSRF tokens
- [ ] Make GraphQL queries
- [ ] Handle local storage
- [ ] Download PDF files
- [ ] Bypass rate limiting

### Phase 5: Anti-Bot Measures
- [ ] Rotate user agents
- [ ] Implement delays
- [ ] Use proxy rotation
- [ ] Handle `/blocked` scenarios
- [ ] Implement retry logic

---

## 🔧 Best Practices

### Rate Limiting
```python
import time
import random

# Add random delays between requests
time.sleep(random.uniform(1, 3))

# Respect rate limits
MAX_REQUESTS_PER_MINUTE = 30
```

### Error Handling
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def scrape_with_retry(url):
    # Your scraping code here
    pass
```

### Session Management
```python
import aiohttp

# Maintain session for multiple requests
async with aiohttp.ClientSession() as session:
    # Login
    await session.post("/api/login", data=credentials)
    
    # Use same session for subsequent requests
    response = await session.get("/api/products")
```

---

## 📊 Performance Metrics

### Target Benchmarks
- **Success Rate**: >95%
- **Average Response Time**: <2s
- **Error Rate**: <5%
- **Data Accuracy**: 100%

### Monitoring Points
1. Request success/failure rates
2. Response times
3. Data completeness
4. Error types and frequencies
5. Rate limit hits

---

## 🚀 Progressive Learning Path

### Week 1: Fundamentals
1. Static HTML scraping (`/products`)
2. CSS selector mastery
3. Basic API usage
4. JSON parsing

### Week 2: Dynamic Content
1. JavaScript rendering
2. Infinite scroll (`/testimonials`)
3. AJAX handling (`/reviews`)
4. Network monitoring

### Week 3: Authentication & Sessions
1. Form submission (`/login`)
2. Cookie management
3. Session persistence
4. Protected route access

### Week 4: Advanced Techniques
1. GraphQL queries (`/api/graphql`)
2. CSRF token handling
3. Local storage access
4. Multi-format data extraction

### Week 5: Anti-Bot & Optimization
1. Rate limiting strategies
2. Proxy implementation
3. User-agent rotation
4. Error recovery

---

## 🎓 Certification Path

### Level 1: Basic Scraper
- Complete all `/products` challenges
- Successfully use all REST API endpoints
- Handle basic pagination

### Level 2: Dynamic Content Handler
- Master infinite scroll
- Handle all AJAX patterns
- Process lazy-loaded content

### Level 3: Authentication Expert
- Implement full login flow
- Manage sessions effectively
- Handle CSRF tokens

### Level 4: Advanced Practitioner
- Use GraphQL effectively
- Bypass anti-bot measures
- Implement robust error handling

### Level 5: Master Scraper
- Complete all challenges
- Achieve >95% success rate
- Optimize for performance

---

## 🔗 Additional Resources

### Related Tools
- **Playwright Inspector**: Debug selectors
- **Chrome DevTools**: Network analysis
- **Postman**: API testing
- **GraphQL Playground**: Query testing

### Community
- ScrapFly Discord
- Web Scraping Reddit
- Stack Overflow tags: `web-scraping`, `playwright`, `beautifulsoup`

### Further Learning
- ScrapFly Academy courses
- Official Playwright documentation
- Python `requests` documentation
- GraphQL specification

---

*Last updated: 2025-08-09*
*web-scraping.dev is continuously updated with new challenges and features.*
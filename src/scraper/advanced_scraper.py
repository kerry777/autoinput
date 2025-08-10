# -*- coding: utf-8 -*-
"""
고급 웹 스크래핑 모듈
web-scraping.dev에서 학습한 기술들을 모듈화
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from dataclasses import dataclass
from enum import Enum

class ScrapingMethod(Enum):
    """스크래핑 방법 열거형"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    API = "api"
    HYBRID = "hybrid"

@dataclass
class ScrapingTarget:
    """스크래핑 대상 정보"""
    url: str
    method: ScrapingMethod
    requires_auth: bool = False
    has_pagination: bool = False
    has_anti_bot: bool = False

class AdvancedScraper:
    """고급 웹 스크래핑 클래스"""
    
    def __init__(self, base_url: str = "https://web-scraping.dev"):
        self.base_url = base_url
        self.session = requests.Session()
        self._setup_headers()
        self.rate_limit_delay = 0.5
        
    def _setup_headers(self):
        """기본 헤더 설정"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def scrape_with_pagination(self, url_pattern: str, max_pages: int = None) -> List[Dict]:
        """페이지네이션이 있는 페이지 스크래핑"""
        all_data = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
            
            url = url_pattern.format(page=page)
            response = self.session.get(url)
            
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            data = self._extract_products(soup)
            
            if not data:
                break
            
            all_data.extend(data)
            print(f"  📄 페이지 {page}: {len(data)}개 항목 수집")
            
            page += 1
            time.sleep(self.rate_limit_delay)
        
        return all_data
    
    def _extract_products(self, soup: BeautifulSoup) -> List[Dict]:
        """제품 정보 추출"""
        products = []
        
        # 다양한 셀렉터 시도
        selectors = [
            ('div.product', 'h3', 'span.price'),
            ('article.product-card', 'h2', 'p.price'),
            ('li.product-item', 'a.title', 'span.cost')
        ]
        
        for container_sel, title_sel, price_sel in selectors:
            containers = soup.select(container_sel)
            if containers:
                for container in containers:
                    title = container.select_one(title_sel)
                    price = container.select_one(price_sel)
                    
                    if title:
                        product = {
                            'title': title.text.strip(),
                            'price': price.text.strip() if price else 'N/A'
                        }
                        
                        # 추가 정보 추출
                        img = container.select_one('img')
                        if img:
                            product['image'] = urljoin(self.base_url, img.get('src', ''))
                        
                        link = container.select_one('a[href]')
                        if link:
                            product['url'] = urljoin(self.base_url, link['href'])
                        
                        products.append(product)
                break
        
        return products
    
    def scrape_api(self, endpoint: str, params: Dict = None) -> Any:
        """API 엔드포인트 스크래핑"""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # JSON 응답 처리
            if 'application/json' in response.headers.get('Content-Type', ''):
                data = response.json()
                
                # 다양한 API 응답 형식 처리
                if isinstance(data, dict):
                    # products 키가 있는 경우
                    if 'products' in data:
                        return data['products']
                    # data 키가 있는 경우
                    elif 'data' in data:
                        return data['data']
                    # results 키가 있는 경우
                    elif 'results' in data:
                        return data['results']
                    else:
                        return data
                elif isinstance(data, list):
                    return data
                else:
                    return data
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            return None
    
    def extract_hidden_data(self, url: str) -> Dict:
        """숨겨진 데이터 추출"""
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        hidden_data = {}
        
        # 1. JavaScript 변수에서 추출
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # window.* 패턴 찾기
                window_vars = re.findall(r'window\.(\w+)\s*=\s*({[^}]+}|\[[^\]]+\])', script.string)
                for var_name, var_value in window_vars:
                    try:
                        hidden_data[f'js_{var_name}'] = json.loads(var_value)
                    except:
                        hidden_data[f'js_{var_name}'] = var_value
                
                # var/let/const 변수 찾기
                js_vars = re.findall(r'(?:var|let|const)\s+(\w+)\s*=\s*({[^}]+}|\[[^\]]+\])', script.string)
                for var_name, var_value in js_vars:
                    try:
                        hidden_data[f'var_{var_name}'] = json.loads(var_value)
                    except:
                        hidden_data[f'var_{var_name}'] = var_value
        
        # 2. data-* 속성에서 추출
        elements_with_data = soup.find_all(attrs=lambda x: x and x.startswith('data-'))
        for elem in elements_with_data:
            for attr, value in elem.attrs.items():
                if attr.startswith('data-'):
                    hidden_data[attr] = value
        
        # 3. JSON-LD 구조화 데이터
        json_ld = soup.find_all('script', type='application/ld+json')
        for idx, script in enumerate(json_ld):
            try:
                hidden_data[f'json_ld_{idx}'] = json.loads(script.string)
            except:
                pass
        
        # 4. 메타 태그
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('property'):
                hidden_data[f"meta_{meta['property']}"] = meta.get('content', '')
            elif meta.get('name'):
                hidden_data[f"meta_{meta['name']}"] = meta.get('content', '')
        
        return hidden_data
    
    def handle_infinite_scroll(self, url: str, max_items: int = 50) -> List[Dict]:
        """무한 스크롤 처리 (API 호출 시뮬레이션)"""
        items = []
        page = 1
        per_page = 10
        
        while len(items) < max_items:
            # 실제로는 JavaScript 실행이 필요하지만, API 호출로 시뮬레이션
            api_url = f"{url}/api/items"
            params = {
                'page': page,
                'per_page': per_page
            }
            
            data = self.scrape_api(api_url, params)
            
            if not data:
                break
            
            items.extend(data)
            page += 1
            time.sleep(self.rate_limit_delay)
        
        return items[:max_items]
    
    def bypass_cloudflare(self, url: str) -> Optional[str]:
        """Cloudflare 우회 시도 (기본적인 방법)"""
        # 실제 Cloudflare 우회는 더 복잡한 기술이 필요
        # 여기서는 기본적인 방법만 구현
        
        headers = self.session.headers.copy()
        headers.update({
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
        
        try:
            response = self.session.get(url, headers=headers)
            
            # Cloudflare 체크
            if 'cf-ray' in response.headers:
                print("⚠️ Cloudflare 감지됨")
                # 여기에 추가 우회 로직 구현 가능
            
            return response.text
            
        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            return None
    
    def scrape_with_cookies(self, url: str, cookies: Dict) -> Optional[str]:
        """쿠키를 사용한 스크래핑"""
        self.session.cookies.update(cookies)
        
        try:
            response = self.session.get(url)
            return response.text
        except Exception as e:
            print(f"❌ 쿠키 스크래핑 실패: {e}")
            return None
    
    def scrape_with_referer(self, url: str, referer: str) -> Optional[str]:
        """Referer 헤더를 사용한 스크래핑"""
        headers = {'Referer': referer}
        
        try:
            response = self.session.get(url, headers=headers)
            return response.text
        except Exception as e:
            print(f"❌ Referer 스크래핑 실패: {e}")
            return None

class ScrapingOrchestrator:
    """스크래핑 작업 조율자"""
    
    def __init__(self):
        self.scraper = AdvancedScraper()
        self.targets = []
    
    def add_target(self, target: ScrapingTarget):
        """스크래핑 대상 추가"""
        self.targets.append(target)
    
    def execute(self) -> Dict[str, Any]:
        """모든 대상 스크래핑 실행"""
        results = {}
        
        for target in self.targets:
            print(f"\n🎯 스크래핑: {target.url}")
            
            if target.method == ScrapingMethod.API:
                data = self.scraper.scrape_api(target.url)
            elif target.has_pagination:
                data = self.scraper.scrape_with_pagination(target.url)
            else:
                response = self.scraper.session.get(target.url)
                soup = BeautifulSoup(response.text, 'html.parser')
                data = self.scraper._extract_products(soup)
            
            results[target.url] = data
            time.sleep(0.5)
        
        return results

# 사용 예제
if __name__ == "__main__":
    # 고급 스크래퍼 초기화
    scraper = AdvancedScraper()
    
    print("🚀 고급 웹 스크래핑 모듈 테스트")
    print("=" * 80)
    
    # 1. API 스크래핑
    print("\n📡 API 스크래핑:")
    api_data = scraper.scrape_api('/api/products')
    if api_data:
        print(f"  ✅ {len(api_data) if isinstance(api_data, list) else 1}개 데이터 수집")
    
    # 2. 페이지네이션
    print("\n📄 페이지네이션 스크래핑:")
    products = scraper.scrape_with_pagination(
        "https://web-scraping.dev/products?page={page}",
        max_pages=2
    )
    print(f"  ✅ 총 {len(products)}개 제품 수집")
    
    # 3. 숨겨진 데이터
    print("\n🔐 숨겨진 데이터 추출:")
    hidden = scraper.extract_hidden_data("https://web-scraping.dev/products/1")
    print(f"  ✅ {len(hidden)}개 숨겨진 데이터 발견")
    
    print("\n" + "=" * 80)
    print("✨ 고급 스크래핑 모듈 준비 완료!")
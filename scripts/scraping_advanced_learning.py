# -*- coding: utf-8 -*-
"""
web-scraping.dev 고급 기능 학습 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Any
import time

class WebScrapingDevExplorer:
    """web-scraping.dev 사이트 탐색 및 학습"""
    
    def __init__(self):
        self.base_url = "https://web-scraping.dev"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def explore_challenges(self) -> Dict[str, List[str]]:
        """모든 챌린지 카테고리와 링크 수집"""
        print("\n🔍 web-scraping.dev 챌린지 탐색 중...")
        
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        challenges = {
            'paging': [],
            'authentication': [],
            'data_extraction': [],
            'anti_scraping': [],
            'dynamic_content': []
        }
        
        # 모든 챌린지 링크 찾기
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # 카테고리별 분류
            if 'page' in href.lower() or 'paging' in href.lower():
                challenges['paging'].append({
                    'url': self.base_url + href if not href.startswith('http') else href,
                    'title': text
                })
            elif 'login' in href.lower() or 'auth' in href.lower() or 'csrf' in href.lower():
                challenges['authentication'].append({
                    'url': self.base_url + href if not href.startswith('http') else href,
                    'title': text
                })
            elif 'block' in href.lower() or 'redirect' in href.lower():
                challenges['anti_scraping'].append({
                    'url': self.base_url + href if not href.startswith('http') else href,
                    'title': text
                })
            elif 'json' in href.lower() or 'pdf' in href.lower() or 'storage' in href.lower():
                challenges['data_extraction'].append({
                    'url': self.base_url + href if not href.startswith('http') else href,
                    'title': text
                })
            elif 'scroll' in href.lower() or 'load' in href.lower() or 'graphql' in href.lower():
                challenges['dynamic_content'].append({
                    'url': self.base_url + href if not href.startswith('http') else href,
                    'title': text
                })
        
        return challenges
    
    def test_product_api(self) -> Dict[str, Any]:
        """Product API 테스트"""
        print("\n🔌 Product API 테스트...")
        
        # 제품 목록 가져오기
        api_url = f"{self.base_url}/api/products"
        response = self.session.get(api_url)
        
        if response.status_code == 200:
            products = response.json()
            print(f"✅ {len(products)} 개 제품 발견")
            
            # 첫 번째 제품 상세 정보
            if products:
                first_product = products[0]
                detail_url = f"{self.base_url}/api/products/{first_product.get('id', 1)}"
                detail_response = self.session.get(detail_url)
                
                if detail_response.status_code == 200:
                    return detail_response.json()
        
        return {}
    
    def test_pagination(self) -> List[Dict]:
        """페이지네이션 테스트"""
        print("\n📄 페이지네이션 테스트...")
        
        all_products = []
        page = 1
        max_pages = 3  # 데모용으로 3페이지만
        
        while page <= max_pages:
            url = f"{self.base_url}/products?page={page}"
            response = self.session.get(url)
            
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.find_all('div', class_='product')
            
            if not products:
                break
            
            print(f"  페이지 {page}: {len(products)}개 제품")
            
            for product in products:
                title = product.find('h3')
                price = product.find('span', class_='price')
                
                if title and price:
                    all_products.append({
                        'title': title.text.strip(),
                        'price': price.text.strip()
                    })
            
            page += 1
            time.sleep(0.5)  # Rate limiting
        
        return all_products
    
    def test_hidden_data(self) -> Dict:
        """숨겨진 데이터 추출 테스트"""
        print("\n🔐 숨겨진 데이터 추출 테스트...")
        
        url = f"{self.base_url}/products/1"
        response = self.session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        hidden_data = {}
        
        # JavaScript 변수에서 데이터 추출
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.' in script.string:
                # window.productData 같은 패턴 찾기
                lines = script.string.split('\n')
                for line in lines:
                    if 'window.' in line and '=' in line:
                        try:
                            # 간단한 파싱 (실제로는 더 정교한 방법 필요)
                            var_name = line.split('window.')[1].split('=')[0].strip()
                            var_value = line.split('=')[1].strip().rstrip(';')
                            
                            # JSON 파싱 시도
                            if var_value.startswith('{') or var_value.startswith('['):
                                try:
                                    hidden_data[var_name] = json.loads(var_value)
                                except:
                                    hidden_data[var_name] = var_value
                        except:
                            pass
        
        # data 속성에서 데이터 추출
        elements_with_data = soup.find_all(attrs={"data-product-id": True})
        for elem in elements_with_data:
            hidden_data['product_id'] = elem.get('data-product-id')
        
        return hidden_data
    
    def generate_report(self, challenges: Dict, api_data: Dict, products: List, hidden: Dict):
        """학습 결과 리포트 생성"""
        print("\n" + "=" * 80)
        print("📊 web-scraping.dev 학습 리포트")
        print("=" * 80)
        
        # 챌린지 요약
        print("\n🎯 발견된 챌린지:")
        for category, items in challenges.items():
            if items:
                print(f"\n  {category.upper()} ({len(items)}개):")
                for item in items[:3]:  # 각 카테고리별 3개만 표시
                    print(f"    • {item['title']}")
        
        # API 데이터
        if api_data:
            print(f"\n🔌 API 데이터 예시:")
            print(f"  제품명: {api_data.get('name', 'N/A')}")
            print(f"  가격: ${api_data.get('price', 'N/A')}")
        
        # 페이지네이션 결과
        if products:
            print(f"\n📄 페이지네이션 결과:")
            print(f"  총 {len(products)}개 제품 수집")
            if products:
                print(f"  첫 제품: {products[0]['title']} - {products[0]['price']}")
        
        # 숨겨진 데이터
        if hidden:
            print(f"\n🔐 숨겨진 데이터 발견:")
            for key, value in list(hidden.items())[:3]:
                print(f"  {key}: {str(value)[:50]}...")
        
        print("\n" + "=" * 80)

def main():
    """메인 실행 함수"""
    explorer = WebScrapingDevExplorer()
    
    # 1. 챌린지 탐색
    challenges = explorer.explore_challenges()
    
    # 2. API 테스트
    api_data = explorer.test_product_api()
    
    # 3. 페이지네이션 테스트
    products = explorer.test_pagination()
    
    # 4. 숨겨진 데이터 추출
    hidden_data = explorer.test_hidden_data()
    
    # 5. 리포트 생성
    explorer.generate_report(challenges, api_data, products, hidden_data)
    
    print("\n✅ 학습 완료! 다음 단계로 모듈화를 진행합니다.")

if __name__ == "__main__":
    main()
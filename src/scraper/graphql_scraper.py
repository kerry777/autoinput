# -*- coding: utf-8 -*-
"""
GraphQL 스크래핑 전문 모듈
"""
import requests
import json
from typing import Dict, List, Any, Optional
import hashlib
import time
from dataclasses import dataclass

@dataclass
class GraphQLQuery:
    """GraphQL 쿼리 객체"""
    query: str
    variables: Dict = None
    operation_name: str = None

class GraphQLScraper:
    """GraphQL API 스크래핑 전문 클래스"""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.query_cache = {}
    
    def execute_query(self, query: GraphQLQuery) -> Dict:
        """GraphQL 쿼리 실행"""
        # 캐시 키 생성
        cache_key = self._generate_cache_key(query)
        
        # 캐시 확인
        if cache_key in self.query_cache:
            print(f"📦 캐시에서 로드: {cache_key[:8]}...")
            return self.query_cache[cache_key]
        
        # 요청 페이로드 구성
        payload = {
            'query': query.query
        }
        
        if query.variables:
            payload['variables'] = query.variables
        
        if query.operation_name:
            payload['operationName'] = query.operation_name
        
        # 요청 실행
        try:
            response = self.session.post(
                self.endpoint,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # 에러 체크
            if 'errors' in data:
                print(f"⚠️ GraphQL 에러: {data['errors']}")
            
            # 캐시 저장
            self.query_cache[cache_key] = data
            
            return data
            
        except Exception as e:
            print(f"❌ 쿼리 실행 실패: {e}")
            return {}
    
    def _generate_cache_key(self, query: GraphQLQuery) -> str:
        """쿼리 캐시 키 생성"""
        key_data = f"{query.query}{json.dumps(query.variables or {})}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def introspect_schema(self) -> Dict:
        """GraphQL 스키마 자동 탐색"""
        introspection_query = GraphQLQuery(
            query="""
            query IntrospectionQuery {
                __schema {
                    types {
                        name
                        kind
                        description
                        fields {
                            name
                            type {
                                name
                                kind
                            }
                        }
                    }
                    queryType {
                        name
                        fields {
                            name
                            description
                            args {
                                name
                                type {
                                    name
                                }
                            }
                        }
                    }
                    mutationType {
                        name
                    }
                }
            }
            """
        )
        
        return self.execute_query(introspection_query)
    
    def paginate_query(self, base_query: str, page_size: int = 20, max_pages: int = None) -> List[Dict]:
        """페이지네이션 처리"""
        all_results = []
        has_next_page = True
        cursor = None
        page = 0
        
        while has_next_page:
            if max_pages and page >= max_pages:
                break
            
            # 커서 기반 페이지네이션 쿼리
            variables = {
                'first': page_size,
                'after': cursor
            }
            
            query = GraphQLQuery(
                query=base_query,
                variables=variables
            )
            
            result = self.execute_query(query)
            
            if 'data' in result:
                # 데이터 추출 (구조에 따라 조정 필요)
                edges = self._extract_edges(result['data'])
                all_results.extend(edges)
                
                # 페이지 정보 추출
                page_info = self._extract_page_info(result['data'])
                has_next_page = page_info.get('hasNextPage', False)
                cursor = page_info.get('endCursor')
                
                print(f"📄 페이지 {page + 1}: {len(edges)}개 항목")
            else:
                break
            
            page += 1
            time.sleep(0.5)  # Rate limiting
        
        return all_results
    
    def _extract_edges(self, data: Dict) -> List:
        """엣지 데이터 추출"""
        # 일반적인 GraphQL 구조 탐색
        for key, value in data.items():
            if isinstance(value, dict):
                if 'edges' in value:
                    return value['edges']
                elif 'nodes' in value:
                    return value['nodes']
                else:
                    # 재귀적 탐색
                    result = self._extract_edges(value)
                    if result:
                        return result
        
        return []
    
    def _extract_page_info(self, data: Dict) -> Dict:
        """페이지 정보 추출"""
        for key, value in data.items():
            if isinstance(value, dict):
                if 'pageInfo' in value:
                    return value['pageInfo']
                else:
                    result = self._extract_page_info(value)
                    if result:
                        return result
        
        return {}
    
    def batch_query(self, queries: List[GraphQLQuery]) -> List[Dict]:
        """배치 쿼리 실행"""
        results = []
        
        for query in queries:
            result = self.execute_query(query)
            results.append(result)
            time.sleep(0.1)  # Rate limiting
        
        return results
    
    def subscribe_to_updates(self, subscription_query: str):
        """GraphQL 구독 (WebSocket 필요)"""
        # 실제 구현은 websocket-client 또는 graphql-ws 필요
        print("⚠️ 구독 기능은 WebSocket 연결이 필요합니다")
        pass

class GraphQLAnalyzer:
    """GraphQL API 분석 도구"""
    
    def __init__(self, scraper: GraphQLScraper):
        self.scraper = scraper
    
    def analyze_api(self) -> Dict:
        """API 구조 분석"""
        print("\n🔍 GraphQL API 분석 중...")
        
        # 스키마 탐색
        schema = self.scraper.introspect_schema()
        
        analysis = {
            'types': [],
            'queries': [],
            'mutations': [],
            'subscriptions': []
        }
        
        if 'data' in schema and '__schema' in schema['data']:
            schema_data = schema['data']['__schema']
            
            # 타입 분석
            for type_info in schema_data.get('types', []):
                if not type_info['name'].startswith('__'):
                    analysis['types'].append({
                        'name': type_info['name'],
                        'kind': type_info['kind'],
                        'fields': len(type_info.get('fields', []) or [])
                    })
            
            # 쿼리 분석
            if schema_data.get('queryType'):
                query_type = schema_data['queryType']
                for field in query_type.get('fields', []):
                    analysis['queries'].append({
                        'name': field['name'],
                        'description': field.get('description', ''),
                        'args': [arg['name'] for arg in field.get('args', [])]
                    })
        
        return analysis
    
    def find_pagination_pattern(self, sample_query_result: Dict) -> str:
        """페이지네이션 패턴 자동 감지"""
        patterns = []
        
        def search_pattern(obj, path=""):
            if isinstance(obj, dict):
                if 'pageInfo' in obj:
                    patterns.append(f"{path}.pageInfo")
                if 'edges' in obj and 'nodes' in obj:
                    patterns.append(f"{path} (Relay pattern)")
                if 'hasNextPage' in obj or 'endCursor' in obj:
                    patterns.append(f"{path} (Cursor-based)")
                if 'page' in obj or 'totalPages' in obj:
                    patterns.append(f"{path} (Page-based)")
                
                for key, value in obj.items():
                    search_pattern(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list) and obj:
                search_pattern(obj[0], f"{path}[0]")
        
        search_pattern(sample_query_result)
        
        if patterns:
            print(f"✅ 페이지네이션 패턴 발견: {patterns[0]}")
            return patterns[0]
        else:
            print("❌ 페이지네이션 패턴을 찾을 수 없습니다")
            return ""

# 실전 예제: 전자상거래 GraphQL API
class EcommerceGraphQLScraper:
    """전자상거래 특화 GraphQL 스크래퍼"""
    
    def __init__(self, endpoint: str):
        self.scraper = GraphQLScraper(endpoint)
    
    def get_products(self, category_id: str = None, limit: int = 100) -> List[Dict]:
        """제품 목록 가져오기"""
        query = """
        query GetProducts($first: Int!, $after: String, $categoryId: ID) {
            products(first: $first, after: $after, categoryId: $categoryId) {
                edges {
                    node {
                        id
                        name
                        price
                        description
                        images {
                            url
                        }
                        category {
                            id
                            name
                        }
                        inventory {
                            available
                        }
                        reviews {
                            rating
                            count
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
                totalCount
            }
        }
        """
        
        return self.scraper.paginate_query(query, page_size=20, max_pages=limit//20)
    
    def get_product_details(self, product_id: str) -> Dict:
        """제품 상세 정보"""
        query = GraphQLQuery(
            query="""
            query GetProductDetails($id: ID!) {
                product(id: $id) {
                    id
                    name
                    price
                    originalPrice
                    description
                    specifications {
                        key
                        value
                    }
                    images {
                        url
                        alt
                    }
                    variants {
                        id
                        name
                        price
                        available
                    }
                    relatedProducts {
                        id
                        name
                        price
                        image
                    }
                }
            }
            """,
            variables={'id': product_id}
        )
        
        return self.scraper.execute_query(query)
    
    def search_products(self, query_text: str, filters: Dict = None) -> List[Dict]:
        """제품 검색"""
        query = GraphQLQuery(
            query="""
            query SearchProducts($query: String!, $filters: ProductFilters) {
                search(query: $query, filters: $filters) {
                    products {
                        id
                        name
                        price
                        image
                        relevanceScore
                    }
                    facets {
                        category {
                            name
                            count
                        }
                        priceRange {
                            min
                            max
                        }
                        brands {
                            name
                            count
                        }
                    }
                    totalResults
                }
            }
            """,
            variables={
                'query': query_text,
                'filters': filters or {}
            }
        )
        
        result = self.scraper.execute_query(query)
        return result.get('data', {}).get('search', {}).get('products', [])

# 사용 예제
if __name__ == "__main__":
    print("🚀 GraphQL 스크래핑 고급 기법")
    print("=" * 80)
    
    # web-scraping.dev GraphQL 엔드포인트 (예제)
    endpoint = "https://web-scraping.dev/api/graphql"
    
    # GraphQL 스크래퍼 초기화
    scraper = GraphQLScraper(endpoint)
    
    # 1. 스키마 탐색
    print("\n📊 스키마 탐색:")
    schema = scraper.introspect_schema()
    if schema:
        print("  ✅ 스키마 정보 수집 완료")
    
    # 2. 간단한 쿼리 실행
    print("\n📡 쿼리 실행:")
    simple_query = GraphQLQuery(
        query="""
        query {
            products(first: 5) {
                edges {
                    node {
                        id
                        name
                        price
                    }
                }
            }
        }
        """
    )
    
    result = scraper.execute_query(simple_query)
    if result:
        print(f"  ✅ 쿼리 실행 성공")
    
    # 3. API 분석
    analyzer = GraphQLAnalyzer(scraper)
    analysis = analyzer.analyze_api()
    
    print(f"\n📈 API 분석 결과:")
    print(f"  • 타입: {len(analysis['types'])}개")
    print(f"  • 쿼리: {len(analysis['queries'])}개")
    print(f"  • 뮤테이션: {len(analysis['mutations'])}개")
    
    print("\n✨ GraphQL 스크래핑 모듈 준비 완료!")
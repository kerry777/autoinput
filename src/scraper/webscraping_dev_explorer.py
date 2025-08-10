# -*- coding: utf-8 -*-
"""
web-scraping.dev 완벽 탐색 및 학습 모듈
모든 챌린지와 시나리오를 체계적으로 학습
"""
import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re
from urllib.parse import urljoin, urlparse

class ChallengeType(Enum):
    """챌린지 유형"""
    PAGING = "paging"
    AUTH = "authentication"
    DATA_EXTRACTION = "data_extraction"
    ANTI_SCRAPING = "anti_scraping"
    DYNAMIC = "dynamic_content"
    API = "api"
    ADVANCED = "advanced"

@dataclass
class Challenge:
    """챌린지 정보"""
    name: str
    url: str
    type: ChallengeType
    difficulty: str
    description: str
    solution: Dict = None
    learned: bool = False

class WebScrapingDevMaster:
    """web-scraping.dev 완벽 마스터 클래스"""
    
    def __init__(self):
        self.base_url = "https://web-scraping.dev"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.challenges = []
        self.solutions = {}
        
    def discover_all_challenges(self) -> List[Challenge]:
        """모든 챌린지 발견 및 분류"""
        print("\n🔍 web-scraping.dev 전체 챌린지 탐색 중...")
        
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 모든 챌린지 섹션 찾기
        challenge_sections = {
            'paging': self._find_paging_challenges(soup),
            'auth': self._find_auth_challenges(soup),
            'data': self._find_data_challenges(soup),
            'anti': self._find_anti_scraping_challenges(soup),
            'dynamic': self._find_dynamic_challenges(soup)
        }
        
        # 챌린지 객체 생성
        for category, items in challenge_sections.items():
            for item in items:
                challenge = Challenge(
                    name=item['name'],
                    url=item['url'],
                    type=self._get_challenge_type(category),
                    difficulty=item.get('difficulty', 'medium'),
                    description=item.get('description', '')
                )
                self.challenges.append(challenge)
        
        print(f"✅ 총 {len(self.challenges)}개 챌린지 발견!")
        return self.challenges
    
    def _find_paging_challenges(self, soup) -> List[Dict]:
        """페이징 챌린지 찾기"""
        challenges = []
        
        # 페이징 관련 링크 패턴
        paging_patterns = [
            r'.*page.*', r'.*paging.*', r'.*pagination.*', 
            r'.*endless.*', r'.*infinite.*', r'.*scroll.*',
            r'.*load.*more.*'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            for pattern in paging_patterns:
                if re.match(pattern, href.lower()) or re.match(pattern, text.lower()):
                    challenges.append({
                        'name': text or href,
                        'url': urljoin(self.base_url, href),
                        'difficulty': self._assess_difficulty(text)
                    })
                    break
        
        return challenges
    
    def _find_auth_challenges(self, soup) -> List[Dict]:
        """인증 챌린지 찾기"""
        challenges = []
        
        auth_patterns = [
            r'.*login.*', r'.*auth.*', r'.*csrf.*',
            r'.*token.*', r'.*session.*', r'.*cookie.*'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            for pattern in auth_patterns:
                if re.match(pattern, href.lower()) or re.match(pattern, text.lower()):
                    challenges.append({
                        'name': text or href,
                        'url': urljoin(self.base_url, href),
                        'difficulty': 'hard' if 'csrf' in text.lower() else 'medium'
                    })
                    break
        
        return challenges
    
    def _find_data_challenges(self, soup) -> List[Dict]:
        """데이터 추출 챌린지 찾기"""
        challenges = []
        
        data_patterns = [
            r'.*json.*', r'.*hidden.*', r'.*extract.*',
            r'.*pdf.*', r'.*download.*', r'.*storage.*'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            for pattern in data_patterns:
                if re.match(pattern, href.lower()) or re.match(pattern, text.lower()):
                    challenges.append({
                        'name': text or href,
                        'url': urljoin(self.base_url, href),
                        'difficulty': 'medium'
                    })
                    break
        
        return challenges
    
    def _find_anti_scraping_challenges(self, soup) -> List[Dict]:
        """Anti-scraping 챌린지 찾기"""
        challenges = []
        
        anti_patterns = [
            r'.*block.*', r'.*protect.*', r'.*captcha.*',
            r'.*redirect.*', r'.*referer.*', r'.*rate.*limit.*'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            for pattern in anti_patterns:
                if re.match(pattern, href.lower()) or re.match(pattern, text.lower()):
                    challenges.append({
                        'name': text or href,
                        'url': urljoin(self.base_url, href),
                        'difficulty': 'hard'
                    })
                    break
        
        return challenges
    
    def _find_dynamic_challenges(self, soup) -> List[Dict]:
        """동적 콘텐츠 챌린지 찾기"""
        challenges = []
        
        dynamic_patterns = [
            r'.*javascript.*', r'.*ajax.*', r'.*spa.*',
            r'.*react.*', r'.*vue.*', r'.*angular.*',
            r'.*graphql.*', r'.*websocket.*'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            for pattern in dynamic_patterns:
                if re.match(pattern, href.lower()) or re.match(pattern, text.lower()):
                    challenges.append({
                        'name': text or href,
                        'url': urljoin(self.base_url, href),
                        'difficulty': 'hard'
                    })
                    break
        
        return challenges
    
    def _get_challenge_type(self, category: str) -> ChallengeType:
        """카테고리를 챌린지 타입으로 변환"""
        mapping = {
            'paging': ChallengeType.PAGING,
            'auth': ChallengeType.AUTH,
            'data': ChallengeType.DATA_EXTRACTION,
            'anti': ChallengeType.ANTI_SCRAPING,
            'dynamic': ChallengeType.DYNAMIC
        }
        return mapping.get(category, ChallengeType.ADVANCED)
    
    def _assess_difficulty(self, text: str) -> str:
        """난이도 평가"""
        hard_keywords = ['advanced', 'complex', 'csrf', 'captcha', 'graphql']
        easy_keywords = ['simple', 'basic', 'intro', 'static']
        
        text_lower = text.lower()
        
        for keyword in hard_keywords:
            if keyword in text_lower:
                return 'hard'
        
        for keyword in easy_keywords:
            if keyword in text_lower:
                return 'easy'
        
        return 'medium'
    
    def solve_challenge(self, challenge: Challenge) -> Dict:
        """챌린지 해결"""
        print(f"\n🎯 챌린지 해결: {challenge.name}")
        print(f"   URL: {challenge.url}")
        print(f"   유형: {challenge.type.value}")
        print(f"   난이도: {challenge.difficulty}")
        
        solution = {}
        
        try:
            if challenge.type == ChallengeType.PAGING:
                solution = self._solve_paging_challenge(challenge)
            elif challenge.type == ChallengeType.AUTH:
                solution = self._solve_auth_challenge(challenge)
            elif challenge.type == ChallengeType.DATA_EXTRACTION:
                solution = self._solve_data_challenge(challenge)
            elif challenge.type == ChallengeType.ANTI_SCRAPING:
                solution = self._solve_anti_scraping_challenge(challenge)
            elif challenge.type == ChallengeType.DYNAMIC:
                solution = self._solve_dynamic_challenge(challenge)
            else:
                solution = self._solve_advanced_challenge(challenge)
            
            challenge.solution = solution
            challenge.learned = True
            self.solutions[challenge.name] = solution
            
            print(f"   ✅ 해결 완료!")
            
        except Exception as e:
            print(f"   ❌ 해결 실패: {e}")
            solution = {'error': str(e)}
        
        return solution
    
    def _solve_paging_challenge(self, challenge: Challenge) -> Dict:
        """페이징 챌린지 해결"""
        solution = {
            'type': 'paging',
            'method': '',
            'code': '',
            'data': []
        }
        
        # 페이지 분석
        response = self.session.get(challenge.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 페이징 유형 감지
        if soup.find('button', text=re.compile('load more', re.I)):
            solution['method'] = 'load_more_button'
            solution['code'] = """
# Load More 버튼 처리
while True:
    load_more = soup.find('button', text='Load More')
    if not load_more:
        break
    # AJAX 요청 시뮬레이션
    next_url = load_more.get('data-url')
    response = session.post(next_url)
    new_items = response.json()['items']
    data.extend(new_items)
"""
        elif soup.find('div', {'class': re.compile('infinite|endless')}):
            solution['method'] = 'infinite_scroll'
            solution['code'] = """
# 무한 스크롤 처리
offset = 0
while True:
    api_url = f'/api/items?offset={offset}&limit=20'
    response = session.get(api_url)
    items = response.json()['items']
    if not items:
        break
    data.extend(items)
    offset += 20
"""
        else:
            solution['method'] = 'traditional_pagination'
            solution['code'] = """
# 전통적 페이지네이션
page = 1
while True:
    url = f'{base_url}?page={page}'
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    items = soup.find_all('div', class_='item')
    if not items:
        break
    data.extend(items)
    page += 1
"""
        
        return solution
    
    def _solve_auth_challenge(self, challenge: Challenge) -> Dict:
        """인증 챌린지 해결"""
        solution = {
            'type': 'authentication',
            'method': '',
            'code': '',
            'headers': {}
        }
        
        response = self.session.get(challenge.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 인증 유형 감지
        if 'csrf' in challenge.url.lower():
            csrf_token = soup.find('input', {'name': 'csrf_token'})
            if csrf_token:
                solution['method'] = 'csrf_token'
                solution['code'] = """
# CSRF 토큰 처리
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
login_data = {
    'username': 'user',
    'password': 'pass',
    'csrf_token': csrf_token
}
response = session.post(login_url, data=login_data)
"""
        elif 'cookie' in challenge.url.lower():
            solution['method'] = 'cookie_auth'
            solution['code'] = """
# 쿠키 인증
session.cookies.set('auth_token', 'secret_token')
response = session.get(protected_url)
"""
        elif 'api' in challenge.url.lower():
            solution['method'] = 'api_key'
            solution['headers'] = {'X-API-Key': 'your_api_key'}
            solution['code'] = """
# API 키 인증
headers = {'X-API-Key': 'your_api_key'}
response = session.get(api_url, headers=headers)
"""
        
        return solution
    
    def _solve_data_challenge(self, challenge: Challenge) -> Dict:
        """데이터 추출 챌린지 해결"""
        solution = {
            'type': 'data_extraction',
            'method': '',
            'code': '',
            'extracted_data': {}
        }
        
        response = self.session.get(challenge.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 숨겨진 데이터 찾기
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'window.' in script.string:
                # JavaScript 변수 추출
                matches = re.findall(r'window\.(\w+)\s*=\s*({.*?});', 
                                   script.string, re.DOTALL)
                for var_name, json_str in matches:
                    try:
                        data = json.loads(json_str)
                        solution['extracted_data'][var_name] = data
                        solution['method'] = 'javascript_extraction'
                    except:
                        pass
        
        # JSON-LD 데이터
        json_ld = soup.find_all('script', type='application/ld+json')
        if json_ld:
            solution['method'] = 'json_ld_extraction'
            for script in json_ld:
                try:
                    data = json.loads(script.string)
                    solution['extracted_data']['json_ld'] = data
                except:
                    pass
        
        solution['code'] = """
# 숨겨진 데이터 추출
# 1. JavaScript 변수
scripts = soup.find_all('script')
for script in scripts:
    if script.string:
        # window.* 패턴 찾기
        
# 2. data-* 속성
elements = soup.find_all(attrs={'data-product': True})
for elem in elements:
    product_data = json.loads(elem['data-product'])
    
# 3. JSON-LD
json_ld = soup.find('script', type='application/ld+json')
if json_ld:
    structured_data = json.loads(json_ld.string)
"""
        
        return solution
    
    def _solve_anti_scraping_challenge(self, challenge: Challenge) -> Dict:
        """Anti-scraping 챌린지 해결"""
        solution = {
            'type': 'anti_scraping',
            'method': '',
            'bypass_technique': '',
            'code': ''
        }
        
        # 다양한 우회 기법 시도
        if 'block' in challenge.url.lower():
            solution['method'] = 'blocking_bypass'
            solution['bypass_technique'] = 'User-Agent rotation + Headers'
            solution['code'] = """
# 차단 우회
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
response = session.get(url, headers=headers)
"""
        elif 'redirect' in challenge.url.lower():
            solution['method'] = 'redirect_handling'
            solution['bypass_technique'] = 'Follow redirects with session'
            solution['code'] = """
# 리디렉션 처리
session.max_redirects = 10
response = session.get(url, allow_redirects=True)
final_url = response.url
"""
        elif 'referer' in challenge.url.lower():
            solution['method'] = 'referer_spoofing'
            solution['bypass_technique'] = 'Set Referer header'
            solution['code'] = """
# Referer 헤더 설정
headers = {'Referer': 'https://google.com'}
response = session.get(url, headers=headers)
"""
        
        return solution
    
    def _solve_dynamic_challenge(self, challenge: Challenge) -> Dict:
        """동적 콘텐츠 챌린지 해결"""
        solution = {
            'type': 'dynamic_content',
            'method': '',
            'tools_needed': [],
            'code': ''
        }
        
        if 'graphql' in challenge.url.lower():
            solution['method'] = 'graphql_query'
            solution['tools_needed'] = ['requests', 'json']
            solution['code'] = """
# GraphQL 쿼리
query = '''
query GetProducts {
    products {
        id
        name
        price
    }
}
'''
response = session.post(
    graphql_endpoint,
    json={'query': query}
)
data = response.json()['data']['products']
"""
        elif 'spa' in challenge.url.lower() or 'react' in challenge.url.lower():
            solution['method'] = 'spa_scraping'
            solution['tools_needed'] = ['selenium', 'playwright']
            solution['code'] = """
# SPA 스크래핑 (Selenium)
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get(url)

# 동적 콘텐츠 대기
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'product'))
)

# 데이터 추출
products = driver.find_elements(By.CLASS_NAME, 'product')
"""
        else:
            solution['method'] = 'ajax_interception'
            solution['tools_needed'] = ['browser devtools', 'network analysis']
            solution['code'] = """
# AJAX 요청 직접 호출
# 1. DevTools에서 네트워크 요청 분석
# 2. API 엔드포인트 찾기
# 3. 직접 호출

api_url = '/api/data'
response = session.get(api_url)
data = response.json()
"""
        
        return solution
    
    def _solve_advanced_challenge(self, challenge: Challenge) -> Dict:
        """고급 챌린지 해결"""
        return {
            'type': 'advanced',
            'method': 'custom_solution',
            'note': 'Requires specific analysis',
            'code': '# Custom solution needed'
        }
    
    def generate_complete_report(self) -> str:
        """완전한 학습 리포트 생성"""
        report = []
        report.append("=" * 80)
        report.append("📚 web-scraping.dev 완벽 학습 리포트")
        report.append("=" * 80)
        
        # 챌린지 요약
        report.append(f"\n📊 전체 챌린지: {len(self.challenges)}개")
        report.append(f"✅ 학습 완료: {sum(1 for c in self.challenges if c.learned)}개")
        report.append(f"❌ 미학습: {sum(1 for c in self.challenges if not c.learned)}개")
        
        # 유형별 분류
        report.append("\n📂 유형별 챌린지:")
        for challenge_type in ChallengeType:
            count = sum(1 for c in self.challenges if c.type == challenge_type)
            learned = sum(1 for c in self.challenges if c.type == challenge_type and c.learned)
            report.append(f"  • {challenge_type.value}: {learned}/{count}")
        
        # 솔루션 상세
        report.append("\n🔧 학습한 솔루션:")
        for challenge in self.challenges:
            if challenge.learned and challenge.solution:
                report.append(f"\n### {challenge.name}")
                report.append(f"- URL: {challenge.url}")
                report.append(f"- 유형: {challenge.type.value}")
                report.append(f"- 방법: {challenge.solution.get('method', 'N/A')}")
                if 'code' in challenge.solution:
                    report.append(f"- 코드 스니펫 포함")
        
        return "\n".join(report)
    
    def export_solutions(self, filename: str = "webscraping_solutions.json"):
        """솔루션 내보내기"""
        export_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_challenges': len(self.challenges),
            'learned_challenges': sum(1 for c in self.challenges if c.learned),
            'solutions': {}
        }
        
        for challenge in self.challenges:
            if challenge.learned:
                export_data['solutions'][challenge.name] = {
                    'url': challenge.url,
                    'type': challenge.type.value,
                    'difficulty': challenge.difficulty,
                    'solution': challenge.solution
                }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 솔루션 저장 완료: {filename}")

# 실행 예제
if __name__ == "__main__":
    print("🚀 web-scraping.dev 완벽 마스터 프로그램")
    print("=" * 80)
    
    # 마스터 클래스 초기화
    master = WebScrapingDevMaster()
    
    # 1. 모든 챌린지 발견
    challenges = master.discover_all_challenges()
    
    # 2. 각 챌린지 해결 (데모: 처음 5개만)
    for challenge in challenges[:5]:
        master.solve_challenge(challenge)
        time.sleep(1)  # Rate limiting
    
    # 3. 리포트 생성
    report = master.generate_complete_report()
    print(report)
    
    # 4. 솔루션 저장
    master.export_solutions("webscraping_dev_solutions.json")
    
    print("\n✨ 학습 완료!")
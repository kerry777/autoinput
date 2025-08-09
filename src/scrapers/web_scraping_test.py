"""
Web-scraping.dev 테스트 모듈
실제 웹 스크래핑 시나리오를 테스트하고 재사용 가능한 패턴을 개발
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
from playwright.async_api import Page, Browser, async_playwright
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TestScenario:
    """테스트 시나리오 정의"""
    name: str
    url: str
    description: str
    selectors: Dict[str, str]
    expected_results: Dict[str, Any]

class WebScrapingTestSuite:
    """web-scraping.dev 테스트 스위트"""
    
    BASE_URL = "https://web-scraping.dev"
    
    # 테스트 시나리오 정의
    SCENARIOS = {
        "basic_table": TestScenario(
            name="Basic Table Scraping",
            url="/table",
            description="HTML 테이블 데이터 추출",
            selectors={
                "table": "table.table",
                "headers": "table.table thead th",
                "rows": "table.table tbody tr"
            },
            expected_results={"min_rows": 10}
        ),
        "infinite_scroll": TestScenario(
            name="Infinite Scroll",
            url="/infinite-scroll",
            description="무한 스크롤 페이지 처리",
            selectors={
                "container": ".container",
                "items": ".item"
            },
            expected_results={"load_more_items": True}
        ),
        "ajax_content": TestScenario(
            name="AJAX Content Loading",
            url="/ajax",
            description="동적 콘텐츠 로딩 처리",
            selectors={
                "load_button": "button.load-data",
                "content": "#dynamic-content"
            },
            expected_results={"dynamic_load": True}
        ),
        "login_form": TestScenario(
            name="Login Form",
            url="/login",
            description="로그인 폼 처리",
            selectors={
                "username": "input[name='username']",
                "password": "input[name='password']",
                "submit": "button[type='submit']",
                "error": ".error-message"
            },
            expected_results={"login_success": False}
        ),
        "product_list": TestScenario(
            name="Product List",
            url="/products",
            description="제품 목록 스크래핑",
            selectors={
                "products": ".product-card",
                "title": ".product-title",
                "price": ".product-price",
                "pagination": ".pagination a"
            },
            expected_results={"has_products": True}
        )
    }
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.results: Dict[str, Any] = {}
        
    async def setup(self):
        """브라우저 초기화"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await context.new_page()
        
    async def teardown(self):
        """브라우저 정리"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    async def test_basic_navigation(self) -> Dict[str, Any]:
        """기본 네비게이션 테스트"""
        result = {
            "test": "basic_navigation",
            "success": False,
            "data": {}
        }
        
        try:
            # 메인 페이지 방문
            await self.page.goto(self.BASE_URL)
            
            # 타이틀 확인
            title = await self.page.title()
            result["data"]["title"] = title
            
            # 네비게이션 링크 찾기
            nav_links = await self.page.query_selector_all("nav a")
            result["data"]["nav_count"] = len(nav_links)
            
            result["success"] = True
            logger.info(f"Basic navigation test passed: {result['data']}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Basic navigation test failed: {e}")
        
        return result
    
    async def test_table_scraping(self) -> Dict[str, Any]:
        """테이블 데이터 추출 테스트"""
        scenario = self.SCENARIOS["basic_table"]
        result = {
            "test": scenario.name,
            "success": False,
            "data": {}
        }
        
        try:
            await self.page.goto(f"{self.BASE_URL}{scenario.url}")
            await self.page.wait_for_selector(scenario.selectors["table"])
            
            # 헤더 추출
            headers = await self.page.query_selector_all(scenario.selectors["headers"])
            header_texts = []
            for header in headers:
                text = await header.text_content()
                header_texts.append(text.strip())
            
            result["data"]["headers"] = header_texts
            
            # 행 데이터 추출
            rows = await self.page.query_selector_all(scenario.selectors["rows"])
            row_data = []
            
            for row in rows[:5]:  # 처음 5개 행만
                cells = await row.query_selector_all("td")
                cell_data = []
                for cell in cells:
                    text = await cell.text_content()
                    cell_data.append(text.strip())
                row_data.append(cell_data)
            
            result["data"]["rows"] = row_data
            result["data"]["total_rows"] = len(rows)
            result["success"] = len(rows) >= scenario.expected_results["min_rows"]
            
            logger.info(f"Table scraping test: found {len(rows)} rows")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Table scraping test failed: {e}")
        
        return result
    
    async def test_infinite_scroll(self) -> Dict[str, Any]:
        """무한 스크롤 테스트"""
        scenario = self.SCENARIOS["infinite_scroll"]
        result = {
            "test": scenario.name,
            "success": False,
            "data": {}
        }
        
        try:
            await self.page.goto(f"{self.BASE_URL}{scenario.url}")
            await self.page.wait_for_selector(scenario.selectors["items"])
            
            # 초기 아이템 수
            initial_items = await self.page.query_selector_all(scenario.selectors["items"])
            result["data"]["initial_count"] = len(initial_items)
            
            # 스크롤 다운
            for _ in range(3):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)  # 로딩 대기
            
            # 추가 로드된 아이템 확인
            final_items = await self.page.query_selector_all(scenario.selectors["items"])
            result["data"]["final_count"] = len(final_items)
            result["data"]["items_loaded"] = len(final_items) - len(initial_items)
            
            result["success"] = len(final_items) > len(initial_items)
            logger.info(f"Infinite scroll test: {len(initial_items)} -> {len(final_items)} items")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Infinite scroll test failed: {e}")
        
        return result
    
    async def test_ajax_loading(self) -> Dict[str, Any]:
        """AJAX 콘텐츠 로딩 테스트"""
        scenario = self.SCENARIOS["ajax_content"]
        result = {
            "test": scenario.name,
            "success": False,
            "data": {}
        }
        
        try:
            await self.page.goto(f"{self.BASE_URL}{scenario.url}")
            
            # 로드 버튼 클릭
            load_button = await self.page.wait_for_selector(scenario.selectors["load_button"])
            await load_button.click()
            
            # 동적 콘텐츠 대기
            content = await self.page.wait_for_selector(
                scenario.selectors["content"],
                state="visible",
                timeout=5000
            )
            
            # 콘텐츠 확인
            content_text = await content.text_content()
            result["data"]["content_loaded"] = bool(content_text)
            result["data"]["content_length"] = len(content_text) if content_text else 0
            
            result["success"] = bool(content_text)
            logger.info(f"AJAX loading test: content loaded with {len(content_text)} chars")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"AJAX loading test failed: {e}")
        
        return result
    
    async def test_form_interaction(self) -> Dict[str, Any]:
        """폼 상호작용 테스트"""
        scenario = self.SCENARIOS["login_form"]
        result = {
            "test": scenario.name,
            "success": False,
            "data": {}
        }
        
        try:
            await self.page.goto(f"{self.BASE_URL}{scenario.url}")
            
            # 폼 필드 입력
            await self.page.fill(scenario.selectors["username"], "testuser")
            await self.page.fill(scenario.selectors["password"], "testpass")
            
            # 제출
            await self.page.click(scenario.selectors["submit"])
            
            # 결과 확인 (에러 메시지 또는 성공 리다이렉트)
            try:
                error = await self.page.wait_for_selector(
                    scenario.selectors["error"],
                    timeout=2000
                )
                error_text = await error.text_content()
                result["data"]["error_message"] = error_text
                result["data"]["login_attempted"] = True
            except:
                # 에러가 없으면 성공으로 간주
                result["data"]["login_attempted"] = True
                result["data"]["current_url"] = self.page.url
            
            result["success"] = True
            logger.info(f"Form interaction test completed")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Form interaction test failed: {e}")
        
        return result
    
    async def test_product_pagination(self) -> Dict[str, Any]:
        """제품 목록 및 페이지네이션 테스트"""
        scenario = self.SCENARIOS["product_list"]
        result = {
            "test": scenario.name,
            "success": False,
            "data": {}
        }
        
        try:
            await self.page.goto(f"{self.BASE_URL}{scenario.url}")
            await self.page.wait_for_selector(scenario.selectors["products"])
            
            # 제품 정보 추출
            products = await self.page.query_selector_all(scenario.selectors["products"])
            product_data = []
            
            for product in products[:3]:  # 처음 3개만
                title_elem = await product.query_selector(scenario.selectors["title"])
                price_elem = await product.query_selector(scenario.selectors["price"])
                
                title = await title_elem.text_content() if title_elem else ""
                price = await price_elem.text_content() if price_elem else ""
                
                product_data.append({
                    "title": title.strip(),
                    "price": price.strip()
                })
            
            result["data"]["products"] = product_data
            result["data"]["total_products"] = len(products)
            
            # 페이지네이션 확인
            pagination = await self.page.query_selector_all(scenario.selectors["pagination"])
            result["data"]["has_pagination"] = len(pagination) > 0
            
            result["success"] = len(products) > 0
            logger.info(f"Product pagination test: found {len(products)} products")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Product pagination test failed: {e}")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        await self.setup()
        
        test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
        
        # 테스트 실행
        tests = [
            self.test_basic_navigation(),
            self.test_table_scraping(),
            self.test_infinite_scroll(),
            self.test_ajax_loading(),
            self.test_form_interaction(),
            self.test_product_pagination()
        ]
        
        for test in tests:
            result = await test
            test_results["tests"].append(result)
            test_results["total_tests"] += 1
            
            if result.get("success"):
                test_results["passed"] += 1
            else:
                test_results["failed"] += 1
        
        await self.teardown()
        
        return test_results


# 재사용 가능한 유틸리티 함수들
class ScrapingPatterns:
    """재사용 가능한 스크래핑 패턴"""
    
    @staticmethod
    async def wait_and_click(page: Page, selector: str, timeout: int = 5000):
        """요소 대기 후 클릭"""
        element = await page.wait_for_selector(selector, timeout=timeout)
        await element.click()
        return element
    
    @staticmethod
    async def extract_table_data(page: Page, table_selector: str) -> List[List[str]]:
        """테이블 데이터 추출"""
        table = await page.wait_for_selector(table_selector)
        
        # 헤더 추출
        headers = await table.query_selector_all("thead th")
        header_data = []
        for h in headers:
            text = await h.text_content()
            header_data.append(text.strip())
        
        # 행 데이터 추출
        rows = await table.query_selector_all("tbody tr")
        row_data = []
        
        for row in rows:
            cells = await row.query_selector_all("td")
            cell_data = []
            for cell in cells:
                text = await cell.text_content()
                cell_data.append(text.strip())
            row_data.append(cell_data)
        
        return [header_data] + row_data
    
    @staticmethod
    async def handle_infinite_scroll(page: Page, item_selector: str, max_scrolls: int = 10):
        """무한 스크롤 처리"""
        items = []
        previous_count = 0
        
        for _ in range(max_scrolls):
            # 현재 아이템 수집
            current_items = await page.query_selector_all(item_selector)
            
            # 새 아이템이 없으면 중단
            if len(current_items) == previous_count:
                break
            
            previous_count = len(current_items)
            
            # 스크롤
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
        
        # 모든 아이템 수집
        all_items = await page.query_selector_all(item_selector)
        for item in all_items:
            text = await item.text_content()
            items.append(text.strip())
        
        return items
    
    @staticmethod
    async def wait_for_ajax_content(page: Page, content_selector: str, trigger_selector: str = None):
        """AJAX 콘텐츠 로딩 대기"""
        if trigger_selector:
            await ScrapingPatterns.wait_and_click(page, trigger_selector)
        
        # 콘텐츠 로딩 대기
        content = await page.wait_for_selector(
            content_selector,
            state="visible",
            timeout=10000
        )
        
        # 추가 로딩 시간
        await asyncio.sleep(0.5)
        
        return await content.text_content()
    
    @staticmethod
    async def handle_pagination(page: Page, next_button_selector: str, data_extractor):
        """페이지네이션 처리"""
        all_data = []
        
        while True:
            # 현재 페이지 데이터 추출
            page_data = await data_extractor(page)
            all_data.extend(page_data)
            
            # 다음 페이지 버튼 찾기
            try:
                next_button = await page.query_selector(next_button_selector)
                if not next_button:
                    break
                
                # 버튼이 비활성화되었는지 확인
                is_disabled = await next_button.get_attribute("disabled")
                if is_disabled:
                    break
                
                # 다음 페이지로 이동
                await next_button.click()
                await asyncio.sleep(1)
                
            except:
                break
        
        return all_data


async def main():
    """테스트 실행"""
    test_suite = WebScrapingTestSuite(headless=False)
    results = await test_suite.run_all_tests()
    
    print("\n=== Web Scraping Test Results ===")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print("\nDetailed Results:")
    
    for test in results['tests']:
        status = "✅" if test.get('success') else "❌"
        print(f"{status} {test['test']}")
        if test.get('error'):
            print(f"   Error: {test['error']}")


if __name__ == "__main__":
    asyncio.run(main())
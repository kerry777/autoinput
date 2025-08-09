"""
Web-scraping.dev Challenge Explorer & Skills Assessment
실제 웹 스크래핑에서 마주치는 모든 챌린지를 체계적으로 테스트하고 기록
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import json
from pathlib import Path
from playwright.async_api import Page, Browser, async_playwright, Response
import logging

logger = logging.getLogger(__name__)

class SkillLevel(Enum):
    """기술 수준"""
    NOT_TESTED = "not_tested"
    FAILED = "failed"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    MASTERED = "mastered"

class ChallengeCategory(Enum):
    """챌린지 카테고리"""
    BASIC = "basic"
    DYNAMIC = "dynamic"
    AUTHENTICATION = "authentication"
    ANTI_SCRAPING = "anti_scraping"
    JAVASCRIPT = "javascript"
    FORMS = "forms"
    FILES = "files"
    ADVANCED = "advanced"
    PERFORMANCE = "performance"

@dataclass
class Challenge:
    """챌린지 정의"""
    id: str
    name: str
    category: ChallengeCategory
    url: str
    description: str
    skills_required: List[str]
    difficulty: int  # 1-5
    test_criteria: Dict[str, Any]
    
@dataclass
class TestResult:
    """테스트 결과"""
    challenge_id: str
    success: bool
    skill_level: SkillLevel
    execution_time: float
    error_message: Optional[str] = None
    data_extracted: Optional[Dict] = None
    techniques_used: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class WebScrapingChallengeExplorer:
    """웹 스크래핑 챌린지 탐색 및 평가 시스템"""
    
    BASE_URL = "https://web-scraping.dev"
    
    # 모든 챌린지 정의
    CHALLENGES = {
        # === BASIC CHALLENGES ===
        "simple_html": Challenge(
            id="simple_html",
            name="Simple HTML Table",
            category=ChallengeCategory.BASIC,
            url="/table",
            description="기본 HTML 테이블 파싱",
            skills_required=["css_selector", "table_parsing"],
            difficulty=1,
            test_criteria={"min_rows": 10, "has_headers": True}
        ),
        "product_list": Challenge(
            id="product_list",
            name="Product List",
            category=ChallengeCategory.BASIC,
            url="/products",
            description="제품 목록 추출",
            skills_required=["css_selector", "data_extraction"],
            difficulty=1,
            test_criteria={"min_products": 20}
        ),
        
        # === DYNAMIC CONTENT ===
        "infinite_scroll": Challenge(
            id="infinite_scroll",
            name="Infinite Scroll",
            category=ChallengeCategory.DYNAMIC,
            url="/infinite-scroll",
            description="무한 스크롤 처리",
            skills_required=["scroll_handling", "dynamic_loading"],
            difficulty=2,
            test_criteria={"min_items": 50}
        ),
        "lazy_loading": Challenge(
            id="lazy_loading",
            name="Lazy Loading Images",
            category=ChallengeCategory.DYNAMIC,
            url="/lazy-loading",
            description="지연 로딩 이미지 처리",
            skills_required=["scroll_handling", "wait_for_images"],
            difficulty=2,
            test_criteria={"all_images_loaded": True}
        ),
        "ajax_data": Challenge(
            id="ajax_data",
            name="AJAX Data Loading",
            category=ChallengeCategory.DYNAMIC,
            url="/ajax",
            description="AJAX 비동기 데이터 로딩",
            skills_required=["wait_for_ajax", "network_monitoring"],
            difficulty=3,
            test_criteria={"ajax_completed": True}
        ),
        
        # === AUTHENTICATION ===
        "login_form": Challenge(
            id="login_form",
            name="Login Form",
            category=ChallengeCategory.AUTHENTICATION,
            url="/login",
            description="로그인 폼 처리",
            skills_required=["form_filling", "session_handling"],
            difficulty=2,
            test_criteria={"login_attempted": True}
        ),
        "cookie_auth": Challenge(
            id="cookie_auth",
            name="Cookie Authentication",
            category=ChallengeCategory.AUTHENTICATION,
            url="/cookie-auth",
            description="쿠키 기반 인증",
            skills_required=["cookie_management", "session_persistence"],
            difficulty=3,
            test_criteria={"authenticated": True}
        ),
        "jwt_auth": Challenge(
            id="jwt_auth",
            name="JWT Authentication",
            category=ChallengeCategory.AUTHENTICATION,
            url="/jwt-auth",
            description="JWT 토큰 인증",
            skills_required=["header_manipulation", "token_handling"],
            difficulty=4,
            test_criteria={"token_obtained": True}
        ),
        
        # === ANTI-SCRAPING ===
        "rate_limiting": Challenge(
            id="rate_limiting",
            name="Rate Limiting",
            category=ChallengeCategory.ANTI_SCRAPING,
            url="/rate-limit",
            description="속도 제한 우회",
            skills_required=["throttling", "retry_strategy"],
            difficulty=3,
            test_criteria={"bypass_rate_limit": True}
        ),
        "user_agent": Challenge(
            id="user_agent",
            name="User Agent Detection",
            category=ChallengeCategory.ANTI_SCRAPING,
            url="/user-agent",
            description="User-Agent 검증",
            skills_required=["header_spoofing"],
            difficulty=2,
            test_criteria={"accepted_user_agent": True}
        ),
        "captcha": Challenge(
            id="captcha",
            name="CAPTCHA Challenge",
            category=ChallengeCategory.ANTI_SCRAPING,
            url="/captcha",
            description="CAPTCHA 처리",
            skills_required=["captcha_solving", "manual_intervention"],
            difficulty=5,
            test_criteria={"captcha_solved": True}
        ),
        
        # === JAVASCRIPT ===
        "spa_navigation": Challenge(
            id="spa_navigation",
            name="SPA Navigation",
            category=ChallengeCategory.JAVASCRIPT,
            url="/spa",
            description="단일 페이지 애플리케이션 네비게이션",
            skills_required=["spa_handling", "route_monitoring"],
            difficulty=3,
            test_criteria={"routes_navigated": 3}
        ),
        "javascript_render": Challenge(
            id="javascript_render",
            name="JavaScript Rendering",
            category=ChallengeCategory.JAVASCRIPT,
            url="/javascript",
            description="JavaScript 렌더링 대기",
            skills_required=["js_execution", "dom_waiting"],
            difficulty=2,
            test_criteria={"js_rendered": True}
        ),
        
        # === FORMS ===
        "multi_step_form": Challenge(
            id="multi_step_form",
            name="Multi-Step Form",
            category=ChallengeCategory.FORMS,
            url="/multi-step-form",
            description="다단계 폼 처리",
            skills_required=["form_navigation", "state_management"],
            difficulty=3,
            test_criteria={"steps_completed": 3}
        ),
        "form_validation": Challenge(
            id="form_validation",
            name="Form Validation",
            category=ChallengeCategory.FORMS,
            url="/form-validation",
            description="폼 검증 처리",
            skills_required=["validation_handling", "error_recovery"],
            difficulty=2,
            test_criteria={"validation_passed": True}
        ),
        
        # === FILES ===
        "file_download": Challenge(
            id="file_download",
            name="File Download",
            category=ChallengeCategory.FILES,
            url="/download",
            description="파일 다운로드 처리",
            skills_required=["download_handling"],
            difficulty=2,
            test_criteria={"file_downloaded": True}
        ),
        "file_upload": Challenge(
            id="file_upload",
            name="File Upload",
            category=ChallengeCategory.FILES,
            url="/upload",
            description="파일 업로드 처리",
            skills_required=["upload_handling"],
            difficulty=2,
            test_criteria={"file_uploaded": True}
        ),
        
        # === ADVANCED ===
        "iframe_content": Challenge(
            id="iframe_content",
            name="iFrame Content",
            category=ChallengeCategory.ADVANCED,
            url="/iframe",
            description="iFrame 내 콘텐츠 접근",
            skills_required=["iframe_handling", "context_switching"],
            difficulty=3,
            test_criteria={"iframe_accessed": True}
        ),
        "shadow_dom": Challenge(
            id="shadow_dom",
            name="Shadow DOM",
            category=ChallengeCategory.ADVANCED,
            url="/shadow-dom",
            description="Shadow DOM 요소 접근",
            skills_required=["shadow_dom_handling"],
            difficulty=4,
            test_criteria={"shadow_element_found": True}
        ),
        "websocket": Challenge(
            id="websocket",
            name="WebSocket Communication",
            category=ChallengeCategory.ADVANCED,
            url="/websocket",
            description="WebSocket 통신 처리",
            skills_required=["websocket_handling"],
            difficulty=4,
            test_criteria={"websocket_connected": True}
        )
    }
    
    def __init__(self, output_dir: str = "challenge_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.results: Dict[str, TestResult] = {}
        self.skills_inventory: Dict[str, SkillLevel] = {}
        
    async def setup(self, headless: bool = False):
        """브라우저 설정"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox']
        )
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        )
        self.page = await context.new_page()
        
        # 네트워크 모니터링
        self.page.on("response", self._on_response)
        
    async def teardown(self):
        """정리"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
    
    async def _on_response(self, response: Response):
        """네트워크 응답 모니터링"""
        if response.status >= 400:
            logger.warning(f"HTTP {response.status}: {response.url}")
    
    async def explore_site(self) -> Dict[str, List[str]]:
        """사이트 탐색 및 챌린지 목록 수집"""
        challenges_found = {
            "available": [],
            "categories": {},
            "difficulty_levels": {}
        }
        
        try:
            # 메인 페이지 방문
            await self.page.goto(self.BASE_URL)
            await self.page.wait_for_load_state("networkidle")
            
            # 챌린지 링크 수집
            links = await self.page.query_selector_all("a[href*='/']")
            
            for link in links:
                href = await link.get_attribute("href")
                text = await link.text_content()
                
                if href and text:
                    challenges_found["available"].append({
                        "url": href,
                        "name": text.strip()
                    })
            
            # 카테고리별 분류
            for challenge_id, challenge in self.CHALLENGES.items():
                category = challenge.category.value
                if category not in challenges_found["categories"]:
                    challenges_found["categories"][category] = []
                challenges_found["categories"][category].append(challenge_id)
                
                # 난이도별 분류
                difficulty = str(challenge.difficulty)
                if difficulty not in challenges_found["difficulty_levels"]:
                    challenges_found["difficulty_levels"][difficulty] = []
                challenges_found["difficulty_levels"][difficulty].append(challenge_id)
            
            logger.info(f"Found {len(challenges_found['available'])} challenges")
            
        except Exception as e:
            logger.error(f"Site exploration failed: {e}")
        
        return challenges_found
    
    async def test_challenge(self, challenge_id: str) -> TestResult:
        """개별 챌린지 테스트"""
        if challenge_id not in self.CHALLENGES:
            return TestResult(
                challenge_id=challenge_id,
                success=False,
                skill_level=SkillLevel.NOT_TESTED,
                execution_time=0,
                error_message="Challenge not found"
            )
        
        challenge = self.CHALLENGES[challenge_id]
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 챌린지별 테스트 실행
            if challenge_id == "simple_html":
                result = await self._test_simple_html(challenge)
            elif challenge_id == "infinite_scroll":
                result = await self._test_infinite_scroll(challenge)
            elif challenge_id == "ajax_data":
                result = await self._test_ajax_data(challenge)
            elif challenge_id == "login_form":
                result = await self._test_login_form(challenge)
            elif challenge_id == "javascript_render":
                result = await self._test_javascript_render(challenge)
            elif challenge_id == "iframe_content":
                result = await self._test_iframe_content(challenge)
            else:
                # 기본 테스트
                result = await self._test_basic_navigation(challenge)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            result.execution_time = execution_time
            
            # 스킬 레벨 평가
            result.skill_level = self._evaluate_skill_level(result)
            
            # 결과 저장
            self.results[challenge_id] = result
            
            # 스킬 인벤토리 업데이트
            for skill in challenge.skills_required:
                if result.success:
                    self.skills_inventory[skill] = SkillLevel.MASTERED
                
            return result
            
        except Exception as e:
            logger.error(f"Challenge test failed: {e}")
            return TestResult(
                challenge_id=challenge_id,
                success=False,
                skill_level=SkillLevel.FAILED,
                execution_time=asyncio.get_event_loop().time() - start_time,
                error_message=str(e)
            )
    
    async def _test_simple_html(self, challenge: Challenge) -> TestResult:
        """HTML 테이블 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            await self.page.wait_for_selector("table", timeout=5000)
            
            # 테이블 데이터 추출
            headers = await self.page.query_selector_all("table thead th")
            rows = await self.page.query_selector_all("table tbody tr")
            
            result.data_extracted = {
                "headers": len(headers),
                "rows": len(rows)
            }
            
            result.success = len(rows) >= challenge.test_criteria["min_rows"]
            result.techniques_used = ["css_selector", "table_parsing"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    async def _test_infinite_scroll(self, challenge: Challenge) -> TestResult:
        """무한 스크롤 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            await self.page.wait_for_selector(".item", timeout=5000)
            
            initial_items = await self.page.query_selector_all(".item")
            
            # 스크롤 처리
            for _ in range(5):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
            
            final_items = await self.page.query_selector_all(".item")
            
            result.data_extracted = {
                "initial_count": len(initial_items),
                "final_count": len(final_items),
                "items_loaded": len(final_items) - len(initial_items)
            }
            
            result.success = len(final_items) >= challenge.test_criteria["min_items"]
            result.techniques_used = ["scroll_handling", "dynamic_loading", "wait_strategy"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    async def _test_ajax_data(self, challenge: Challenge) -> TestResult:
        """AJAX 데이터 로딩 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            
            # AJAX 요청 모니터링
            ajax_completed = False
            
            async def check_ajax(response: Response):
                nonlocal ajax_completed
                if "api" in response.url or "ajax" in response.url:
                    ajax_completed = True
            
            self.page.on("response", check_ajax)
            
            # 데이터 로드 버튼 클릭
            load_button = await self.page.query_selector("button.load-data")
            if load_button:
                await load_button.click()
                await asyncio.sleep(2)
            
            result.data_extracted = {
                "ajax_completed": ajax_completed
            }
            
            result.success = ajax_completed
            result.techniques_used = ["ajax_monitoring", "network_interception", "async_waiting"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    async def _test_login_form(self, challenge: Challenge) -> TestResult:
        """로그인 폼 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            
            # 폼 필드 입력
            username_field = await self.page.query_selector("input[name='username']")
            password_field = await self.page.query_selector("input[name='password']")
            submit_button = await self.page.query_selector("button[type='submit']")
            
            if username_field and password_field and submit_button:
                await username_field.fill("testuser")
                await password_field.fill("testpass")
                await submit_button.click()
                
                await asyncio.sleep(1)
                
                result.data_extracted = {
                    "form_submitted": True,
                    "current_url": self.page.url
                }
                
                result.success = True
                result.techniques_used = ["form_filling", "input_handling", "submit_action"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    async def _test_javascript_render(self, challenge: Challenge) -> TestResult:
        """JavaScript 렌더링 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            
            # JS 렌더링 대기
            await self.page.wait_for_function(
                "() => document.querySelector('#dynamic-content') !== null",
                timeout=10000
            )
            
            content = await self.page.query_selector("#dynamic-content")
            if content:
                text = await content.text_content()
                result.data_extracted = {
                    "content_rendered": True,
                    "content_length": len(text) if text else 0
                }
                result.success = True
                result.techniques_used = ["js_execution_wait", "dom_polling", "dynamic_content_detection"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    async def _test_iframe_content(self, challenge: Challenge) -> TestResult:
        """iFrame 콘텐츠 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            
            # iFrame 찾기
            iframe = await self.page.query_selector("iframe")
            if iframe:
                # iFrame 내부로 전환
                frame = await iframe.content_frame()
                if frame:
                    # iFrame 내 요소 찾기
                    iframe_content = await frame.query_selector("body")
                    if iframe_content:
                        text = await iframe_content.text_content()
                        result.data_extracted = {
                            "iframe_accessed": True,
                            "content_found": bool(text)
                        }
                        result.success = True
                        result.techniques_used = ["iframe_switching", "frame_context", "nested_content_access"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    async def _test_basic_navigation(self, challenge: Challenge) -> TestResult:
        """기본 네비게이션 테스트"""
        result = TestResult(challenge_id=challenge.id, success=False, skill_level=SkillLevel.NOT_TESTED, execution_time=0)
        
        try:
            await self.page.goto(f"{self.BASE_URL}{challenge.url}")
            await self.page.wait_for_load_state("networkidle")
            
            result.data_extracted = {
                "page_loaded": True,
                "url": self.page.url
            }
            result.success = True
            result.techniques_used = ["basic_navigation"]
            
        except Exception as e:
            result.error_message = str(e)
        
        return result
    
    def _evaluate_skill_level(self, result: TestResult) -> SkillLevel:
        """스킬 레벨 평가"""
        if not result.success:
            return SkillLevel.FAILED
        
        # 실행 시간과 기술 사용에 따른 평가
        if result.execution_time < 1:
            if len(result.techniques_used) > 3:
                return SkillLevel.MASTERED
            elif len(result.techniques_used) > 1:
                return SkillLevel.ADVANCED
            else:
                return SkillLevel.INTERMEDIATE
        elif result.execution_time < 5:
            return SkillLevel.INTERMEDIATE
        else:
            return SkillLevel.BASIC
    
    async def run_full_assessment(self) -> Dict[str, Any]:
        """전체 평가 실행"""
        await self.setup()
        
        assessment_report = {
            "timestamp": datetime.now().isoformat(),
            "total_challenges": len(self.CHALLENGES),
            "tested": 0,
            "passed": 0,
            "failed": 0,
            "skill_levels": {},
            "category_scores": {},
            "detailed_results": []
        }
        
        # 사이트 탐색
        site_info = await self.explore_site()
        assessment_report["site_exploration"] = site_info
        
        # 난이도 순으로 챌린지 실행
        sorted_challenges = sorted(
            self.CHALLENGES.items(),
            key=lambda x: x[1].difficulty
        )
        
        for challenge_id, challenge in sorted_challenges:
            logger.info(f"Testing: {challenge.name} (Difficulty: {challenge.difficulty})")
            
            result = await self.test_challenge(challenge_id)
            assessment_report["tested"] += 1
            
            if result.success:
                assessment_report["passed"] += 1
            else:
                assessment_report["failed"] += 1
            
            # 카테고리별 점수
            category = challenge.category.value
            if category not in assessment_report["category_scores"]:
                assessment_report["category_scores"][category] = {
                    "total": 0,
                    "passed": 0
                }
            assessment_report["category_scores"][category]["total"] += 1
            if result.success:
                assessment_report["category_scores"][category]["passed"] += 1
            
            # 상세 결과
            assessment_report["detailed_results"].append({
                "challenge": challenge.name,
                "category": category,
                "difficulty": challenge.difficulty,
                "success": result.success,
                "skill_level": result.skill_level.value,
                "execution_time": result.execution_time,
                "techniques_used": result.techniques_used,
                "error": result.error_message
            })
        
        # 스킬 인벤토리 요약
        assessment_report["skill_levels"] = {
            skill: level.value 
            for skill, level in self.skills_inventory.items()
        }
        
        await self.teardown()
        
        # 보고서 저장
        self.save_assessment_report(assessment_report)
        
        return assessment_report
    
    def save_assessment_report(self, report: Dict[str, Any]):
        """평가 보고서 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 형식으로 저장
        json_file = self.output_dir / f"assessment_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        # 요약 보고서 생성
        summary_file = self.output_dir / f"summary_{timestamp}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_report(report))
        
        logger.info(f"Assessment report saved to {json_file}")
    
    def _generate_summary_report(self, report: Dict[str, Any]) -> str:
        """요약 보고서 생성"""
        summary = f"""# Web Scraping Skills Assessment Report

Generated: {report['timestamp']}

## Overall Results
- Total Challenges: {report['total_challenges']}
- Tested: {report['tested']}
- Passed: {report['passed']} ({report['passed']/report['tested']*100:.1f}%)
- Failed: {report['failed']}

## Category Scores
"""
        
        for category, scores in report['category_scores'].items():
            percentage = scores['passed'] / scores['total'] * 100 if scores['total'] > 0 else 0
            summary += f"- **{category}**: {scores['passed']}/{scores['total']} ({percentage:.1f}%)\n"
        
        summary += "\n## Skill Inventory\n"
        for skill, level in report['skill_levels'].items():
            summary += f"- {skill}: {level}\n"
        
        summary += "\n## Detailed Challenge Results\n"
        for result in report['detailed_results']:
            status = "✅" if result['success'] else "❌"
            summary += f"\n### {status} {result['challenge']}\n"
            summary += f"- Category: {result['category']}\n"
            summary += f"- Difficulty: {result['difficulty']}/5\n"
            summary += f"- Skill Level: {result['skill_level']}\n"
            summary += f"- Execution Time: {result['execution_time']:.2f}s\n"
            if result['techniques_used']:
                summary += f"- Techniques: {', '.join(result['techniques_used'])}\n"
            if result['error']:
                summary += f"- Error: {result['error']}\n"
        
        return summary


async def main():
    """메인 실행 함수"""
    explorer = WebScrapingChallengeExplorer()
    
    print("🔍 Starting Web Scraping Skills Assessment...")
    print("=" * 60)
    
    report = await explorer.run_full_assessment()
    
    print("\n📊 Assessment Complete!")
    print("=" * 60)
    print(f"Total Challenges: {report['total_challenges']}")
    print(f"Passed: {report['passed']}/{report['tested']}")
    print(f"Success Rate: {report['passed']/report['tested']*100:.1f}%")
    
    print("\n📈 Category Performance:")
    for category, scores in report['category_scores'].items():
        percentage = scores['passed'] / scores['total'] * 100 if scores['total'] > 0 else 0
        print(f"  {category}: {percentage:.1f}%")
    
    print("\n✅ Skills Acquired:")
    for skill, level in report['skill_levels'].items():
        if level != "not_tested":
            print(f"  - {skill}: {level}")
    
    print(f"\n📁 Report saved to: challenge_results/")


if __name__ == "__main__":
    asyncio.run(main())
"""
Self-Healing Selector System
셀렉터가 실패할 때 자동으로 대체 셀렉터를 찾아 복구하는 시스템
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import hashlib
from pathlib import Path
from playwright.async_api import Page, ElementHandle
import logging

logger = logging.getLogger(__name__)

@dataclass
class SelectorStrategy:
    """셀렉터 전략"""
    type: str  # css, xpath, text, role, testid
    value: str
    confidence: float = 1.0
    last_used: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0

@dataclass 
class ElementFingerprint:
    """요소의 고유 특성"""
    tag_name: str
    text_content: Optional[str] = None
    class_names: List[str] = field(default_factory=list)
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    href: Optional[str] = None
    role: Optional[str] = None
    data_attributes: Dict[str, str] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)  # top, left, width, height
    parent_tag: Optional[str] = None
    sibling_count: int = 0
    
    def to_hash(self) -> str:
        """요소의 해시값 생성"""
        data = {
            "tag": self.tag_name,
            "text": self.text_content,
            "classes": sorted(self.class_names),
            "id": self.id
        }
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

class SelfHealingSelector:
    """자가치유 셀렉터 시스템"""
    
    def __init__(self, cache_dir: str = "selector_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.selector_cache: Dict[str, List[SelectorStrategy]] = {}
        self.element_fingerprints: Dict[str, ElementFingerprint] = {}
        self.load_cache()
    
    def load_cache(self):
        """캐시 로드"""
        cache_file = self.cache_dir / "selectors.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # JSON을 SelectorStrategy 객체로 변환
                    for key, strategies in data.items():
                        self.selector_cache[key] = [
                            SelectorStrategy(**s) for s in strategies
                        ]
            except Exception as e:
                logger.error(f"Failed to load selector cache: {e}")
    
    def save_cache(self):
        """캐시 저장"""
        cache_file = self.cache_dir / "selectors.json"
        try:
            # SelectorStrategy 객체를 JSON으로 변환
            data = {}
            for key, strategies in self.selector_cache.items():
                data[key] = [
                    {
                        "type": s.type,
                        "value": s.value,
                        "confidence": s.confidence,
                        "success_count": s.success_count,
                        "failure_count": s.failure_count
                    }
                    for s in strategies
                ]
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save selector cache: {e}")
    
    async def get_element_fingerprint(self, element: ElementHandle) -> ElementFingerprint:
        """요소의 지문 생성"""
        try:
            # 요소 정보 추출
            properties = await element.evaluate("""
                (element) => {
                    const rect = element.getBoundingClientRect();
                    const parent = element.parentElement;
                    const dataAttrs = {};
                    
                    // data-* 속성 수집
                    for (const attr of element.attributes) {
                        if (attr.name.startsWith('data-')) {
                            dataAttrs[attr.name] = attr.value;
                        }
                    }
                    
                    return {
                        tagName: element.tagName.toLowerCase(),
                        textContent: element.textContent?.trim() || null,
                        className: element.className || '',
                        id: element.id || null,
                        name: element.getAttribute('name') || null,
                        type: element.getAttribute('type') || null,
                        href: element.getAttribute('href') || null,
                        role: element.getAttribute('role') || null,
                        dataAttributes: dataAttrs,
                        position: {
                            top: Math.round(rect.top),
                            left: Math.round(rect.left),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        },
                        parentTag: parent ? parent.tagName.toLowerCase() : null,
                        siblingCount: parent ? parent.children.length : 0
                    };
                }
            """)
            
            return ElementFingerprint(
                tag_name=properties['tagName'],
                text_content=properties['textContent'],
                class_names=properties['className'].split() if properties['className'] else [],
                id=properties['id'],
                name=properties['name'],
                type=properties['type'],
                href=properties['href'],
                role=properties['role'],
                data_attributes=properties['dataAttributes'],
                position=properties['position'],
                parent_tag=properties['parentTag'],
                sibling_count=properties['siblingCount']
            )
        except Exception as e:
            logger.error(f"Failed to get element fingerprint: {e}")
            return None
    
    def generate_selector_strategies(self, fingerprint: ElementFingerprint) -> List[SelectorStrategy]:
        """요소 지문을 기반으로 다양한 셀렉터 전략 생성"""
        strategies = []
        
        # ID 셀렉터 (가장 신뢰도 높음)
        if fingerprint.id:
            strategies.append(SelectorStrategy(
                type="css",
                value=f"#{fingerprint.id}",
                confidence=1.0
            ))
        
        # data-testid 셀렉터
        if 'data-testid' in fingerprint.data_attributes:
            strategies.append(SelectorStrategy(
                type="css",
                value=f"[data-testid='{fingerprint.data_attributes['data-testid']}']",
                confidence=0.95
            ))
        
        # Class 조합 셀렉터
        if fingerprint.class_names:
            class_selector = "." + ".".join(fingerprint.class_names[:3])  # 최대 3개 클래스
            strategies.append(SelectorStrategy(
                type="css",
                value=f"{fingerprint.tag_name}{class_selector}",
                confidence=0.8
            ))
        
        # 텍스트 기반 셀렉터
        if fingerprint.text_content and len(fingerprint.text_content) < 50:
            strategies.append(SelectorStrategy(
                type="text",
                value=fingerprint.text_content,
                confidence=0.7
            ))
        
        # Role 기반 셀렉터
        if fingerprint.role:
            strategies.append(SelectorStrategy(
                type="role",
                value=fingerprint.role,
                confidence=0.75
            ))
        
        # Name 속성 셀렉터
        if fingerprint.name:
            strategies.append(SelectorStrategy(
                type="css",
                value=f"{fingerprint.tag_name}[name='{fingerprint.name}']",
                confidence=0.85
            ))
        
        # Type 속성 셀렉터 (input 요소)
        if fingerprint.type and fingerprint.tag_name == "input":
            strategies.append(SelectorStrategy(
                type="css",
                value=f"input[type='{fingerprint.type}']",
                confidence=0.6
            ))
        
        # XPath - 부모와의 관계
        if fingerprint.parent_tag:
            xpath = f"//{fingerprint.parent_tag}//{fingerprint.tag_name}"
            if fingerprint.text_content:
                xpath += f"[contains(text(), '{fingerprint.text_content[:20]}')]"
            strategies.append(SelectorStrategy(
                type="xpath",
                value=xpath,
                confidence=0.5
            ))
        
        # 정렬: 신뢰도 높은 순으로
        strategies.sort(key=lambda s: s.confidence, reverse=True)
        
        return strategies
    
    async def find_element(self, page: Page, identifier: str, 
                          primary_selector: str = None) -> Optional[ElementHandle]:
        """요소 찾기 (자가치유 포함)"""
        
        # 캐시된 전략들 가져오기
        strategies = self.selector_cache.get(identifier, [])
        
        # primary_selector가 제공되면 최우선으로 시도
        if primary_selector:
            strategies.insert(0, SelectorStrategy(
                type="css",
                value=primary_selector,
                confidence=1.0
            ))
        
        # 각 전략 시도
        for strategy in strategies:
            try:
                element = await self._try_selector(page, strategy)
                if element:
                    # 성공 카운트 증가
                    strategy.success_count += 1
                    strategy.last_used = datetime.now()
                    self.save_cache()
                    logger.info(f"Found element using {strategy.type}: {strategy.value}")
                    return element
            except Exception as e:
                # 실패 카운트 증가
                strategy.failure_count += 1
                logger.debug(f"Strategy failed {strategy.type}: {e}")
        
        # 모든 전략 실패 시 자가치유 시도
        logger.warning(f"All strategies failed for {identifier}, attempting self-healing")
        return await self._self_heal(page, identifier, primary_selector)
    
    async def _try_selector(self, page: Page, strategy: SelectorStrategy) -> Optional[ElementHandle]:
        """단일 셀렉터 전략 시도"""
        try:
            if strategy.type == "css":
                return await page.query_selector(strategy.value)
            elif strategy.type == "xpath":
                return await page.query_selector(f"xpath={strategy.value}")
            elif strategy.type == "text":
                return await page.get_by_text(strategy.value).first
            elif strategy.type == "role":
                return await page.get_by_role(strategy.value).first
            elif strategy.type == "testid":
                return await page.get_by_test_id(strategy.value).first
            else:
                return await page.query_selector(strategy.value)
        except:
            return None
    
    async def _self_heal(self, page: Page, identifier: str, 
                        hint_selector: str = None) -> Optional[ElementHandle]:
        """자가치유: 새로운 셀렉터 찾기"""
        
        # 힌트가 있으면 유사한 요소 찾기
        if hint_selector:
            try:
                # 비슷한 요소들 찾기
                similar_elements = await self._find_similar_elements(page, hint_selector)
                
                for element in similar_elements:
                    # 요소 지문 생성
                    fingerprint = await self.get_element_fingerprint(element)
                    if fingerprint:
                        # 새로운 전략 생성
                        new_strategies = self.generate_selector_strategies(fingerprint)
                        
                        # 캐시 업데이트
                        self.selector_cache[identifier] = new_strategies
                        self.element_fingerprints[identifier] = fingerprint
                        self.save_cache()
                        
                        logger.info(f"Self-healed selector for {identifier}")
                        return element
            except Exception as e:
                logger.error(f"Self-healing failed: {e}")
        
        return None
    
    async def _find_similar_elements(self, page: Page, hint_selector: str) -> List[ElementHandle]:
        """유사한 요소 찾기"""
        similar_elements = []
        
        try:
            # 태그명 추출
            tag_match = hint_selector.split('[')[0].split('.')[0].split('#')[0]
            if not tag_match:
                tag_match = 'div'  # 기본값
            
            # 같은 태그의 모든 요소 가져오기
            all_elements = await page.query_selector_all(tag_match)
            
            # 속성 기반 유사도 계산
            for element in all_elements[:20]:  # 최대 20개만 검사
                try:
                    # 클래스나 텍스트가 비슷한지 확인
                    classes = await element.get_attribute('class')
                    text = await element.text_content()
                    
                    if hint_selector in str(classes) or (text and len(text) < 100):
                        similar_elements.append(element)
                except:
                    continue
            
        except Exception as e:
            logger.error(f"Failed to find similar elements: {e}")
        
        return similar_elements
    
    async def record_successful_element(self, identifier: str, element: ElementHandle):
        """성공적으로 찾은 요소 기록"""
        try:
            # 요소 지문 생성
            fingerprint = await self.get_element_fingerprint(element)
            if fingerprint:
                # 전략 생성 및 저장
                strategies = self.generate_selector_strategies(fingerprint)
                self.selector_cache[identifier] = strategies
                self.element_fingerprints[identifier] = fingerprint
                self.save_cache()
                logger.info(f"Recorded element strategies for {identifier}")
        except Exception as e:
            logger.error(f"Failed to record element: {e}")


class SmartSelector:
    """스마트 셀렉터 - 간단한 사용을 위한 래퍼"""
    
    def __init__(self, page: Page, healing_system: SelfHealingSelector = None):
        self.page = page
        self.healing_system = healing_system or SelfHealingSelector()
    
    async def find(self, identifier: str, selector: str = None) -> Optional[ElementHandle]:
        """요소 찾기"""
        return await self.healing_system.find_element(self.page, identifier, selector)
    
    async def click(self, identifier: str, selector: str = None):
        """요소 클릭"""
        element = await self.find(identifier, selector)
        if element:
            await element.click()
            return True
        return False
    
    async def fill(self, identifier: str, value: str, selector: str = None):
        """입력 필드 채우기"""
        element = await self.find(identifier, selector)
        if element:
            await element.fill(value)
            return True
        return False
    
    async def get_text(self, identifier: str, selector: str = None) -> Optional[str]:
        """텍스트 가져오기"""
        element = await self.find(identifier, selector)
        if element:
            return await element.text_content()
        return None
    
    async def wait_and_find(self, identifier: str, selector: str = None, 
                           timeout: int = 5000) -> Optional[ElementHandle]:
        """요소 대기 후 찾기"""
        try:
            if selector:
                await self.page.wait_for_selector(selector, timeout=timeout)
            return await self.find(identifier, selector)
        except:
            return await self.find(identifier, selector)
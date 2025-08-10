# ExtJS 웹 애플리케이션 스크래핑 완벽 가이드

## 📌 ExtJS란?

ExtJS는 Sencha에서 개발한 엔터프라이즈급 JavaScript 프레임워크로, 복잡한 웹 애플리케이션을 구축하는 데 사용됩니다.

### 주요 특징
- **완전한 SPA (Single Page Application)**: 페이지 새로고침 없이 동작
- **동적 DOM 생성**: JavaScript로 모든 UI 요소를 동적으로 생성
- **복잡한 컴포넌트 구조**: 트리, 그리드, 폼 등 고급 UI 컴포넌트
- **데이터 스토어 기반**: 클라이언트 사이드 데이터 관리
- **이벤트 기반 아키텍처**: 사용자 상호작용이 이벤트로 처리

## 🔍 ExtJS 스크래핑의 도전 과제

### 1. 동적 콘텐츠 렌더링
```javascript
// ExtJS는 페이지 로드 후 JavaScript로 UI를 생성
Ext.create('Ext.grid.Panel', {
    store: dataStore,
    columns: [...],
    renderTo: Ext.getBody()
});
```
**문제**: 일반적인 HTTP 요청으로는 빈 HTML만 받게 됨
**해결**: Playwright/Selenium 같은 브라우저 자동화 도구 필수

### 2. 복잡한 셀렉터
```html
<!-- ExtJS가 생성하는 복잡한 ID와 클래스 -->
<div id="ext-gen1234" class="x-panel x-panel-default x-grid">
    <div id="gridview-1056-body" class="x-grid-body">
```
**문제**: ID가 동적으로 생성되어 매번 바뀜
**해결**: 클래스 기반 선택자 또는 ExtJS API 직접 활용

### 3. 비동기 데이터 로딩
```javascript
// Store가 비동기로 데이터 로드
store.load({
    callback: function(records, operation, success) {
        // 데이터 로드 완료
    }
});
```
**문제**: 데이터 로딩 완료 시점을 알기 어려움
**해결**: 명시적 대기 전략 필요

## 💡 ExtJS 스크래핑 전략

### 1. ExtJS API 직접 활용 (최선의 방법)

```python
# Playwright를 사용한 ExtJS 컴포넌트 접근
async def get_extjs_store_data(page):
    """ExtJS Store에서 직접 데이터 추출"""
    
    data = await page.evaluate("""
        () => {
            // ExtJS 스토어 찾기
            const store = Ext.StoreManager.lookup('myStoreId');
            // 또는
            const grid = Ext.ComponentQuery.query('grid')[0];
            const store = grid.getStore();
            
            // 데이터 추출
            return store.getData().items.map(record => record.data);
        }
    """)
    return data
```

### 2. ExtJS 컴포넌트 쿼리 활용

```python
async def click_extjs_button(page, button_text):
    """ExtJS 버튼 클릭"""
    
    await page.evaluate(f"""
        () => {{
            // 텍스트로 버튼 찾기
            const button = Ext.ComponentQuery.query('button{{text:"{button_text}"}}')[0];
            if (button) {{
                button.fireEvent('click', button);
                return true;
            }}
            return false;
        }}
    """)
```

### 3. ExtJS 이벤트 시스템 활용

```python
async def wait_for_store_load(page, store_id):
    """스토어 로드 완료 대기"""
    
    await page.evaluate(f"""
        () => new Promise((resolve) => {{
            const store = Ext.StoreManager.lookup('{store_id}');
            if (store.isLoaded()) {{
                resolve();
            }} else {{
                store.on('load', () => resolve(), {{single: true}});
            }}
        }})
    """)
```

## 🛠️ 실전 ExtJS 스크래핑 유틸리티

### ExtJS Helper 클래스

```python
class ExtJSHelper:
    """ExtJS 애플리케이션 스크래핑 헬퍼"""
    
    def __init__(self, page):
        self.page = page
    
    async def wait_for_extjs(self):
        """ExtJS 로드 완료 대기"""
        await self.page.wait_for_function(
            "() => typeof Ext !== 'undefined' && Ext.isReady"
        )
    
    async def get_grid_data(self, grid_selector=None):
        """그리드 데이터 추출"""
        return await self.page.evaluate("""
            (selector) => {
                let grid;
                if (selector) {
                    grid = Ext.ComponentQuery.query(selector)[0];
                } else {
                    grid = Ext.ComponentQuery.query('grid')[0];
                }
                
                if (!grid) return null;
                
                const store = grid.getStore();
                const columns = grid.getColumns().map(col => ({
                    dataIndex: col.dataIndex,
                    text: col.text
                }));
                
                const data = store.getData().items.map(record => record.data);
                
                return {
                    columns: columns,
                    data: data,
                    total: store.getTotalCount()
                };
            }
        """, grid_selector)
    
    async def click_menu(self, menu_text):
        """메뉴 클릭"""
        return await self.page.evaluate(f"""
            () => {{
                // 트리 메뉴에서 텍스트로 노드 찾기
                const tree = Ext.ComponentQuery.query('treepanel')[0];
                if (tree) {{
                    const node = tree.getStore().findNode('text', '{menu_text}');
                    if (node) {{
                        tree.getSelectionModel().select(node);
                        tree.fireEvent('itemclick', tree, node);
                        return true;
                    }}
                }}
                
                // 일반 메뉴에서 찾기
                const menuItem = Ext.ComponentQuery.query('menuitem{{text:"{menu_text}"}}')[0];
                if (menuItem) {{
                    menuItem.fireEvent('click', menuItem);
                    return true;
                }}
                
                return false;
            }}
        """)
    
    async def fill_form(self, form_data):
        """폼 데이터 입력"""
        return await self.page.evaluate("""
            (data) => {
                const form = Ext.ComponentQuery.query('form')[0];
                if (form) {
                    form.getForm().setValues(data);
                    return true;
                }
                return false;
            }
        """, form_data)
    
    async def submit_form(self):
        """폼 제출"""
        return await self.page.evaluate("""
            () => {
                const form = Ext.ComponentQuery.query('form')[0];
                if (form) {
                    form.getForm().submit();
                    return true;
                }
                return false;
            }
        """)
    
    async def wait_for_loading(self):
        """로딩 마스크 대기"""
        await self.page.wait_for_function("""
            () => {
                const masks = Ext.ComponentQuery.query('loadmask');
                return masks.every(mask => !mask.isVisible());
            }
        """)
    
    async def get_message_box_text(self):
        """메시지 박스 텍스트 가져오기"""
        return await self.page.evaluate("""
            () => {
                const msgBox = Ext.Msg;
                if (msgBox && msgBox.isVisible()) {
                    return msgBox.getMsg();
                }
                return null;
            }
        """)
    
    async def close_all_windows(self):
        """모든 윈도우 닫기"""
        await self.page.evaluate("""
            () => {
                Ext.WindowManager.each(function(win) {
                    win.close();
                });
            }
        """)
```

## 📊 MEK-ICS (OMEGA Plus) 특화 전략

### 1. 모듈 기반 네비게이션

```python
async def navigate_to_module(page, module_name):
    """MEK-ICS 모듈 이동"""
    
    module_map = {
        '영업관리': '14',
        '생산관리': '15',
        '구매/자재': '16',
        '재고관리': '18',
        '품질관리': '65'
    }
    
    module_id = module_map.get(module_name)
    if module_id:
        await page.evaluate(f"""
            () => {{
                if (typeof changeModule === 'function') {{
                    changeModule('{module_id}');
                }}
            }}
        """)
```

### 2. 트리 메뉴 탐색

```python
async def expand_tree_node(page, node_text):
    """트리 노드 확장"""
    
    await page.evaluate(f"""
        () => {{
            const tree = Ext.ComponentQuery.query('treepanel')[0];
            const node = tree.getStore().findNode('text', '{node_text}');
            if (node && !node.isExpanded()) {{
                node.expand();
            }}
        }}
    """)
```

## 🚀 최적화 팁

### 1. 대기 전략
```python
# ExtJS 로드 완료 대기
await page.wait_for_function("() => typeof Ext !== 'undefined' && Ext.isReady")

# 스토어 로드 대기
await page.wait_for_function("""
    () => {
        const store = Ext.StoreManager.lookup('myStore');
        return store && store.isLoaded();
    }
""")

# Ajax 요청 완료 대기
await page.wait_for_function("() => Ext.Ajax.isLoading() === false")
```

### 2. 성능 최적화
```python
# 불필요한 리소스 차단
async def setup_page_optimization(page):
    # 이미지, 스타일시트 등 차단
    await page.route('**/*.{png,jpg,jpeg,gif,css}', lambda route: route.abort())
    
    # ExtJS 디버그 모드 비활성화
    await page.evaluate("() => { Ext.Loader.setConfig({enabled: false}); }")
```

### 3. 에러 처리
```python
async def safe_extjs_action(page, action_code):
    """안전한 ExtJS 액션 실행"""
    
    try:
        result = await page.evaluate(f"""
            () => {{
                try {{
                    {action_code}
                    return {{success: true}};
                }} catch (e) {{
                    return {{success: false, error: e.toString()}};
                }}
            }}
        """)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## 📋 체크리스트

### ExtJS 스크래핑 시작 전 확인사항

- [ ] ExtJS 버전 확인 (4.x, 5.x, 6.x, 7.x)
- [ ] 인증 방식 파악 (세션, 토큰, 쿠키)
- [ ] 주요 컴포넌트 ID/클래스 패턴 분석
- [ ] Store 구조 및 데이터 모델 이해
- [ ] Ajax 엔드포인트 매핑
- [ ] 에러 처리 및 메시지 박스 패턴
- [ ] 로딩 인디케이터 패턴

## 🔧 트러블슈팅

### 문제 1: "Ext is not defined"
**원인**: ExtJS가 아직 로드되지 않음
**해결**: 
```python
await page.wait_for_function("() => typeof Ext !== 'undefined'")
```

### 문제 2: 동적 ID로 요소를 찾을 수 없음
**원인**: ExtJS가 매번 다른 ID 생성
**해결**: ComponentQuery 사용
```python
await page.evaluate("Ext.ComponentQuery.query('grid[title=\"My Grid\"]')[0]")
```

### 문제 3: 스토어 데이터가 비어있음
**원인**: 비동기 로딩이 완료되지 않음
**해결**: 
```python
await page.wait_for_function("""
    () => {
        const grid = Ext.ComponentQuery.query('grid')[0];
        return grid && grid.getStore().getCount() > 0;
    }
""")
```

## 📚 참고 자료

- [ExtJS 6.2 Documentation](https://docs.sencha.com/extjs/6.2.0/)
- [ExtJS Component Query Guide](https://docs.sencha.com/extjs/6.2.0/guides/components/components_query.html)
- [ExtJS Store API](https://docs.sencha.com/extjs/6.2.0/classic/Ext.data.Store.html)
- [Playwright Documentation](https://playwright.dev/python/)

## 💼 실전 예제: MEK-ICS ERP 자동화

```python
from playwright.async_api import async_playwright
from extjs_helper import ExtJSHelper

async def automate_mekics_order_entry():
    """MEK-ICS 주문 입력 자동화"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 로그인
        await page.goto("https://it.mek-ics.com/mekics/login/login.do")
        # ... 로그인 처리 ...
        
        # ExtJS Helper 초기화
        extjs = ExtJSHelper(page)
        await extjs.wait_for_extjs()
        
        # 영업관리 모듈로 이동
        await navigate_to_module(page, '영업관리')
        await page.wait_for_timeout(3000)
        
        # 주문입력 메뉴 클릭
        await extjs.click_menu('주문입력')
        await extjs.wait_for_loading()
        
        # 그리드 데이터 추출
        order_data = await extjs.get_grid_data('grid[title="주문목록"]')
        print(f"주문 건수: {order_data['total']}")
        
        # 새 주문 입력
        await extjs.fill_form({
            'customerCode': 'C001',
            'orderDate': '2024-08-10',
            'productCode': 'P001',
            'quantity': 100
        })
        
        await extjs.submit_form()
        
        # 결과 확인
        message = await extjs.get_message_box_text()
        if message:
            print(f"시스템 메시지: {message}")
        
        await browser.close()

# 실행
import asyncio
asyncio.run(automate_mekics_order_entry())
```

## 🎯 핵심 요약

1. **ExtJS는 100% JavaScript 기반**: 반드시 브라우저 자동화 도구 사용
2. **ExtJS API 직접 활용이 가장 효율적**: DOM 셀렉터보다 ComponentQuery 선호
3. **비동기 처리가 핵심**: 모든 작업에 적절한 대기 전략 필요
4. **스토어 중심 사고**: 데이터는 Store에서, UI는 Component에서
5. **이벤트 기반 상호작용**: fireEvent()로 사용자 액션 시뮬레이션

---

*이 문서는 ExtJS 6.2.0과 OMEGA Plus ERP 시스템을 기준으로 작성되었습니다.*
*지속적으로 업데이트되는 living document입니다.*
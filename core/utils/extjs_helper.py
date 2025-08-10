#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ExtJS Helper - ExtJS 애플리케이션 자동화 유틸리티
ExtJS 6.x 기반 웹 애플리케이션 스크래핑을 위한 헬퍼 클래스
"""

from typing import Dict, List, Any, Optional
import asyncio
from playwright.async_api import Page


class ExtJSHelper:
    """ExtJS 애플리케이션 스크래핑 헬퍼"""
    
    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page 객체
        """
        self.page = page
    
    async def wait_for_extjs(self, timeout: int = 30000) -> bool:
        """ExtJS 프레임워크 로드 완료 대기
        
        Args:
            timeout: 대기 시간 (밀리초)
            
        Returns:
            bool: ExtJS 로드 성공 여부
        """
        try:
            await self.page.wait_for_function(
                "() => typeof Ext !== 'undefined' && Ext.isReady",
                timeout=timeout
            )
            
            # ExtJS 버전 정보 가져오기
            version = await self.page.evaluate("""
                () => {
                    if (typeof Ext !== 'undefined' && Ext.getVersion) {
                        return Ext.getVersion().version;
                    }
                    return null;
                }
            """)
            
            if version:
                print(f"[ExtJS] 프레임워크 로드 완료 (버전: {version})")
            
            return True
            
        except Exception as e:
            print(f"[ExtJS] 프레임워크 로드 실패: {e}")
            return False
    
    async def get_grid_data(self, grid_selector: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """ExtJS 그리드에서 데이터 추출
        
        Args:
            grid_selector: 그리드 선택자 (예: 'grid[title="주문목록"]')
            
        Returns:
            dict: 그리드 데이터 (columns, data, total)
        """
        try:
            return await self.page.evaluate("""
                (selector) => {
                    let grid;
                    if (selector) {
                        grid = Ext.ComponentQuery.query(selector)[0];
                    } else {
                        // 첫 번째 그리드 찾기
                        grid = Ext.ComponentQuery.query('grid')[0];
                    }
                    
                    if (!grid) return null;
                    
                    const store = grid.getStore();
                    if (!store) return null;
                    
                    // 컬럼 정보
                    const columns = grid.getColumns()
                        .filter(col => !col.hidden)
                        .map(col => ({
                            dataIndex: col.dataIndex,
                            text: col.text || col.header
                        }));
                    
                    // 데이터 추출
                    const data = store.getData().items.map(record => record.data);
                    
                    return {
                        columns: columns,
                        data: data,
                        total: store.getTotalCount(),
                        currentPage: store.currentPage,
                        pageSize: store.pageSize
                    };
                }
            """, grid_selector)
            
        except Exception as e:
            print(f"[ExtJS] 그리드 데이터 추출 실패: {e}")
            return None
    
    async def click_menu(self, menu_text: str) -> bool:
        """메뉴 항목 클릭
        
        Args:
            menu_text: 메뉴 텍스트
            
        Returns:
            bool: 클릭 성공 여부
        """
        try:
            result = await self.page.evaluate(f"""
                () => {{
                    // 트리 패널에서 찾기
                    const trees = Ext.ComponentQuery.query('treepanel');
                    for (let tree of trees) {{
                        const node = tree.getStore().findNode('text', '{menu_text}');
                        if (node) {{
                            tree.getSelectionModel().select(node);
                            tree.fireEvent('itemclick', tree, node);
                            return true;
                        }}
                    }}
                    
                    // 메뉴 아이템에서 찾기
                    const menuItem = Ext.ComponentQuery.query('menuitem{{text:"{menu_text}"}}')[0];
                    if (menuItem) {{
                        menuItem.fireEvent('click', menuItem);
                        return true;
                    }}
                    
                    // 버튼에서 찾기
                    const button = Ext.ComponentQuery.query('button{{text:"{menu_text}"}}')[0];
                    if (button) {{
                        button.fireEvent('click', button);
                        return true;
                    }}
                    
                    return false;
                }}
            """)
            
            if result:
                print(f"[ExtJS] '{menu_text}' 클릭 성공")
                await self.wait_for_loading()
            else:
                print(f"[ExtJS] '{menu_text}' 찾을 수 없음")
            
            return result
            
        except Exception as e:
            print(f"[ExtJS] 메뉴 클릭 실패: {e}")
            return False
    
    async def fill_form(self, form_data: Dict[str, Any], form_selector: Optional[str] = None) -> bool:
        """폼 데이터 입력
        
        Args:
            form_data: 입력할 데이터 딕셔너리
            form_selector: 폼 선택자
            
        Returns:
            bool: 입력 성공 여부
        """
        try:
            return await self.page.evaluate("""
                (data, selector) => {
                    let form;
                    if (selector) {
                        form = Ext.ComponentQuery.query(selector)[0];
                    } else {
                        form = Ext.ComponentQuery.query('form')[0];
                    }
                    
                    if (form && form.getForm) {
                        form.getForm().setValues(data);
                        return true;
                    }
                    
                    // 개별 필드 설정 시도
                    for (let fieldName in data) {
                        const field = Ext.ComponentQuery.query(`field[name="${fieldName}"]`)[0];
                        if (field) {
                            field.setValue(data[fieldName]);
                        }
                    }
                    
                    return true;
                }
            """, form_data, form_selector)
            
        except Exception as e:
            print(f"[ExtJS] 폼 입력 실패: {e}")
            return False
    
    async def submit_form(self, form_selector: Optional[str] = None) -> bool:
        """폼 제출
        
        Args:
            form_selector: 폼 선택자
            
        Returns:
            bool: 제출 성공 여부
        """
        try:
            return await self.page.evaluate("""
                (selector) => {
                    let form;
                    if (selector) {
                        form = Ext.ComponentQuery.query(selector)[0];
                    } else {
                        form = Ext.ComponentQuery.query('form')[0];
                    }
                    
                    if (form && form.getForm) {
                        if (form.getForm().isValid()) {
                            form.getForm().submit();
                            return true;
                        }
                    }
                    
                    // 저장 버튼 클릭 시도
                    const saveBtn = Ext.ComponentQuery.query('button[text="저장"]')[0] ||
                                   Ext.ComponentQuery.query('button[text="Save"]')[0];
                    if (saveBtn) {
                        saveBtn.fireEvent('click', saveBtn);
                        return true;
                    }
                    
                    return false;
                }
            """, form_selector)
            
        except Exception as e:
            print(f"[ExtJS] 폼 제출 실패: {e}")
            return False
    
    async def wait_for_loading(self, timeout: int = 30000) -> None:
        """로딩 완료 대기
        
        Args:
            timeout: 대기 시간 (밀리초)
        """
        try:
            # 로딩 마스크 대기
            await self.page.wait_for_function(
                """
                () => {
                    // 로딩 마스크 확인
                    const masks = Ext.ComponentQuery.query('loadmask');
                    const allHidden = masks.every(mask => !mask.isVisible());
                    
                    // Ajax 로딩 확인
                    const ajaxLoading = typeof Ext.Ajax !== 'undefined' ? 
                                       Ext.Ajax.isLoading() === false : true;
                    
                    return allHidden && ajaxLoading;
                }
                """,
                timeout=timeout
            )
            
        except Exception as e:
            print(f"[ExtJS] 로딩 대기 타임아웃: {e}")
    
    async def get_store_data(self, store_id: str) -> Optional[List[Dict[str, Any]]]:
        """Store에서 직접 데이터 가져오기
        
        Args:
            store_id: Store ID
            
        Returns:
            list: Store 데이터 리스트
        """
        try:
            return await self.page.evaluate(f"""
                () => {{
                    const store = Ext.StoreManager.lookup('{store_id}');
                    if (store) {{
                        return store.getData().items.map(record => record.data);
                    }}
                    return null;
                }}
            """)
            
        except Exception as e:
            print(f"[ExtJS] Store 데이터 추출 실패: {e}")
            return None
    
    async def wait_for_store_load(self, store_id: str, timeout: int = 30000) -> bool:
        """Store 로드 완료 대기
        
        Args:
            store_id: Store ID
            timeout: 대기 시간 (밀리초)
            
        Returns:
            bool: 로드 성공 여부
        """
        try:
            await self.page.wait_for_function(
                f"""
                () => {{
                    const store = Ext.StoreManager.lookup('{store_id}');
                    return store && store.isLoaded() && !store.isLoading();
                }}
                """,
                timeout=timeout
            )
            return True
            
        except Exception as e:
            print(f"[ExtJS] Store 로드 대기 실패: {e}")
            return False
    
    async def get_message_box_text(self) -> Optional[str]:
        """메시지 박스 텍스트 가져오기
        
        Returns:
            str: 메시지 텍스트
        """
        try:
            return await self.page.evaluate("""
                () => {
                    if (Ext.Msg && Ext.Msg.isVisible()) {
                        return Ext.Msg.getMsg();
                    }
                    
                    // 커스텀 메시지 박스 확인
                    const msgBox = Ext.ComponentQuery.query('messagebox[hidden=false]')[0];
                    if (msgBox) {
                        return msgBox.msg;
                    }
                    
                    return null;
                }
            """)
            
        except Exception as e:
            print(f"[ExtJS] 메시지 박스 텍스트 추출 실패: {e}")
            return None
    
    async def close_message_box(self) -> bool:
        """메시지 박스 닫기
        
        Returns:
            bool: 닫기 성공 여부
        """
        try:
            return await self.page.evaluate("""
                () => {
                    if (Ext.Msg && Ext.Msg.isVisible()) {
                        Ext.Msg.hide();
                        return true;
                    }
                    
                    const msgBox = Ext.ComponentQuery.query('messagebox[hidden=false]')[0];
                    if (msgBox) {
                        msgBox.close();
                        return true;
                    }
                    
                    return false;
                }
            """)
            
        except Exception as e:
            print(f"[ExtJS] 메시지 박스 닫기 실패: {e}")
            return False
    
    async def close_all_windows(self) -> int:
        """모든 윈도우 닫기
        
        Returns:
            int: 닫은 윈도우 개수
        """
        try:
            return await self.page.evaluate("""
                () => {
                    let count = 0;
                    Ext.WindowManager.each(function(win) {
                        win.close();
                        count++;
                    });
                    return count;
                }
            """)
            
        except Exception as e:
            print(f"[ExtJS] 윈도우 닫기 실패: {e}")
            return 0
    
    async def expand_tree_node(self, node_text: str, tree_selector: Optional[str] = None) -> bool:
        """트리 노드 확장
        
        Args:
            node_text: 노드 텍스트
            tree_selector: 트리 선택자
            
        Returns:
            bool: 확장 성공 여부
        """
        try:
            return await self.page.evaluate("""
                (text, selector) => {
                    let tree;
                    if (selector) {
                        tree = Ext.ComponentQuery.query(selector)[0];
                    } else {
                        tree = Ext.ComponentQuery.query('treepanel')[0];
                    }
                    
                    if (tree) {
                        const node = tree.getStore().findNode('text', text);
                        if (node) {
                            if (!node.isExpanded()) {
                                node.expand();
                            }
                            return true;
                        }
                    }
                    
                    return false;
                }
            """, node_text, tree_selector)
            
        except Exception as e:
            print(f"[ExtJS] 트리 노드 확장 실패: {e}")
            return False
    
    async def get_component_property(self, component_query: str, property_name: str) -> Any:
        """컴포넌트 속성 가져오기
        
        Args:
            component_query: 컴포넌트 쿼리 (예: 'grid[title="목록"]')
            property_name: 속성 이름
            
        Returns:
            Any: 속성 값
        """
        try:
            return await self.page.evaluate(f"""
                () => {{
                    const component = Ext.ComponentQuery.query('{component_query}')[0];
                    if (component) {{
                        return component.{property_name};
                    }}
                    return null;
                }}
            """)
            
        except Exception as e:
            print(f"[ExtJS] 컴포넌트 속성 추출 실패: {e}")
            return None
    
    async def fire_event(self, component_query: str, event_name: str, *args) -> bool:
        """컴포넌트 이벤트 발생
        
        Args:
            component_query: 컴포넌트 쿼리
            event_name: 이벤트 이름
            *args: 이벤트 인자
            
        Returns:
            bool: 이벤트 발생 성공 여부
        """
        try:
            return await self.page.evaluate("""
                (query, eventName, args) => {
                    const component = Ext.ComponentQuery.query(query)[0];
                    if (component) {
                        component.fireEvent(eventName, ...args);
                        return true;
                    }
                    return false;
                }
            """, component_query, event_name, list(args))
            
        except Exception as e:
            print(f"[ExtJS] 이벤트 발생 실패: {e}")
            return False


class MEKICSHelper(ExtJSHelper):
    """MEK-ICS (OMEGA Plus) 전용 헬퍼"""
    
    def __init__(self, page: Page):
        super().__init__(page)
        
        # MEK-ICS 모듈 ID 매핑
        self.module_map = {
            '기준정보': '11',
            '인사/급여관리': '12',
            '회계관리': '13',
            '영업관리': '14',
            '생산관리': '15',
            '구매/자재': '16',
            '재고관리': '18',
            '원가관리': '21',
            '품질관리': '65',
            'AS': '64',
            '장비관리': '32',
            'TV현황판': '20'
        }
    
    async def navigate_to_module(self, module_name: str) -> bool:
        """MEK-ICS 모듈로 이동
        
        Args:
            module_name: 모듈 이름 (예: '영업관리')
            
        Returns:
            bool: 이동 성공 여부
        """
        module_id = self.module_map.get(module_name)
        if not module_id:
            print(f"[MEK-ICS] 알 수 없는 모듈: {module_name}")
            return False
        
        try:
            result = await self.page.evaluate(f"""
                () => {{
                    if (typeof changeModule === 'function') {{
                        changeModule('{module_id}');
                        return true;
                    }}
                    return false;
                }}
            """)
            
            if result:
                print(f"[MEK-ICS] '{module_name}' 모듈로 이동")
                await self.wait_for_loading()
            
            return result
            
        except Exception as e:
            print(f"[MEK-ICS] 모듈 이동 실패: {e}")
            return False
    
    async def get_current_module(self) -> Optional[str]:
        """현재 모듈 가져오기
        
        Returns:
            str: 현재 모듈 이름
        """
        try:
            module_id = await self.page.evaluate("""
                () => {
                    // 현재 활성 모듈 ID 찾기
                    const header = document.querySelector('.moduleNameBox');
                    if (header) {
                        return header.innerText;
                    }
                    return null;
                }
            """)
            
            return module_id
            
        except Exception as e:
            print(f"[MEK-ICS] 현재 모듈 확인 실패: {e}")
            return None
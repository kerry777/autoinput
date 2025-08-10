#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEK-ICS 매출현황 실제 작동 버전
프레임을 고려한 정확한 자동화
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def run():
    site_dir = Path("sites/mekics")
    data_dir = site_dir / "data"
    
    config_path = site_dir / "config" / "settings.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            downloads_path=str(data_dir)
        )
        
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul',
            viewport={'width': 1920, 'height': 1080},
            accept_downloads=True
        )
        
        cookie_file = data_dir / "cookies.json"
        if cookie_file.exists():
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("쿠키 로드 완료")
        
        page = await context.new_page()
        
        try:
            # 1. 메인 페이지
            print("\n1. 메인 페이지 접속...")
            await page.goto("https://it.mek-ics.com/mekics/main_mics.do")
            await page.wait_for_timeout(5000)
            
            # 2. 영업관리 모듈 클릭
            print("2. 영업관리 모듈 클릭...")
            await page.evaluate("() => { if(typeof changeModule === 'function') changeModule('14'); }")
            await page.wait_for_timeout(5000)
            
            # 3. 매출관리 메뉴 확장
            print("3. 매출관리 메뉴 클릭...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText.includes('매출관리')) {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(2000)
            
            # 4. 매출현황조회 클릭
            print("4. 매출현황조회 클릭...")
            await page.evaluate("""
                () => {
                    const nodes = document.querySelectorAll('.x-tree-node-text');
                    for(let node of nodes) {
                        if(node.innerText && node.innerText === '매출현황조회') {
                            node.click();
                            break;
                        }
                    }
                }
            """)
            await page.wait_for_timeout(5000)
            
            # 5. 프레임 확인 및 작업 프레임 선택
            print("\n5. 프레임 구조 확인...")
            frames = page.frames
            print(f"   총 프레임 수: {len(frames)}")
            
            # 메인 프레임이 아닌 실제 컨텐츠 프레임 찾기
            work_frame = None
            for frame in frames:
                if "about:blank" not in frame.url and frame != page.main_frame:
                    work_frame = frame
                    print(f"   작업 프레임: {frame.url}")
                    break
            
            if not work_frame:
                work_frame = page  # 프레임이 없으면 메인 페이지 사용
                print("   메인 페이지에서 작업")
            
            # 6. 날짜 설정 - 직접 입력 방식
            print("\n6. 날짜 설정 (2024.08.05 ~ 2024.08.09)...")
            
            # ExtJS가 로드될 때까지 대기
            await work_frame.wait_for_function("() => typeof Ext !== 'undefined'")
            
            # 날짜 필드 찾아서 값 설정
            date_result = await work_frame.evaluate("""
                () => {
                    const result = [];
                    
                    // 방법 1: name 속성으로 직접 찾기
                    const fromInput = document.querySelector('input[name="SALE_FR_DATE"]');
                    const toInput = document.querySelector('input[name="SALE_TO_DATE"]');
                    
                    if(fromInput && toInput) {
                        fromInput.value = '2024.08.05';
                        toInput.value = '2024.08.09';
                        
                        // change 이벤트 발생
                        fromInput.dispatchEvent(new Event('change', { bubbles: true }));
                        toInput.dispatchEvent(new Event('change', { bubbles: true }));
                        
                        result.push('DOM 직접 설정 완료');
                    }
                    
                    // 방법 2: ExtJS 컴포넌트로 설정
                    if(typeof Ext !== 'undefined') {
                        const dateFields = Ext.ComponentQuery.query('datefield');
                        
                        if(dateFields.length >= 2) {
                            // 첫 번째 필드 = 시작일
                            dateFields[0].setValue(new Date(2024, 7, 5));  // 8월 5일
                            // 두 번째 필드 = 종료일  
                            dateFields[1].setValue(new Date(2024, 7, 9));  // 8월 9일
                            
                            result.push(`ExtJS 날짜 설정: ${dateFields.length}개 필드`);
                        }
                        
                        // 각 필드의 레이블 확인
                        dateFields.forEach((field, idx) => {
                            const label = field.getFieldLabel ? field.getFieldLabel() : '';
                            const value = field.getValue ? field.getValue() : '';
                            result.push(`필드${idx}: ${label} = ${value}`);
                        });
                    }
                    
                    return result;
                }
            """)
            
            for res in date_result:
                print(f"   - {res}")
            
            # 7. 구분을 '전체'로 변경
            print("\n7. 국내/해외 구분을 '전체'로 설정...")
            combo_result = await work_frame.evaluate("""
                () => {
                    if(typeof Ext !== 'undefined') {
                        const combos = Ext.ComponentQuery.query('combobox');
                        
                        for(let combo of combos) {
                            const label = combo.getFieldLabel ? combo.getFieldLabel() : '';
                            const name = combo.getName ? combo.getName() : '';
                            
                            // 구분 관련 콤보박스 찾기
                            if(label.includes('구분') || name.includes('DIV') || label.includes('국내')) {
                                // 전체 선택 (보통 빈값 또는 'ALL')
                                combo.setValue('');
                                return `구분 설정 완료: ${label}`;
                            }
                        }
                        
                        // 첫 번째 콤보박스를 구분으로 가정
                        if(combos.length > 0) {
                            combos[0].setValue('');
                            return '첫 번째 콤보박스를 전체로 설정';
                        }
                    }
                    return '구분 콤보박스 미발견';
                }
            """)
            print(f"   - {combo_result}")
            
            # 8. 조회 실행
            print("\n8. 조회 실행...")
            
            # ExtJS 버튼으로 시도
            query_result = await work_frame.evaluate("""
                () => {
                    if(typeof Ext !== 'undefined') {
                        const buttons = Ext.ComponentQuery.query('button');
                        
                        for(let btn of buttons) {
                            const text = btn.getText ? btn.getText() : '';
                            
                            // '조회' 텍스트를 포함하는 버튼
                            if(text.includes('조회') || text.toLowerCase().includes('search')) {
                                btn.fireEvent('click', btn);
                                return `조회 버튼 클릭: ${text}`;
                            }
                        }
                    }
                    
                    // DOM에서 직접 찾기
                    const buttons = document.querySelectorAll('button, a[class*="btn"]');
                    for(let btn of buttons) {
                        const text = btn.innerText || btn.textContent || '';
                        if(text.includes('조회')) {
                            btn.click();
                            return 'DOM 조회 버튼 클릭';
                        }
                    }
                    
                    return '조회 버튼 미발견';
                }
            """)
            print(f"   - {query_result}")
            
            # F2 키도 누르기
            await page.keyboard.press('F2')
            print("   - F2 키 입력")
            
            # 데이터 로딩 대기
            print("\n9. 데이터 로딩 대기...")
            await page.wait_for_timeout(7000)
            
            # 10. 그리드 데이터 확인
            print("\n10. 조회 결과 확인...")
            grid_info = await work_frame.evaluate("""
                () => {
                    if(typeof Ext !== 'undefined') {
                        const grids = Ext.ComponentQuery.query('grid');
                        
                        if(grids.length > 0) {
                            const grid = grids[0];
                            const store = grid.getStore();
                            const count = store.getCount();
                            
                            // 처음 3개 데이터 샘플
                            const items = store.getData().items.slice(0, 3);
                            const sample = items.map(item => {
                                const data = item.data;
                                // 주요 필드만 추출
                                return {
                                    거래처: data.CUST_NAME || data.cust_name || '',
                                    매출일: data.SALE_DATE || data.sale_date || '',
                                    금액: data.SALE_AMT || data.sale_amt || 0
                                };
                            });
                            
                            return {
                                count: count,
                                total: store.getTotalCount(),
                                sample: sample
                            };
                        }
                    }
                    
                    // DOM에서 직접 확인
                    const rows = document.querySelectorAll('.x-grid-row');
                    return {
                        count: rows.length,
                        total: rows.length
                    };
                }
            """)
            
            print(f"   조회 건수: {grid_info['count']}건")
            if grid_info.get('sample'):
                print("   샘플 데이터:")
                for row in grid_info['sample']:
                    print(f"     - {row}")
            
            # 11. 엑셀 다운로드
            print("\n11. 엑셀 다운로드...")
            
            # 다운로드 이벤트 리스너 설정
            async with page.expect_download() as download_info:
                # 엑셀 버튼 클릭
                excel_result = await work_frame.evaluate("""
                    () => {
                        // 툴팁으로 찾기
                        const elements = document.querySelectorAll('[title*="엑셀"], [tooltip*="엑셀"]');
                        if(elements.length > 0) {
                            elements[0].click();
                            return '엑셀 요소 클릭 (툴팁)';
                        }
                        
                        // ExtJS 버튼
                        if(typeof Ext !== 'undefined') {
                            const buttons = Ext.ComponentQuery.query('button');
                            
                            for(let btn of buttons) {
                                const text = btn.getText ? btn.getText() : '';
                                const tooltip = btn.tooltip || '';
                                
                                if(text.includes('엑셀') || text.includes('Excel') ||
                                   tooltip.includes('엑셀') || tooltip.includes('Excel')) {
                                    btn.fireEvent('click', btn);
                                    return `ExtJS 엑셀 버튼 클릭: ${text || tooltip}`;
                                }
                            }
                            
                            // 툴바 아이템
                            const tools = Ext.ComponentQuery.query('tool');
                            for(let tool of tools) {
                                if(tool.tooltip && tool.tooltip.includes('엑셀')) {
                                    tool.fireEvent('click', tool);
                                    return '엑셀 툴 클릭';
                                }
                            }
                        }
                        
                        // 아이콘 클래스로 찾기
                        const icons = document.querySelectorAll('[class*="excel"], [class*="xls"]');
                        if(icons.length > 0) {
                            icons[0].click();
                            return '엑셀 아이콘 클릭';
                        }
                        
                        return '엑셀 버튼 미발견';
                    }
                """)
                print(f"   - {excel_result}")
                
                # 다운로드 대기
                try:
                    download = await download_info.value
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_path = data_dir / f"매출현황_{timestamp}.xlsx"
                    await download.save_as(str(save_path))
                    print(f"   ✅ 저장 완료: {save_path}")
                except:
                    print("   ⚠️ 다운로드 실패 - 수동으로 클릭 필요")
            
            # 12. 스크린샷
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = data_dir / f"매출조회완료_{timestamp}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"\n12. 스크린샷 저장: {screenshot_path}")
            
            print("\n" + "="*60)
            print("✅ 매출현황 자동화 완료!")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # 오류 시 스크린샷
            await page.screenshot(path=str(data_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
        
        finally:
            print("\n30초 후 브라우저 종료...")
            await page.wait_for_timeout(30000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
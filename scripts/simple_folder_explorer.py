#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단한 Bizmeka 폴더 탐색기
유니코드 오류 없는 버전
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright


async def explore_folders():
    """폴더 탐색"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()
        
        try:
            # 기존 쿠키 로드 (수동으로)
            cookie_file = Path("sites/bizmeka/data/cookies.json")
            if cookie_file.exists():
                import json
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print("[OK] 쿠키 로드 완료")
            
            # 메인 페이지
            await page.goto("https://bizmeka.com")
            await page.wait_for_timeout(3000)
            
            # 메일 시스템
            mail_link = await page.query_selector('a[href*="mail"]')
            if mail_link:
                await mail_link.click()
                await page.wait_for_timeout(3000)
            
            if len(context.pages) > 1:
                page = context.pages[-1]
            
            # 팝업 처리
            for _ in range(3):
                await page.keyboard.press('Escape')
                await page.wait_for_timeout(500)
            
            # 폴더 탐색
            print("\n[FOLDERS] mnu_로 시작하는 모든 링크 찾기...")
            
            mnu_links = await page.query_selector_all('[id^="mnu_"]')
            print(f"발견된 링크 수: {len(mnu_links)}")
            
            folders = []
            for i, link in enumerate(mnu_links):
                try:
                    link_id = await link.get_attribute('id') or ''
                    link_text = await link.inner_text() or ''
                    
                    if link_text.strip():
                        folders.append({
                            'index': i,
                            'id': link_id,
                            'text': link_text.strip()
                        })
                        print(f"  {i+1}. {link_text.strip()} ({link_id})")
                
                except Exception as e:
                    print(f"  ERROR {i}: {e}")
            
            # 각 폴더 테스트
            print(f"\n[TEST] 각 폴더 클릭 테스트...")
            
            results = []
            for folder in folders[:5]:  # 처음 5개만
                try:
                    print(f"\n--- 테스트: {folder['text']} ---")
                    
                    # 폴더 클릭
                    folder_link = await page.query_selector(f"#{folder['id']}")
                    if folder_link:
                        await folder_link.click()
                        await page.wait_for_timeout(3000)
                        
                        # 팝업 처리
                        await page.keyboard.press('Escape')
                        await page.wait_for_timeout(1000)
                        
                        # 메일 아이템 확인
                        mail_items = await page.query_selector_all('li.m_data')
                        print(f"  메일 수: {len(mail_items)}개")
                        
                        # 샘플 데이터
                        if mail_items:
                            first_item = mail_items[0]
                            from_name = await first_item.get_attribute('data-fromname') or ''
                            subject_elem = await first_item.query_selector('p.m_subject')
                            subject = ''
                            if subject_elem:
                                subject = await subject_elem.inner_text() or ''
                            
                            print(f"  샘플: {from_name} - {subject[:30]}...")
                        
                        results.append({
                            'folder': folder['text'],
                            'id': folder['id'],
                            'mail_count': len(mail_items),
                            'accessible': True
                        })
                    else:
                        print(f"  링크를 찾을 수 없음")
                        results.append({
                            'folder': folder['text'],
                            'id': folder['id'],
                            'mail_count': 0,
                            'accessible': False
                        })
                
                except Exception as e:
                    print(f"  오류: {e}")
                    results.append({
                        'folder': folder['text'],
                        'id': folder['id'],
                        'mail_count': 0,
                        'accessible': False,
                        'error': str(e)
                    })
            
            # 결과 출력
            print(f"\n{'='*50}")
            print("탐색 결과:")
            print(f"{'='*50}")
            
            total_accessible = 0
            total_mails = 0
            
            for result in results:
                status = "[OK]" if result['accessible'] else "[FAIL]"
                print(f"{status} {result['folder']}: {result['mail_count']}개")
                
                if result['accessible']:
                    total_accessible += 1
                    total_mails += result['mail_count']
            
            print(f"\n요약:")
            print(f"  - 접근 가능한 폴더: {total_accessible}개")
            print(f"  - 총 메일 수: {total_mails}개")
            
            # JSON 저장
            import json
            output_file = "sites/bizmeka/data/folder_exploration_results.json"
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': str(asyncio.get_event_loop().time()),
                    'total_folders_found': len(folders),
                    'tested_folders': len(results),
                    'accessible_folders': total_accessible,
                    'total_mails': total_mails,
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n결과 저장: {output_file}")
            
        except Exception as e:
            print(f"전체 오류: {e}")
            
        finally:
            print("Enter를 누르면 종료...")
            try:
                input()
            except:
                await asyncio.sleep(5)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_folders())
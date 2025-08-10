#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bizmeka 메일 폴더 탐색 실험 스크립트
모든 메일 폴더를 발견하고 구조를 분석
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.async_api import async_playwright
from sites.bizmeka import BizmekaAuth


class MailFolderExplorer:
    """메일 폴더 탐색 및 분석 클래스"""
    
    def __init__(self):
        self.page = None
        self.context = None
        self.discovered_folders = []
        
    async def setup_browser(self, context, page):
        """브라우저 설정"""
        self.context = context
        self.page = page
    
    async def discover_all_folders(self):
        """모든 메일 폴더 발견"""
        print("\n🔍 메일 폴더 탐색 중...")
        
        folders = []
        
        try:
            # mnu_로 시작하는 모든 링크 찾기
            mnu_links = await self.page.query_selector_all('[id^="mnu_"]')
            print(f"   → {len(mnu_links)}개의 mnu_ 링크 발견")
            
            for i, link in enumerate(mnu_links):
                try:
                    folder_info = {
                        'index': i,
                        'id': await link.get_attribute('id') or '',
                        'text': await link.inner_text() or '',
                        'onclick': await link.get_attribute('onclick') or '',
                        'href': await link.get_attribute('href') or '',
                        'class': await link.get_attribute('class') or '',
                        'title': await link.get_attribute('title') or ''
                    }
                    
                    # 메일 관련 폴더만 필터링
                    folder_id = folder_info['id'].lower()
                    if any(keyword in folder_id for keyword in ['inbox', 'sent', 'draft', 'trash', 'spam', 'mail']):
                        folders.append(folder_info)
                        print(f"   ✅ 메일 폴더 발견: {folder_info['text']} ({folder_info['id']})")
                    elif folder_info['text'] and len(folder_info['text'].strip()) > 0:
                        folders.append(folder_info)
                        print(f"   📁 기타 폴더: {folder_info['text']} ({folder_info['id']})")
                        
                except Exception as e:
                    print(f"   ❌ 링크 {i} 분석 실패: {e}")
                    continue
            
            # 프레임 내부도 확인
            for frame in self.page.frames:
                if 'mail' in frame.url.lower():
                    print(f"\n🖼️ 메일 프레임에서 추가 탐색: {frame.url[:50]}...")
                    try:
                        frame_links = await frame.query_selector_all('[id^="mnu_"], a:contains("메일"), a:contains("폴더")')
                        print(f"   → 프레임에서 {len(frame_links)}개 추가 링크 발견")
                        
                        for link in frame_links:
                            folder_info = {
                                'frame_url': frame.url,
                                'id': await link.get_attribute('id') or '',
                                'text': await link.inner_text() or '',
                                'onclick': await link.get_attribute('onclick') or ''
                            }
                            
                            if folder_info['text'].strip():
                                folders.append(folder_info)
                                print(f"   📫 프레임 폴더: {folder_info['text']}")
                                
                    except Exception as e:
                        print(f"   ❌ 프레임 탐색 실패: {e}")
            
            self.discovered_folders = folders
            return folders
            
        except Exception as e:
            print(f"❌ 폴더 발견 실패: {e}")
            return []
    
    async def analyze_folder_structure(self, folder_info):
        """특정 폴더의 구조 분석"""
        folder_name = folder_info.get('text', 'Unknown')
        folder_id = folder_info.get('id', '')
        
        print(f"\n📊 '{folder_name}' 폴더 구조 분석 중...")
        
        analysis = {
            'folder_name': folder_name,
            'folder_id': folder_id,
            'accessible': False,
            'mail_count': 0,
            'structure': {},
            'sample_data': [],
            'error': None
        }
        
        try:
            # 폴더 클릭 시도
            if folder_id:
                folder_link = await self.page.query_selector(f'#{folder_id}')
                if folder_link:
                    print(f"   → 폴더 클릭: {folder_id}")
                    await folder_link.click()
                    await self.page.wait_for_timeout(3000)
                    analysis['accessible'] = True
                    
                    # 팝업 처리
                    for _ in range(3):
                        await self.page.keyboard.press('Escape')
                        await self.page.wait_for_timeout(500)
                    
                    # 메일 아이템 확인
                    mail_items = await self.page.query_selector_all('li.m_data')
                    analysis['mail_count'] = len(mail_items)
                    print(f"   → 메일 아이템 수: {len(mail_items)}개")
                    
                    # 구조 분석
                    if mail_items:
                        # 첫 번째 메일로 구조 분석
                        first_mail = mail_items[0]
                        
                        structure = {
                            'has_checkbox': bool(await first_mail.query_selector('input[type="checkbox"]')),
                            'has_star': bool(await first_mail.query_selector('.btn_star')),
                            'has_attachment': bool(await first_mail.query_selector('.m_file')),
                            'has_sender': bool(await first_mail.query_selector('.m_sender')),
                            'has_subject': bool(await first_mail.query_selector('.m_subject')),
                            'has_date': bool(await first_mail.query_selector('.m_date')),
                            'has_size': bool(await first_mail.query_selector('.m_size'))
                        }
                        
                        analysis['structure'] = structure
                        print(f"   → 구조 특징: {structure}")
                        
                        # 샘플 데이터 수집 (최대 3개)
                        for i, item in enumerate(mail_items[:3]):
                            try:
                                sample = {
                                    'index': i,
                                    'id': await item.get_attribute('id') or '',
                                    'data_key': await item.get_attribute('data-key') or '',
                                    'data_fromname': await item.get_attribute('data-fromname') or '',
                                    'data_fromaddr': await item.get_attribute('data-fromaddr') or '',
                                    'class': await item.get_attribute('class') or '',
                                }
                                
                                # 텍스트 정보 추출
                                sender_elem = await item.query_selector('.m_sender')
                                subject_elem = await item.query_selector('.m_subject')
                                date_elem = await item.query_selector('.m_date')
                                size_elem = await item.query_selector('.m_size')
                                
                                if sender_elem:
                                    sample['sender_text'] = await sender_elem.inner_text()
                                if subject_elem:
                                    sample['subject_text'] = await subject_elem.inner_text()
                                if date_elem:
                                    sample['date_text'] = await date_elem.inner_text()
                                if size_elem:
                                    sample['size_text'] = await size_elem.inner_text()
                                
                                analysis['sample_data'].append(sample)
                                
                                # 첫 번째 샘플만 출력
                                if i == 0:
                                    print(f"   → 샘플: {sample.get('sender_text', '')} - {sample.get('subject_text', '')[:30]}...")
                                
                            except Exception as e:
                                print(f"   ❌ 샘플 {i} 분석 실패: {e}")
                    
                    # 페이지네이션 확인
                    pagination_links = await self.page.query_selector_all('a[href*="page"], .pagination a, a:has-text("2"), a:has-text("다음")')
                    analysis['has_pagination'] = len(pagination_links) > 0
                    print(f"   → 페이지네이션: {'있음' if analysis['has_pagination'] else '없음'}")
                    
                else:
                    print(f"   ❌ 폴더 링크를 찾을 수 없음: {folder_id}")
            else:
                print(f"   ❌ 폴더 ID가 없음")
                
        except Exception as e:
            print(f"   ❌ 분석 실패: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    async def save_analysis_results(self, all_analyses):
        """분석 결과를 파일로 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON 저장
        json_path = f'sites/bizmeka/data/folder_analysis_{timestamp}.json'
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': timestamp,
                'total_folders': len(self.discovered_folders),
                'analyzed_folders': len(all_analyses),
                'folder_analyses': all_analyses
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 분석 결과 저장: {json_path}")
        
        # 텍스트 리포트 저장
        report_path = f'sites/bizmeka/data/folder_report_{timestamp}.txt'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"Bizmeka 메일 폴더 분석 리포트\n")
            f.write(f"생성 시간: {timestamp}\n")
            f.write(f"총 발견 폴더: {len(self.discovered_folders)}개\n")
            f.write(f"분석 완료 폴더: {len(all_analyses)}개\n")
            f.write("="*60 + "\n\n")
            
            for analysis in all_analyses:
                f.write(f"폴더명: {analysis['folder_name']}\n")
                f.write(f"폴더ID: {analysis['folder_id']}\n")
                f.write(f"접근 가능: {'예' if analysis['accessible'] else '아니오'}\n")
                f.write(f"메일 수: {analysis['mail_count']}개\n")
                
                if analysis['structure']:
                    f.write("구조 특징:\n")
                    for key, value in analysis['structure'].items():
                        f.write(f"  - {key}: {'있음' if value else '없음'}\n")
                
                if analysis['sample_data']:
                    f.write("샘플 데이터:\n")
                    for i, sample in enumerate(analysis['sample_data'][:2], 1):
                        f.write(f"  {i}. {sample.get('sender_text', '')} - {sample.get('subject_text', '')}\n")
                
                f.write("\n" + "-"*40 + "\n\n")
        
        print(f"📄 텍스트 리포트 저장: {report_path}")
        
        return json_path, report_path


async def main():
    """메인 탐색 함수"""
    print("="*60)
    print("Bizmeka 메일 폴더 완전 탐색")
    print("="*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        page = await context.new_page()
        
        try:
            # 1. 로그인
            print("\n1. 인증 및 메일 시스템 접속...")
            auth = BizmekaAuth()
            await auth.setup_browser(context, page)
            
            if not await auth.ensure_login():
                print("❌ 로그인 실패")
                return
            
            # 메일 시스템으로 이동
            await page.goto("https://bizmeka.com")
            await page.wait_for_timeout(2000)
            
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
            
            # 2. 폴더 탐색
            explorer = MailFolderExplorer()
            await explorer.setup_browser(context, page)
            
            folders = await explorer.discover_all_folders()
            
            if not folders:
                print("❌ 발견된 폴더가 없습니다")
                return
            
            print(f"\n📂 총 {len(folders)}개 폴더 발견")
            
            # 3. 각 폴더 분석
            all_analyses = []
            
            for i, folder in enumerate(folders, 1):
                print(f"\n--- 폴더 {i}/{len(folders)} ---")
                analysis = await explorer.analyze_folder_structure(folder)
                all_analyses.append(analysis)
                
                # 분석 간 딜레이
                await page.wait_for_timeout(2000)
            
            # 4. 결과 저장
            json_path, report_path = await explorer.save_analysis_results(all_analyses)
            
            # 5. 요약 출력
            print("\n" + "="*60)
            print("🎉 탐색 완료!")
            print("="*60)
            
            accessible_count = sum(1 for a in all_analyses if a['accessible'])
            total_mails = sum(a['mail_count'] for a in all_analyses)
            
            print(f"📊 결과 요약:")
            print(f"  • 총 폴더: {len(folders)}개")
            print(f"  • 접근 가능: {accessible_count}개")
            print(f"  • 총 메일: {total_mails:,}개")
            
            print(f"\n📁 접근 가능한 폴더들:")
            for analysis in all_analyses:
                if analysis['accessible']:
                    print(f"  ✅ {analysis['folder_name']}: {analysis['mail_count']}개 메일")
            
            print(f"\n💾 저장된 파일:")
            print(f"  • JSON: {json_path}")
            print(f"  • 리포트: {report_path}")
            
        except Exception as e:
            print(f"\n💥 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            input("\nEnter를 누르면 브라우저를 닫습니다...")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
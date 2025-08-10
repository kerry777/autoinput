#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
웹사이트 구조 완전 분석 도구
- 프레임워크 감지
- 보안 메커니즘 파악
- 인증 방식 분석
- DOM 구조 매핑
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import json

class SiteAnalyzer:
    def __init__(self):
        self.analysis_result = {
            'url': '',
            'framework': {},
            'security': {},
            'authentication': {},
            'dom_structure': {},
            'network': {},
            'javascript': {},
            'forms': {},
            'api_endpoints': []
        }
        
    async def analyze_site(self, url):
        """사이트 완전 분석"""
        print(f"\n{'='*60}")
        print(f"사이트 구조 분석: {url}")
        print(f"{'='*60}\n")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 네트워크 요청 모니터링
        network_requests = []
        
        async def log_request(request):
            network_requests.append({
                'url': request.url,
                'method': request.method,
                'headers': request.headers,
                'post_data': request.post_data
            })
        
        page.on('request', log_request)
        
        try:
            # 페이지 로드
            await page.goto(url)
            await page.wait_for_timeout(3000)
            
            # 1. 프레임워크 감지
            framework_info = await self.detect_framework(page)
            print(f"[1] 프레임워크 분석")
            print(f"    - 타입: {framework_info.get('type', '알 수 없음')}")
            print(f"    - 렌더링: {framework_info.get('rendering', '알 수 없음')}")
            print(f"    - SPA: {framework_info.get('is_spa', False)}")
            
            # 2. 보안 메커니즘 분석
            security_info = await self.analyze_security(page)
            print(f"\n[2] 보안 메커니즘")
            print(f"    - CSRF 토큰: {security_info.get('has_csrf', False)}")
            print(f"    - 캡차: {security_info.get('has_captcha', False)}")
            print(f"    - 자동화 탐지: {security_info.get('automation_detection', False)}")
            
            # 3. 인증 방식 분석
            auth_info = await self.analyze_authentication(page)
            print(f"\n[3] 인증 방식")
            print(f"    - 로그인 폼: {auth_info.get('has_login_form', False)}")
            print(f"    - OAuth: {auth_info.get('has_oauth', False)}")
            print(f"    - 2FA: {auth_info.get('has_2fa', False)}")
            
            # 4. DOM 구조 분석
            dom_info = await self.analyze_dom_structure(page)
            print(f"\n[4] DOM 구조")
            print(f"    - 입력 필드: {dom_info.get('input_count', 0)}개")
            print(f"    - 버튼: {dom_info.get('button_count', 0)}개")
            print(f"    - 폼: {dom_info.get('form_count', 0)}개")
            print(f"    - iframe: {dom_info.get('iframe_count', 0)}개")
            
            # 5. JavaScript 분석
            js_info = await self.analyze_javascript(page)
            print(f"\n[5] JavaScript 환경")
            print(f"    - jQuery: {js_info.get('has_jquery', False)}")
            print(f"    - React: {js_info.get('has_react', False)}")
            print(f"    - Vue: {js_info.get('has_vue', False)}")
            print(f"    - Angular: {js_info.get('has_angular', False)}")
            
            # 6. 네트워크 분석
            print(f"\n[6] 네트워크 분석")
            api_endpoints = self.analyze_network(network_requests)
            print(f"    - API 엔드포인트: {len(api_endpoints)}개")
            for endpoint in api_endpoints[:5]:  # 처음 5개만
                print(f"      • {endpoint}")
            
            # 7. 로그인 전략 제안
            strategy = self.suggest_login_strategy(framework_info, security_info, auth_info, dom_info)
            print(f"\n[7] 권장 로그인 전략")
            for step in strategy:
                print(f"    {step}")
            
            # 결과 저장
            self.save_analysis_result(url, framework_info, security_info, auth_info, dom_info, js_info, api_endpoints)
            
            print(f"\n{'='*60}")
            print("분석 완료! 결과가 site_analysis.json에 저장되었습니다.")
            print(f"{'='*60}\n")
            
            await page.wait_for_timeout(10000)
            
        finally:
            await browser.close()
            await playwright.stop()
    
    async def detect_framework(self, page):
        """프레임워크 감지"""
        return await page.evaluate("""
            () => {
                const info = {
                    type: 'unknown',
                    rendering: 'server-side',
                    is_spa: false,
                    technologies: []
                };
                
                // React 감지
                if (window.React || document.querySelector('[data-reactroot]')) {
                    info.type = 'React';
                    info.is_spa = true;
                    info.rendering = 'client-side';
                    info.technologies.push('React');
                }
                
                // Vue 감지
                if (window.Vue || document.querySelector('[data-v-]')) {
                    info.type = 'Vue';
                    info.is_spa = true;
                    info.rendering = 'client-side';
                    info.technologies.push('Vue');
                }
                
                // Angular 감지
                if (window.ng || document.querySelector('[ng-app]')) {
                    info.type = 'Angular';
                    info.is_spa = true;
                    info.rendering = 'client-side';
                    info.technologies.push('Angular');
                }
                
                // Flutter Web 감지
                if (document.querySelector('flt-glass-pane') || window.flutterCanvasKit) {
                    info.type = 'Flutter';
                    info.rendering = 'canvas';
                    info.is_spa = true;
                    info.technologies.push('Flutter');
                }
                
                // jQuery 감지
                if (window.jQuery) {
                    info.technologies.push('jQuery');
                    if (info.type === 'unknown') {
                        info.type = 'Traditional (jQuery)';
                    }
                }
                
                // JSP/Spring 감지
                const hasJSessionId = document.cookie.includes('JSESSIONID');
                const hasSpringCSRF = document.querySelector('[name*="csrf"]');
                if (hasJSessionId || hasSpringCSRF) {
                    info.technologies.push('Java/Spring');
                    info.rendering = 'server-side';
                }
                
                return info;
            }
        """)
    
    async def analyze_security(self, page):
        """보안 메커니즘 분석"""
        return await page.evaluate("""
            () => {
                const security = {
                    has_csrf: false,
                    has_captcha: false,
                    automation_detection: false,
                    security_headers: [],
                    login_attempts_limit: false
                };
                
                // CSRF 토큰 확인
                const csrfTokens = document.querySelectorAll('[name*="csrf"], [name*="token"], [name*="CSRF"]');
                security.has_csrf = csrfTokens.length > 0;
                
                // 캡차 확인
                const captchaElements = document.querySelectorAll('[class*="captcha"], [id*="captcha"], img[src*="captcha"]');
                security.has_captcha = captchaElements.length > 0;
                
                // reCAPTCHA 확인
                if (window.grecaptcha || document.querySelector('.g-recaptcha')) {
                    security.has_captcha = true;
                    security.captcha_type = 'reCAPTCHA';
                }
                
                // 자동화 탐지 확인
                if (navigator.webdriver === true) {
                    security.automation_detection = true;
                }
                
                // 로그인 시도 제한 확인
                const errorMessages = document.body.innerText;
                if (errorMessages.includes('5회') || errorMessages.includes('잠금') || errorMessages.includes('locked')) {
                    security.login_attempts_limit = true;
                }
                
                return security;
            }
        """)
    
    async def analyze_authentication(self, page):
        """인증 방식 분석"""
        return await page.evaluate("""
            () => {
                const auth = {
                    has_login_form: false,
                    has_oauth: false,
                    has_2fa: false,
                    login_fields: [],
                    submit_method: 'unknown'
                };
                
                // 로그인 폼 확인
                const loginForm = document.querySelector('form[action*="login"], form#loginForm');
                auth.has_login_form = loginForm !== null;
                
                // 로그인 필드 찾기
                const usernameField = document.querySelector('input[type="text"][name*="user"], input[type="text"][name*="id"], input[type="email"]');
                const passwordField = document.querySelector('input[type="password"]');
                
                if (usernameField) {
                    auth.login_fields.push({
                        type: 'username',
                        selector: '#' + usernameField.id || '[name="' + usernameField.name + '"]'
                    });
                }
                
                if (passwordField) {
                    auth.login_fields.push({
                        type: 'password',
                        selector: '#' + passwordField.id || '[name="' + passwordField.name + '"]'
                    });
                }
                
                // OAuth 확인
                const oauthButtons = document.querySelectorAll('[href*="oauth"], [onclick*="oauth"], [class*="social-login"]');
                auth.has_oauth = oauthButtons.length > 0;
                
                // 2FA 확인
                const otpFields = document.querySelectorAll('input[name*="otp"], input[name*="code"], input[placeholder*="인증"]');
                auth.has_2fa = otpFields.length > 0;
                
                // Submit 방식 확인
                if (loginForm) {
                    auth.submit_method = loginForm.method || 'POST';
                    auth.submit_action = loginForm.action;
                }
                
                return auth;
            }
        """)
    
    async def analyze_dom_structure(self, page):
        """DOM 구조 분석"""
        return await page.evaluate("""
            () => {
                const dom = {
                    input_count: document.querySelectorAll('input').length,
                    button_count: document.querySelectorAll('button, input[type="submit"], input[type="button"]').length,
                    form_count: document.querySelectorAll('form').length,
                    iframe_count: document.querySelectorAll('iframe').length,
                    hidden_inputs: [],
                    visible_inputs: []
                };
                
                // 숨겨진 입력 필드
                document.querySelectorAll('input[type="hidden"]').forEach(input => {
                    dom.hidden_inputs.push({
                        name: input.name,
                        value: input.value
                    });
                });
                
                // 보이는 입력 필드
                document.querySelectorAll('input:not([type="hidden"])').forEach(input => {
                    if (input.offsetParent !== null) {
                        dom.visible_inputs.push({
                            type: input.type,
                            name: input.name,
                            id: input.id,
                            placeholder: input.placeholder
                        });
                    }
                });
                
                return dom;
            }
        """)
    
    async def analyze_javascript(self, page):
        """JavaScript 환경 분석"""
        return await page.evaluate("""
            () => {
                return {
                    has_jquery: typeof jQuery !== 'undefined',
                    has_react: typeof React !== 'undefined' || !!document.querySelector('[data-reactroot]'),
                    has_vue: typeof Vue !== 'undefined',
                    has_angular: typeof ng !== 'undefined',
                    has_axios: typeof axios !== 'undefined',
                    has_fetch: typeof fetch !== 'undefined'
                };
            }
        """)
    
    def analyze_network(self, requests):
        """네트워크 요청 분석"""
        api_endpoints = []
        for req in requests:
            url = req['url']
            if any(keyword in url for keyword in ['api', 'login', 'auth', 'ajax', '.do', '.action']):
                if url not in api_endpoints:
                    api_endpoints.append(url)
        return api_endpoints
    
    def suggest_login_strategy(self, framework, security, auth, dom):
        """로그인 전략 제안"""
        strategy = []
        
        if framework.get('type') == 'Flutter':
            strategy.append("• Flutter 감지: Tab 키 네비게이션 사용 필요")
            strategy.append("• Canvas 렌더링: 일반 DOM 선택자 사용 불가")
            
        if security.get('has_csrf'):
            strategy.append("• CSRF 토큰 추출 후 요청에 포함 필요")
            
        if security.get('has_captcha'):
            strategy.append("• 캡차 처리 필요: 수동 입력 또는 OCR/API 서비스")
            
        if security.get('login_attempts_limit'):
            strategy.append("• 로그인 시도 제한 있음: 신중한 접근 필요")
            
        if security.get('automation_detection'):
            strategy.append("• 자동화 탐지 있음: 브라우저 설정 조정 필요")
            
        if auth.get('has_2fa'):
            strategy.append("• 2단계 인증 있음: OTP 처리 필요")
            
        if framework.get('is_spa'):
            strategy.append("• SPA 애플리케이션: 동적 로딩 대기 필요")
            
        return strategy if strategy else ["• 표준 폼 제출 방식 사용 가능"]
    
    def save_analysis_result(self, url, framework, security, auth, dom, js, endpoints):
        """분석 결과 저장"""
        result = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'framework': framework,
            'security': security,
            'authentication': auth,
            'dom_structure': dom,
            'javascript': js,
            'api_endpoints': endpoints[:10]  # 처음 10개만 저장
        }
        
        with open('site_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

async def main():
    analyzer = SiteAnalyzer()
    
    # Bizmeka 분석
    await analyzer.analyze_site("https://ezsso.bizmeka.com/loginForm.do")

if __name__ == "__main__":
    asyncio.run(main())
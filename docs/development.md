# 🛠️ AutoInput 개발 가이드

## 목차

1. [프로젝트 구조](#프로젝트-구조)
2. [개발 환경 설정](#개발-환경-설정)
3. [핵심 모듈 개발](#핵심-모듈-개발)
4. [API 개발](#api-개발)
5. [데이터베이스](#데이터베이스)
6. [테스트 작성](#테스트-작성)
7. [디버깅](#디버깅)
8. [성능 최적화](#성능-최적화)
9. [보안 고려사항](#보안-고려사항)
10. [배포](#배포)

## 프로젝트 구조

```
autoinput/
├── src/
│   ├── core/               # 핵심 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── automation.py   # Playwright 자동화 엔진
│   │   ├── config.py       # 설정 관리
│   │   ├── scheduler.py    # 스케줄링 시스템
│   │   └── security.py     # 보안 및 암호화
│   │
│   ├── scrapers/           # 웹 스크래핑 모듈
│   │   ├── __init__.py
│   │   ├── base.py         # 기본 스크래퍼 클래스
│   │   ├── selectors.py    # 셀렉터 관리
│   │   └── insurance.py    # 보험청구 스크래퍼
│   │
│   ├── parsers/            # 문서 파싱 모듈
│   │   ├── __init__.py
│   │   ├── excel.py        # Excel 파서
│   │   ├── pdf.py          # PDF 파서
│   │   ├── hwp.py          # HWP 파서
│   │   └── base.py         # 기본 파서 인터페이스
│   │
│   ├── validators/         # 데이터 검증 모듈
│   │   ├── __init__.py
│   │   ├── schema.py       # 스키마 검증
│   │   └── rules.py        # 비즈니스 규칙 검증
│   │
│   ├── ui/                 # 웹 인터페이스
│   │   ├── __init__.py
│   │   ├── api/            # REST API 엔드포인트
│   │   ├── models/         # 데이터 모델
│   │   └── schemas/        # Pydantic 스키마
│   │
│   └── utils/              # 유틸리티 함수
│       ├── __init__.py
│       ├── logging.py      # 로깅 설정
│       ├── encryption.py   # 암호화 유틸
│       └── helpers.py      # 헬퍼 함수
│
├── tests/                  # 테스트 코드
├── config/                 # 설정 파일
├── scripts/                # 유틸리티 스크립트
└── docs/                   # 문서
```

## 개발 환경 설정

### 1. Python 가상환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 활성화
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필수 환경 변수 설정
DATABASE_URL=postgresql://user:pass@localhost:5432/autoinput
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key
```

### 3. 데이터베이스 초기화

```bash
# 데이터베이스 생성
createdb autoinput

# 마이그레이션 실행
alembic upgrade head
```

### 4. Playwright 설치

```bash
# 브라우저 설치
playwright install chromium firefox

# 의존성 설치 (Linux)
playwright install-deps
```

## 핵심 모듈 개발

### AutomationEngine 클래스

```python
# src/core/automation.py

from playwright.async_api import async_playwright, Page
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AutomationEngine:
    """웹 자동화 엔진"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page: Optional[Page] = None
        
    async def start(self):
        """브라우저 시작"""
        self.playwright = await async_playwright().start()
        
        # 브라우저 옵션 설정
        browser_args = []
        if self.config.get('proxy'):
            browser_args.append(f'--proxy-server={self.config["proxy"]}')
            
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.get('headless', False),
            args=browser_args
        )
        
        # 컨텍스트 생성 (쿠키, 로컬 스토리지 유지)
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent=self.config.get('user_agent'),
            locale='ko-KR',
            timezone_id='Asia/Seoul'
        )
        
        # 인증서 처리 (필요시)
        if self.config.get('certificates'):
            await self.context.add_cookies(self.config['certificates'])
            
        self.page = await self.context.new_page()
        
    async def execute_scenario(self, scenario: Dict[str, Any]):
        """시나리오 실행"""
        for step in scenario['steps']:
            await self._execute_step(step)
            
    async def _execute_step(self, step: Dict[str, Any]):
        """단계별 실행"""
        action = step['action']
        
        if action == 'navigate':
            await self.page.goto(step['url'])
        elif action == 'fill':
            await self.page.fill(step['selector'], step['value'])
        elif action == 'click':
            await self.page.click(step['selector'])
        elif action == 'wait':
            await self.page.wait_for_selector(step['selector'])
        elif action == 'screenshot':
            await self.page.screenshot(path=step['path'])
        # ... 추가 액션들
```

### 셀렉터 자가치유 시스템

```python
# src/scrapers/selectors.py

from typing import List, Dict, Optional
import difflib

class SelectorManager:
    """셀렉터 관리 및 자가치유"""
    
    def __init__(self):
        self.selector_history = {}
        self.fallback_strategies = []
        
    async def find_element(self, page, selector_config: Dict):
        """요소 찾기 (자가치유 포함)"""
        
        # 1. 기본 셀렉터 시도
        primary = selector_config['primary']
        element = await page.query_selector(primary)
        
        if element:
            return element
            
        # 2. 대체 셀렉터 시도
        for fallback in selector_config.get('fallbacks', []):
            element = await page.query_selector(fallback)
            if element:
                logger.info(f"Using fallback selector: {fallback}")
                return element
                
        # 3. 자가치유 시도
        element = await self._self_heal(page, selector_config)
        if element:
            return element
            
        raise Exception(f"Element not found: {primary}")
        
    async def _self_heal(self, page, selector_config):
        """셀렉터 자가치유"""
        
        # 텍스트 기반 검색
        if text := selector_config.get('text'):
            element = await page.get_by_text(text).first
            if element:
                logger.info(f"Self-healed using text: {text}")
                return element
                
        # 속성 기반 검색
        if attrs := selector_config.get('attributes'):
            for attr, value in attrs.items():
                selector = f'[{attr}="{value}"]'
                element = await page.query_selector(selector)
                if element:
                    logger.info(f"Self-healed using attribute: {selector}")
                    return element
                    
        # 유사도 기반 검색
        if similar := await self._find_similar_element(page, selector_config):
            return similar
            
        return None
        
    async def _find_similar_element(self, page, selector_config):
        """유사한 요소 찾기"""
        # DOM 구조 분석 및 유사도 계산
        # ...
        pass
```

### 문서 파서 구현

```python
# src/parsers/excel.py

import pandas as pd
from typing import Dict, List, Any
from src.parsers.base import BaseParser

class ExcelParser(BaseParser):
    """Excel 파일 파서"""
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema = self._load_schema(schema_path) if schema_path else None
        
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """Excel 파일 파싱"""
        try:
            # 모든 시트 읽기
            sheets = pd.read_excel(file_path, sheet_name=None)
            
            result = {}
            for sheet_name, df in sheets.items():
                # 데이터 정제
                df = self._clean_dataframe(df)
                
                # 스키마 검증
                if self.schema:
                    self._validate_against_schema(df, sheet_name)
                    
                result[sheet_name] = df.to_dict('records')
                
            return result
            
        except Exception as e:
            logger.error(f"Excel parsing error: {e}")
            raise
            
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임 정제"""
        # 빈 행/열 제거
        df = df.dropna(how='all')
        df = df.dropna(axis='columns', how='all')
        
        # 컬럼명 정규화
        df.columns = [str(col).strip() for col in df.columns]
        
        # 데이터 타입 추론
        df = df.infer_objects()
        
        return df
        
    def _validate_against_schema(self, df: pd.DataFrame, sheet_name: str):
        """스키마 검증"""
        if sheet_name not in self.schema:
            return
            
        schema = self.schema[sheet_name]
        
        # 필수 컬럼 확인
        required_cols = schema.get('required_columns', [])
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
            
        # 데이터 타입 검증
        for col, dtype in schema.get('column_types', {}).items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)
```

## API 개발

### FastAPI 라우터 구현

```python
# src/ui/api/automation.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List
from src.ui.schemas.automation import (
    AutomationRequest, 
    AutomationResponse,
    TaskStatus
)
from src.core.automation import AutomationEngine
from src.ui.models.task import Task

router = APIRouter(prefix="/api/automation", tags=["automation"])

@router.post("/start", response_model=AutomationResponse)
async def start_automation(
    request: AutomationRequest,
    background_tasks: BackgroundTasks,
    engine: AutomationEngine = Depends(get_engine)
):
    """자동화 작업 시작"""
    
    # 작업 생성
    task = Task.create(
        name=request.name,
        scenario=request.scenario,
        schedule=request.schedule
    )
    
    # 백그라운드에서 실행
    background_tasks.add_task(
        run_automation,
        task_id=task.id,
        engine=engine,
        scenario=request.scenario
    )
    
    return AutomationResponse(
        task_id=task.id,
        status="started",
        message="자동화 작업이 시작되었습니다"
    )

@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """작업 상태 조회"""
    task = Task.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
        
    return TaskStatus(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        result=task.result,
        error=task.error
    )

@router.post("/stop/{task_id}")
async def stop_automation(task_id: str):
    """자동화 작업 중지"""
    task = Task.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
        
    task.cancel()
    return {"message": "작업이 중지되었습니다"}

async def run_automation(task_id: str, engine: AutomationEngine, scenario: dict):
    """백그라운드 자동화 실행"""
    task = Task.get(task_id)
    
    try:
        task.update_status("running")
        
        # 시나리오 실행
        result = await engine.execute_scenario(scenario)
        
        task.complete(result)
        
    except Exception as e:
        logger.error(f"Automation error: {e}")
        task.fail(str(e))
```

### WebSocket 실시간 통신

```python
# src/ui/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

class ConnectionManager:
    """WebSocket 연결 관리"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
    async def send_message(self, client_id: str, message: dict):
        if websocket := self.active_connections.get(client_id):
            await websocket.send_json(message)
            
    async def broadcast(self, message: dict):
        for websocket in self.active_connections.values():
            await websocket.send_json(message)

manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_json()
            
            # 메시지 처리
            if data['type'] == 'subscribe':
                # 작업 구독
                await subscribe_to_task(client_id, data['task_id'])
            elif data['type'] == 'command':
                # 명령 실행
                await execute_command(client_id, data['command'])
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

## 데이터베이스

### SQLAlchemy 모델

```python
# src/ui/models/base.py

from sqlalchemy import create_engine, Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class BaseModel(Base):
    """기본 모델"""
    __abstract__ = True
    
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

```python
# src/ui/models/task.py

from sqlalchemy import Column, String, JSON, Enum
from src.ui.models.base import BaseModel
import enum

class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    """작업 모델"""
    __tablename__ = "tasks"
    
    name = Column(String, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    scenario = Column(JSON)
    schedule = Column(JSON)
    result = Column(JSON)
    error = Column(String)
    progress = Column(JSON)
```

### Alembic 마이그레이션

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Add task table"

# 마이그레이션 실행
alembic upgrade head

# 롤백
alembic downgrade -1
```

## 테스트 작성

### 단위 테스트

```python
# tests/test_automation.py

import pytest
from unittest.mock import Mock, patch
from src.core.automation import AutomationEngine

@pytest.fixture
async def engine():
    """테스트용 엔진 fixture"""
    config = {'headless': True}
    engine = AutomationEngine(config)
    await engine.start()
    yield engine
    await engine.stop()

@pytest.mark.asyncio
async def test_navigation(engine):
    """페이지 네비게이션 테스트"""
    await engine.page.goto("https://example.com")
    assert "Example" in await engine.page.title()

@pytest.mark.asyncio
async def test_form_filling(engine):
    """폼 입력 테스트"""
    await engine.page.goto("https://example.com/form")
    
    # 폼 필드 입력
    await engine.page.fill("#name", "테스트")
    await engine.page.fill("#email", "test@example.com")
    
    # 제출
    await engine.page.click("#submit")
    
    # 결과 확인
    success = await engine.page.wait_for_selector(".success-message")
    assert success is not None
```

### 통합 테스트

```python
# tests/integration/test_workflow.py

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_complete_workflow():
    """전체 워크플로우 테스트"""
    
    # 1. 파일 업로드
    with open("test_data.xlsx", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": f}
        )
    assert response.status_code == 200
    file_id = response.json()["file_id"]
    
    # 2. 데이터 파싱
    response = client.post(f"/api/parse/{file_id}")
    assert response.status_code == 200
    
    # 3. 자동화 실행
    response = client.post(
        "/api/automation/start",
        json={
            "name": "테스트 자동화",
            "scenario": {...}
        }
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    
    # 4. 상태 확인
    response = client.get(f"/api/automation/status/{task_id}")
    assert response.status_code == 200
```

## 디버깅

### Playwright 디버깅

```python
# 디버그 모드 실행
import os
os.environ['PWDEBUG'] = '1'

# 또는 Inspector 사용
await page.pause()  # 실행 일시정지

# 스크린샷 저장
await page.screenshot(path="debug.png")

# 콘솔 로그 캡처
page.on("console", lambda msg: print(f"Console: {msg.text}"))

# 네트워크 요청 모니터링
page.on("request", lambda req: print(f"Request: {req.url}"))
page.on("response", lambda res: print(f"Response: {res.url} - {res.status}"))
```

### 로깅 설정

```python
# src/utils/logging.py

import logging
import structlog
from loguru import logger

def setup_logging():
    """로깅 설정"""
    
    # Loguru 설정
    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        level="INFO",
        format="{time} {level} {message}",
        backtrace=True,
        diagnose=True
    )
    
    # Structlog 설정
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

## 성능 최적화

### 비동기 처리

```python
# 병렬 처리 예시
import asyncio

async def process_multiple_pages(urls: List[str]):
    """여러 페이지 동시 처리"""
    tasks = []
    
    for url in urls:
        task = asyncio.create_task(process_page(url))
        tasks.append(task)
        
    results = await asyncio.gather(*tasks)
    return results

# 세마포어를 이용한 동시 실행 제한
semaphore = asyncio.Semaphore(5)  # 최대 5개 동시 실행

async def limited_process(url: str):
    async with semaphore:
        return await process_page(url)
```

### 캐싱

```python
# Redis 캐싱 예시
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time=3600):
    """결과 캐싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 캐시 확인
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
                
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과 캐싱
            redis_client.setex(
                cache_key,
                expire_time,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

## 보안 고려사항

### 데이터 암호화

```python
# src/utils/encryption.py

from cryptography.fernet import Fernet
from src.core.config import settings

class Encryptor:
    """데이터 암호화 클래스"""
    
    def __init__(self):
        self.key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(self.key)
        
    def encrypt(self, data: str) -> str:
        """문자열 암호화"""
        return self.cipher.encrypt(data.encode()).decode()
        
    def decrypt(self, encrypted: str) -> str:
        """문자열 복호화"""
        return self.cipher.decrypt(encrypted.encode()).decode()
        
    def encrypt_file(self, file_path: str):
        """파일 암호화"""
        with open(file_path, 'rb') as f:
            data = f.read()
            
        encrypted = self.cipher.encrypt(data)
        
        with open(f"{file_path}.enc", 'wb') as f:
            f.write(encrypted)
```

### 인증/인가

```python
# src/ui/api/auth.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    """JWT 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """현재 사용자 확인"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    return username
```

## 배포

### Docker 배포

```dockerfile
# Dockerfile.prod

FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# 보안을 위한 non-root 사용자 생성
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# 빌더에서 패키지 복사
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Playwright 설치
RUN playwright install --with-deps chromium

# 애플리케이션 복사
COPY --chown=appuser:appuser . .

USER appuser

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose 프로덕션

```yaml
# docker-compose.prod.yml

version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: autoinput-app
    ports:
      - "8000:8000"
    environment:
      - ENV=production
    env_file:
      - .env.prod
    networks:
      - autoinput-network
    restart: always
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    container_name: autoinput-db
    environment:
      POSTGRES_DB: autoinput
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - autoinput-network
    restart: always

  redis:
    image: redis:7-alpine
    container_name: autoinput-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - autoinput-network
    restart: always

  nginx:
    image: nginx:alpine
    container_name: autoinput-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    networks:
      - autoinput-network
    depends_on:
      - app
    restart: always

networks:
  autoinput-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 모니터링 설정

```yaml
# monitoring/prometheus.yml

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'autoinput'
    static_configs:
      - targets: ['app:8000']
```

---

이 개발 가이드는 AutoInput 프로젝트의 핵심 개발 프로세스를 다룹니다. 추가 질문이나 구체적인 구현 예시가 필요하면 언제든 문의해주세요.
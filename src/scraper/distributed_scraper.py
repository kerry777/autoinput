# -*- coding: utf-8 -*-
"""
분산 스크래핑 아키텍처
대규모 스크래핑을 위한 분산 처리 시스템
"""
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue, Empty
import threading
import pickle
import redis
from datetime import datetime, timedelta

class TaskStatus(Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class ScrapingTask:
    """스크래핑 작업 단위"""
    task_id: str
    url: str
    method: str = "GET"
    headers: Dict = None
    data: Dict = None
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = None
    created_at: datetime = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class TaskQueue:
    """작업 큐 관리"""
    
    def __init__(self, use_redis: bool = False, redis_host: str = 'localhost'):
        self.use_redis = use_redis
        
        if use_redis:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=6379, db=0)
                self.redis_client.ping()
                print("✅ Redis 연결 성공")
            except:
                print("⚠️ Redis 연결 실패, 로컬 큐 사용")
                self.use_redis = False
                self.local_queue = Queue()
        else:
            self.local_queue = Queue()
    
    def push(self, task: ScrapingTask):
        """작업 추가"""
        if self.use_redis:
            serialized = pickle.dumps(task)
            self.redis_client.rpush('scraping_tasks', serialized)
        else:
            self.local_queue.put(task)
    
    def pop(self, timeout: int = 1) -> Optional[ScrapingTask]:
        """작업 가져오기"""
        if self.use_redis:
            result = self.redis_client.blpop('scraping_tasks', timeout=timeout)
            if result:
                return pickle.loads(result[1])
        else:
            try:
                return self.local_queue.get(timeout=timeout)
            except Empty:
                return None
    
    def size(self) -> int:
        """큐 크기"""
        if self.use_redis:
            return self.redis_client.llen('scraping_tasks')
        else:
            return self.local_queue.qsize()

class AsyncScraper:
    """비동기 스크래퍼"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = None
        self.session = None
    
    async def __aenter__(self):
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def fetch(self, task: ScrapingTask) -> ScrapingTask:
        """비동기 페치"""
        async with self.semaphore:
            try:
                task.status = TaskStatus.RUNNING
                
                async with self.session.request(
                    task.method,
                    task.url,
                    headers=task.headers,
                    data=task.data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'application/json' in content_type:
                            task.result = await response.json()
                        else:
                            task.result = await response.text()
                        
                        task.status = TaskStatus.COMPLETED
                    else:
                        task.error = f"HTTP {response.status}"
                        task.status = TaskStatus.FAILED
                
            except asyncio.TimeoutError:
                task.error = "Timeout"
                task.status = TaskStatus.FAILED
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
            
            finally:
                task.completed_at = datetime.now()
            
            return task
    
    async def batch_fetch(self, tasks: List[ScrapingTask]) -> List[ScrapingTask]:
        """배치 페치"""
        results = await asyncio.gather(
            *[self.fetch(task) for task in tasks],
            return_exceptions=True
        )
        
        return [r if isinstance(r, ScrapingTask) else tasks[i] 
                for i, r in enumerate(results)]

class Worker(threading.Thread):
    """워커 스레드"""
    
    def __init__(self, worker_id: int, task_queue: TaskQueue, result_queue: Queue,
                 scraper_func: Callable):
        super().__init__()
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.scraper_func = scraper_func
        self.running = True
        self.processed_count = 0
    
    def run(self):
        """워커 실행"""
        print(f"🔧 Worker {self.worker_id} 시작")
        
        while self.running:
            task = self.task_queue.pop(timeout=1)
            
            if task is None:
                continue
            
            # 작업 처리
            try:
                result = self.scraper_func(task)
                self.result_queue.put(result)
                self.processed_count += 1
                
                if self.processed_count % 10 == 0:
                    print(f"  Worker {self.worker_id}: {self.processed_count}개 처리")
                
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                self.result_queue.put(task)
    
    def stop(self):
        """워커 정지"""
        self.running = False

class DistributedScraper:
    """분산 스크래핑 조율자"""
    
    def __init__(self, num_workers: int = 4, use_async: bool = True,
                 use_multiprocessing: bool = False):
        self.num_workers = num_workers
        self.use_async = use_async
        self.use_multiprocessing = use_multiprocessing
        
        self.task_queue = TaskQueue()
        self.result_queue = Queue()
        self.workers = []
        
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'retried': 0,
            'start_time': None,
            'end_time': None
        }
    
    def add_task(self, url: str, **kwargs) -> str:
        """작업 추가"""
        task_id = f"task_{self.stats['total']}_{int(time.time())}"
        task = ScrapingTask(
            task_id=task_id,
            url=url,
            **kwargs
        )
        
        self.task_queue.push(task)
        self.stats['total'] += 1
        
        return task_id
    
    def add_urls(self, urls: List[str]):
        """URL 리스트 추가"""
        task_ids = []
        for url in urls:
            task_id = self.add_task(url)
            task_ids.append(task_id)
        
        return task_ids
    
    async def run_async(self) -> List[ScrapingTask]:
        """비동기 실행"""
        print(f"\n🚀 비동기 스크래핑 시작 (동시 실행: {self.num_workers})")
        self.stats['start_time'] = datetime.now()
        
        results = []
        tasks = []
        
        # 모든 작업 수집
        while True:
            task = self.task_queue.pop(timeout=0)
            if task is None:
                break
            tasks.append(task)
        
        # 배치 처리
        async with AsyncScraper(max_concurrent=self.num_workers) as scraper:
            batch_size = self.num_workers * 2
            
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i+batch_size]
                batch_results = await scraper.batch_fetch(batch)
                
                for result in batch_results:
                    if result.status == TaskStatus.COMPLETED:
                        self.stats['completed'] += 1
                    elif result.status == TaskStatus.FAILED:
                        if result.retry_count < result.max_retries:
                            result.retry_count += 1
                            result.status = TaskStatus.RETRYING
                            self.stats['retried'] += 1
                            self.task_queue.push(result)
                        else:
                            self.stats['failed'] += 1
                
                results.extend(batch_results)
                
                # 진행 상황 출력
                print(f"  진행: {len(results)}/{len(tasks)} "
                      f"(성공: {self.stats['completed']}, 실패: {self.stats['failed']})")
        
        self.stats['end_time'] = datetime.now()
        return results
    
    def run_threaded(self, scraper_func: Callable) -> List[ScrapingTask]:
        """스레드 기반 실행"""
        print(f"\n🔄 스레드 기반 스크래핑 시작 (워커: {self.num_workers})")
        self.stats['start_time'] = datetime.now()
        
        # 워커 생성
        for i in range(self.num_workers):
            worker = Worker(i, self.task_queue, self.result_queue, scraper_func)
            worker.start()
            self.workers.append(worker)
        
        # 결과 수집
        results = []
        while len(results) < self.stats['total']:
            try:
                result = self.result_queue.get(timeout=1)
                results.append(result)
                
                if result.status == TaskStatus.COMPLETED:
                    self.stats['completed'] += 1
                elif result.status == TaskStatus.FAILED:
                    self.stats['failed'] += 1
                
                # 진행 상황
                if len(results) % 10 == 0:
                    print(f"  수집: {len(results)}/{self.stats['total']}")
                
            except Empty:
                # 모든 워커가 종료되었는지 확인
                if all(not w.is_alive() for w in self.workers):
                    break
        
        # 워커 정지
        for worker in self.workers:
            worker.stop()
        
        for worker in self.workers:
            worker.join()
        
        self.stats['end_time'] = datetime.now()
        return results
    
    def run_multiprocess(self, scraper_func: Callable) -> List[ScrapingTask]:
        """멀티프로세스 실행"""
        print(f"\n⚡ 멀티프로세스 스크래핑 시작 (프로세스: {self.num_workers})")
        self.stats['start_time'] = datetime.now()
        
        # 작업 수집
        tasks = []
        while True:
            task = self.task_queue.pop(timeout=0)
            if task is None:
                break
            tasks.append(task)
        
        results = []
        
        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # 작업 제출
            futures = {executor.submit(scraper_func, task): task 
                      for task in tasks}
            
            # 결과 수집
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result.status == TaskStatus.COMPLETED:
                        self.stats['completed'] += 1
                    else:
                        self.stats['failed'] += 1
                    
                    # 진행 상황
                    if len(results) % 10 == 0:
                        print(f"  처리: {len(results)}/{len(tasks)}")
                        
                except Exception as e:
                    task = futures[future]
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    results.append(task)
                    self.stats['failed'] += 1
        
        self.stats['end_time'] = datetime.now()
        return results
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['duration'] = f"{duration:.2f}초"
            stats['speed'] = f"{stats['completed'] / duration:.2f} req/s" if duration > 0 else "N/A"
        
        return stats
    
    def print_summary(self):
        """요약 출력"""
        stats = self.get_stats()
        
        print("\n" + "=" * 80)
        print("📊 스크래핑 요약")
        print("-" * 40)
        print(f"  총 작업: {stats['total']}")
        print(f"  완료: {stats['completed']} ({stats['completed']/stats['total']*100:.1f}%)")
        print(f"  실패: {stats['failed']}")
        print(f"  재시도: {stats['retried']}")
        
        if 'duration' in stats:
            print(f"  소요 시간: {stats['duration']}")
            print(f"  처리 속도: {stats['speed']}")
        
        print("=" * 80)

# 샘플 스크래퍼 함수
def simple_scraper(task: ScrapingTask) -> ScrapingTask:
    """간단한 동기 스크래퍼"""
    import requests
    
    try:
        response = requests.get(task.url, headers=task.headers, timeout=10)
        
        if response.status_code == 200:
            task.result = response.text[:1000]  # 처음 1000자만
            task.status = TaskStatus.COMPLETED
        else:
            task.error = f"HTTP {response.status_code}"
            task.status = TaskStatus.FAILED
            
    except Exception as e:
        task.error = str(e)
        task.status = TaskStatus.FAILED
    
    task.completed_at = datetime.now()
    return task

# 사용 예제
async def main():
    """메인 실행 함수"""
    print("🌐 분산 스크래핑 시스템 테스트")
    print("=" * 80)
    
    # 테스트 URL들
    test_urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/2",
        "https://httpbin.org/json",
        "https://httpbin.org/html",
        "https://httpbin.org/status/200"
    ] * 2  # 10개 작업
    
    # 분산 스크래퍼 초기화
    scraper = DistributedScraper(num_workers=3)
    
    # 작업 추가
    print(f"\n📝 {len(test_urls)}개 작업 추가")
    scraper.add_urls(test_urls)
    
    # 비동기 실행
    if scraper.use_async:
        results = await scraper.run_async()
    else:
        results = scraper.run_threaded(simple_scraper)
    
    # 결과 요약
    scraper.print_summary()
    
    print("\n✨ 분산 스크래핑 완료!")

if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())
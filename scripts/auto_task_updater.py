#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
자동 태스크 업데이트 시스템
작업 진행 시 자동으로 태스크 리스트 업데이트
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskManager:
    """태스크 상태 관리 및 자동 업데이트"""
    
    def __init__(self):
        self.task_file = "data/tasks.json"
        self.log_file = "logs/task_history.log"
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        self.tasks = self.load_tasks()
    
    def load_tasks(self) -> Dict:
        """태스크 목록 불러오기"""
        if os.path.exists(self.task_file):
            with open(self.task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_tasks(self):
        """태스크 목록 저장"""
        with open(self.task_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)
    
    def log_change(self, task_id: str, old_status: str, new_status: str, notes: str = ""):
        """상태 변경 로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} | Task {task_id} | {old_status} → {new_status}"
        if notes:
            log_entry += f" | {notes}"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
        
        # 콘솔에도 출력
        print(f"📝 {log_entry}")
    
    def start_task(self, task_id: str, task_name: str = None) -> bool:
        """태스크 시작 (pending → in_progress)"""
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "name": task_name or f"Task {task_id}",
                "status": TaskStatus.PENDING.value,
                "started_at": None,
                "completed_at": None,
                "notes": []
            }
        
        task = self.tasks[task_id]
        old_status = task["status"]
        
        if old_status == TaskStatus.PENDING.value:
            task["status"] = TaskStatus.IN_PROGRESS.value
            task["started_at"] = datetime.now().isoformat()
            self.save_tasks()
            self.log_change(task_id, old_status, task["status"], f"Started: {task['name']}")
            return True
        else:
            print(f"⚠️  Task {task_id} is already {old_status}")
            return False
    
    def complete_task(self, task_id: str, notes: str = "") -> bool:
        """태스크 완료 (in_progress → completed)"""
        if task_id not in self.tasks:
            print(f"❌ Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        old_status = task["status"]
        
        if old_status == TaskStatus.IN_PROGRESS.value:
            task["status"] = TaskStatus.COMPLETED.value
            task["completed_at"] = datetime.now().isoformat()
            if notes:
                task["notes"].append(notes)
            self.save_tasks()
            self.log_change(task_id, old_status, task["status"], notes)
            
            # 완료 통계 출력
            self.print_progress()
            return True
        else:
            print(f"⚠️  Task {task_id} is not in progress (current: {old_status})")
            return False
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """태스크 실패 처리"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        old_status = task["status"]
        task["status"] = TaskStatus.FAILED.value
        task["error"] = error
        task["failed_at"] = datetime.now().isoformat()
        self.save_tasks()
        self.log_change(task_id, old_status, task["status"], f"Error: {error}")
        return True
    
    def block_task(self, task_id: str, reason: str) -> bool:
        """태스크 차단 (대기 필요)"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        old_status = task["status"]
        task["status"] = TaskStatus.BLOCKED.value
        task["blocked_reason"] = reason
        self.save_tasks()
        self.log_change(task_id, old_status, task["status"], f"Blocked: {reason}")
        return True
    
    def add_note(self, task_id: str, note: str):
        """태스크에 메모 추가"""
        if task_id in self.tasks:
            self.tasks[task_id]["notes"].append({
                "timestamp": datetime.now().isoformat(),
                "note": note
            })
            self.save_tasks()
            print(f"📌 Note added to {task_id}: {note}")
    
    def print_progress(self):
        """전체 진행 상황 출력"""
        total = len(self.tasks)
        if total == 0:
            return
        
        completed = sum(1 for t in self.tasks.values() 
                       if t["status"] == TaskStatus.COMPLETED.value)
        in_progress = sum(1 for t in self.tasks.values() 
                         if t["status"] == TaskStatus.IN_PROGRESS.value)
        failed = sum(1 for t in self.tasks.values() 
                    if t["status"] == TaskStatus.FAILED.value)
        blocked = sum(1 for t in self.tasks.values() 
                     if t["status"] == TaskStatus.BLOCKED.value)
        
        progress = (completed / total) * 100
        
        print("\n" + "=" * 50)
        print("📊 Task Progress Summary")
        print("=" * 50)
        print(f"✅ Completed: {completed}/{total} ({progress:.1f}%)")
        print(f"🔄 In Progress: {in_progress}")
        print(f"⏳ Pending: {total - completed - in_progress - failed - blocked}")
        print(f"❌ Failed: {failed}")
        print(f"🚫 Blocked: {blocked}")
        print("=" * 50 + "\n")
    
    def get_current_task(self) -> Optional[Dict]:
        """현재 진행 중인 태스크 반환"""
        for task_id, task in self.tasks.items():
            if task["status"] == TaskStatus.IN_PROGRESS.value:
                return {"id": task_id, **task}
        return None
    
    def list_tasks(self, status: Optional[TaskStatus] = None):
        """태스크 목록 출력"""
        print("\n📋 Task List")
        print("-" * 60)
        
        for task_id, task in self.tasks.items():
            if status and task["status"] != status.value:
                continue
            
            status_emoji = {
                TaskStatus.PENDING.value: "⏳",
                TaskStatus.IN_PROGRESS.value: "🔄",
                TaskStatus.COMPLETED.value: "✅",
                TaskStatus.FAILED.value: "❌",
                TaskStatus.BLOCKED.value: "🚫"
            }
            
            emoji = status_emoji.get(task["status"], "❓")
            print(f"{emoji} [{task_id}] {task['name']} - {task['status']}")
            
            if task.get("notes"):
                for note in task["notes"]:
                    if isinstance(note, dict):
                        print(f"   📝 {note['note']}")
                    else:
                        print(f"   📝 {note}")


# 데코레이터로 자동 업데이트
def track_task(task_id: str, task_name: str = None):
    """함수 실행 시 자동으로 태스크 상태 업데이트하는 데코레이터"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = TaskManager()
            
            # 태스크 시작
            manager.start_task(task_id, task_name or func.__name__)
            
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                
                # 성공 시 완료 처리
                manager.complete_task(task_id, f"Function {func.__name__} completed successfully")
                return result
                
            except Exception as e:
                # 실패 시 에러 기록
                manager.fail_task(task_id, str(e))
                raise
        
        return wrapper
    return decorator


# 사용 예시
@track_task("login_test_001", "Login Test - web-scraping.dev")
def test_login():
    """로그인 테스트 함수"""
    print("로그인 테스트 실행 중...")
    # 실제 로그인 로직
    import time
    time.sleep(2)
    print("로그인 성공!")
    return True


if __name__ == "__main__":
    # 태스크 매니저 테스트
    manager = TaskManager()
    
    print("""
    ╔══════════════════════════════════════════╗
    ║        태스크 자동 업데이트 시스템        ║
    ╚══════════════════════════════════════════╝
    """)
    
    # 수동 태스크 관리 예시
    manager.start_task("test_001", "수동 테스트 태스크")
    manager.add_note("test_001", "테스트 시작")
    
    import time
    time.sleep(1)
    
    manager.complete_task("test_001", "테스트 완료")
    
    # 데코레이터 사용 예시
    test_login()
    
    # 전체 상태 출력
    manager.list_tasks()
    manager.print_progress()
#!/usr/bin/env python3
"""
Simple Taskmaster CLI - 작업 관리 도구 (의존성 최소화)
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def load_tasks(file_path='parsed_tasks.json'):
    """작업 데이터 로드"""
    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def print_tree(data):
    """작업 트리 출력"""
    print("\n=== AutoInput Task Tree ===\n")
    
    if not data:
        print("[ERROR] No task data found. Run PRD parser first.")
        return
    
    print(f"Project: {data.get('project', 'Unknown')}")
    print(f"Version: {data.get('version', '0.0.0')}")
    print(f"Created: {data.get('created', 'Unknown')}")
    print()
    
    # Phase별 출력
    for phase in data.get('phases', []):
        # Phase 헤더
        status_icon = '[O]' if phase.get('status') == 'completed' else '[>]' if phase.get('status') == 'in_progress' else '[ ]'
        progress = phase.get('progress', 0)
        print(f"{status_icon} {phase['name']} ({progress}%)")
        
        # 작업 목록
        tasks = phase.get('tasks', [])
        for i, task in enumerate(tasks):
            is_last = (i == len(tasks) - 1)
            prefix = "  └─" if is_last else "  ├─"
            
            task_status = '[x]' if task.get('status') == 'completed' else '[>]' if task.get('status') == 'in_progress' else '[ ]'
            task_line = f"{prefix} {task_status} [{task['id']}] {task['name']}"
            
            # 서브태스크가 있으면 표시
            if task.get('subtasks', 0) > 0:
                task_line += f" ({task['subtasks']} subtasks)"
            
            print(task_line)
        
        print()  # Phase 간 구분

def print_status(data):
    """프로젝트 상태 출력"""
    print("\n=== AutoInput Project Status ===\n")
    
    if not data:
        print("[ERROR] No task data found. Run PRD parser first.")
        return
    
    stats = data.get('statistics', {})
    
    print(f"Project: {data.get('project', 'Unknown')}")
    print(f"Version: {data.get('version', '0.0.0')}")
    print()
    
    # 통계 정보
    print("[Task Statistics]")
    print(f"  Total Tasks: {stats.get('total_tasks', 0)}")
    print(f"  Total Requirements: {stats.get('total_requirements', 0)}")
    print()
    
    # 우선순위 분포
    print("[Priority Distribution]")
    priority_dist = stats.get('priority_distribution', {})
    for priority in ['P0', 'P1', 'P2', 'P3']:
        if priority in priority_dist:
            print(f"  {priority}: {priority_dist[priority]} tasks")
    print()
    
    # 타입 분포
    print("[Type Distribution]")
    type_dist = stats.get('type_distribution', {})
    for task_type, count in type_dist.items():
        print(f"  {task_type}: {count} tasks")
    print()
    
    # Phase 요약
    print("[Phase Summary]")
    for phase in data.get('phases', []):
        progress = phase.get('progress', 0)
        task_count = len(phase.get('tasks', []))
        print(f"  {phase['name']}: {task_count} tasks ({progress}%)")

def print_roadmap(data):
    """로드맵 출력"""
    print("\n=== Project Roadmap ===\n")
    
    if not data:
        print("[ERROR] No task data found. Run PRD parser first.")
        return
    
    print(f"Project: {data.get('project', 'Unknown')}")
    print()
    
    # Phase별 로드맵
    for i, phase in enumerate(data.get('phases', []), 1):
        status = phase.get('status', 'pending')
        if status == 'completed':
            status_text = "[COMPLETED]"
            symbol = "[X]"
        elif status == 'in_progress':
            status_text = "[IN PROGRESS]"
            symbol = "[>]"
        else:
            status_text = "[PENDING]"
            symbol = "[ ]"
        
        progress = phase.get('progress', 0)
        progress_bar = '#' * (progress // 10) + '-' * (10 - progress // 10)
        
        print(f"{symbol} Phase {i}: {phase['name']}")
        print(f"    Status: {status_text}")
        print(f"    Progress: [{progress_bar}] {progress}%")
        print(f"    Priority: {phase.get('priority', 'medium').upper()}")
        print(f"    Tasks: {len(phase.get('tasks', []))} total")
        
        # 처음 3개 작업만 표시
        tasks = phase.get('tasks', [])[:3]
        if tasks:
            print("    Key Tasks:")
            for task in tasks:
                print(f"      - [{task['id']}] {task['name']}")
            if len(phase.get('tasks', [])) > 3:
                print(f"      ... and {len(phase.get('tasks', [])) - 3} more")
        print()

def print_next(data):
    """다음 추천 작업 출력"""
    print("\n=== Next Recommended Tasks ===\n")
    
    if not data:
        print("[ERROR] No task data found. Run PRD parser first.")
        return
    
    recommendations = []
    
    # 우선순위 순서대로 Phase 확인
    priority_order = ['critical', 'high', 'medium', 'low']
    phases_by_priority = {}
    
    for phase in data.get('phases', []):
        priority = phase.get('priority', 'medium')
        if priority not in phases_by_priority:
            phases_by_priority[priority] = []
        phases_by_priority[priority].append(phase)
    
    # 우선순위 순서대로 작업 수집
    for priority in priority_order:
        if priority in phases_by_priority:
            for phase in phases_by_priority[priority]:
                if phase.get('status') != 'completed':
                    for task in phase.get('tasks', []):
                        if task.get('status', 'pending') == 'pending':
                            recommendations.append({
                                'task': task,
                                'phase': phase['name'],
                                'priority': priority
                            })
                            if len(recommendations) >= 5:
                                break
                if len(recommendations) >= 5:
                    break
        if len(recommendations) >= 5:
            break
    
    if not recommendations:
        print("[SUCCESS] All tasks are completed or in progress!")
        return
    
    print("Recommended tasks to work on next:\n")
    for i, rec in enumerate(recommendations[:5], 1):
        priority_text = rec['priority'].upper()
        print(f"{i}. [{rec['task']['id']}] {rec['task']['name']}")
        print(f"   Phase: {rec['phase']}")
        print(f"   Priority: {priority_text}")
        if rec['task'].get('subtasks', 0) > 0:
            print(f"   Subtasks: {rec['task']['subtasks']}")
        print()
    
    print("\nTip: Start with the highest priority tasks first!")

def main():
    """메인 실행 함수"""
    import io
    
    # UTF-8 인코딩 설정
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: python taskmaster_simple.py <command>")
        print("\nAvailable commands:")
        print("  list     - Show task tree")
        print("  status   - Show project status")
        print("  roadmap  - Show project roadmap")
        print("  next     - Show recommended next tasks")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # 작업 데이터 로드
    data = load_tasks()
    
    if command == 'list':
        print_tree(data)
    elif command == 'status':
        print_status(data)
    elif command == 'roadmap':
        print_roadmap(data)
    elif command == 'next':
        print_next(data)
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("Use 'list', 'status', 'roadmap', or 'next'")
        sys.exit(1)

if __name__ == "__main__":
    main()
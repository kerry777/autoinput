#!/usr/bin/env python3
"""
Enhanced Taskmaster Status - 프로젝트 상태 대시보드
"""

import json
import sys
import io
from pathlib import Path
from datetime import datetime

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_tasks(file_path='parsed_tasks.json'):
    """작업 데이터 로드"""
    if Path(file_path).exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def calculate_metrics(data):
    """프로젝트 메트릭 계산"""
    if not data:
        return {}
    
    metrics = {
        'total_tasks': 0,
        'total_subtasks': 0,
        'completed_tasks': 0,
        'in_progress_tasks': 0,
        'pending_tasks': 0,
        'critical_tasks': 0,
        'high_priority_tasks': 0,
        'estimated_hours': 0,
        'completion_rate': 0
    }
    
    for phase in data.get('phases', []):
        tasks = phase.get('tasks', [])
        metrics['total_tasks'] += len(tasks)
        
        # 우선순위별 카운트
        priority = phase.get('priority', '').lower()
        if priority == 'critical':
            metrics['critical_tasks'] += len(tasks)
        elif priority == 'high':
            metrics['high_priority_tasks'] += len(tasks)
        
        # 상태별 카운트
        for task in tasks:
            status = task.get('status', 'pending')
            if status == 'completed':
                metrics['completed_tasks'] += 1
            elif status == 'in_progress':
                metrics['in_progress_tasks'] += 1
            else:
                metrics['pending_tasks'] += 1
            
            # 서브태스크 카운트
            metrics['total_subtasks'] += task.get('subtasks', 0)
            
            # 예상 시간 (기본값: 태스크당 8시간)
            metrics['estimated_hours'] += 8
    
    # 완료율 계산
    if metrics['total_tasks'] > 0:
        metrics['completion_rate'] = (metrics['completed_tasks'] / metrics['total_tasks']) * 100
    
    return metrics

def print_dashboard(data):
    """상태 대시보드 출력"""
    print("=" * 60)
    print(" " * 15 + "AUTOINPUT PROJECT DASHBOARD")
    print("=" * 60)
    print()
    
    if not data:
        print("[ERROR] No project data found.")
        print("Run: python scripts/simple_prd_parser.py sample_prd.txt")
        return
    
    # 프로젝트 정보
    print("📋 PROJECT INFORMATION")
    print("-" * 40)
    print(f"  Project Name    : {data.get('project', 'Unknown')}")
    print(f"  Version         : {data.get('version', '0.0.0')}")
    print(f"  Last Updated    : {data.get('created', 'Unknown')[:10]}")
    print()
    
    # 메트릭 계산
    metrics = calculate_metrics(data)
    stats = data.get('statistics', {})
    
    # 진행 상황
    print("📊 PROGRESS OVERVIEW")
    print("-" * 40)
    completion = metrics['completion_rate']
    progress_bar = "█" * int(completion / 5) + "░" * (20 - int(completion / 5))
    print(f"  Overall Progress: [{progress_bar}] {completion:.1f}%")
    print(f"  Completed       : {metrics['completed_tasks']}/{metrics['total_tasks']} tasks")
    print(f"  In Progress     : {metrics['in_progress_tasks']} tasks")
    print(f"  Pending         : {metrics['pending_tasks']} tasks")
    print()
    
    # 작업 통계
    print("📈 TASK STATISTICS")
    print("-" * 40)
    print(f"  Total Requirements : {stats.get('total_requirements', 0)}")
    print(f"  Total Tasks        : {metrics['total_tasks']}")
    print(f"  Total Subtasks     : {metrics['total_subtasks']}")
    print(f"  Estimated Hours    : {metrics['estimated_hours']} hours")
    print(f"  Estimated Days     : {metrics['estimated_hours'] / 8:.1f} days")
    print()
    
    # 우선순위 분포
    print("🎯 PRIORITY BREAKDOWN")
    print("-" * 40)
    priority_dist = stats.get('priority_distribution', {})
    
    for priority, label in [('P0', 'Critical'), ('P1', 'High'), ('P2', 'Medium'), ('P3', 'Low')]:
        count = priority_dist.get(priority, 0)
        if count > 0:
            percentage = (count / metrics['total_tasks']) * 100 if metrics['total_tasks'] > 0 else 0
            bar_length = int(percentage / 5)
            bar = "▓" * bar_length + "░" * (20 - bar_length)
            print(f"  {priority} ({label:8s}): [{bar}] {count:2d} tasks ({percentage:5.1f}%)")
    print()
    
    # Phase 상태
    print("📦 PHASE STATUS")
    print("-" * 40)
    
    for i, phase in enumerate(data.get('phases', []), 1):
        task_count = len(phase.get('tasks', []))
        progress = phase.get('progress', 0)
        status = phase.get('status', 'pending')
        
        # 상태 아이콘
        if status == 'completed':
            icon = "✅"
        elif status == 'in_progress':
            icon = "🔄"
        else:
            icon = "⏳"
        
        # 미니 진행률 바
        mini_bar = "█" * (progress // 20) + "░" * (5 - progress // 20)
        
        print(f"  {icon} Phase {i}: {phase['name'][:30]:30s}")
        print(f"     Tasks: {task_count:2d} | Progress: [{mini_bar}] {progress:3d}%")
    print()
    
    # 다음 액션
    print("⚡ RECOMMENDED ACTIONS")
    print("-" * 40)
    
    if metrics['critical_tasks'] > 0 and metrics['completed_tasks'] == 0:
        print("  1. Start with Critical Priority tasks (P0)")
        print("     → Run: python scripts/taskmaster_simple.py next")
    elif metrics['in_progress_tasks'] == 0:
        print("  1. Begin working on highest priority pending tasks")
        print("     → Run: python scripts/taskmaster_simple.py next")
    elif metrics['in_progress_tasks'] > 5:
        print("  1. Focus on completing in-progress tasks")
        print("     → Too many tasks in progress, complete some first")
    else:
        print("  1. Continue with current tasks")
        print("     → Good progress! Keep going")
    
    print()
    print("  2. View detailed task list")
    print("     → Run: python scripts/taskmaster_simple.py list")
    print()
    print("  3. Check project roadmap")
    print("     → Run: python scripts/taskmaster_simple.py roadmap")
    print()
    
    # 푸터
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def main():
    """메인 실행 함수"""
    data = load_tasks()
    print_dashboard(data)

if __name__ == "__main__":
    main()
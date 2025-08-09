#!/usr/bin/env python3
"""
Taskmaster CLI - 프로젝트 작업 관리 도구
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.panel import Panel
from rich import print as rprint

console = Console()

class TaskStatus(Enum):
    PENDING = "⏳ pending"
    IN_PROGRESS = "🔄 in_progress"
    COMPLETED = "✅ completed"
    BLOCKED = "🚫 blocked"
    CANCELLED = "❌ cancelled"

class TaskPriority(Enum):
    CRITICAL = "🔴 Critical"
    HIGH = "🟡 High"
    MEDIUM = "🟢 Medium"
    LOW = "⚪ Low"

class TaskManager:
    """작업 관리 클래스"""
    
    def __init__(self, data_file: str = "tasks.json"):
        self.data_file = Path(data_file)
        self.tasks = self.load_tasks()
        
    def load_tasks(self) -> Dict:
        """작업 데이터 로드"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.get_default_tasks()
    
    def save_tasks(self):
        """작업 데이터 저장"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
    
    def get_default_tasks(self) -> Dict:
        """기본 작업 구조"""
        return {
            "project": "AutoInput",
            "version": "0.1.0",
            "created": datetime.now().isoformat(),
            "phases": [
                {
                    "id": "phase1",
                    "name": "📦 Foundation Setup",
                    "status": "in_progress",
                    "priority": "critical",
                    "progress": 60,
                    "tasks": [
                        {"id": "1.1", "name": "Project initialization", "status": "completed"},
                        {"id": "1.2", "name": "Development environment", "status": "completed"},
                        {"id": "1.3", "name": "Documentation", "status": "completed"},
                        {"id": "1.4", "name": "Database setup", "status": "pending"},
                        {"id": "1.5", "name": "Authentication system", "status": "pending"}
                    ]
                },
                {
                    "id": "phase2",
                    "name": "🔧 Core Engine Development",
                    "status": "pending",
                    "priority": "critical",
                    "progress": 0,
                    "tasks": [
                        {"id": "2.1", "name": "Playwright engine", "status": "pending"},
                        {"id": "2.2", "name": "Selector management", "status": "pending"},
                        {"id": "2.3", "name": "Self-healing system", "status": "pending"},
                        {"id": "2.4", "name": "Scenario recorder", "status": "pending"},
                        {"id": "2.5", "name": "Error handling", "status": "pending"}
                    ]
                }
            ]
        }
    
    def get_statistics(self) -> Dict:
        """프로젝트 통계"""
        total_tasks = 0
        completed_tasks = 0
        in_progress_tasks = 0
        blocked_tasks = 0
        
        for phase in self.tasks.get("phases", []):
            for task in phase.get("tasks", []):
                total_tasks += 1
                status = task.get("status", "pending")
                if status == "completed":
                    completed_tasks += 1
                elif status == "in_progress":
                    in_progress_tasks += 1
                elif status == "blocked":
                    blocked_tasks += 1
        
        overall_progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total": total_tasks,
            "completed": completed_tasks,
            "in_progress": in_progress_tasks,
            "blocked": blocked_tasks,
            "pending": total_tasks - completed_tasks - in_progress_tasks - blocked_tasks,
            "progress": overall_progress
        }
    
    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """작업 상태 업데이트"""
        for phase in self.tasks.get("phases", []):
            for task in phase.get("tasks", []):
                if task.get("id") == task_id:
                    task["status"] = new_status
                    task["updated"] = datetime.now().isoformat()
                    self.update_phase_progress(phase)
                    self.save_tasks()
                    return True
        return False
    
    def update_phase_progress(self, phase: Dict):
        """단계별 진행률 업데이트"""
        tasks = phase.get("tasks", [])
        if not tasks:
            return
        
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        phase["progress"] = int((completed / len(tasks)) * 100)
        
        # 단계 상태 업데이트
        if phase["progress"] == 0:
            phase["status"] = "pending"
        elif phase["progress"] == 100:
            phase["status"] = "completed"
        else:
            phase["status"] = "in_progress"

@click.group()
def cli():
    """AutoInput Taskmaster - 프로젝트 작업 관리 도구"""
    pass

@cli.command()
def status():
    """프로젝트 전체 상태 표시"""
    manager = TaskManager()
    stats = manager.get_statistics()
    
    # 헤더 패널
    header = Panel(
        f"[bold cyan]AutoInput Project Status[/bold cyan]\n"
        f"Version: {manager.tasks.get('version', 'N/A')}\n"
        f"Overall Progress: [bold green]{stats['progress']:.1f}%[/bold green]",
        title="🎯 Taskmaster",
        border_style="cyan"
    )
    console.print(header)
    
    # 통계 테이블
    table = Table(title="📊 Task Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Status", style="cyan", width=15)
    table.add_column("Count", justify="right", style="green")
    table.add_column("Percentage", justify="right")
    
    table.add_row("✅ Completed", str(stats['completed']), 
                  f"{stats['completed']/stats['total']*100:.1f}%")
    table.add_row("🔄 In Progress", str(stats['in_progress']), 
                  f"{stats['in_progress']/stats['total']*100:.1f}%")
    table.add_row("⏳ Pending", str(stats['pending']), 
                  f"{stats['pending']/stats['total']*100:.1f}%")
    table.add_row("🚫 Blocked", str(stats['blocked']), 
                  f"{stats['blocked']/stats['total']*100:.1f}%")
    table.add_row("─" * 15, "─" * 5, "─" * 10, style="dim")
    table.add_row("Total", str(stats['total']), "100.0%", style="bold")
    
    console.print(table)

@cli.command()
def list():
    """모든 작업 목록 표시"""
    manager = TaskManager()
    
    tree = Tree("🎯 [bold cyan]AutoInput Task Tree[/bold cyan]")
    
    for phase in manager.tasks.get("phases", []):
        # 단계 노드
        phase_status = "✅" if phase["status"] == "completed" else "🔄" if phase["status"] == "in_progress" else "⏳"
        phase_node = tree.add(
            f"{phase_status} {phase['name']} "
            f"[dim]({phase['progress']}% - {phase['priority']})[/dim]"
        )
        
        # 작업 노드
        for task in phase.get("tasks", []):
            task_status = "✅" if task["status"] == "completed" else "🔄" if task["status"] == "in_progress" else "⏳"
            task_text = f"{task_status} [{task['id']}] {task['name']}"
            
            if task["status"] == "completed":
                phase_node.add(f"[green]{task_text}[/green]")
            elif task["status"] == "in_progress":
                phase_node.add(f"[yellow]{task_text}[/yellow]")
            elif task["status"] == "blocked":
                phase_node.add(f"[red]{task_text}[/red]")
            else:
                phase_node.add(f"[dim]{task_text}[/dim]")
    
    console.print(tree)

@cli.command()
@click.argument('task_id')
@click.argument('status', type=click.Choice(['pending', 'in_progress', 'completed', 'blocked', 'cancelled']))
def update(task_id: str, status: str):
    """작업 상태 업데이트"""
    manager = TaskManager()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Updating task {task_id}...", total=1)
        
        if manager.update_task_status(task_id, status):
            progress.update(task, completed=1)
            console.print(f"[green]✅ Task {task_id} updated to {status}[/green]")
        else:
            console.print(f"[red]❌ Task {task_id} not found[/red]")

@cli.command()
def roadmap():
    """프로젝트 로드맵 표시"""
    manager = TaskManager()
    
    console.print("[bold cyan]📍 Project Roadmap[/bold cyan]\n")
    
    for i, phase in enumerate(manager.tasks.get("phases", []), 1):
        # 단계 상태에 따른 스타일
        if phase["status"] == "completed":
            style = "green"
            icon = "✅"
        elif phase["status"] == "in_progress":
            style = "yellow"
            icon = "🔄"
        else:
            style = "dim"
            icon = "⏳"
        
        # 진행률 바
        progress_bar = "█" * (phase["progress"] // 10) + "░" * (10 - phase["progress"] // 10)
        
        console.print(
            f"{icon} [bold {style}]Phase {i}: {phase['name']}[/bold {style}]\n"
            f"   Progress: [{style}]{progress_bar}[/{style}] {phase['progress']}%\n"
            f"   Priority: {phase['priority'].upper()}\n"
            f"   Tasks: {len([t for t in phase['tasks'] if t['status'] == 'completed'])}/{len(phase['tasks'])} completed\n"
        )

@cli.command()
def next():
    """다음 작업할 태스크 추천"""
    manager = TaskManager()
    
    console.print("[bold cyan]🎯 Next Recommended Tasks[/bold cyan]\n")
    
    recommendations = []
    
    for phase in manager.tasks.get("phases", []):
        if phase["status"] != "completed":
            for task in phase.get("tasks", []):
                if task["status"] == "pending":
                    recommendations.append({
                        "task": task,
                        "phase": phase["name"],
                        "priority": phase["priority"]
                    })
                    if len(recommendations) >= 5:
                        break
        if len(recommendations) >= 5:
            break
    
    if not recommendations:
        console.print("[green]🎉 All tasks are completed or in progress![/green]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Task", style="white")
    table.add_column("Phase", style="yellow")
    table.add_column("Priority", style="red")
    
    for rec in recommendations[:5]:
        priority_icon = "🔴" if rec["priority"] == "critical" else "🟡" if rec["priority"] == "high" else "🟢"
        table.add_row(
            rec["task"]["id"],
            rec["task"]["name"],
            rec["phase"],
            f"{priority_icon} {rec['priority'].upper()}"
        )
    
    console.print(table)
    console.print("\n💡 [dim]Tip: Use 'taskmaster update <task_id> in_progress' to start working on a task[/dim]")

@cli.command()
def init():
    """작업 데이터 초기화"""
    manager = TaskManager()
    
    if manager.data_file.exists():
        if not click.confirm("Task data already exists. Override?"):
            console.print("[yellow]Initialization cancelled[/yellow]")
            return
    
    manager.tasks = manager.get_default_tasks()
    manager.save_tasks()
    console.print("[green]✅ Task data initialized successfully[/green]")

@cli.command()
@click.option('--output', '-o', default='tasks_export.json', help='Export file name')
def export(output: str):
    """작업 데이터 내보내기"""
    manager = TaskManager()
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(manager.tasks, f, ensure_ascii=False, indent=2)
    
    console.print(f"[green]✅ Tasks exported to {output}[/green]")

if __name__ == "__main__":
    cli()
#!/usr/bin/env python3
"""
PRD Parser - Product Requirements Document를 작업 목록으로 변환
"""

import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.progress import track

console = Console()

class RequirementType(Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    TECHNICAL = "technical"
    BUSINESS = "business"
    UX = "ux"

class Priority(Enum):
    CRITICAL = "P0"
    HIGH = "P1"
    MEDIUM = "P2"
    LOW = "P3"

@dataclass
class Requirement:
    """요구사항 데이터 클래스"""
    id: str
    title: str
    description: str
    type: RequirementType
    priority: Priority
    acceptance_criteria: List[str]
    dependencies: List[str]
    estimated_hours: int
    tags: List[str]

@dataclass
class Epic:
    """에픽 데이터 클래스"""
    id: str
    title: str
    description: str
    requirements: List[Requirement]
    priority: Priority
    milestone: Optional[str]

@dataclass
class Task:
    """작업 데이터 클래스"""
    id: str
    title: str
    description: str
    type: str
    priority: str
    estimated_hours: int
    dependencies: List[str]
    parent_id: Optional[str]
    tags: List[str]
    acceptance_criteria: List[str]
    status: str = "pending"

class PRDParser:
    """PRD 문서 파서"""
    
    def __init__(self):
        self.epics: List[Epic] = []
        self.requirements: List[Requirement] = []
        self.tasks: List[Task] = []
        self.metadata: Dict = {}
        
    def parse_file(self, file_path: str) -> Dict:
        """PRD 파일 파싱"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"PRD file not found: {file_path}")
        
        content = path.read_text(encoding='utf-8')
        
        # 파일 형식에 따라 다른 파서 사용
        if path.suffix == '.md':
            return self.parse_markdown(content)
        elif path.suffix == '.txt':
            return self.parse_text(content)
        elif path.suffix in ['.yaml', '.yml']:
            return self.parse_yaml(content)
        elif path.suffix == '.json':
            return self.parse_json(content)
        else:
            # 기본적으로 텍스트로 처리
            return self.parse_text(content)
    
    def parse_markdown(self, content: str) -> Dict:
        """Markdown 형식 PRD 파싱"""
        lines = content.split('\n')
        current_section = None
        current_epic = None
        current_requirement = None
        
        for line in lines:
            line = line.strip()
            
            # 메타데이터 추출
            if line.startswith('# '):
                self.metadata['title'] = line[2:].strip()
            
            # 에픽 추출 (## Epic:)
            elif line.startswith('## Epic:') or line.startswith('## 에픽:'):
                epic_title = line.split(':', 1)[1].strip()
                current_epic = {
                    'id': f"EPIC-{len(self.epics) + 1}",
                    'title': epic_title,
                    'requirements': []
                }
                self.epics.append(current_epic)
            
            # 요구사항 추출 (### Requirement:)
            elif line.startswith('### Requirement:') or line.startswith('### 요구사항:'):
                req_title = line.split(':', 1)[1].strip()
                current_requirement = {
                    'id': f"REQ-{len(self.requirements) + 1}",
                    'title': req_title,
                    'description': '',
                    'acceptance_criteria': [],
                    'epic_id': current_epic['id'] if current_epic else None
                }
                self.requirements.append(current_requirement)
            
            # 우선순위 추출
            elif line.startswith('Priority:') or line.startswith('우선순위:'):
                priority = line.split(':', 1)[1].strip()
                if current_requirement:
                    current_requirement['priority'] = self._parse_priority(priority)
            
            # 인수 조건 추출
            elif line.startswith('- [ ]') or line.startswith('- [x]'):
                criteria = line[5:].strip()
                if current_requirement:
                    current_requirement['acceptance_criteria'].append(criteria)
            
            # 태그 추출
            elif line.startswith('Tags:') or line.startswith('태그:'):
                tags = line.split(':', 1)[1].strip()
                if current_requirement:
                    current_requirement['tags'] = [t.strip() for t in tags.split(',')]
        
        return self._convert_to_tasks()
    
    def parse_text(self, content: str) -> Dict:
        """텍스트 형식 PRD 파싱"""
        lines = content.split('\n')
        sections = {}
        current_section = None
        current_content = []
        
        for line in lines:
            # 섹션 헤더 감지
            if self._is_section_header(line):
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line.strip().rstrip(':')
                current_content = []
            else:
                current_content.append(line)
        
        # 마지막 섹션 저장
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        # 섹션별로 파싱
        self._parse_sections(sections)
        
        return self._convert_to_tasks()
    
    def parse_yaml(self, content: str) -> Dict:
        """YAML 형식 PRD 파싱"""
        data = yaml.safe_load(content)
        
        if 'metadata' in data:
            self.metadata = data['metadata']
        
        if 'epics' in data:
            for epic_data in data['epics']:
                self._parse_epic_data(epic_data)
        
        if 'requirements' in data:
            for req_data in data['requirements']:
                self._parse_requirement_data(req_data)
        
        return self._convert_to_tasks()
    
    def parse_json(self, content: str) -> Dict:
        """JSON 형식 PRD 파싱"""
        data = json.loads(content)
        
        if 'metadata' in data:
            self.metadata = data['metadata']
        
        if 'epics' in data:
            for epic_data in data['epics']:
                self._parse_epic_data(epic_data)
        
        if 'requirements' in data:
            for req_data in data['requirements']:
                self._parse_requirement_data(req_data)
        
        return self._convert_to_tasks()
    
    def _is_section_header(self, line: str) -> bool:
        """섹션 헤더인지 확인"""
        headers = [
            '개요:', 'Overview:',
            '목적:', 'Purpose:',
            '요구사항:', 'Requirements:',
            '기능 요구사항:', 'Functional Requirements:',
            '비기능 요구사항:', 'Non-Functional Requirements:',
            '제약사항:', 'Constraints:',
            '가정:', 'Assumptions:',
            '위험:', 'Risks:',
            '일정:', 'Timeline:',
            '마일스톤:', 'Milestones:'
        ]
        
        line = line.strip()
        return any(line.startswith(header) for header in headers)
    
    def _parse_sections(self, sections: Dict[str, str]):
        """섹션별 내용 파싱"""
        # 요구사항 섹션 파싱
        req_sections = [
            '요구사항', 'Requirements',
            '기능 요구사항', 'Functional Requirements'
        ]
        
        for section_name in req_sections:
            if section_name in sections:
                self._parse_requirements_section(sections[section_name])
        
        # 메타데이터 추출
        if '개요' in sections or 'Overview' in sections:
            overview = sections.get('개요', sections.get('Overview', ''))
            self.metadata['overview'] = overview.strip()
        
        if '목적' in sections or 'Purpose' in sections:
            purpose = sections.get('목적', sections.get('Purpose', ''))
            self.metadata['purpose'] = purpose.strip()
    
    def _parse_requirements_section(self, content: str):
        """요구사항 섹션 파싱"""
        lines = content.strip().split('\n')
        current_req = None
        
        for line in lines:
            line = line.strip()
            
            # 번호가 있는 요구사항 (1. XXX, 1) XXX)
            if re.match(r'^\d+[\.\)]\s+', line):
                if current_req:
                    self.requirements.append(current_req)
                
                req_text = re.sub(r'^\d+[\.\)]\s+', '', line)
                current_req = {
                    'id': f"REQ-{len(self.requirements) + 1}",
                    'title': req_text,
                    'description': '',
                    'priority': 'P2',  # 기본 우선순위
                    'type': 'functional',
                    'acceptance_criteria': [],
                    'tags': []
                }
            
            # 하위 항목 (-, *, •)
            elif re.match(r'^[-\*•]\s+', line) and current_req:
                item = re.sub(r'^[-\*•]\s+', '', line)
                current_req['acceptance_criteria'].append(item)
            
            # 설명 추가
            elif line and current_req:
                current_req['description'] += ' ' + line
        
        # 마지막 요구사항 저장
        if current_req:
            self.requirements.append(current_req)
    
    def _parse_priority(self, priority_text: str) -> str:
        """우선순위 텍스트 파싱"""
        priority_text = priority_text.lower()
        
        if any(word in priority_text for word in ['critical', '긴급', '필수', 'p0']):
            return 'P0'
        elif any(word in priority_text for word in ['high', '높음', '중요', 'p1']):
            return 'P1'
        elif any(word in priority_text for word in ['medium', '보통', '중간', 'p2']):
            return 'P2'
        elif any(word in priority_text for word in ['low', '낮음', '선택', 'p3']):
            return 'P3'
        else:
            return 'P2'  # 기본값
    
    def _parse_epic_data(self, epic_data: Dict):
        """에픽 데이터 파싱"""
        epic = {
            'id': epic_data.get('id', f"EPIC-{len(self.epics) + 1}"),
            'title': epic_data.get('title', 'Untitled Epic'),
            'description': epic_data.get('description', ''),
            'priority': epic_data.get('priority', 'P2'),
            'requirements': []
        }
        self.epics.append(epic)
        
        # 에픽 내 요구사항 파싱
        if 'requirements' in epic_data:
            for req_data in epic_data['requirements']:
                req_data['epic_id'] = epic['id']
                self._parse_requirement_data(req_data)
    
    def _parse_requirement_data(self, req_data: Dict):
        """요구사항 데이터 파싱"""
        requirement = {
            'id': req_data.get('id', f"REQ-{len(self.requirements) + 1}"),
            'title': req_data.get('title', 'Untitled Requirement'),
            'description': req_data.get('description', ''),
            'type': req_data.get('type', 'functional'),
            'priority': req_data.get('priority', 'P2'),
            'acceptance_criteria': req_data.get('acceptance_criteria', []),
            'dependencies': req_data.get('dependencies', []),
            'estimated_hours': req_data.get('estimated_hours', 0),
            'tags': req_data.get('tags', []),
            'epic_id': req_data.get('epic_id')
        }
        self.requirements.append(requirement)
    
    def _convert_to_tasks(self) -> Dict:
        """요구사항을 작업으로 변환"""
        tasks = []
        
        # 에픽을 Phase로 변환
        for epic in self.epics:
            phase_task = Task(
                id=epic['id'],
                title=epic['title'],
                description=epic.get('description', ''),
                type='phase',
                priority=epic.get('priority', 'P2'),
                estimated_hours=0,
                dependencies=[],
                parent_id=None,
                tags=['epic'],
                acceptance_criteria=[]
            )
            tasks.append(phase_task)
        
        # 요구사항을 Task로 변환
        for req in self.requirements:
            # 메인 태스크 생성
            main_task = Task(
                id=req['id'],
                title=req['title'],
                description=req.get('description', ''),
                type=req.get('type', 'functional'),
                priority=req.get('priority', 'P2'),
                estimated_hours=req.get('estimated_hours', 8),
                dependencies=req.get('dependencies', []),
                parent_id=req.get('epic_id'),
                tags=req.get('tags', []),
                acceptance_criteria=req.get('acceptance_criteria', [])
            )
            tasks.append(main_task)
            
            # 인수 조건을 서브태스크로 변환
            for i, criteria in enumerate(req.get('acceptance_criteria', [])):
                sub_task = Task(
                    id=f"{req['id']}-{i+1}",
                    title=criteria,
                    description=f"Acceptance criteria for {req['title']}",
                    type='subtask',
                    priority=req.get('priority', 'P2'),
                    estimated_hours=2,
                    dependencies=[],
                    parent_id=req['id'],
                    tags=['acceptance_criteria'],
                    acceptance_criteria=[]
                )
                tasks.append(sub_task)
        
        return {
            'metadata': self.metadata,
            'epics': self.epics,
            'requirements': self.requirements,
            'tasks': [asdict(task) for task in tasks],
            'statistics': self._calculate_statistics(tasks)
        }
    
    def _calculate_statistics(self, tasks: List[Task]) -> Dict:
        """통계 계산"""
        total_tasks = len(tasks)
        total_hours = sum(task.estimated_hours for task in tasks)
        
        priority_count = {}
        type_count = {}
        
        for task in tasks:
            # 우선순위별 카운트
            priority = task.priority
            priority_count[priority] = priority_count.get(priority, 0) + 1
            
            # 타입별 카운트
            task_type = task.type
            type_count[task_type] = type_count.get(task_type, 0) + 1
        
        return {
            'total_tasks': total_tasks,
            'total_hours': total_hours,
            'total_days': total_hours / 8,  # 8시간 = 1일
            'priority_distribution': priority_count,
            'type_distribution': type_count
        }

class TaskGenerator:
    """작업 생성기"""
    
    def __init__(self, parsed_data: Dict):
        self.data = parsed_data
        
    def generate_taskmaster_format(self) -> Dict:
        """Taskmaster 형식으로 변환"""
        phases = []
        
        # 에픽별로 Phase 생성
        for epic in self.data.get('epics', []):
            phase = {
                'id': epic['id'],
                'name': epic['title'],
                'status': 'pending',
                'priority': epic.get('priority', 'P2'),
                'progress': 0,
                'tasks': []
            }
            
            # 해당 에픽의 태스크 찾기
            for task in self.data.get('tasks', []):
                if task.get('parent_id') == epic['id']:
                    phase['tasks'].append({
                        'id': task['id'],
                        'name': task['title'],
                        'status': 'pending',
                        'estimated_hours': task.get('estimated_hours', 8),
                        'dependencies': task.get('dependencies', [])
                    })
            
            phases.append(phase)
        
        # 에픽이 없는 태스크들을 별도 Phase로
        orphan_tasks = []
        for task in self.data.get('tasks', []):
            if not task.get('parent_id') and task['type'] != 'phase':
                orphan_tasks.append({
                    'id': task['id'],
                    'name': task['title'],
                    'status': 'pending',
                    'estimated_hours': task.get('estimated_hours', 8),
                    'dependencies': task.get('dependencies', [])
                })
        
        if orphan_tasks:
            phases.append({
                'id': 'general',
                'name': '📋 General Requirements',
                'status': 'pending',
                'priority': 'P2',
                'progress': 0,
                'tasks': orphan_tasks
            })
        
        return {
            'project': self.data.get('metadata', {}).get('title', 'Untitled Project'),
            'version': '0.1.0',
            'created': datetime.now().isoformat(),
            'metadata': self.data.get('metadata', {}),
            'phases': phases,
            'statistics': self.data.get('statistics', {})
        }
    
    def generate_jira_format(self) -> List[Dict]:
        """JIRA 형식으로 변환"""
        jira_issues = []
        
        for task in self.data.get('tasks', []):
            issue = {
                'project': 'AUTOINPUT',
                'summary': task['title'],
                'description': task['description'],
                'issuetype': self._map_to_jira_type(task['type']),
                'priority': self._map_to_jira_priority(task['priority']),
                'labels': task.get('tags', []),
                'timeoriginalestimate': f"{task.get('estimated_hours', 8)}h",
                'acceptance_criteria': task.get('acceptance_criteria', [])
            }
            
            if task.get('parent_id'):
                issue['parent'] = task['parent_id']
            
            jira_issues.append(issue)
        
        return jira_issues
    
    def _map_to_jira_type(self, task_type: str) -> str:
        """JIRA 이슈 타입으로 매핑"""
        type_mapping = {
            'phase': 'Epic',
            'functional': 'Story',
            'technical': 'Task',
            'bug': 'Bug',
            'subtask': 'Sub-task'
        }
        return type_mapping.get(task_type, 'Task')
    
    def _map_to_jira_priority(self, priority: str) -> str:
        """JIRA 우선순위로 매핑"""
        priority_mapping = {
            'P0': 'Highest',
            'P1': 'High',
            'P2': 'Medium',
            'P3': 'Low'
        }
        return priority_mapping.get(priority, 'Medium')
    
    def generate_github_issues(self) -> List[Dict]:
        """GitHub Issues 형식으로 변환"""
        issues = []
        
        for task in self.data.get('tasks', []):
            issue = {
                'title': task['title'],
                'body': self._generate_github_body(task),
                'labels': self._generate_github_labels(task),
                'milestone': None
            }
            
            # 에픽을 마일스톤으로 사용
            if task.get('parent_id'):
                issue['milestone'] = task['parent_id']
            
            issues.append(issue)
        
        return issues
    
    def _generate_github_body(self, task: Dict) -> str:
        """GitHub 이슈 본문 생성"""
        body = f"## Description\n{task['description']}\n\n"
        
        if task.get('acceptance_criteria'):
            body += "## Acceptance Criteria\n"
            for criteria in task['acceptance_criteria']:
                body += f"- [ ] {criteria}\n"
            body += "\n"
        
        if task.get('dependencies'):
            body += "## Dependencies\n"
            for dep in task['dependencies']:
                body += f"- #{dep}\n"
            body += "\n"
        
        if task.get('estimated_hours'):
            body += f"## Estimated Time\n{task['estimated_hours']} hours\n"
        
        return body
    
    def _generate_github_labels(self, task: Dict) -> List[str]:
        """GitHub 라벨 생성"""
        labels = task.get('tags', []).copy()
        
        # 우선순위 라벨
        priority_labels = {
            'P0': 'priority: critical',
            'P1': 'priority: high',
            'P2': 'priority: medium',
            'P3': 'priority: low'
        }
        if task.get('priority') in priority_labels:
            labels.append(priority_labels[task['priority']])
        
        # 타입 라벨
        type_labels = {
            'functional': 'type: feature',
            'technical': 'type: technical',
            'bug': 'type: bug',
            'documentation': 'type: docs'
        }
        if task.get('type') in type_labels:
            labels.append(type_labels[task['type']])
        
        return labels

@click.command()
@click.argument('prd_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='tasks.json', help='Output file name')
@click.option('--format', '-f', type=click.Choice(['taskmaster', 'jira', 'github']), 
              default='taskmaster', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def parse_prd(prd_file: str, output: str, format: str, verbose: bool):
    """PRD 문서를 파싱하여 작업 목록으로 변환"""
    
    console.print(f"[cyan]📄 Parsing PRD: {prd_file}[/cyan]")
    
    # PRD 파싱
    parser = PRDParser()
    
    try:
        parsed_data = parser.parse_file(prd_file)
        
        if verbose:
            # 파싱 결과 표시
            stats = parsed_data.get('statistics', {})
            
            panel = Panel(
                f"✅ Successfully parsed PRD\n\n"
                f"📊 Statistics:\n"
                f"  • Total Tasks: {stats.get('total_tasks', 0)}\n"
                f"  • Total Hours: {stats.get('total_hours', 0)}\n"
                f"  • Estimated Days: {stats.get('total_days', 0):.1f}\n",
                title="[bold green]Parsing Complete[/bold green]",
                border_style="green"
            )
            console.print(panel)
            
            # 우선순위 분포
            if stats.get('priority_distribution'):
                table = Table(title="Priority Distribution")
                table.add_column("Priority", style="cyan")
                table.add_column("Count", justify="right")
                
                for priority, count in stats['priority_distribution'].items():
                    table.add_row(priority, str(count))
                
                console.print(table)
        
        # 작업 생성
        generator = TaskGenerator(parsed_data)
        
        if format == 'taskmaster':
            output_data = generator.generate_taskmaster_format()
            output_file = output if output.endswith('.json') else f"{output}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]✅ Taskmaster format saved to {output_file}[/green]")
            
        elif format == 'jira':
            output_data = generator.generate_jira_format()
            output_file = output if output.endswith('.json') else f"{output}_jira.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]✅ JIRA format saved to {output_file}[/green]")
            
        elif format == 'github':
            output_data = generator.generate_github_issues()
            output_file = output if output.endswith('.json') else f"{output}_github.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            console.print(f"[green]✅ GitHub Issues format saved to {output_file}[/green]")
        
        # 작업 트리 표시
        if verbose:
            tree = Tree("📋 [bold cyan]Generated Task Tree[/bold cyan]")
            
            taskmaster_data = generator.generate_taskmaster_format()
            for phase in taskmaster_data['phases']:
                phase_node = tree.add(f"📦 {phase['name']} ({len(phase['tasks'])} tasks)")
                
                for task in phase['tasks'][:5]:  # 처음 5개만 표시
                    phase_node.add(f"• {task['name']}")
                
                if len(phase['tasks']) > 5:
                    phase_node.add(f"... and {len(phase['tasks']) - 5} more")
            
            console.print(tree)
    
    except Exception as e:
        console.print(f"[red]❌ Error parsing PRD: {e}[/red]")
        raise

if __name__ == "__main__":
    parse_prd()
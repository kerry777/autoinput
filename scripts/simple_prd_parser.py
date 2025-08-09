#!/usr/bin/env python3
"""
Simple PRD Parser - PRD 문서를 작업 목록으로 변환 (의존성 최소화)
"""

import json
import re
from datetime import datetime
from pathlib import Path

def parse_prd_file(file_path):
    """PRD 파일을 파싱하여 작업 목록 생성"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 결과 저장용 구조
    result = {
        'project': 'AutoInput',
        'version': '0.1.0',
        'created': datetime.now().isoformat(),
        'phases': [],
        'requirements': [],
        'tasks': []
    }
    
    # 섹션별로 분리
    lines = content.split('\n')
    current_section = None
    requirements = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # 섹션 헤더 감지
        if '기능 요구사항' in line or 'Functional Requirements' in line:
            current_section = 'functional'
            continue
        elif '비기능 요구사항' in line or 'Non-Functional Requirements' in line:
            current_section = 'non-functional'
            continue
        elif '마일스톤' in line or 'Milestones' in line:
            current_section = 'milestones'
            continue
        
        # 요구사항 파싱 (번호로 시작하는 줄)
        if current_section in ['functional', 'non-functional']:
            # 메인 요구사항 (1. xxx 형태)
            match = re.match(r'^(\d+)\.\s+(.+)', line_stripped)
            if match:
                req_num = match.group(1)
                req_title = match.group(2)
                
                requirement = {
                    'id': f'REQ-{req_num}',
                    'title': req_title,
                    'type': current_section,
                    'priority': 'P2',  # 기본값
                    'subtasks': [],
                    'description': ''
                }
                requirements.append(requirement)
            
            # 우선순위 파싱
            elif 'Priority:' in line_stripped or '우선순위:' in line_stripped:
                if requirements:
                    priority_text = line_stripped.split(':', 1)[1].strip().lower()
                    if 'critical' in priority_text or '긴급' in priority_text:
                        requirements[-1]['priority'] = 'P0'
                    elif 'high' in priority_text or '높음' in priority_text:
                        requirements[-1]['priority'] = 'P1'
                    elif 'medium' in priority_text or '보통' in priority_text:
                        requirements[-1]['priority'] = 'P2'
                    elif 'low' in priority_text or '낮음' in priority_text:
                        requirements[-1]['priority'] = 'P3'
            
            # 서브 항목 (- xxx 형태)
            elif line_stripped.startswith('-') and requirements:
                subtask = line_stripped[1:].strip()
                requirements[-1]['subtasks'].append(subtask)
        
        # 마일스톤 파싱
        elif current_section == 'milestones':
            match = re.match(r'^(\d+)\.\s+Phase\s+(\d+)\s*\(([^)]+)\):\s*(.+)', line_stripped)
            if match:
                phase_num = match.group(2)
                duration = match.group(3)
                phase_desc = match.group(4)
                
                phase = {
                    'id': f'phase-{phase_num}',
                    'name': f'Phase {phase_num}: {phase_desc}',
                    'duration': duration,
                    'status': 'pending',
                    'tasks': []
                }
                result['phases'].append(phase)
    
    # 요구사항을 작업으로 변환
    task_id = 1
    for req in requirements:
        # 메인 태스크
        main_task = {
            'id': f'TASK-{task_id}',
            'req_id': req['id'],
            'title': req['title'],
            'type': req['type'],
            'priority': req['priority'],
            'status': 'pending',
            'subtasks': []
        }
        
        task_id += 1
        
        # 서브 태스크
        for subtask_title in req['subtasks']:
            subtask = {
                'id': f'TASK-{task_id}',
                'parent_id': main_task['id'],
                'title': subtask_title,
                'type': 'subtask',
                'priority': req['priority'],
                'status': 'pending'
            }
            main_task['subtasks'].append(subtask)
            task_id += 1
        
        result['tasks'].append(main_task)
    
    # 통계 생성
    result['statistics'] = {
        'total_requirements': len(requirements),
        'total_tasks': task_id - 1,
        'priority_distribution': {},
        'type_distribution': {}
    }
    
    # 우선순위별 카운트
    for task in result['tasks']:
        priority = task['priority']
        result['statistics']['priority_distribution'][priority] = \
            result['statistics']['priority_distribution'].get(priority, 0) + 1
        
        task_type = task['type']
        result['statistics']['type_distribution'][task_type] = \
            result['statistics']['type_distribution'].get(task_type, 0) + 1
    
    return result

def generate_taskmaster_format(parsed_data):
    """Taskmaster 형식으로 변환"""
    
    # Phase별로 작업 그룹화
    phases = []
    
    # 우선순위별로 Phase 생성
    priority_phases = {
        'P0': {
            'id': 'critical',
            'name': '[P0] Critical Priority Tasks',
            'priority': 'critical',
            'tasks': []
        },
        'P1': {
            'id': 'high',
            'name': '[P1] High Priority Tasks',
            'priority': 'high',
            'tasks': []
        },
        'P2': {
            'id': 'medium',
            'name': '[P2] Medium Priority Tasks',
            'priority': 'medium',
            'tasks': []
        },
        'P3': {
            'id': 'low',
            'name': '[P3] Low Priority Tasks',
            'priority': 'low',
            'tasks': []
        }
    }
    
    # 작업을 우선순위별로 분류
    for task in parsed_data['tasks']:
        priority = task['priority']
        phase_task = {
            'id': task['id'],
            'name': task['title'],
            'status': 'pending',
            'type': task['type'],
            'subtasks': len(task.get('subtasks', []))
        }
        priority_phases[priority]['tasks'].append(phase_task)
    
    # 비어있지 않은 Phase만 추가
    for phase in priority_phases.values():
        if phase['tasks']:
            phase['progress'] = 0
            phase['status'] = 'pending'
            phases.append(phase)
    
    return {
        'project': parsed_data['project'],
        'version': parsed_data['version'],
        'created': parsed_data['created'],
        'phases': phases,
        'statistics': parsed_data['statistics']
    }

def main():
    """메인 실행 함수"""
    import sys
    import io
    
    # UTF-8 인코딩 설정
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: python simple_prd_parser.py <prd_file>")
        sys.exit(1)
    
    prd_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'parsed_tasks.json'
    
    print(f"[Parsing PRD: {prd_file}]")
    
    try:
        # PRD 파싱
        parsed_data = parse_prd_file(prd_file)
        
        # Taskmaster 형식으로 변환
        taskmaster_data = generate_taskmaster_format(parsed_data)
        
        # 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(taskmaster_data, f, ensure_ascii=False, indent=2)
        
        # 결과 출력
        stats = parsed_data['statistics']
        print(f"\n[SUCCESS] Successfully parsed PRD")
        print(f"\n[Statistics]")
        print(f"  - Total Requirements: {stats['total_requirements']}")
        print(f"  - Total Tasks: {stats['total_tasks']}")
        print(f"\n[Priority Distribution]")
        for priority, count in stats['priority_distribution'].items():
            print(f"  - {priority}: {count} tasks")
        print(f"\n[Type Distribution]")
        for task_type, count in stats['type_distribution'].items():
            print(f"  - {task_type}: {count} tasks")
        print(f"\n[SUCCESS] Output saved to: {output_file}")
        
        # 생성된 Phase 요약
        print(f"\n[Generated Phases]")
        for phase in taskmaster_data['phases']:
            print(f"  - {phase['name']}: {len(phase['tasks'])} tasks")
    
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
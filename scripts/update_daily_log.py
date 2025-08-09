#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update DAILY_LOG.md with today's activities
Automatically track what was done each day

Usage:
    python update_daily_log.py "작업 내용" [--category "카테고리"]
    python update_daily_log.py --summary  # Generate summary from git commits
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import argparse
import subprocess
import re

DAILY_LOG = Path("DAILY_LOG.md")
WEEKDAYS_KR = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']

def get_today_section():
    """Get today's date section header"""
    now = datetime.now()
    weekday = WEEKDAYS_KR[now.weekday()]
    return f"## {now.strftime('%Y-%m-%d')} ({weekday})"

def add_log_entry(content: str, category: str = None):
    """Add a new log entry for today"""
    
    if not DAILY_LOG.exists():
        print("[ERROR] DAILY_LOG.md not found")
        return False
    
    log_content = DAILY_LOG.read_text(encoding='utf-8')
    today_section = get_today_section()
    
    # Check if today's section exists
    if today_section not in log_content:
        # Add new section for today
        new_section = f"""
{today_section}

### 🎯 오늘의 주요 작업

#### 1. {category or '작업 항목'}
- ✅ {content}

### 📂 변경된 파일
```
[자동 수집 예정]
```

### 💡 주요 결정 사항
- 

### 🔄 다음 작업 예정
- [ ] 

---
"""
        # Insert after the horizontal line at the top
        lines = log_content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:
                insert_pos = i + 1
                break
        
        lines.insert(insert_pos, new_section)
        log_content = '\n'.join(lines)
    else:
        # Add to existing section
        lines = log_content.split('\n')
        for i, line in enumerate(lines):
            if today_section in line:
                # Find the work items section
                for j in range(i, len(lines)):
                    if '#### ' in lines[j] or '### 🎯' in lines[j]:
                        # Insert after this line
                        entry = f"- ✅ {content}"
                        lines.insert(j + 1, entry)
                        break
                break
        log_content = '\n'.join(lines)
    
    # Update last modified time
    log_content = re.sub(
        r'> Last Updated: .*',
        f'> Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        log_content
    )
    
    # Write back
    DAILY_LOG.write_text(log_content, encoding='utf-8')
    print(f"[SUCCESS] Added log entry for {datetime.now().strftime('%Y-%m-%d')}")
    return True

def generate_summary_from_git():
    """Generate summary from today's git commits"""
    
    try:
        # Get today's commits
        today = datetime.now().strftime('%Y-%m-%d')
        result = subprocess.run(
            ['git', 'log', '--since', f'{today} 00:00:00', '--pretty=format:%s'],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            commits = result.stdout.strip().split('\n')
            print(f"[INFO] Found {len(commits)} commits today:")
            for commit in commits:
                print(f"  - {commit}")
            
            # Group commits by type
            docs_commits = [c for c in commits if 'docs' in c.lower()]
            feat_commits = [c for c in commits if 'feat' in c.lower()]
            fix_commits = [c for c in commits if 'fix' in c.lower()]
            
            summary = []
            if docs_commits:
                summary.append(f"Documentation updates ({len(docs_commits)} commits)")
            if feat_commits:
                summary.append(f"New features ({len(feat_commits)} commits)")
            if fix_commits:
                summary.append(f"Bug fixes ({len(fix_commits)} commits)")
            
            if summary:
                return ', '.join(summary)
        else:
            print("[INFO] No commits found today")
            
    except Exception as e:
        print(f"[WARNING] Could not get git commits: {str(e)}")
    
    return None

def get_changed_files():
    """Get list of files changed today"""
    
    try:
        # Get files changed today
        today = datetime.now().strftime('%Y-%m-%d')
        result = subprocess.run(
            ['git', 'log', '--since', f'{today} 00:00:00', '--name-only', '--pretty=format:'],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            files = [f for f in result.stdout.strip().split('\n') if f]
            unique_files = list(set(files))
            return unique_files[:10]  # Limit to 10 files
            
    except Exception:
        pass
    
    return []

def auto_update_log():
    """Automatically update log with today's activities"""
    
    # Get git summary
    git_summary = generate_summary_from_git()
    
    # Get changed files
    changed_files = get_changed_files()
    
    if git_summary or changed_files:
        if git_summary:
            add_log_entry(git_summary, "Git Activity")
        
        # Update changed files section if exists
        if changed_files and DAILY_LOG.exists():
            log_content = DAILY_LOG.read_text(encoding='utf-8')
            today_section = get_today_section()
            
            if today_section in log_content:
                # Replace the changed files section
                files_str = '\n'.join([f"- {f}" for f in changed_files])
                pattern = r'### 📂 변경된 파일\n```\n\[자동 수집 예정\]\n```'
                replacement = f'### 📂 변경된 파일\n```\n{files_str}\n```'
                log_content = re.sub(pattern, replacement, log_content)
                
                DAILY_LOG.write_text(log_content, encoding='utf-8')
                print(f"[INFO] Updated changed files list")
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Update daily project log',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_daily_log.py "Implemented file versioning system"
  python update_daily_log.py "Fixed encoding issues" --category "Bug Fix"
  python update_daily_log.py --summary  # Auto-generate from git
        """
    )
    
    parser.add_argument('content', nargs='?', help='Log entry content')
    parser.add_argument('--category', help='Category for the log entry')
    parser.add_argument('--summary', action='store_true', help='Generate summary from git commits')
    
    args = parser.parse_args()
    
    if args.summary:
        auto_update_log()
    elif args.content:
        add_log_entry(args.content, args.category)
    else:
        print("[ERROR] Provide content or use --summary flag")
        sys.exit(1)

if __name__ == "__main__":
    main()
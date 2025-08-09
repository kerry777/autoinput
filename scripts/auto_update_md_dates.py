#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pre-commit hook to automatically update modification dates for changed MD files
Only updates if content has actually changed

Usage:
    python auto_update_md_dates.py <file1.md> <file2.md> ...
"""

import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

def has_content_changed(filepath: str) -> bool:
    """Check if file content has actually changed using git diff"""
    
    try:
        # Check if file is staged
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', filepath],
            capture_output=True,
            text=True
        )
        
        if filepath in result.stdout:
            # Check if it's more than just formatting
            diff_result = subprocess.run(
                ['git', 'diff', '--cached', filepath],
                capture_output=True,
                text=True
            )
            
            # Simple heuristic: if diff has more than 5 lines, it's substantial
            diff_lines = diff_result.stdout.strip().split('\n')
            actual_changes = [l for l in diff_lines if l.startswith('+') or l.startswith('-')]
            
            # Filter out just date changes
            substantial_changes = [
                l for l in actual_changes 
                if not re.search(r'Last Modified|last updated|updated:', l, re.IGNORECASE)
            ]
            
            return len(substantial_changes) > 2
            
    except Exception:
        # If git commands fail, assume no change
        return False
    
    return False

def update_file_date(filepath: str) -> bool:
    """Update the modification date in filename if content changed"""
    
    filepath = Path(filepath)
    
    # Check naming pattern
    pattern = r'^(.+?)_(\d{8})_(\d{8})\.md$'
    match = re.match(pattern, filepath.name)
    
    if not match:
        # File doesn't follow convention, skip
        return True
    
    base_name = match.group(1)
    creation_date = match.group(2)
    old_mod_date = match.group(3)
    
    # Get today's date
    today = datetime.now().strftime('%Y%m%d')
    
    # Skip if already today's date
    if old_mod_date == today:
        return True
    
    # Check if content actually changed
    if not has_content_changed(str(filepath)):
        print(f"[SKIP] {filepath.name}: No substantial changes detected")
        return True
    
    # Create new filename
    new_filename = f"{base_name}_{creation_date}_{today}.md"
    new_filepath = filepath.parent / new_filename
    
    # Rename file
    try:
        # Use git mv to maintain history
        result = subprocess.run(
            ['git', 'mv', str(filepath), str(new_filepath)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[AUTO-UPDATE] {filepath.name} -> {new_filename}")
            
            # Stage the rename
            subprocess.run(['git', 'add', str(new_filepath)], capture_output=True)
            
            return True
        else:
            # Fallback to regular rename
            filepath.rename(new_filepath)
            print(f"[UPDATE] {filepath.name} -> {new_filename}")
            return True
            
    except Exception as e:
        print(f"[WARNING] Could not update {filepath}: {str(e)}")
        return True  # Don't block commit

def main():
    """Main function for pre-commit hook"""
    
    if len(sys.argv) < 2:
        sys.exit(0)
    
    for filepath in sys.argv[1:]:
        if filepath.endswith('.md'):
            update_file_date(filepath)
    
    # Always exit successfully to not block commits
    sys.exit(0)

if __name__ == "__main__":
    main()
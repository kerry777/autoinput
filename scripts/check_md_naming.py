#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pre-commit hook to validate Markdown file naming convention
Ensures all .md files follow the date versioning format

Usage:
    python check_md_naming.py <file1.md> <file2.md> ...
"""

import sys
import re
from pathlib import Path

# Directories exempt from date versioning
EXEMPT_DIRS = [
    '.github',
    'node_modules',
    '.git',
    'venv',
    'env',
    '__pycache__'
]

# Files exempt from date versioning
EXEMPT_FILES = [
    'LICENSE.md',
    'SECURITY.md'
]

def check_md_naming(filepath: str) -> bool:
    """Check if markdown file follows naming convention"""
    
    filepath = Path(filepath)
    
    # Check if file is in exempt directory
    for parent in filepath.parents:
        if parent.name in EXEMPT_DIRS:
            return True
    
    # Check if file is exempt
    if filepath.name in EXEMPT_FILES:
        return True
    
    # Check naming pattern
    pattern = r'^.+_\d{8}_\d{8}\.md$'
    
    if not re.match(pattern, filepath.name):
        return False
    
    # Validate date format
    filename = filepath.stem
    match = re.search(r'_(\d{8})_(\d{8})$', filename)
    
    if match:
        creation_date = match.group(1)
        mod_date = match.group(2)
        
        # Basic date validation (YYYYMMDD)
        try:
            from datetime import datetime
            datetime.strptime(creation_date, '%Y%m%d')
            datetime.strptime(mod_date, '%Y%m%d')
            
            # Check logical ordering
            if int(creation_date) > int(mod_date):
                print(f"[ERROR] {filepath}: Creation date cannot be after modification date")
                return False
                
        except ValueError:
            print(f"[ERROR] {filepath}: Invalid date format")
            return False
    
    return True

def main():
    """Main function for pre-commit hook"""
    
    if len(sys.argv) < 2:
        print("Usage: check_md_naming.py <file1.md> <file2.md> ...")
        sys.exit(1)
    
    failed_files = []
    
    for filepath in sys.argv[1:]:
        if filepath.endswith('.md'):
            if not check_md_naming(filepath):
                failed_files.append(filepath)
                print(f"[FAIL] {filepath}: Does not follow naming convention (filename_YYYYMMDD_YYYYMMDD.md)")
    
    if failed_files:
        print(f"\n[ERROR] {len(failed_files)} file(s) do not follow the naming convention:")
        for f in failed_files:
            print(f"  - {f}")
        print("\n[FIX] Use: python scripts/create_md_with_date.py or rename_docs_with_date.py")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
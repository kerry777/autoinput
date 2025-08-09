#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create new Markdown file with date versioning
Automatically adds creation and modification dates to filename

Usage:
    python create_md_with_date.py "filename" "Document Title" [directory]
    python create_md_with_date.py "deployment-guide" "Deployment Guide" docs
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import argparse

def create_md_with_date(filename: str, title: str = None, directory: str = "docs"):
    """Create a new markdown file with date versioning"""
    
    # Clean filename (remove .md if provided)
    if filename.endswith('.md'):
        filename = filename[:-3]
    
    # Remove any existing dates from filename
    import re
    filename = re.sub(r'_\d{8}_\d{8}$', '', filename)
    
    # Get current date
    today = datetime.now().strftime('%Y%m%d')
    
    # Create filename with dates
    dated_filename = f"{filename}_{today}_{today}.md"
    
    # Create full path
    base_dir = Path(directory)
    base_dir.mkdir(exist_ok=True)
    filepath = base_dir / dated_filename
    
    # Check if file already exists
    if filepath.exists():
        print(f"[ERROR] File already exists: {filepath}")
        return False
    
    # Create document content
    if not title:
        title = filename.replace('-', ' ').replace('_', ' ').title()
    
    content = f"""# {title}

## Overview

[Document overview goes here]

## Section 1

[Content for section 1]

## Section 2

[Content for section 2]

## Section 3

[Content for section 3]

---

**Created**: {datetime.now().strftime('%Y-%m-%d')}
**Last Modified**: {datetime.now().strftime('%Y-%m-%d')}
**Version**: 1.0.0
"""
    
    # Write file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[SUCCESS] Created new file: {filepath}")
        print(f"[INFO] Filename format: {dated_filename}")
        print(f"[INFO] Creation date: {today}")
        print(f"[INFO] Modification date: {today}")
        
        # Also update the project rules tracking
        update_tracking_log(dated_filename, directory)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to create file: {str(e)}")
        return False

def update_tracking_log(filename: str, directory: str):
    """Update the document tracking log"""
    
    log_file = Path("docs/DOCUMENT_TRACKING_LOG.md")
    
    # Create log entry
    today = datetime.now().strftime('%Y-%m-%d')
    log_entry = f"| {filename} | {directory}/ | {today} | {today} | Initial creation |\n"
    
    # Create or append to log file
    if not log_file.exists():
        header = f"""# Document Tracking Log

## Active Documents

| Filename | Directory | Created | Modified | Notes |
|----------|-----------|---------|----------|-------|
{log_entry}"""
        log_file.write_text(header, encoding='utf-8')
    else:
        content = log_file.read_text(encoding='utf-8')
        if filename not in content:
            # Add to the table
            lines = content.split('\n')
            # Find the table and add the new entry
            for i, line in enumerate(lines):
                if line.startswith('|----------|'):
                    lines.insert(i + 1, log_entry.strip())
                    break
            log_file.write_text('\n'.join(lines), encoding='utf-8')
    
    print(f"[INFO] Updated tracking log: {log_file}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Create new Markdown file with date versioning',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_md_with_date.py "api-guide"
  python create_md_with_date.py "api-guide" "API Guide"
  python create_md_with_date.py "api-guide" "API Guide" docs
  python create_md_with_date.py "readme" "Project README" .
        """
    )
    
    parser.add_argument('filename', help='Base filename (without dates or .md)')
    parser.add_argument('title', nargs='?', help='Document title (optional)')
    parser.add_argument('directory', nargs='?', default='docs', help='Target directory (default: docs)')
    
    args = parser.parse_args()
    
    # Create the file
    success = create_md_with_date(args.filename, args.title, args.directory)
    
    if success:
        print("\n[TIP] To update the modification date later, use:")
        print(f"  python scripts/update_md_date.py {args.directory}/{args.filename}_*.md")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
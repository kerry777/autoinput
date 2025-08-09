#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update modification date for existing Markdown files
Maintains creation date, updates modification date to today

Usage:
    python update_md_date.py <file_path>
    python update_md_date.py docs/deployment-guide_20250809_20250809.md
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
import shutil
import argparse

def update_md_date(filepath: str):
    """Update the modification date of a markdown file"""
    
    filepath = Path(filepath)
    
    # Check if file exists
    if not filepath.exists():
        print(f"[ERROR] File not found: {filepath}")
        return False
    
    # Check if it's a markdown file
    if not filepath.suffix == '.md':
        print(f"[ERROR] Not a markdown file: {filepath}")
        return False
    
    # Extract dates from filename
    filename = filepath.stem
    pattern = r'^(.+?)_(\d{8})_(\d{8})$'
    match = re.match(pattern, filename)
    
    if not match:
        print(f"[WARNING] File doesn't follow date naming convention: {filepath}")
        print("[INFO] Use rename_docs_with_date.py to add dates first")
        return False
    
    base_name = match.group(1)
    creation_date = match.group(2)
    old_mod_date = match.group(3)
    
    # Get today's date
    today = datetime.now().strftime('%Y%m%d')
    
    # Check if update is needed
    if old_mod_date == today:
        print(f"[INFO] File already has today's date: {filepath}")
        return True
    
    # Create new filename
    new_filename = f"{base_name}_{creation_date}_{today}.md"
    new_filepath = filepath.parent / new_filename
    
    # Check if new file already exists
    if new_filepath.exists() and new_filepath != filepath:
        print(f"[ERROR] Target file already exists: {new_filepath}")
        return False
    
    # Update file content metadata if present
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Update Last Modified date in content if it exists
        old_date_pattern = r'\*\*Last Modified\*\*: \d{4}-\d{2}-\d{2}'
        new_date_str = f"**Last Modified**: {datetime.now().strftime('%Y-%m-%d')}"
        
        if re.search(old_date_pattern, content):
            content = re.sub(old_date_pattern, new_date_str, content)
        else:
            # Add modification date if not present
            if '---' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.strip() == '---':
                        lines.insert(i, f"\n{new_date_str}")
                        break
                content = '\n'.join(lines)
        
        # Write updated content
        filepath.write_text(content, encoding='utf-8')
        
    except Exception as e:
        print(f"[WARNING] Could not update content metadata: {str(e)}")
    
    # Rename file
    try:
        shutil.move(str(filepath), str(new_filepath))
        print(f"[SUCCESS] Updated file date:")
        print(f"  From: {filepath.name}")
        print(f"  To:   {new_filepath.name}")
        print(f"[INFO] Creation date preserved: {creation_date}")
        print(f"[INFO] Modification date updated: {old_mod_date} -> {today}")
        
        # Update tracking log
        update_tracking_log(filepath.name, new_filepath.name)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to rename file: {str(e)}")
        return False

def update_tracking_log(old_name: str, new_name: str):
    """Update the document tracking log"""
    
    log_file = Path("docs/DOCUMENT_VERSION_CONTROL_20250809.md")
    
    if log_file.exists():
        try:
            content = log_file.read_text(encoding='utf-8')
            content = content.replace(old_name, new_name)
            
            # Add update entry
            today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_entry = f"\n- {today}: Updated {new_name}"
            
            # Find the update history section and add entry
            if "## Update History" in content:
                content += update_entry
            else:
                content += f"\n\n## Update History\n{update_entry}"
            
            log_file.write_text(content, encoding='utf-8')
            print(f"[INFO] Updated version control log")
            
        except Exception as e:
            print(f"[WARNING] Could not update tracking log: {str(e)}")

def batch_update(pattern: str):
    """Update multiple files matching a pattern"""
    
    from glob import glob
    files = glob(pattern)
    
    if not files:
        print(f"[WARNING] No files found matching: {pattern}")
        return
    
    print(f"[INFO] Found {len(files)} files to update")
    
    success_count = 0
    for filepath in files:
        if update_md_date(filepath):
            success_count += 1
    
    print(f"\n[SUMMARY] Updated {success_count}/{len(files)} files")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Update modification date for Markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_md_date.py docs/api-guide_20250809_20250809.md
  python update_md_date.py "docs/*_20250809_20250809.md" --batch
  python update_md_date.py --help
        """
    )
    
    parser.add_argument('filepath', help='Path to markdown file or pattern (with --batch)')
    parser.add_argument('--batch', action='store_true', help='Update multiple files matching pattern')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without doing it')
    
    args = parser.parse_args()
    
    if args.batch:
        batch_update(args.filepath)
    else:
        success = update_md_date(args.filepath)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
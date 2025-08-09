# Claude Code Configuration - AutoInput Project

## File Naming Rules

### MANDATORY: Markdown File Date Versioning

All Markdown (.md) files created in this project MUST follow the date versioning format:

```
filename_YYYYMMDD_YYYYMMDD.md
```

- First date: Creation date (never changes)
- Second date: Last modification date (updates when content changes)

### Implementation

When creating new .md files:
1. Always use the date format
2. Use helper script: `python scripts/create_md_with_date.py "filename" "Title"`
3. Both dates should be today's date for new files

When modifying .md files:
1. Update the second date if making substantial changes
2. Use helper script: `python scripts/update_md_date.py filepath`
3. Keep creation date unchanged

### Examples

✅ Correct:
- `deployment-guide_20250809_20250809.md` (new file)
- `deployment-guide_20250809_20250815.md` (modified on Aug 15)

❌ Incorrect:
- `deployment-guide.md` (missing dates)
- `deployment-guide_2025-08-09.md` (wrong format)

### Enforcement

- Pre-commit hooks validate naming convention
- CI/CD pipeline checks all .md files
- Helper scripts ensure compliance

### Exceptions

These directories/files are exempt:
- `.github/` directory
- `node_modules/`
- `LICENSE.md`
- `SECURITY.md`

---

## Other Project Standards

### Git Commits
Include date when referencing dated files:
```
docs: Update deployment-architecture (20250815)
```

### Python Scripts
All scripts in `/scripts/` should include:
- UTF-8 encoding declaration
- Docstrings with usage examples
- Error handling with clear messages

### Documentation
- Use clear section headers
- Include creation/modification dates at bottom
- Add version numbers for major documents

---

**This configuration is loaded by Claude Code automatically**
**Last Updated**: 2025-08-09
# 📋 AutoInput Project Rules and Standards

## 📅 File Naming Convention

### Markdown Documentation Files (.md)

All markdown files MUST follow the date versioning format:

```
filename_YYYYMMDD_YYYYMMDD.md
```

- **First date (YYYYMMDD)**: Creation date
- **Second date (YYYYMMDD)**: Last modification date

#### Examples
- `deployment-architecture_20250809_20250809.md` (newly created)
- `deployment-architecture_20250809_20250815.md` (modified on Aug 15)

#### Exceptions
These files are exempt from date versioning:
- `.github/` directory files (templates)
- `node_modules/` (if any)
- Third-party documentation

### Implementation Rules

1. **New File Creation**
   - Always add dates when creating new .md files
   - Use current date for both creation and modification dates
   - Format: `filename_YYYYMMDD_YYYYMMDD.md`

2. **File Modification**
   - Update the second date when making substantial changes
   - Keep the first date unchanged (creation date)
   - Minor fixes (typos, formatting) don't require date update

3. **Automated Enforcement**
   - Use `scripts/add_date_to_new_md.py` for new files
   - Use `scripts/update_md_date.py` for modifications
   - Pre-commit hooks will validate naming convention

## 🔧 Helper Scripts

### Create New MD File with Date
```bash
python scripts/create_md_with_date.py "filename" "Title"
# Creates: filename_YYYYMMDD_YYYYMMDD.md
```

### Update MD File Date
```bash
python scripts/update_md_date.py docs/filename_20250809_20250809.md
# Renames to: filename_20250809_YYYYMMDD.md (today's date)
```

## 📝 Git Commit Message Convention

When working with dated files:
```
docs: Update deployment-architecture (20250815)
feat: Add new monitoring guide (20250815)
fix: Correct process flow in workflow doc (20250815)
```

## 🚨 Validation Rules

### Pre-commit Check
All .md files in these directories MUST have date format:
- `/docs/`
- `/` (root level documentation)

### CI/CD Pipeline
GitHub Actions will validate:
1. File naming convention compliance
2. Date format correctness (YYYYMMDD)
3. Logical date ordering (creation <= modification)

## 📊 Version Control Strategy

### Date-based Versioning
- **Daily Changes**: Update modification date only
- **Major Revisions**: Consider archiving old version
- **Historical Tracking**: Use Git for detailed history

### Git Integration
```bash
# View file history
git log --follow docs/filename_*

# Compare versions
git diff HEAD~1 docs/filename_*
```

## 🎯 Benefits of This System

1. **Instant Visibility**: Know when documents were created/updated at a glance
2. **No Conflicts**: Date-based naming prevents overwrites
3. **Easy Sorting**: Files naturally sort by date in file explorers
4. **Audit Trail**: Clear documentation lifecycle tracking
5. **Consistency**: Uniform approach across entire project

## 🔄 Migration for Existing Files

For files without dates, use the batch rename script:
```bash
python scripts/rename_docs_with_date.py
```

## 📋 Compliance Checklist

- [ ] All new .md files include creation and modification dates
- [ ] Scripts are used for file creation/modification
- [ ] Team members are aware of naming convention
- [ ] Pre-commit hooks are enabled
- [ ] CI/CD validation is active

---

**Last Updated**: 2025-08-09
**Rule Version**: 1.0.0
**Enforcement**: MANDATORY for all project contributors
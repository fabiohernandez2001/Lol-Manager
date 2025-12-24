---
description: Create a Pull Request from current branch to main with comprehensive summary
---

You are tasked with creating a Pull Request from the current branch to the main branch.

Follow these steps carefully:

1. **Gather Information** - Run these commands in parallel:
   - `git status` - Check current state
   - `git log --oneline main..HEAD` - Show commits to be included
   - `git diff main...HEAD --stat` - Show file changes summary
   - `git rev-parse --abbrev-ref --symbolic-full-name @{u}` - Check remote tracking

2. **Analyze Changes**:
   - Review ALL commits that will be included (not just the latest)
   - Understand what features/fixes are being added
   - Identify any breaking changes
   - Note database migrations or dependency changes

3. **Push to Remote** (if needed):
   - Check if branch needs to be pushed
   - Use `git push -u origin <branch>` if needed

4. **Create PR**:
   Use the following format:

   ```bash
   gh pr create --base main --head <current-branch> \
     --title "<Concise PR Title>" \
     --body "$(cat <<'EOF'
   ## Summary

   <2-3 bullet points describing what this PR does>

   ## Changes Overview

   <Organized breakdown of changes by category>

   ## Test Plan

   - [x] <What was tested>
   - [ ] <What should be tested manually>

   ## Database Impact

   <Any migrations, schema changes, or data modifications>

   ## Breaking Changes

   <List any breaking changes, or state "None">

   ## Checklist

   - [x] Code follows project guidelines
   - [x] Tests pass
   - [x] Documentation updated
   - [x] No breaking changes (or documented)

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   EOF
   )"
   ```

5. **Return PR URL**:
   - Show the URL of the created PR
   - Confirm successful creation

## Important Guidelines:

- **DO NOT** use TodoWrite or Task tools
- **DO** analyze ALL commits since diverging from main
- **DO** include comprehensive test plan
- **DO** note any database/architecture impacts
- **DO** list breaking changes explicitly
- **DO** return the PR URL when done

## PR Title Format:

Use descriptive titles that summarize the changes:
- "Phase X.Y: Feature Description"
- "Fix: Brief description of bug fix"
- "Feature: New capability added"
- "Refactor: What was refactored"

## PR Body Sections:

Always include:
1. **Summary** - High-level overview
2. **Changes Overview** - Detailed breakdown
3. **Test Plan** - What was tested and what needs testing
4. **Database Impact** - Migrations, schema changes
5. **Breaking Changes** - Explicit list or "None"
6. **Checklist** - Standard quality checks

Make the PR comprehensive but scannable with good formatting.

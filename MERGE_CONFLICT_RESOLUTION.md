# Git Merge Conflict Resolution for Auth Template Fix

## Issue
Git push rejected with error: "Updates were rejected because the remote contains work that you do not have locally"

## Solution Steps

### 1. Pull Remote Changes First
```bash
git pull origin main
```

### 2. Resolve Any Merge Conflicts (if they occur)
If there are conflicts, git will show which files need resolution. Edit the conflicted files to resolve the conflicts, then:
```bash
git add <conflicted-files>
git commit -m "Resolve merge conflicts"
```

### 3. Stage Auth Template Files
```bash
git add auth/templates/
git add auth/__init__.py
```

### 4. Commit the Auth Fix
```bash
git commit -m "🚨 DEPLOYMENT FIX: Add missing auth templates to repository

- Add complete auth/templates/ directory to fix Render TemplateNotFound errors
- Include login.html with fixed OIDC route references
- Include register.html, profile.html, and base.html
- Enhanced auth blueprint configuration for proper template resolution
- Resolves production deployment failure on Render"
```

### 5. Push to GitHub
```bash
git push origin main
```

## Alternative: Force Push (Use with Caution)
If you're confident your local changes should override remote changes:
```bash
git push origin main --force
```

## Expected Result
After successful push:
- auth/templates/ directory will be in GitHub repository
- Render can access template files during deployment
- Authentication routes will work in production
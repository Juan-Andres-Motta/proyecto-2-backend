# SonarCloud Setup Guide

Complete guide to set up SonarCloud for code quality and coverage analysis on your repositories.

---

## 🎯 Overview

**SonarCloud Projects**:
- ✅ **Backend Repository** (`proyecto-2-backend`) - One SonarCloud project for entire backend
- ✅ **Frontend Repository** (`proyecto-2-frontend`) - One SonarCloud project for frontend

**What You Get**:
- Static code analysis (bugs, code smells, vulnerabilities)
- Code coverage tracking
- Technical debt measurement
- PR quality checks
- Historical trend analysis

---

## 📋 Step 1: Create SonarCloud Account

### 1.1 Sign Up

1. Go to **[sonarcloud.io](https://sonarcloud.io)**
2. Click **"Log in"** or **"Start now"**
3. Select **"Sign up with GitHub"**
4. Authorize SonarCloud to access your GitHub repositories

### 1.2 Create Organization

1. After login, click **"+"** → **"Create new organization"**
2. Select your GitHub user or organization
3. Enter a unique **organization key** (e.g., `your-username` or `medisupply-team`)
4. Choose plan:
   - **Free** - for public repositories
   - **Paid** (~€10/month) - for private repositories

**📝 Save your organization key!** You'll need it later.

Example: `medisupply-team`

---

## 📋 Step 2: Import Backend Repository

### 2.1 Create Backend Project

1. In SonarCloud, click **"+"** → **"Analyze new project"**
2. Find and select **`proyecto-2-backend`**
3. Click **"Set Up"**
4. Choose **"With GitHub Actions"** (recommended)
5. SonarCloud will show:
   - **Project Key**: e.g., `your-org_proyecto-2-backend`
   - **Token**: A secret token (starts with `sqp_`)

### 2.2 Save Backend Token

**Copy and save** the `SONAR_TOKEN` - you'll add it to GitHub secrets.

---

## 📋 Step 3: Configure Backend GitHub Secrets

1. Go to your **`proyecto-2-backend`** repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Add these secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `SONAR_TOKEN` | Token from SonarCloud | `sqp_abc123...` |
| `SONAR_ORGANIZATION` | Your organization key | `medisupply-team` |

---

## 📋 Step 4: Verify Backend Configuration

The backend already has the necessary files:

✅ **`sonar-project.properties`** - Configuration file (at repo root)
✅ **`.github/workflows/sonarcloud.yml`** - GitHub Actions workflow

### 4.1 Update Project Key (if needed)

If SonarCloud assigned a different project key than `proyecto-2-backend`:

1. Open `sonar-project.properties`
2. Change line:
   ```properties
   sonar.projectKey=your-actual-project-key-from-sonarcloud
   ```
3. Commit and push

---

## 📋 Step 5: Test Backend Analysis

### 5.1 Trigger Workflow

Push to `main` or `develop` branch:

```bash
git add .
git commit -m "chore: configure SonarCloud"
git push origin main
```

### 5.2 Check GitHub Actions

1. Go to **Actions** tab in GitHub
2. Find **"SonarCloud Analysis"** workflow
3. Wait for it to complete (takes 3-5 minutes)

### 5.3 View Results in SonarCloud

1. Go to [sonarcloud.io](https://sonarcloud.io)
2. Click your organization
3. Open **`proyecto-2-backend`** project
4. You'll see:
   - Code coverage %
   - Bugs, vulnerabilities, code smells
   - Quality gate status

---

## 📋 Step 6: Import Frontend Repository

### 6.1 Create Frontend Project

1. In SonarCloud, click **"+"** → **"Analyze new project"**
2. Select **`proyecto-2-frontend`**
3. Click **"Set Up"**
4. Choose **"With GitHub Actions"**
5. Copy the **`SONAR_TOKEN`** (or reuse the same token from backend)

### 6.2 Add Frontend GitHub Secrets

Go to **`proyecto-2-frontend`** repository on GitHub:

1. **Settings** → **Secrets and variables** → **Actions**
2. Add:
   - `SONAR_TOKEN`
   - `SONAR_ORGANIZATION`

---

## 📋 Step 7: Configure Frontend Repository

### 7.1 Create `sonar-project.properties`

At the **root** of your frontend repo:

```properties
# SonarCloud Configuration - Frontend Repository

sonar.projectKey=proyecto-2-frontend
sonar.projectName=MediSupply Frontend
sonar.projectVersion=1.0

# Source directories (adjust based on your framework)
sonar.sources=src,app,pages,components

# Exclusions
sonar.exclusions=**/node_modules/**,**/*.test.ts,**/*.test.tsx,**/*.test.js,**/*.test.jsx,**/__tests__/**,**/coverage/**,**/dist/**,**/build/**,**/.next/**,**/public/**,**/*.config.js,**/*.config.ts

# Test files
sonar.tests=src,app,pages,components
sonar.test.inclusions=**/*.test.ts,**/*.test.tsx,**/*.test.js,**/*.test.jsx,**/__tests__/**

# Coverage (LCOV format from Jest/Vitest)
sonar.javascript.lcov.reportPaths=coverage/lcov.info
sonar.typescript.lcov.reportPaths=coverage/lcov.info

# Encoding
sonar.sourceEncoding=UTF-8

# SCM
sonar.scm.provider=git

# Quality Gate
sonar.qualitygate.wait=true
```

**Note**: Adjust `sonar.sources` based on your project structure (Next.js, React, Vue, etc.)

### 7.2 Create GitHub Actions Workflow

Create **`.github/workflows/sonarcloud.yml`** in frontend repo:

```yaml
name: SonarCloud Analysis

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarcloud:
    name: SonarCloud
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for SonarCloud

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'  # Adjust to your version
          cache: 'npm'  # Or 'yarn' / 'pnpm'

      - name: Install dependencies
        run: npm ci  # Or: yarn install --frozen-lockfile

      - name: Run tests with coverage
        run: npm run test:coverage  # Adjust to your test script
        continue-on-error: true

      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@master
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          args: >
            -Dsonar.organization=${{ secrets.SONAR_ORGANIZATION }}

      - name: Quality Gate Check
        uses: SonarSource/sonarqube-quality-gate-action@master
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        continue-on-error: true
```

### 7.3 Update `package.json`

Add coverage script:

**For Jest**:
```json
{
  "scripts": {
    "test": "jest",
    "test:coverage": "jest --coverage"
  }
}
```

**For Vitest**:
```json
{
  "scripts": {
    "test": "vitest run",
    "test:coverage": "vitest run --coverage"
  }
}
```

### 7.4 Configure Coverage Output

Ensure your test runner generates `lcov.info`:

**Jest** (`jest.config.js`):
```javascript
module.exports = {
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov'],
};
```

**Vitest** (`vitest.config.ts`):
```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8', // or 'istanbul'
      reporter: ['text', 'lcov'],
    },
  },
});
```

---

## 📋 Step 8: Test Frontend Analysis

1. Commit and push the new files:
   ```bash
   git add sonar-project.properties .github/workflows/sonarcloud.yml
   git commit -m "chore: add SonarCloud configuration"
   git push origin main
   ```

2. Check **Actions** tab on GitHub

3. View results in [sonarcloud.io](https://sonarcloud.io)

---

## 🎯 Understanding Results

### Dashboard Metrics

| Metric | Description | Good Target |
|--------|-------------|-------------|
| **Reliability** | Bugs in code | A rating (0 bugs) |
| **Security** | Vulnerabilities | A rating (0 vulns) |
| **Maintainability** | Code smells | A rating |
| **Coverage** | Test coverage % | ≥ 70% |
| **Duplications** | Duplicate code | < 3% |

### Quality Gate

Default conditions:
- ✅ Coverage on new code ≥ 80%
- ✅ Duplications ≤ 3%
- ✅ Maintainability rating = A
- ✅ Reliability rating = A
- ✅ Security rating = A

**Status**:
- 🟢 **Passed** - All conditions met, can merge
- 🔴 **Failed** - Fix issues before merging

---

## 🔧 Customizing Quality Gates

### Create Custom Quality Gate

1. Go to SonarCloud → **Quality Gates**
2. Click **"Create"**
3. Add conditions:
   - Coverage on new code ≥ 70%
   - Maintainability rating = A
   - Security rating = A
   - Duplicated lines ≤ 3%
4. Click **"Set as Default"** or assign to specific projects

### Recommended for Python Backend

```
Coverage on New Code: ≥ 70%
Reliability Rating: A
Security Rating: A
Maintainability Rating: A
```

### Recommended for JavaScript Frontend

```
Coverage on New Code: ≥ 60%
Reliability Rating: A
Security Rating: A
Maintainability Rating: A
```

---

## 🚀 Pull Request Integration

Once configured, SonarCloud will:

1. ✅ Add a **comment to PRs** with analysis summary
2. ✅ Show **inline issues** in code diff
3. ✅ **Block merge** if quality gate fails (optional)
4. ✅ Track only **new code issues** (not existing tech debt)

### Enable PR Decoration

1. In SonarCloud → Your project
2. **Administration** → **General Settings** → **Pull Requests**
3. Ensure **GitHub integration** is enabled
4. Enable **"Decorate Pull Requests"**

---

## ❓ Troubleshooting

### Problem: "No coverage reports found"

**Solution**:
1. Verify test coverage is generated:
   ```bash
   # Backend
   poetry run pytest --cov=src --cov-report=xml

   # Frontend
   npm run test:coverage
   ```
2. Check that `coverage.xml` (backend) or `coverage/lcov.info` (frontend) exists
3. Verify paths in `sonar-project.properties`

### Problem: "SONAR_TOKEN authentication failed"

**Solution**:
1. Regenerate token: SonarCloud → **My Account** → **Security** → **Generate Token**
2. Update GitHub secret: **Settings** → **Secrets** → Update `SONAR_TOKEN`

### Problem: "Project key already exists"

**Solution**:
1. Use the exact project key shown in SonarCloud
2. Or delete the old project and re-import

### Problem: "Quality Gate failed"

**Solution**:
1. Check SonarCloud dashboard for specific issues
2. Fix bugs, vulnerabilities, or code smells
3. Add tests to increase coverage
4. Or adjust quality gate thresholds (if appropriate)

### Problem: Frontend coverage not showing

**Solution**:
1. Check coverage format is `lcov`:
   ```bash
   cat coverage/lcov.info  # Should show coverage data
   ```
2. Verify `sonar.javascript.lcov.reportPaths` in config
3. Ensure tests run BEFORE SonarCloud scan in workflow

---

## 📊 Viewing Results by Microservice

While the backend is one SonarCloud project, you can filter results:

1. Go to project dashboard
2. Click **"Code"** tab
3. Browse folders:
   - `bff/`
   - `catalog/src/`
   - `order/src/`
   - `seller/src/`
   - etc.

Or use **Measures** tab → Filter by directory.

---

## 📚 Useful Commands

### Backend (Python)

```bash
# Run tests with coverage for one service
cd catalog
poetry run pytest --cov=src --cov-report=xml --cov-report=term

# Run all tests from root (example script)
for dir in bff catalog inventory order seller; do
  cd $dir && poetry run pytest --cov && cd ..
done
```

### Frontend (JavaScript)

```bash
# Run tests with coverage
npm run test:coverage

# View coverage report
open coverage/lcov-report/index.html
```

---

## 🎓 Next Steps

1. ✅ Set up SonarCloud account
2. ✅ Import backend repository
3. ✅ Import frontend repository
4. ✅ Configure GitHub secrets
5. ✅ Run first analysis
6. ✅ Review and fix issues
7. ✅ Configure quality gates
8. ✅ Enable PR checks
9. ✅ Share with team

---

## 📖 Resources

- **SonarCloud**: [sonarcloud.io](https://sonarcloud.io)
- **Documentation**: [docs.sonarcloud.io](https://docs.sonarcloud.io)
- **Python Guide**: [docs.sonarcloud.io/enriching/languages/python](https://docs.sonarcloud.io/enriching/languages/python/)
- **JavaScript Guide**: [docs.sonarcloud.io/enriching/languages/javascript](https://docs.sonarcloud.io/enriching/languages/javascript/)

---

**Version**: 1.0
**Updated**: 2025-10-19

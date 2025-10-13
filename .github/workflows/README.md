# GitHub Actions Test Workflow

## Overview

This workflow automatically detects changed microservices in pull requests and runs unit tests with coverage analysis. It requires a minimum of **70% code coverage** to pass.

## Workflow Features

### 1. **Change Detection**
- Uses `dorny/paths-filter@v3` to detect which microservice directories have changed
- Only runs tests for affected services (efficient CI/CD)
- Supports 7 microservices: bff, catalog, client, delivery, inventory, order, seller

### 2. **Test Execution**
Each affected service runs:
```bash
poetry run pytest --cov=<module> --cov-report=xml --cov-report=term --cov-fail-under=70
```

### 3. **Coverage Requirements**
- **Minimum**: 70% code coverage
- **Green**: ≥70% (✅)
- **Orange**: ≥60% (⚠️)
- **Red**: <60% (❌)

### 4. **Coverage Comments**
- Uses `py-cov-action/python-coverage-comment-action@v3`
- Posts automated coverage report as PR comment
- Shows:
  - Overall coverage percentage
  - Coverage change from baseline
  - File-by-file breakdown
  - Only visible on pull requests

## Workflow Structure

```yaml
jobs:
  detect-changes:
    # Detects which services changed

  test-<service>:
    # Runs for each changed service
    steps:
      - Checkout code
      - Setup Python 3.13
      - Install Poetry
      - Install dependencies
      - Run tests with coverage (fails if <70%)
      - Generate coverage comment (PR only)
```

## Local Testing

### BFF Service
```bash
cd bff
poetry run pytest --cov=web --cov=common --cov=config --cov-report=xml --cov-report=term --cov-fail-under=70
```

### Catalog Service
```bash
cd catalog
poetry run pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=70
```

### Using Docker (recommended)
```bash
# BFF
cd bff
docker build -f Dockerfile.test -t bff-test .
docker run --rm bff-test poetry run pytest --cov=web --cov=common --cov=config --cov-report=xml --cov-report=term --cov-fail-under=70

# Catalog
cd catalog
docker build -f Dockerfile.test -t catalog-test .
docker run --rm catalog-test poetry run pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=70
```

## Current Test Coverage

| Service | Tests | Coverage | Status |
|---------|-------|----------|--------|
| BFF | 40/40 | 89.62% | ✅ |
| Catalog | 49/49 | 93.08% | ✅ |

## Configuration Files

### BFF (`bff/pyproject.toml`)
```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["web", "common", "config"]
omit = ["*/tests/*", "*/__pycache__/*", "*/.venv/*"]

[tool.coverage.report]
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.coverage.xml]
output = "coverage.xml"
```

### Catalog (`catalog/pyproject.toml`)
```toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["."]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*", "*/alembic/*", "*/.venv/*"]

[tool.coverage.report]
precision = 2
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]

[tool.coverage.xml]
output = "coverage.xml"
```

## How It Works in PRs

1. **Developer pushes changes** to a branch affecting `bff/` or `catalog/`
2. **GitHub Actions detects changes** using path filters
3. **Tests run automatically** with coverage analysis
4. **If coverage < 70%**: Build fails ❌
5. **If coverage ≥ 70%**: Build passes ✅
6. **Coverage comment posted** to PR with detailed report

## Example Coverage Comment

```markdown
## Coverage Report - BFF Service

**Overall Coverage:** 89.62% 🟢
**Coverage Change:** +2.50%

### Coverage by File
| File | Coverage |
|------|----------|
| common/health_service.py | 100.00% |
| web/schemas/catalog_schemas.py | 100.00% |
| web/controllers/products_controller.py | 78.21% |
| ... | ... |

**Minimum Required:** 70%
```

## Troubleshooting

### Tests fail locally but pass in CI
- Ensure you're using Python 3.13
- Run `poetry install` to sync dependencies
- Check that pytest-cov is installed: `poetry show pytest-cov`

### Coverage comment not appearing
- Only appears on pull requests (not direct pushes)
- Requires `pull-requests: write` permission
- Check GitHub Actions logs for errors

### Coverage calculation differs
- Ensure `coverage.xml` is generated
- Check coverage source paths in `pyproject.toml`
- Verify all modules are included in `--cov` flags

## Dependencies

- Python 3.13
- Poetry (latest)
- pytest 8.4+
- pytest-cov 6.0+
- pytest-asyncio 0.25+

## Maintenance

To add a new microservice:
1. Add path filter in `detect-changes` job
2. Copy one of the `test-<service>` jobs
3. Update service name and working directory
4. Adjust `--cov` modules as needed

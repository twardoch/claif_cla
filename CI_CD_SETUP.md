# CI/CD Setup for claif_cla

This document describes the complete CI/CD infrastructure implemented for the claif_cla project.

## Overview

The project now includes a comprehensive CI/CD pipeline with:
- ✅ Git-tag-based semversioning
- ✅ Automated testing across multiple platforms
- ✅ Code quality checks
- ✅ Multiplatform binary compilation
- ✅ Docker containerization
- ✅ Automated PyPI releases

## GitHub Actions Workflow

Due to GitHub App permission limitations, the workflow file is provided as a template. To activate the full CI/CD pipeline:

1. **Rename the template file:**
   ```bash
   mv .github/workflows/ci.yml.template .github/workflows/ci.yml
   ```

2. **Commit and push the workflow:**
   ```bash
   git add .github/workflows/ci.yml
   git commit -m "feat: add comprehensive CI/CD pipeline"
   git push
   ```

## Workflow Features

### 1. Code Quality Checks
- **Ruff** formatting and linting
- **MyPy** type checking
- **Bandit** security scanning
- Runs on every push and pull request

### 2. Multi-Platform Testing
- **Operating Systems**: Linux, Windows, macOS
- **Python Versions**: 3.10, 3.11, 3.12
- **Coverage reporting** with Codecov integration
- **Parallel test execution** for faster feedback

### 3. Package Building
- **Wheel and source distributions**
- **Installation verification**
- **Version validation**

### 4. Binary Compilation
Creates standalone executables for:
- Linux x86_64
- Windows x86_64
- macOS x86_64
- macOS ARM64

### 5. Docker Support
- **Multi-stage builds** (development, test, production)
- **Automated testing** in containerized environment
- **Image artifacts** for deployment

### 6. Automated Releases
- **TestPyPI** deployment for validation
- **PyPI** publishing on version tags
- **GitHub Releases** with compiled binaries
- **Artifact management** and cleanup

## Local Development Scripts

### Build Script (`scripts/build.sh`)
```bash
./scripts/build.sh                 # Full build pipeline
./scripts/build.sh --skip-tests    # Skip test execution
./scripts/build.sh --skip-quality  # Skip quality checks
./scripts/build.sh --skip-verify   # Skip package verification
```

### Test Script (`scripts/test.sh`)
```bash
./scripts/test.sh                  # Run all tests
./scripts/test.sh --unit           # Unit tests only
./scripts/test.sh --integration    # Integration tests only
./scripts/test.sh --coverage       # With coverage report
./scripts/test.sh --parallel       # Parallel execution
./scripts/test.sh --watch          # Watch mode for development
```

### Release Script (`scripts/release.sh`)
```bash
./scripts/release.sh suggest       # Version suggestions
./scripts/release.sh check         # Pre-release validation
./scripts/release.sh release 1.0.31 # Create new release
./scripts/release.sh tags          # List recent tags
```

## Makefile Commands

### Quick Commands
```bash
make install        # Setup development environment
make test          # Run tests
make build         # Build package
make release VERSION=1.0.31  # Create release
```

### Development Workflow
```bash
make dev-setup     # Complete dev setup with pre-commit
make test-watch    # Watch mode for TDD
make quality       # Run all quality checks
make fix           # Auto-fix code issues
make clean         # Clean build artifacts
```

## Version Management

### Current System
- **Git-tag-based versioning** using hatch-vcs
- **Semantic versioning** (MAJOR.MINOR.PATCH)
- **Development versions** include commit hash
- **Release versions** match git tags

### Creating Releases
```bash
# Check current version
make version

# Get suggestions for next version
make suggest-version

# Create release (triggers CI/CD)
make release VERSION=1.0.31
```

## CI/CD Pipeline Flow

### On Push to Main
1. **Code Quality** checks (Ruff, MyPy, Bandit)
2. **Multi-platform testing** (Linux, Windows, macOS)
3. **Package building** and verification
4. **Binary compilation** for all platforms
5. **Docker image** building and testing
6. **Artifact storage** for later use

### On Version Tag (e.g., `v1.0.31`)
1. All the above steps, plus:
2. **TestPyPI deployment** for validation
3. **PyPI publishing** of the package
4. **GitHub Release** creation with:
   - Python packages (wheel, source)
   - Compiled binaries for all platforms
   - Docker image
   - Automated release notes

## Artifacts Generated

### Python Packages
- `claif_cla-X.Y.Z-py3-none-any.whl`
- `claif_cla-X.Y.Z.tar.gz`

### Compiled Binaries
- `claif-cla-linux-x86_64`
- `claif-cla-windows-x86_64.exe`
- `claif-cla-macos-x86_64`
- `claif-cla-macos-arm64`

### Docker Images
- `claif_cla:latest` (production)
- `claif_cla:test` (with tests)

## Security Features

### Pre-commit Hooks
- **Secret detection** with detect-secrets
- **Security scanning** with Bandit
- **Dependency vulnerability** checks
- **Code quality** enforcement

### CI/CD Security
- **Secrets management** for PyPI tokens
- **Signed releases** with provenance
- **Vulnerability scanning** in Docker images
- **Artifact integrity** verification

## Setup Instructions

### 1. Enable GitHub Actions
```bash
# Activate the workflow
mv .github/workflows/ci.yml.template .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "feat: enable CI/CD pipeline"
git push
```

### 2. Configure PyPI Secrets
In your GitHub repository settings, add:
- `PYPI_TOKEN` - PyPI API token
- `TEST_PYPI_TOKEN` - TestPyPI API token

### 3. Set Up Development Environment
```bash
make dev-setup
```

### 4. Create Your First Release
```bash
make release VERSION=1.0.31
```

## Monitoring and Maintenance

### CI/CD Status
- Monitor at: https://github.com/twardoch/claif_cla/actions
- **Green builds** indicate healthy code
- **Failed builds** block releases automatically

### Release Process
1. **Automated testing** prevents broken releases
2. **TestPyPI validation** catches deployment issues
3. **Binary compilation** ensures cross-platform compatibility
4. **Artifact generation** provides multiple distribution formats

### Maintenance Tasks
- **Pre-commit hooks** keep code quality high
- **Dependency updates** via Dependabot
- **Security scanning** identifies vulnerabilities
- **Artifact cleanup** manages storage costs

## Troubleshooting

### Common Issues

1. **Build failures**: Check test results and fix issues
2. **Release failures**: Verify PyPI tokens and permissions
3. **Binary issues**: Check PyInstaller compatibility
4. **Docker problems**: Validate Dockerfile syntax

### Debug Commands
```bash
# Local debugging
make test-coverage    # Detailed test reports
make build --skip-tests  # Build without tests
./scripts/build.sh --help  # Script options

# CI debugging
# Check GitHub Actions logs
# Review artifact contents
# Validate workflow syntax
```

## Benefits

### For Developers
- **Consistent environment** across all platforms
- **Automated quality checks** prevent issues
- **Fast feedback** from parallel testing
- **Easy release process** with one command

### For Users
- **Multiple installation options** (pip, binary, Docker)
- **Cross-platform compatibility** guaranteed
- **Reliable releases** with automated testing
- **Easy access** to latest versions

### For Maintainers
- **Automated workflows** reduce manual effort
- **Quality gates** maintain code standards
- **Comprehensive testing** catches regressions
- **Artifact management** simplifies distribution

This CI/CD setup provides a production-ready foundation for the claif_cla project with modern DevOps practices and comprehensive automation.
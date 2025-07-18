#!/bin/bash
# this_file: scripts/build.sh
# Build script for claif_cla package

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Please install it first:"
        echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# Create virtual environment if it doesn't exist
setup_venv() {
    if [[ ! -d ".venv" ]]; then
        log_info "Creating virtual environment..."
        uv venv --python 3.12
    fi
    
    log_info "Activating virtual environment..."
    source .venv/bin/activate
    
    log_info "Installing dependencies..."
    uv pip install ".[dev,test]"
}

# Run code quality checks
run_quality_checks() {
    log_info "Running code quality checks..."
    
    log_info "Running ruff format check..."
    if ! ruff format --check --respect-gitignore src/claif_cla tests; then
        log_error "Code formatting issues found. Run 'ruff format --respect-gitignore src/claif_cla tests' to fix."
        return 1
    fi
    
    log_info "Running ruff lint..."
    if ! ruff check src/claif_cla tests; then
        log_error "Linting issues found. Run 'ruff check --fix src/claif_cla tests' to fix."
        return 1
    fi
    
    log_info "Running mypy type checking..."
    if ! mypy src/claif_cla; then
        log_error "Type checking issues found."
        return 1
    fi
    
    log_success "All code quality checks passed!"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    # Run tests with coverage
    if ! python -m pytest tests/ --cov=src/claif_cla --cov-report=term-missing --cov-report=xml --cov-report=html; then
        log_error "Tests failed!"
        return 1
    fi
    
    log_success "All tests passed!"
}

# Build package
build_package() {
    log_info "Building package..."
    
    # Clean previous builds
    rm -rf dist/ build/ *.egg-info/
    
    # Build package
    if ! uv run python -m build --outdir dist; then
        log_error "Package build failed!"
        return 1
    fi
    
    log_success "Package built successfully!"
    
    # List built files
    log_info "Built files:"
    ls -la dist/
}

# Verify package
verify_package() {
    log_info "Verifying package..."
    
    # Check if both wheel and source distribution exist
    if [[ ! -f dist/*.whl ]]; then
        log_error "Wheel file not found!"
        return 1
    fi
    
    if [[ ! -f dist/*.tar.gz ]]; then
        log_error "Source distribution not found!"
        return 1
    fi
    
    # Test installation in temporary environment
    log_info "Testing package installation..."
    TEMP_DIR=$(mktemp -d)
    
    # Create temporary venv and test installation
    (
        cd "$TEMP_DIR"
        uv venv test_env
        source test_env/bin/activate
        
        # Install the built package
        uv pip install "$PROJECT_ROOT"/dist/*.whl
        
        # Test import
        python -c "import claif_cla; print(f'Successfully imported claif_cla version {claif_cla.__version__}')"
        
        # Test CLI
        python -m claif_cla.cli --help > /dev/null
    )
    
    # Clean up
    rm -rf "$TEMP_DIR"
    
    log_success "Package verification completed successfully!"
}

# Main function
main() {
    log_info "Starting claif_cla build process..."
    
    # Parse arguments
    SKIP_TESTS=false
    SKIP_QUALITY=false
    SKIP_VERIFY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-quality)
                SKIP_QUALITY=true
                shift
                ;;
            --skip-verify)
                SKIP_VERIFY=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-tests     Skip running tests"
                echo "  --skip-quality   Skip code quality checks"
                echo "  --skip-verify    Skip package verification"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run build pipeline
    check_uv
    setup_venv
    
    if [[ "$SKIP_QUALITY" == "false" ]]; then
        run_quality_checks
    fi
    
    if [[ "$SKIP_TESTS" == "false" ]]; then
        run_tests
    fi
    
    build_package
    
    if [[ "$SKIP_VERIFY" == "false" ]]; then
        verify_package
    fi
    
    log_success "Build process completed successfully!"
    
    # Show final information
    echo ""
    log_info "Build artifacts:"
    ls -la dist/
    echo ""
    log_info "Current version: $(python -c 'import claif_cla; print(claif_cla.__version__)')"
}

# Run main function
main "$@"
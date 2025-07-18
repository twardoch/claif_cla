#!/bin/bash
# this_file: scripts/test.sh
# Test script for claif_cla package

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

# Setup virtual environment
setup_venv() {
    if [[ ! -d ".venv" ]]; then
        log_info "Creating virtual environment..."
        uv venv --python 3.12
    fi
    
    log_info "Activating virtual environment..."
    source .venv/bin/activate
    
    log_info "Installing test dependencies..."
    uv pip install ".[test]"
}

# Run specific test categories
run_unit_tests() {
    log_info "Running unit tests..."
    python -m pytest tests/ -m "unit" -v --tb=short
}

run_integration_tests() {
    log_info "Running integration tests..."
    python -m pytest tests/ -m "integration" -v --tb=short
}

run_all_tests() {
    log_info "Running all tests..."
    python -m pytest tests/ -v --tb=short
}

# Run tests with coverage
run_tests_with_coverage() {
    log_info "Running tests with coverage..."
    python -m pytest tests/ \
        --cov=src/claif_cla \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-report=html \
        --cov-config=pyproject.toml \
        -v
}

# Run tests in parallel
run_tests_parallel() {
    log_info "Running tests in parallel..."
    python -m pytest tests/ -n auto -v --tb=short
}

# Run performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    python -m pytest tests/ -m "benchmark" --benchmark-only -v
}

# Run tests with specific markers
run_marked_tests() {
    local marker=$1
    log_info "Running tests with marker: $marker"
    python -m pytest tests/ -m "$marker" -v --tb=short
}

# Generate coverage report
generate_coverage_report() {
    log_info "Generating coverage report..."
    python -m pytest tests/ \
        --cov=src/claif_cla \
        --cov-report=html \
        --cov-report=term-missing \
        --cov-config=pyproject.toml \
        --quiet
    
    log_success "Coverage report generated in htmlcov/"
    
    # Show coverage summary
    coverage report --show-missing
}

# Watch mode for development
watch_tests() {
    log_info "Starting test watch mode..."
    log_info "Watching for changes in src/ and tests/ directories..."
    
    # Simple watch implementation
    while true; do
        # Get checksums of all Python files
        NEW_CHECKSUM=$(find src/ tests/ -name "*.py" -exec md5sum {} \; 2>/dev/null | md5sum)
        
        if [[ -z "${OLD_CHECKSUM:-}" ]] || [[ "$NEW_CHECKSUM" != "$OLD_CHECKSUM" ]]; then
            OLD_CHECKSUM=$NEW_CHECKSUM
            clear
            echo "$(date): Running tests..."
            python -m pytest tests/ --tb=short -q
        fi
        
        sleep 2
    done
}

# Main function
main() {
    log_info "Starting claif_cla test runner..."
    
    # Parse arguments
    TEST_TYPE="all"
    COVERAGE=false
    PARALLEL=false
    WATCH=false
    MARKER=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --unit)
                TEST_TYPE="unit"
                shift
                ;;
            --integration)
                TEST_TYPE="integration"
                shift
                ;;
            --performance)
                TEST_TYPE="performance"
                shift
                ;;
            --coverage)
                COVERAGE=true
                shift
                ;;
            --parallel)
                PARALLEL=true
                shift
                ;;
            --watch)
                WATCH=true
                shift
                ;;
            --marker)
                MARKER="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --unit           Run only unit tests"
                echo "  --integration    Run only integration tests"
                echo "  --performance    Run only performance/benchmark tests"
                echo "  --coverage       Run tests with coverage report"
                echo "  --parallel       Run tests in parallel"
                echo "  --watch          Watch for changes and re-run tests"
                echo "  --marker MARKER  Run tests with specific marker"
                echo "  -h, --help       Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                          # Run all tests"
                echo "  $0 --unit --coverage        # Run unit tests with coverage"
                echo "  $0 --parallel               # Run all tests in parallel"
                echo "  $0 --marker slow           # Run tests marked as 'slow'"
                echo "  $0 --watch                 # Watch mode for development"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Setup environment
    check_uv
    setup_venv
    
    # Run tests based on options
    if [[ "$WATCH" == "true" ]]; then
        watch_tests
    elif [[ -n "$MARKER" ]]; then
        run_marked_tests "$MARKER"
    elif [[ "$COVERAGE" == "true" ]]; then
        run_tests_with_coverage
    elif [[ "$PARALLEL" == "true" ]]; then
        run_tests_parallel
    else
        case $TEST_TYPE in
            unit)
                run_unit_tests
                ;;
            integration)
                run_integration_tests
                ;;
            performance)
                run_performance_tests
                ;;
            all)
                run_all_tests
                ;;
            *)
                log_error "Unknown test type: $TEST_TYPE"
                exit 1
                ;;
        esac
    fi
    
    log_success "Test execution completed!"
}

# Run main function
main "$@"
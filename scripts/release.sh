#!/bin/bash
# this_file: scripts/release.sh
# Release script for claif_cla package

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

# Check if git is clean
check_git_clean() {
    if [[ -n "$(git status --porcelain)" ]]; then
        log_error "Git working directory is not clean. Please commit or stash changes first."
        git status
        exit 1
    fi
}

# Check if on main branch
check_main_branch() {
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ "$current_branch" != "main" ]]; then
        log_error "You must be on the main branch to create a release. Current branch: $current_branch"
        exit 1
    fi
}

# Get current version
get_current_version() {
    python -c "import claif_cla; print(claif_cla.__version__)" 2>/dev/null || echo "unknown"
}

# Validate version format
validate_version() {
    local version=$1
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $version. Expected format: X.Y.Z"
        exit 1
    fi
}

# Check if tag exists
check_tag_exists() {
    local tag=$1
    if git tag -l | grep -q "^$tag$"; then
        log_error "Tag $tag already exists!"
        exit 1
    fi
}

# Run pre-release checks
run_pre_release_checks() {
    log_info "Running pre-release checks..."
    
    # Run build script with all checks
    if ! "$SCRIPT_DIR/build.sh"; then
        log_error "Build script failed!"
        exit 1
    fi
    
    log_success "Pre-release checks passed!"
}

# Create git tag
create_git_tag() {
    local version=$1
    local tag="v$version"
    
    log_info "Creating git tag: $tag"
    
    # Create annotated tag
    git tag -a "$tag" -m "Release version $version"
    
    log_success "Git tag created: $tag"
    
    # Show tag info
    git show "$tag" --no-patch
}

# Push tag to remote
push_tag() {
    local version=$1
    local tag="v$version"
    
    log_info "Pushing tag to remote..."
    
    # Push tag to origin
    git push origin "$tag"
    
    log_success "Tag pushed to remote: $tag"
}

# Create release
create_release() {
    local version=$1
    local tag="v$version"
    
    log_info "Creating release for version: $version"
    
    # Pre-release checks
    check_git_clean
    check_main_branch
    validate_version "$version"
    check_tag_exists "$tag"
    
    # Run tests and build
    run_pre_release_checks
    
    # Create and push tag
    create_git_tag "$version"
    push_tag "$version"
    
    log_success "Release $version created successfully!"
    log_info "GitHub Actions will now build and publish the package to PyPI."
    log_info "You can monitor the release at: https://github.com/twardoch/claif_cla/actions"
}

# Show next version suggestion
suggest_next_version() {
    local current_version=$(get_current_version)
    
    if [[ "$current_version" == "unknown" ]]; then
        log_warning "Could not determine current version"
        return
    fi
    
    log_info "Current version: $current_version"
    
    # Parse current version
    if [[ "$current_version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
        local major="${BASH_REMATCH[1]}"
        local minor="${BASH_REMATCH[2]}"
        local patch="${BASH_REMATCH[3]}"
        
        echo "Suggested next versions:"
        echo "  Patch: $major.$minor.$((patch + 1))"
        echo "  Minor: $major.$((minor + 1)).0"
        echo "  Major: $((major + 1)).0.0"
    fi
}

# List recent tags
list_recent_tags() {
    log_info "Recent tags:"
    git tag -l --sort=-version:refname | head -10
}

# Main function
main() {
    log_info "claif_cla release script"
    
    # Parse arguments
    if [[ $# -eq 0 ]]; then
        echo "Usage: $0 [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  release VERSION    Create a new release with the specified version"
        echo "  suggest           Show suggested next version"
        echo "  tags              List recent tags"
        echo "  check             Run pre-release checks without creating release"
        echo ""
        echo "Examples:"
        echo "  $0 release 1.0.30  # Create release v1.0.30"
        echo "  $0 suggest         # Show version suggestions"
        echo "  $0 check           # Run pre-release checks"
        exit 0
    fi
    
    case $1 in
        release)
            if [[ $# -ne 2 ]]; then
                log_error "Usage: $0 release VERSION"
                exit 1
            fi
            create_release "$2"
            ;;
        suggest)
            suggest_next_version
            ;;
        tags)
            list_recent_tags
            ;;
        check)
            run_pre_release_checks
            ;;
        -h|--help)
            main
            ;;
        *)
            log_error "Unknown command: $1"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
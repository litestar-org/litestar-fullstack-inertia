#!/usr/bin/env bash
# =============================================================================
# Railway Deployment Script
# =============================================================================
# This script handles deployment of the Litestar Fullstack Inertia application
# to Railway, including database migrations.
#
# Prerequisites:
#   - Railway CLI installed and authenticated
#   - Project initialized with ./setup.sh
#
# Usage:
#   ./deploy.sh [--detach]
#
# Options:
#   --detach          Don't wait for deployment to complete
#
# Note: Migrations run automatically via preDeployCommand in railway.json
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DETACH=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case $1 in
        --detach)
            DETACH=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check Railway CLI
    if ! check_command railway; then
        log_error "Railway CLI not installed. Run ./setup.sh first."
        exit 1
    fi

    # Check authentication
    if ! railway whoami &> /dev/null; then
        log_error "Not authenticated with Railway. Run 'railway login'."
        exit 1
    fi

    # Check if project is linked by running railway status
    cd "${PROJECT_ROOT}"
    if ! railway status &> /dev/null; then
        log_error "Project not linked. Run ./setup.sh first or 'railway link'."
        exit 1
    fi

    # Verify railway.json exists
    if [ ! -f "${PROJECT_ROOT}/railway.json" ]; then
        log_error "railway.json not found in project root."
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

# -----------------------------------------------------------------------------
# Build Verification
# -----------------------------------------------------------------------------

verify_build() {
    log_info "Verifying build configuration..."

    cd "${PROJECT_ROOT}"

    # Check Dockerfile exists
    if [ ! -f "tools/deploy/docker/Dockerfile.distroless" ]; then
        log_error "Dockerfile not found at tools/deploy/docker/Dockerfile.distroless"
        exit 1
    fi

    # Check package.json and pyproject.toml exist
    if [ ! -f "package.json" ]; then
        log_error "package.json not found"
        exit 1
    fi

    if [ ! -f "pyproject.toml" ]; then
        log_error "pyproject.toml not found"
        exit 1
    fi

    log_success "Build configuration verified"
}

# -----------------------------------------------------------------------------
# Enable Metal Builds
# -----------------------------------------------------------------------------

enable_metal_builds() {
    log_info "Enabling metal builds for faster Docker builds..."

    cd "${PROJECT_ROOT}"

    # Check if metal builds is already enabled
    if railway variables --kv 2>/dev/null | grep -q "RAILWAY_USE_METAL_BUILDS=true"; then
        log_success "Metal builds already enabled"
        return 0
    fi

    # Enable metal builds
    railway variables --set "RAILWAY_USE_METAL_BUILDS=true" --skip-deploys
    log_success "Metal builds enabled"
}

# -----------------------------------------------------------------------------
# Configure Port Variable
# -----------------------------------------------------------------------------

configure_port() {
    log_info "Configuring LITESTAR_PORT variable..."

    cd "${PROJECT_ROOT}"

    # Check if LITESTAR_PORT is already set
    if railway variables --kv 2>/dev/null | grep -q "LITESTAR_PORT="; then
        log_success "LITESTAR_PORT already configured"
        return 0
    fi

    # Set LITESTAR_PORT to reference Railway's PORT variable
    railway variables --set 'LITESTAR_PORT=${{PORT}}' --skip-deploys
    log_success "LITESTAR_PORT configured to use Railway's PORT"
}

# -----------------------------------------------------------------------------
# Deployment
# -----------------------------------------------------------------------------

deploy() {
    log_info "Starting deployment..."

    cd "${PROJECT_ROOT}"

    if [ "${DETACH}" = true ]; then
        railway up --detach
        log_success "Deployment started (detached mode)"
        log_info "Use 'railway logs' to monitor deployment"
    else
        railway up
        log_success "Deployment complete"
    fi
}

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------

health_check() {
    log_info "Checking deployment health..."

    cd "${PROJECT_ROOT}"

    # Get the deployment URL
    DEPLOY_URL=$(railway status --json 2>/dev/null | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

    if [ -z "${DEPLOY_URL}" ]; then
        log_warn "Could not determine deployment URL"
        log_info "Check Railway dashboard for deployment status"
        return 0
    fi

    # Wait a moment for the service to start
    sleep 5

    # Check health endpoint
    if curl -sf "${DEPLOY_URL}/health" > /dev/null 2>&1; then
        log_success "Health check passed: ${DEPLOY_URL}/health"
    else
        log_warn "Health check failed or pending. The service may still be starting."
        log_info "Check status: railway logs"
    fi
}

# -----------------------------------------------------------------------------
# Display Summary
# -----------------------------------------------------------------------------

display_summary() {
    cd "${PROJECT_ROOT}"

    echo ""
    echo "=============================================="
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "=============================================="
    echo ""
    echo "Useful commands:"
    echo "  railway open     - Open Railway dashboard"
    echo "  railway logs     - View application logs"
    echo "  railway status   - Check deployment status"
    echo "  railway run bash - SSH into container"
    echo ""
    echo "=============================================="
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    echo ""
    echo "=============================================="
    echo "Railway Deployment"
    echo "=============================================="
    echo ""

    preflight_checks
    verify_build
    enable_metal_builds
    configure_port
    deploy

    if [ "${DETACH}" = false ]; then
        health_check
    fi

    display_summary
}

main "$@"

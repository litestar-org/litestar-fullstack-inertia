#!/usr/bin/env bash
# =============================================================================
# Railway Project Setup Script
# =============================================================================
# This script automates the initial setup of a Railway project for the
# Litestar Fullstack Inertia application.
#
# Prerequisites:
#   - Railway account
#   - Node.js 18+ (for Railway CLI)
#
# Usage:
#   ./setup.sh
#
# The script will prompt for the project name interactively.
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
PROJECT_NAME=""

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
# Prompt for Project Name
# -----------------------------------------------------------------------------

prompt_project_name() {
    echo ""
    read -p "Enter project name [litestar-fullstack-demo]: " PROJECT_NAME
    PROJECT_NAME="${PROJECT_NAME:-litestar-fullstack-demo}"
    echo ""
}

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check for Node.js
    if ! check_command node; then
        log_error "Node.js is required but not installed."
        log_info "Install Node.js from https://nodejs.org/"
        exit 1
    fi

    # Check for npm
    if ! check_command npm; then
        log_error "npm is required but not installed."
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

# -----------------------------------------------------------------------------
# Railway CLI Installation
# -----------------------------------------------------------------------------

install_railway_cli() {
    if check_command railway; then
        log_info "Railway CLI already installed: $(railway --version)"
        return 0
    fi

    log_info "Installing Railway CLI..."
    npm install -g @railway/cli

    if check_command railway; then
        log_success "Railway CLI installed: $(railway --version)"
    else
        log_error "Failed to install Railway CLI"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Railway Authentication
# -----------------------------------------------------------------------------

authenticate_railway() {
    log_info "Checking Railway authentication..."

    if railway whoami &> /dev/null; then
        log_success "Already authenticated as: $(railway whoami)"
        return 0
    fi

    log_info "Please authenticate with Railway..."
    railway login

    if railway whoami &> /dev/null; then
        log_success "Authenticated as: $(railway whoami)"
    else
        log_error "Authentication failed"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Project Creation
# -----------------------------------------------------------------------------

create_project() {
    log_info "Creating Railway project: ${PROJECT_NAME}"

    cd "${PROJECT_ROOT}"

    # Check if Railway project is already linked
    if railway status &> /dev/null; then
        log_warn "Railway project already linked in this directory"
        read -p "Do you want to reinitialize? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping project creation"
            return 0
        fi
    fi

    # Create new project
    railway init --name "${PROJECT_NAME}"
    log_success "Project created: ${PROJECT_NAME}"
}

# -----------------------------------------------------------------------------
# Database Provisioning
# -----------------------------------------------------------------------------

provision_database() {
    log_info "Provisioning PostgreSQL database..."

    cd "${PROJECT_ROOT}"

    # Add PostgreSQL service
    railway add --database postgres

    log_success "PostgreSQL database provisioned"
    log_info "Database connection will be available via DATABASE_URL"
}

# -----------------------------------------------------------------------------
# Environment Variables
# -----------------------------------------------------------------------------

setup_environment() {
    log_info "Setting up environment variables..."

    cd "${PROJECT_ROOT}"

    # Generate a secure secret key
    SECRET_KEY=$(openssl rand -base64 32 | tr -d '=' | tr '+/' '-_')

    # Set essential variables
    # LITESTAR_PORT references Railway's injected PORT variable
    railway variables --set "SECRET_KEY=${SECRET_KEY}" \
        --set "LITESTAR_DEBUG=false" \
        --set "VITE_DEV_MODE=false" \
        --set "EMAIL_ENABLED=false" \
        --set "EMAIL_BACKEND=console" \
        --set 'LITESTAR_PORT=${{PORT}}'

    log_success "Environment variables configured"
    log_warn "Remember to configure Resend for email functionality"
    log_info "Use ./env-setup.sh --email to configure Resend"
}

# -----------------------------------------------------------------------------
# Create and Link App Service
# -----------------------------------------------------------------------------

link_services() {
    log_info "Creating application service..."

    cd "${PROJECT_ROOT}"

    # Create a new empty service for the app and link current directory
    railway add --service "app"
    railway service link app

    log_success "Application service created and linked"
}

# -----------------------------------------------------------------------------
# Display Summary
# -----------------------------------------------------------------------------

display_summary() {
    echo ""
    echo "=============================================="
    echo -e "${GREEN}Railway Setup Complete!${NC}"
    echo "=============================================="
    echo ""
    echo "Project: ${PROJECT_NAME}"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure SMTP for email (optional):"
    echo "     ./env-setup.sh"
    echo ""
    echo "  2. Deploy your application:"
    echo "     ./deploy.sh"
    echo ""
    echo "  3. Open Railway dashboard:"
    echo "     railway open"
    echo ""
    echo "  4. View logs:"
    echo "     railway logs"
    echo ""
    echo "=============================================="
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    echo ""
    echo "=============================================="
    echo "Railway Project Setup"
    echo "=============================================="

    preflight_checks
    install_railway_cli
    authenticate_railway
    prompt_project_name
    create_project
    provision_database
    link_services
    setup_environment
    display_summary
}

main "$@"

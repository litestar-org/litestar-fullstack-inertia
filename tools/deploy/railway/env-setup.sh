#!/usr/bin/env bash
# =============================================================================
# Railway Environment Configuration Script
# =============================================================================
# This script helps configure environment variables for the Railway deployment,
# including Resend settings for email functionality.
#
# Prerequisites:
#   - Railway CLI installed and authenticated
#   - Project initialized with ./setup.sh
#
# Usage:
#   ./env-setup.sh [--email] [--from-file .env.railway]
#
# Options:
#   --email          Configure Resend email settings interactively
#   --from-file      Load variables from an env file
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CONFIGURE_EMAIL=false
ENV_FILE=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case $1 in
        --email)
            CONFIGURE_EMAIL=true
            shift
            ;;
        --from-file)
            ENV_FILE="$2"
            shift 2
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

# -----------------------------------------------------------------------------
# Pre-flight Checks
# -----------------------------------------------------------------------------

preflight_checks() {
    log_info "Running pre-flight checks..."

    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not installed. Run ./setup.sh first."
        exit 1
    fi

    # Check authentication
    if ! railway whoami &> /dev/null; then
        log_error "Not authenticated with Railway. Run 'railway login'."
        exit 1
    fi

    log_success "Pre-flight checks passed"
}

# -----------------------------------------------------------------------------
# Load From File
# -----------------------------------------------------------------------------

load_from_file() {
    if [ -z "${ENV_FILE}" ]; then
        return 0
    fi

    if [ ! -f "${ENV_FILE}" ]; then
        log_error "Environment file not found: ${ENV_FILE}"
        exit 1
    fi

    log_info "Loading environment variables from: ${ENV_FILE}"

    cd "${PROJECT_ROOT}"

    # Read file and set variables
    while IFS='=' read -r key value || [ -n "$key" ]; do
        # Skip empty lines and comments
        [[ -z "$key" || "$key" =~ ^# ]] && continue

        # Remove quotes from value
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")

        # Skip if value is empty or a placeholder
        [[ -z "$value" || "$value" == "your-"* ]] && continue

        log_info "Setting: $key"
        railway variables --set "${key}=${value}"
    done < "${ENV_FILE}"

    log_success "Environment variables loaded from file"
}

# -----------------------------------------------------------------------------
# Resend Configuration
# -----------------------------------------------------------------------------

configure_email() {
    echo ""
    echo "=============================================="
    echo "Resend Email Configuration"
    echo "=============================================="
    echo ""
    log_info "Resend provides 3,000 emails/month on the free tier"
    log_info "Get your API key at: https://resend.com/api-keys"
    echo ""

    read -p "Enter Resend API key: " RESEND_API_KEY
    read -p "Enter 'From' email address (must be verified in Resend): " EMAIL_FROM

    log_info "Configuring Resend..."

    cd "${PROJECT_ROOT}"

    railway variables --set "EMAIL_ENABLED=true" \
        --set "EMAIL_BACKEND=resend" \
        --set "EMAIL_FROM=${EMAIL_FROM}" \
        --set "RESEND_API_KEY=${RESEND_API_KEY}"

    log_success "Resend configured successfully"
}

# -----------------------------------------------------------------------------
# Display Current Variables
# -----------------------------------------------------------------------------

display_variables() {
    echo ""
    echo "=============================================="
    echo "Current Environment Variables"
    echo "=============================================="

    cd "${PROJECT_ROOT}"

    railway variables

    echo ""
}

# -----------------------------------------------------------------------------
# Main Menu
# -----------------------------------------------------------------------------

main_menu() {
    echo ""
    echo "=============================================="
    echo "Railway Environment Configuration"
    echo "=============================================="
    echo ""
    echo "Options:"
    echo "  1. View current variables"
    echo "  2. Configure Resend for email"
    echo "  3. Set custom variable"
    echo "  4. Load from .env file"
    echo "  5. Exit"
    echo ""

    read -p "Select option (1-5): " choice

    cd "${PROJECT_ROOT}"

    case $choice in
        1)
            display_variables
            main_menu
            ;;
        2)
            configure_email
            main_menu
            ;;
        3)
            read -p "Variable name: " var_name
            read -p "Variable value: " var_value
            railway variables --set "${var_name}=${var_value}"
            log_success "Variable set: ${var_name}"
            main_menu
            ;;
        4)
            read -p "Path to .env file: " env_path
            ENV_FILE="${env_path}"
            load_from_file
            main_menu
            ;;
        5)
            log_info "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid selection"
            main_menu
            ;;
    esac
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    preflight_checks

    # If specific flags were passed, execute and exit
    if [ -n "${ENV_FILE}" ]; then
        load_from_file
        exit 0
    fi

    if [ "${CONFIGURE_EMAIL}" = true ]; then
        configure_email
        exit 0
    fi

    # Otherwise, show interactive menu
    main_menu
}

main "$@"

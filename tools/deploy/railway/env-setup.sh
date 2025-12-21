#!/usr/bin/env bash
# =============================================================================
# Railway Environment Configuration Script
# =============================================================================
# Helper script for configuring optional environment variables.
# For initial setup, use ./deploy.sh instead.
#
# Usage:
#   ./env-setup.sh                    # Interactive menu
#   ./env-setup.sh --email            # Configure Resend email
#   ./env-setup.sh --from-file .env   # Load variables from file
#   ./env-setup.sh --set KEY=VALUE    # Set a single variable
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
SET_VAR=""
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
        --set)
            SET_VAR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./env-setup.sh [--email] [--from-file .env] [--set KEY=VALUE]"
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
    # Check Railway CLI
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not installed. Run ./deploy.sh first."
        exit 1
    fi

    # Check authentication
    if ! railway whoami &> /dev/null; then
        log_error "Not authenticated with Railway. Run 'railway login'."
        exit 1
    fi

    # Check if project is linked
    cd "${PROJECT_ROOT}"
    if ! railway status &> /dev/null; then
        log_error "No Railway project linked. Run ./deploy.sh first."
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Load From File
# -----------------------------------------------------------------------------

load_from_file() {
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
        railway variables --set "${key}=${value}" --skip-deploys
    done < "${ENV_FILE}"

    log_success "Environment variables loaded from file"
}

# -----------------------------------------------------------------------------
# Email Configuration
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
    log_info "Redeploy to apply changes: ./deploy.sh"
}

# -----------------------------------------------------------------------------
# Set Single Variable
# -----------------------------------------------------------------------------

set_variable() {
    if [[ ! "${SET_VAR}" =~ = ]]; then
        log_error "Invalid format. Use: --set KEY=VALUE"
        exit 1
    fi

    cd "${PROJECT_ROOT}"
    railway variables --set "${SET_VAR}"
    log_success "Variable set: ${SET_VAR%%=*}"
}

# -----------------------------------------------------------------------------
# Display Variables
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
# Interactive Menu
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
            read -p "Variable (KEY=VALUE): " var_input
            railway variables --set "${var_input}"
            log_success "Variable set: ${var_input%%=*}"
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

    # Handle specific flags
    if [ -n "${ENV_FILE}" ]; then
        load_from_file
        exit 0
    fi

    if [ -n "${SET_VAR}" ]; then
        set_variable
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
